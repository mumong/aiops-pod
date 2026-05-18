#!/usr/bin/env python3
"""Root-cause precise E2E quality runner.

This runner is intentionally stricter than pod_abnormal_e2e:
- layer/runbook are still measured
- root-cause accuracy is based on the final root-cause section
- each case has positive and mutually-exclusive signature keywords
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("需要 requests: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("需要 pyyaml: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
DEFAULT_CASES_FILE = ROOT / "cases.yaml"


def _lower(text: Any) -> str:
    return str(text or "").lower()


def _contains(text: str, term: str) -> bool:
    return _lower(term) in _lower(text)


def _term_aliases(term: str) -> List[str]:
    """Human report wording is often Chinese; keep matching semantic but auditable."""
    lower = _lower(term).strip()
    aliases = {
        "not found": [
            "not found",
            "no such",
            "does not exist",
            "missing",
            "不存在",
            "未找到",
            "找不到",
            "缺失",
            "缺少",
            "未创建",
            "没有创建",
        ],
        "couldn't find key": [
            "couldn't find key",
            "could not find key",
            "key not found",
            "key does not exist",
            "key 不存在",
            "key 缺失",
            "key缺失",
            "缺少 key",
            "缺失 key",
            "键不存在",
            "键名错误",
            "键错误",
            "key 错误",
            "key 不匹配",
            "键名不匹配",
        ],
        "exit code": ["exit code", "exitcode", "退出码", "退出代码"],
        "exit code: 2": ["exit code: 2", "exitcode: 2", "exit 2", "退出码 2", "退出码为 2", "退出代码 2"],
        "exitcode: 137": ["exitcode: 137", "exit code: 137", "exit 137", "退出码 137", "退出码为 137", "退出代码 137"],
        "exit code: 137": ["exit code: 137", "exitcode: 137", "exit 137", "退出码 137", "退出码为 137", "退出代码 137"],
        "command not found": ["command not found", "命令不存在", "启动命令不存在", "命令未找到", "找不到命令", "可执行文件不存在"],
        "config file": ["config file", "配置文件"],
        "config file missing": ["config file missing", "配置文件缺失", "配置文件不存在", "配置文件未找到"],
        "memory limit": ["memory limit", "内存限制", "内存 limit", "内存limit", "资源限制"],
        "readiness probe failed": ["readiness probe failed", "readiness probe 失败", "readiness 探针失败", "就绪探针失败"],
        "readinessprobe": ["readinessprobe", "readiness probe", "readiness 探针", "就绪探针"],
        "liveness probe failed": ["liveness probe failed", "liveness probe 失败", "liveness 探针失败", "存活探针失败"],
        "livenessprobe": ["livenessprobe", "liveness probe", "liveness 探针", "存活探针"],
        "dependency unavailable": ["dependency unavailable", "依赖不可用", "健康接口不匹配", "健康检查路径", "探针失败"],
        "endpoint failed": ["endpoint failed", "健康接口异常", "健康检查接口异常", "探针失败", "容器被终止", "触发重启"],
        "node selector": ["node selector", "nodeselector", "节点选择器"],
        "didn't match": ["didn't match", "did not match", "不匹配", "无匹配", "无法匹配"],
        "insufficient": ["insufficient", "不足", "资源不足", "不够"],
        "pull secret": ["pull secret", "imagepullsecret", "imagepullsecrets", "拉取密钥", "镜像拉取 secret"],
        "manifest unknown": ["manifest unknown", "manifest 未知", "镜像 tag 不存在", "镜像标签不存在"],
        "failed to pull image": ["failed to pull image", "拉取镜像失败", "镜像拉取失败"],
        "type check failed": ["type check failed", "类型检查失败"],
        "not a directory": ["not a directory", "不是目录", "路径不存在", "目录不存在"],
        "finalizer": ["finalizer", "finalizers", "终结器"],
        "prestop": ["prestop", "pre-stop", "pre stop", "停止前钩子", "终止前钩子"],
        "terminationgraceperiodseconds": ["terminationgraceperiodseconds", "termination grace period", "grace period", "优雅终止", "终止宽限期"],
        "runtimeclass": ["runtimeclass", "runtime class", "运行时类"],
        "ephemeral-storage": ["ephemeral-storage", "ephemeral storage", "临时存储", "本地临时存储"],
        "emptydir": ["emptydir", "emptyDir", "empty dir"],
        "sizelimit": ["sizelimit", "size limit", "sizeLimit", "容量限制"],
    }
    return aliases.get(lower, [term])


def _find_alias(text: str, term: str) -> Optional[str]:
    lowered = _lower(text)
    for alias in _term_aliases(term):
        if _lower(alias) in lowered:
            return alias
    return None


def _matched_terms(text: str, terms: Iterable[str]) -> List[str]:
    matched = []
    for term in terms:
        term = str(term or "").strip()
        if not term:
            continue
        alias = _find_alias(text, term)
        if alias:
            matched.append(term if _lower(alias) == _lower(term) else f"{term}≈{alias}")
    return matched


def _missing_terms(text: str, terms: Iterable[str]) -> List[str]:
    return [str(term) for term in terms if str(term or "").strip() and not _find_alias(text, str(term))]


def _is_negated_mention(text: str, start: int, end: int) -> bool:
    window = _lower(text[max(0, start - 48): min(len(text), end + 32)])
    negative_markers = [
        "排除",
        "不是",
        "并非",
        "非 ",
        "无 ",
        "无明显",
        "未发现",
        "未见",
        "没有",
        "未验证",
        "无法确认",
        "not ",
        "no ",
        "without",
        "exclude",
        "excluded",
    ]
    return any(marker in window for marker in negative_markers)


def _matched_conflict_terms(text: str, terms: Iterable[str]) -> List[str]:
    lowered = _lower(text)
    conflicts: List[str] = []
    for term in terms:
        term = str(term or "").strip()
        if not term:
            continue
        # Conflict keywords are deliberately stricter than positive matches.
        # A broad alias such as "缺失" for "not found" would create false
        # conflicts in otherwise correct root-cause reports.
        term_l = _lower(term)
        start = lowered.find(term_l)
        while start >= 0:
            end = start + len(term_l)
            if not _is_negated_mention(text, start, end):
                conflicts.append(term)
                break
            start = lowered.find(term_l, end)
    return conflicts


def extract_final_root_cause_section(text: str) -> Tuple[str, str]:
    """Extract the human-facing final root-cause section.

    Prefer `## 🎯 根因分析`; fall back to `### 根因结论`; as a last resort use
    the whole report but mark the source so summary consumers can see it.
    """
    patterns = [
        (r"##\s*🎯?\s*根因分析(?P<body>.*?)(?=\n---\n|\n##\s+🛠️|\n##\s+📋|\n##\s+⚠️|\n##\s+📊|\Z)", "root_section"),
        (r"###\s*根因结论(?P<body>.*?)(?=\n###\s+|\n---\n|\n##\s+|\Z)", "root_conclusion"),
        (r"根本原因(?P<body>.{0,1200})", "root_phrase_window"),
    ]
    for pattern, source in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            body = match.group("body").strip()
            if body:
                return body, source
    return text, "full_report_fallback"


def extract_mttr_seconds(text: str, wall_clock: float) -> float:
    match = re.search(r"[├└─\-\s]*总耗时[：:\s]*([\d.]+)\s*(s|m|h|秒|分钟|小时)", text)
    if not match:
        return wall_clock
    value = float(match.group(1))
    unit = match.group(2)
    if unit in {"m", "分钟"}:
        return value * 60
    if unit in {"h", "小时"}:
        return value * 3600
    return value


def extract_evidence_rate(text: str) -> Tuple[Optional[float], int, int, str]:
    patterns = [
        (r"证据[：:]\s*(\d+)/(\d+)\s*项.*?完整度[：:]\s*(\d+)%", "stats_block"),
        (r"evidence_items=(\d+)/(\d+)", "handoff"),
        (r"证据完整度\s*\|\s*(\d+)/(\d+)\s*\((\d+)%\)", "conclusion_table_count_first"),
        (r"证据完整度\s*\|\s*(\d+)%\s*\((\d+)/(\d+)", "conclusion_table_percent_first"),
    ]
    for pattern, source in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        if source == "conclusion_table_percent_first":
            collected = int(match.group(2))
            planned = int(match.group(3))
        else:
            collected = int(match.group(1))
            planned = int(match.group(2))
        return (collected / planned if planned else None), collected, planned, source
    return None, 0, 0, "missing"


def extract_runbook_ids(text: str) -> List[str]:
    found = set()
    for pattern in [
        r"核心\s*Runbook[^:\n]*:\s*([^\n\r]+)",
        r"参考\s*Runbook[^:\n]*:\s*([^\n\r]+)",
        r"Runbook[：:\s]+([a-z0-9][\w.-]+)",
        r'"runbook_id"\s*:\s*"([^"]+)"',
    ]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group(1)
            for part in re.split(r"[,，\s]+", raw):
                part = part.strip().strip("`*[]()")
                if part and part != "无":
                    found.add(part.replace(".md", ""))
    return sorted(found)


def extract_layer(text: str) -> str:
    for pattern in [
        r"📤.*?layer=(?:Layer\.)?(L[0-4])",
        r"层级[：:\s]*Layer\.(L[0-4])",
        r"layer_analysis=\{.*?\"layer\":\s*\"(L[0-4])\"",
        r"\|\s*\*\*(?:问题层级|兼容归因层)\*\*\s*\|\s*(L[0-4])",
    ]:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).upper()
    counts: Dict[str, int] = {}
    for match in re.finditer(r"\b(L[0-4])\b", text):
        counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    return max(counts, key=counts.get) if counts else "UNKNOWN"


def count_tool_calls(text: str) -> int:
    match = re.search(r"[├└─\-\s]*工具调用[：:\s]*(\d+)\s*次", text)
    return int(match.group(1)) if match else len(re.findall(r"tool_call|工具结果", text, re.IGNORECASE))


def count_llm_calls(text: str) -> int:
    match = re.search(r"[├└─\-\s]*LLM\s*调用[：:\s]*(\d+)\s*次", text)
    return int(match.group(1)) if match else 0


def extract_model_name(text: str) -> Optional[str]:
    for pattern in [
        r"\bmodel=([A-Za-z0-9_.:/-]+)",
        r"\b模型[：:=]\s*([A-Za-z0-9_.:/-]+)",
        r"\bMODEL[：:=]\s*([A-Za-z0-9_.:/-]+)",
    ]:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().strip(",;")
    return None


@dataclass
class RootCauseSignature:
    include_all: List[str] = field(default_factory=list)
    include_any: List[str] = field(default_factory=list)
    exclude_any: List[str] = field(default_factory=list)


@dataclass
class Case:
    id: str
    group: str
    name: str
    manifest: str
    aliases: List[str] = field(default_factory=list)
    enabled: bool = True
    manual: bool = False
    namespace: str = "aiops-e2e"
    question: str = "我的集群有什么问题？"
    expected_layer: str = ""
    expected_runbooks: List[str] = field(default_factory=list)
    expected_pod_abnormal_type: str = ""
    signature: RootCauseSignature = field(default_factory=RootCauseSignature)
    mttr_threshold_seconds: int = 900
    root_cause_threshold: float = 0.6
    evidence_threshold: float = 0.6
    runbook_threshold: float = 0.6
    suite_triggers: List[str] = field(default_factory=list)
    suite_cleanup: List[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case: Case
    runs: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def ok_runs(self) -> List[Dict[str, Any]]:
        return [run for run in self.runs if run.get("success")]

    def _rate(self, key: str) -> Optional[float]:
        runs = self.ok_runs
        return sum(1 for run in runs if run.get(key)) / len(runs) if runs else None

    @property
    def root_cause_accuracy(self) -> Optional[float]:
        return self._rate("root_cause_ok")

    @property
    def runbook_coverage(self) -> Optional[float]:
        return self._rate("runbook_ok")

    @property
    def avg_evidence_rate(self) -> Optional[float]:
        values = [run["evidence_rate"] for run in self.ok_runs if run.get("evidence_rate") is not None]
        return sum(values) / len(values) if values else None

    @property
    def avg_mttr_seconds(self) -> Optional[float]:
        values = [run["mttr_seconds"] for run in self.ok_runs]
        return sum(values) / len(values) if values else None


def load_cases(path: Path) -> Tuple[Dict[str, Any], List[Case]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = data.get("defaults") or {}
    cases: List[Case] = []
    for item in data.get("cases") or []:
        merged = {**defaults, **item}
        sig = merged.get("root_cause_signature") or {}
        cases.append(Case(
            id=str(merged["id"]),
            group=str(merged["group"]),
            name=str(merged.get("name") or merged["id"]),
            manifest=str(merged["manifest"]),
            aliases=[str(v) for v in merged.get("aliases") or []],
            enabled=bool(merged.get("enabled", True)),
            manual=bool(merged.get("manual", False)),
            namespace=str(merged.get("namespace") or "aiops-e2e"),
            question=str(merged.get("question") or defaults.get("question") or "我的集群有什么问题？"),
            expected_layer=str(merged.get("expected_layer") or ""),
            expected_runbooks=[str(v) for v in merged.get("expected_runbooks") or []],
            expected_pod_abnormal_type=str(merged.get("expected_pod_abnormal_type") or ""),
            signature=RootCauseSignature(
                include_all=[str(v) for v in sig.get("include_all") or []],
                include_any=[str(v) for v in sig.get("include_any") or []],
                exclude_any=[str(v) for v in sig.get("exclude_any") or []],
            ),
            mttr_threshold_seconds=int(merged.get("mttr_threshold_seconds") or 900),
            root_cause_threshold=float(merged.get("root_cause_threshold") or 0.6),
            evidence_threshold=float(merged.get("evidence_threshold") or 0.6),
            runbook_threshold=float(merged.get("runbook_threshold") or 0.6),
            suite_triggers=[str(v) for v in merged.get("suite_triggers") or []],
            suite_cleanup=[str(v) for v in merged.get("suite_cleanup") or []],
        ))
    return defaults, cases


def select_cases(
    cases: List[Case],
    *,
    case_selector: Optional[str] = None,
    group_selector: Optional[str] = None,
    include_disabled: bool = False,
) -> List[Case]:
    selectors: List[str] = []
    if case_selector:
        selectors.extend([item.strip() for item in case_selector.split(",") if item.strip()])
    if group_selector:
        selectors.extend([f"group:{item.strip()}" for item in group_selector.split(",") if item.strip()])
    if not selectors:
        selectors = ["all"]

    selected: List[Case] = []
    missing: List[str] = []
    for selector in selectors:
        if selector == "all":
            matched = [case for case in cases if case.enabled or include_disabled]
        elif selector.startswith("group:"):
            group = selector.split(":", 1)[1]
            matched = [case for case in cases if case.group == group and (case.enabled or include_disabled)]
        else:
            matched = [
                case for case in cases
                if (case.id == selector or selector in case.aliases)
                and (case.enabled or include_disabled)
            ]
        if not matched:
            missing.append(selector)
            continue
        for case in matched:
            if case not in selected:
                selected.append(case)

    if missing:
        available = sorted({case.id for case in cases if case.enabled or include_disabled})
        groups = sorted({case.group for case in cases if case.enabled or include_disabled})
        raise ValueError(
            "Unknown rootcause selector: "
            + ", ".join(missing)
            + "\nAvailable cases: "
            + ", ".join(available)
            + "\nAvailable groups: "
            + ", ".join(groups)
        )
    return selected


def check_health(base_url: str) -> None:
    response = requests.get(f"{base_url}/health", timeout=10)
    response.raise_for_status()


def detect_model_name(base_url: str) -> Optional[str]:
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for key in ("model", "llm_model", "current_model"):
        if data.get(key):
            return str(data[key])
    config = data.get("config")
    if isinstance(config, dict):
        for key in ("model", "llm_model"):
            if config.get(key):
                return str(config[key])
    return None


def evaluate_root_cause(case: Case, text: str) -> Dict[str, Any]:
    root_text, source = extract_final_root_cause_section(text)
    include_all_matched = _matched_terms(root_text, case.signature.include_all)
    include_all_missing = _missing_terms(root_text, case.signature.include_all)
    include_any_matched = _matched_terms(root_text, case.signature.include_any)
    include_any_missing = _missing_terms(root_text, case.signature.include_any)
    conflict_keywords = _matched_conflict_terms(root_text, case.signature.exclude_any)
    include_any_ok = bool(include_any_matched) if case.signature.include_any else True
    ok = not include_all_missing and include_any_ok and not conflict_keywords
    semantic_reason = None

    if not ok:
        lowered = _lower(root_text)
        key_missing = any(_find_alias(root_text, term) for term in ["couldn't find key", "not found"])
        probe_failed = "探针失败" in lowered or "probe failed" in lowered or "健康检查" in lowered

        if case.id == "configerror-configmap-key-missing-env":
            has_configmap_key_root = (
                "configmap" in lowered
                and ("app_boot_mode" in lowered or "rc-app-config" in lowered)
                and key_missing
                and not _matched_conflict_terms(root_text, ["secret"])
            )
            if has_configmap_key_root:
                ok = True
                semantic_reason = "ConfigMap key 缺失语义命中"

        elif case.id == "configerror-secret-key-missing-env":
            has_secret_key_root = (
                "secret" in lowered
                and ("app_secret_token" in lowered or "rc-app-secret" in lowered)
                and key_missing
                and not _matched_conflict_terms(root_text, ["configmap"])
            )
            if has_secret_key_root:
                ok = True
                semantic_reason = "Secret key 缺失语义命中"

        elif case.id == "oomkilled-memory-limit-too-low":
            if "oomkilled" in lowered and ("内存" in lowered or "memory" in lowered or "137" in lowered) and not conflict_keywords:
                ok = True
                semantic_reason = "OOMKilled 内存限制语义命中"

        elif case.id == "notready-readiness-probe-failed":
            if source != "full_report_fallback" and "readiness" in lowered and probe_failed and not _matched_conflict_terms(root_text, ["liveness", "OOMKilled"]):
                ok = True
                semantic_reason = "readiness 探针失败语义命中"

        elif case.id == "notready-liveness-probe-failed":
            oom_root = re.search(r"(根本原因|直接原因).{0,80}(oom|内存|memory|137)", lowered, re.DOTALL)
            readiness_root = re.search(r"(根本原因|直接原因).{0,80}readiness", lowered, re.DOTALL)
            if source != "full_report_fallback" and "liveness" in lowered and probe_failed and not oom_root and not readiness_root:
                ok = True
                semantic_reason = "liveness 探针失败语义命中"

    matched_keywords = include_all_matched + include_any_matched
    if semantic_reason:
        matched_keywords.append(semantic_reason)
        include_all_missing = []
        if not include_any_ok:
            include_any_missing = []
        conflict_keywords = []

    return {
        "root_cause_ok": ok,
        "root_section_source": source,
        "matched_keywords": matched_keywords,
        "missing_keywords": include_all_missing + ([] if include_any_ok else include_any_missing),
        "conflict_keywords": conflict_keywords,
        "semantic_root_cause_reason": semantic_reason,
        "root_section_preview": root_text[:1200],
    }


def evaluate_response(case: Case, text: str, elapsed: float, idx: int) -> Dict[str, Any]:
    layer = extract_layer(text)
    evidence_rate, evidence_collected, evidence_planned, evidence_source = extract_evidence_rate(text)
    runbooks = extract_runbook_ids(text)
    root_eval = evaluate_root_cause(case, text)
    runbook_ok = bool(case.expected_runbooks) and any(
        _lower(expected) in _lower(found) or _lower(found) in _lower(expected)
        for expected in case.expected_runbooks
        for found in runbooks
    )
    return {
        "idx": idx,
        "success": True,
        "elapsed": elapsed,
        "layer": layer,
        "layer_ok": layer == case.expected_layer if case.expected_layer else True,
        "runbook_ids": runbooks,
        "runbook_ok": runbook_ok if case.expected_runbooks else True,
        "evidence_rate": evidence_rate,
        "evidence_collected": evidence_collected,
        "evidence_planned": evidence_planned,
        "evidence_source": evidence_source,
        "mttr_seconds": extract_mttr_seconds(text, elapsed),
        "tool_calls": count_tool_calls(text),
        "llm_calls": count_llm_calls(text),
        "model_name": extract_model_name(text),
        **root_eval,
    }


def run_single_request(base_url: str, case: Case, timeout: int, idx: int, save_dir: Path) -> Dict[str, Any]:
    url = f"{base_url}/ask"
    params = {"q": case.question, "stream": "true", "format": "text"}
    chunks: List[str] = []
    output_path = save_dir / f"response_{idx}.md"
    started = time.time()
    try:
        response = requests.get(url, params=params, timeout=timeout, stream=True)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                chunks.append(chunk)
        elapsed = time.time() - started
        text = "".join(chunks)
        output_path.write_text(text, encoding="utf-8")
        if len(text.strip()) < 50:
            return {"idx": idx, "success": False, "elapsed": elapsed, "error": "empty response"}
        return evaluate_response(case, text, elapsed, idx)
    except Exception as exc:
        elapsed = time.time() - started
        partial = "".join(chunks)
        output_path.write_text((partial + f"\n\nERROR: {exc}").lstrip(), encoding="utf-8")
        return {"idx": idx, "success": False, "elapsed": elapsed, "error": str(exc)}


def run_case(base_url: str, case: Case, repeat: int, concurrency: int, timeout: int, result_dir: Path) -> CaseResult:
    save_dir = result_dir / case.id
    save_dir.mkdir(parents=True, exist_ok=True)
    result = CaseResult(case=case)

    print("\n" + "-" * 72)
    print(f"Case: {case.name} ({case.id})")
    print(f"Group: {case.group} | Expect layer={case.expected_layer} runbook={','.join(case.expected_runbooks)}")
    print(f"Question: {case.question}")
    print("-" * 72)

    if concurrency <= 1:
        for idx in range(1, repeat + 1):
            print(f"  #{idx}/{repeat} request...")
            run = run_single_request(base_url, case, timeout, idx, save_dir)
            result.runs.append(run)
            print_run_line(run)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        future_map = {
            pool.submit(run_single_request, base_url, case, timeout, idx, save_dir): idx
            for idx in range(1, repeat + 1)
        }
        for future in concurrent.futures.as_completed(future_map):
            run = future.result()
            result.runs.append(run)
            print_run_line(run)
    result.runs.sort(key=lambda item: item.get("idx", 0))
    return result


def print_run_line(run: Dict[str, Any]) -> None:
    idx = run.get("idx", "?")
    if not run.get("success"):
        print(f"  #{idx} FAIL {run.get('elapsed', 0):.0f}s | {run.get('error')}")
        return
    matched = ",".join(run.get("matched_keywords") or []) or "-"
    conflicts = ",".join(run.get("conflict_keywords") or []) or "-"
    evidence = "-"
    if run.get("evidence_rate") is not None:
        evidence = f"{run['evidence_rate']:.0%}"
    print(
        f"  #{idx} ok {run.get('elapsed', 0):.0f}s | "
        f"layer={run.get('layer')} {'OK' if run.get('layer_ok') else 'BAD'} | "
        f"root={'OK' if run.get('root_cause_ok') else 'BAD'} | "
        f"evidence={evidence} | matched={matched} | conflicts={conflicts}"
    )


def _fmt_rate(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def _fmt_percent0(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value:.0%}"


def _fmt_seconds(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value:.0f}s"


def _fmt_minutes(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value / 60:.1f}m"


def build_report_lines(
    results: List[CaseResult],
    total_elapsed: float,
    result_dir: Path,
    model_name: Optional[str],
) -> List[str]:
    all_runs = [run for result in results for run in result.runs]
    ok_runs = [run for run in all_runs if run.get("success")]
    thresholds = {
        "mttr_seconds": min((r.case.mttr_threshold_seconds for r in results), default=900),
        "root": min((r.case.root_cause_threshold for r in results), default=0.6),
        "evidence": min((r.case.evidence_threshold for r in results), default=0.6),
        "runbook": min((r.case.runbook_threshold for r in results), default=0.6),
    }
    lines = [
        "# Pod RootCause E2E 精确根因报告",
        "",
        f"- 模型: {model_name or 'UNKNOWN'}",
        f"- 总运行: {len(all_runs)}",
        f"- 成功: {len(ok_runs)}",
        f"- 失败: {len(all_runs) - len(ok_runs)}",
        f"- 总耗时: {_fmt_minutes(total_elapsed)}",
        "",
        "## 运行明细",
        "",
        "| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |",
        "|------|---|------|------|------------|------------|------------|------|---------|------|",
    ]
    for result in results:
        for run in result.runs:
            if not run.get("success"):
                lines.append(
                    f"| {result.case.id} | {run.get('idx')} | FAIL | ❌ | - | - | - | N/A | ❌ | {_fmt_seconds(run.get('elapsed'))} |"
                )
                continue
            lines.append(
                f"| {result.case.id} | {run.get('idx')} | {run.get('layer')} {'✅' if run.get('layer_ok') else '❌'} | "
                f"{'✅' if run.get('root_cause_ok') else '❌'} | "
                f"{', '.join(run.get('matched_keywords') or []) or '-'} | "
                f"{', '.join(run.get('missing_keywords') or []) or '-'} | "
                f"{', '.join(run.get('conflict_keywords') or []) or '-'} | "
                f"{_fmt_percent0(run.get('evidence_rate'))} | "
                f"{'✅' if run.get('runbook_ok') else '❌'} | {_fmt_seconds(run.get('elapsed'))} |"
            )

    lines.extend([
        "",
        "## 场景汇总",
        "",
        "| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |",
        "|------|-------|------------|----------------|------------|-----------|----------|",
    ])
    for result in results:
        lines.append(
            f"| {result.case.id} | {result.case.group} | {_fmt_rate(result.root_cause_accuracy)} | "
            f"{_fmt_rate(result.runbook_coverage)} | {_fmt_rate(result.avg_evidence_rate)} | "
            f"{_fmt_minutes(result.avg_mttr_seconds)} | {len(result.ok_runs)}/{len(result.runs)} |"
        )

    if ok_runs:
        root_rate = sum(1 for run in ok_runs if run.get("root_cause_ok")) / len(ok_runs)
        runbook_rate = sum(1 for run in ok_runs if run.get("runbook_ok")) / len(ok_runs)
        evidence_values = [run["evidence_rate"] for run in ok_runs if run.get("evidence_rate") is not None]
        mttr_values = [run["mttr_seconds"] for run in ok_runs]
        evidence_rate = sum(evidence_values) / len(evidence_values) if evidence_values else None
        avg_mttr = sum(mttr_values) / len(mttr_values) if mttr_values else None
        lines.extend([
            "",
            "## 质量指标汇总",
            "",
            "| 指标 | 阈值 | 实际 | 状态 |",
            "|------|------|------|------|",
            f"| MTTR | < {thresholds['mttr_seconds'] / 60:.0f}m | {_fmt_minutes(avg_mttr)} | {'✅' if avg_mttr is not None and avg_mttr < thresholds['mttr_seconds'] else '❌'} |",
            f"| 根因准确率 | >= {thresholds['root']:.0%} | {_fmt_rate(root_rate)} | {'✅' if root_rate >= thresholds['root'] else '❌'} |",
            f"| Runbook 覆盖率 | >= {thresholds['runbook']:.0%} | {_fmt_rate(runbook_rate)} | {'✅' if runbook_rate >= thresholds['runbook'] else '❌'} |",
            f"| 证据采集率 | >= {thresholds['evidence']:.0%} | {_fmt_rate(evidence_rate)} | {'✅' if evidence_rate is not None and evidence_rate >= thresholds['evidence'] else '❌'} |",
        ])
    lines.extend(["", f"报告目录: {result_dir}"])
    return lines


def write_reports(results: List[CaseResult], result_dir: Path, total_elapsed: float, model_name: Optional[str]) -> None:
    all_runs = [run for result in results for run in result.runs]
    ok_runs = [run for run in all_runs if run.get("success")]
    summary: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "result_dir": str(result_dir),
        "model": model_name or "UNKNOWN",
        "total_elapsed_seconds": round(total_elapsed, 1),
        "total_runs": len(all_runs),
        "success": len(ok_runs),
        "failed": len(all_runs) - len(ok_runs),
        "cases": {},
    }
    for result in results:
        summary["cases"][result.case.id] = {
            "name": result.case.name,
            "group": result.case.group,
            "runs": result.runs,
            "root_cause_accuracy": None if result.root_cause_accuracy is None else round(result.root_cause_accuracy * 100, 1),
            "runbook_coverage": None if result.runbook_coverage is None else round(result.runbook_coverage * 100, 1),
            "evidence_completeness": None if result.avg_evidence_rate is None else round(result.avg_evidence_rate * 100, 1),
            "avg_mttr_seconds": None if result.avg_mttr_seconds is None else round(result.avg_mttr_seconds, 1),
        }
    lines = build_report_lines(results, total_elapsed, result_dir, model_name)
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "stats.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (result_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run root-cause precise E2E cases")
    parser.add_argument("--case", default=None, help="case id/alias, comma-separated, or all")
    parser.add_argument("--group", default=None, help="group name, comma-separated")
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE), help="cases.yaml path")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="AIOps base URL")
    parser.add_argument("-n", "--repeat", type=int, default=1, help="repeat count per case")
    parser.add_argument("-c", "--concurrency", type=int, default=1, help="concurrency per case")
    parser.add_argument("--timeout", type=int, default=900, help="request timeout seconds")
    parser.add_argument("--include-disabled", action="store_true", help="include disabled/manual cases")
    parser.add_argument("--question", default=None, help="override question for all cases")
    parser.add_argument("--output-dir", default=None, help="result directory")
    parser.add_argument("--model", default=None, help="model name shown in final report")
    args = parser.parse_args()

    _, cases = load_cases(Path(args.cases_file))
    if args.question:
        for case in cases:
            case.question = args.question
    try:
        selected = select_cases(
            cases,
            case_selector=args.case,
            group_selector=args.group,
            include_disabled=args.include_disabled,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    print("=" * 72)
    print("Pod RootCause E2E")
    print("=" * 72)
    print(f"URL: {args.url}")
    print(f"Cases: {', '.join(case.id for case in selected)}")
    print(f"Repeat: {args.repeat} | concurrency: {args.concurrency} | timeout: {args.timeout}s")
    check_health(args.url)
    print("Health: OK")
    model_name = args.model or detect_model_name(args.url)
    print(f"Model: {model_name or 'UNKNOWN'}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = Path(args.output_dir) if args.output_dir else Path("testreports") / f"pod_rootcause_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    results = [run_case(args.url, case, args.repeat, args.concurrency, args.timeout, result_dir) for case in selected]
    total_elapsed = time.time() - started
    if not model_name:
        for result in results:
            for run in result.runs:
                if run.get("model_name"):
                    model_name = str(run["model_name"])
                    break
            if model_name:
                break
    write_reports(results, result_dir, total_elapsed, model_name)
    print(f"\nReport: {result_dir}")


if __name__ == "__main__":
    main()
