#!/usr/bin/env python3
"""Pod abnormal E2E quality runner.

Runs /ask against pod_abnormal_type-focused cases and computes:
- MTTR
- root cause accuracy
- evidence completeness
- runbook coverage
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import threading
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


def _contains_any(text: str, expected: Iterable[str]) -> bool:
    lowered = _lower(text)
    return any(_lower(item) in lowered for item in expected if str(item or "").strip())


def _contains_all_or_most(text: str, expected: Iterable[str]) -> Tuple[bool, int, int]:
    terms = [str(item).strip() for item in expected if str(item or "").strip()]
    if not terms:
        return True, 0, 0
    lowered = _lower(text)
    matched = sum(1 for term in terms if _lower(term) in lowered)
    required = 1 if len(terms) <= 2 else max(2, (len(terms) + 1) // 2)
    return matched >= required, matched, len(terms)


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
        rate = collected / planned if planned else None
        return rate, collected, planned, source

    match = re.search(r"计划\s*(\d+)\s*项.*?实际采集\s*(\d+)\s*项", text, re.DOTALL)
    if match:
        planned = int(match.group(1))
        collected = int(match.group(2))
        rate = collected / planned if planned else None
        return rate, collected, planned, "collection_summary"

    return None, 0, 0, "missing"


def extract_runbook_ids(text: str) -> List[str]:
    found = set()
    for pattern in [
        r"核心\s*Runbook[^:\n]*:\s*([^\n\r]+)",
        r"参考\s*Runbook[^:\n]*:\s*([^\n\r]+)",
        r"Runbook[：:\s]+([a-z0-9][\w.-]+)",
    ]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group(1)
            for part in re.split(r"[,，\s]+", raw):
                part = part.strip().strip("`*[]()")
                if part and part != "无":
                    found.add(part.replace(".md", ""))

    for match in re.finditer(r"fetch_runbook.*?([a-z0-9][\w.-]+\.md)", text, re.IGNORECASE):
        found.add(match.group(1).replace(".md", ""))
    for match in re.finditer(r"<runbook>\s*#\s*([^\n\r]+)", text):
        found.add(match.group(1).strip())
    for match in re.finditer(r'"runbook_id"\s*:\s*"([^"]+)"', text):
        found.add(match.group(1).replace(".md", ""))
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


def extract_confidence(text: str) -> Optional[float]:
    for pattern in [
        r"置信度[：:\s|]*(?:高|中|低)?\s*\(?(\d{1,3})%\)?",
        r'"confidence"\s*:\s*(0?\.\d+|1(?:\.0+)?)',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        value = float(match.group(1))
        return value / 100 if value > 1 else value
    return None


def count_tool_calls(text: str) -> int:
    match = re.search(r"[├└─\-\s]*工具调用[：:\s]*(\d+)\s*次", text)
    if match:
        return int(match.group(1))
    return len(re.findall(r"调用工具|tool_call|工具结果", text, re.IGNORECASE))


def count_llm_calls(text: str) -> int:
    match = re.search(r"[├└─\-\s]*LLM\s*调用[：:\s]*(\d+)\s*次", text)
    return int(match.group(1)) if match else 0


@dataclass
class Case:
    id: str
    name: str
    enabled: bool = True
    manual: bool = False
    namespace: str = "aiops-e2e"
    question: str = "我的集群有什么问题？"
    expected_pod_abnormal_type: str = ""
    expected_layer: str = ""
    expected_status: List[str] = field(default_factory=list)
    expected_runbooks: List[str] = field(default_factory=list)
    root_cause_keywords: List[str] = field(default_factory=list)
    evidence_keywords: List[str] = field(default_factory=list)
    mttr_threshold_seconds: int = 900
    root_cause_threshold: float = 0.8
    evidence_threshold: float = 0.8
    runbook_threshold: float = 0.8


@dataclass
class CaseResult:
    case: Case
    runs: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def ok_runs(self) -> List[Dict[str, Any]]:
        return [run for run in self.runs if run.get("success")]

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

    def _rate(self, key: str) -> Optional[float]:
        runs = self.ok_runs
        return sum(1 for run in runs if run.get(key)) / len(runs) if runs else None


def load_cases(path: Path) -> Tuple[Dict[str, Any], List[Case]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = data.get("defaults") or {}
    cases = []
    for item in data.get("cases") or []:
        merged = {**defaults, **item}
        cases.append(Case(
            id=merged["id"],
            name=merged["name"],
            enabled=bool(merged.get("enabled", True)),
            manual=bool(merged.get("manual", False)),
            namespace=str(merged.get("namespace") or "aiops-e2e"),
            question=str(merged.get("question") or defaults.get("question") or "我的集群有什么问题？"),
            expected_pod_abnormal_type=str(merged.get("expected_pod_abnormal_type") or ""),
            expected_layer=str(merged.get("expected_layer") or ""),
            expected_status=list(merged.get("expected_status") or []),
            expected_runbooks=list(merged.get("expected_runbooks") or []),
            root_cause_keywords=list(merged.get("root_cause_keywords") or []),
            evidence_keywords=list(merged.get("evidence_keywords") or []),
            mttr_threshold_seconds=int(merged.get("mttr_threshold_seconds") or 900),
            root_cause_threshold=float(merged.get("root_cause_threshold") or 0.8),
            evidence_threshold=float(merged.get("evidence_threshold") or 0.8),
            runbook_threshold=float(merged.get("runbook_threshold") or 0.8),
        ))
    return defaults, cases


def check_health(base_url: str) -> None:
    response = requests.get(f"{base_url}/health", timeout=10)
    response.raise_for_status()


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


def evaluate_response(case: Case, text: str, wall_clock: float, idx: int = 0) -> Dict[str, Any]:
    mttr = extract_mttr_seconds(text, wall_clock)
    evidence_rate, evidence_collected, evidence_planned, evidence_source = extract_evidence_rate(text)
    runbook_ids = extract_runbook_ids(text)
    layer = extract_layer(text)
    confidence = extract_confidence(text)

    type_ok = _contains_any(text, [case.expected_pod_abnormal_type]) if case.expected_pod_abnormal_type else True
    layer_ok = layer == case.expected_layer if case.expected_layer else True
    root_keywords_ok, root_keywords_matched, root_keywords_total = _contains_all_or_most(
        text, case.root_cause_keywords
    )
    root_cause_ok = type_ok and root_keywords_ok

    evidence_keywords_ok, evidence_keywords_matched, evidence_keywords_total = _contains_all_or_most(
        text, case.evidence_keywords
    )
    evidence_ok = evidence_rate is not None and evidence_rate >= case.evidence_threshold and evidence_keywords_ok

    expected_runbooks = [item.replace(".md", "").lower() for item in case.expected_runbooks]
    runbook_text = " ".join(runbook_ids).lower()
    runbook_ok = any(expected in runbook_text for expected in expected_runbooks) if expected_runbooks else True

    return {
        "idx": idx,
        "success": True,
        "elapsed": wall_clock,
        "mttr_seconds": mttr,
        "mttr_ok": mttr <= case.mttr_threshold_seconds,
        "layer": layer,
        "layer_ok": layer_ok,
        "confidence": confidence,
        "pod_abnormal_type_ok": type_ok,
        "root_cause_ok": root_cause_ok,
        "root_keywords_matched": root_keywords_matched,
        "root_keywords_total": root_keywords_total,
        "evidence_rate": evidence_rate,
        "evidence_collected": evidence_collected,
        "evidence_planned": evidence_planned,
        "evidence_source": evidence_source,
        "evidence_keywords_ok": evidence_keywords_ok,
        "evidence_keywords_matched": evidence_keywords_matched,
        "evidence_keywords_total": evidence_keywords_total,
        "evidence_ok": evidence_ok,
        "runbook_ids": runbook_ids,
        "runbook_ok": runbook_ok,
        "tool_calls": count_tool_calls(text),
        "llm_calls": count_llm_calls(text),
        "response_length": len(text),
    }


def run_case(base_url: str, case: Case, repeat: int, concurrency: int, timeout: int, result_dir: Path) -> CaseResult:
    case_dir = result_dir / case.id
    case_dir.mkdir(parents=True, exist_ok=True)
    result = CaseResult(case=case)
    print(f"\n{'-' * 72}")
    print(f"Case: {case.name} ({case.id})")
    print(f"Expect: pod_abnormal_type={case.expected_pod_abnormal_type} layer={case.expected_layer} runbook={','.join(case.expected_runbooks)}")
    print(f"Question: {case.question}")
    print(f"{'-' * 72}")

    lock = threading.Lock()

    def _one(i: int) -> Dict[str, Any]:
        with lock:
            print(f"  #{i}/{repeat} request...")
        run = run_single_request(base_url, case, timeout, i, case_dir)
        with lock:
            if run.get("success"):
                ev = "N/A" if run.get("evidence_rate") is None else f"{run['evidence_rate']:.0%}"
                print(
                    f"  #{i} ok {run['elapsed']:.0f}s | root={'OK' if run['root_cause_ok'] else 'BAD'} "
                    f"| evidence={ev} | runbook={'OK' if run['runbook_ok'] else 'BAD'} | layer={run['layer']}"
                )
            else:
                print(f"  #{i} failed: {run.get('error')}")
        return run

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_one, i) for i in range(1, repeat + 1)]
        for future in concurrent.futures.as_completed(futures):
            result.runs.append(future.result())
    return result


def _fmt_rate(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def write_reports(results: List[CaseResult], result_dir: Path, total_elapsed: float) -> None:
    all_runs = [run for result in results for run in result.runs]
    ok_runs = [run for run in all_runs if run.get("success")]

    summary: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "result_dir": str(result_dir),
        "total_elapsed_seconds": round(total_elapsed, 1),
        "total_runs": len(all_runs),
        "success": len(ok_runs),
        "failed": len(all_runs) - len(ok_runs),
        "cases": {},
    }

    lines = [
        "# Pod Abnormal E2E Summary",
        "",
        f"- total runs: {len(all_runs)}",
        f"- success: {len(ok_runs)}",
        f"- failed: {len(all_runs) - len(ok_runs)}",
        f"- elapsed: {total_elapsed:.1f}s",
        "",
        "| Case | Root Cause | Evidence | Runbook | MTTR | Runs |",
        "|------|------------|----------|---------|------|------|",
    ]

    for result in results:
        case = result.case
        ok = result.ok_runs
        root_rate = result.root_cause_accuracy
        runbook_rate = result.runbook_coverage
        evidence_rate = result.avg_evidence_rate
        mttr = result.avg_mttr_seconds
        summary["cases"][case.id] = {
            "name": case.name,
            "expected_pod_abnormal_type": case.expected_pod_abnormal_type,
            "expected_layer": case.expected_layer,
            "expected_runbooks": case.expected_runbooks,
            "runs": result.runs,
            "root_cause_accuracy": None if root_rate is None else round(root_rate * 100, 1),
            "evidence_completeness": None if evidence_rate is None else round(evidence_rate * 100, 1),
            "runbook_coverage": None if runbook_rate is None else round(runbook_rate * 100, 1),
            "avg_mttr_seconds": None if mttr is None else round(mttr, 1),
        }
        mttr_text = "N/A" if mttr is None else f"{mttr / 60:.1f}m"
        lines.append(
            f"| {case.id} | {_fmt_rate(root_rate)} | {_fmt_rate(evidence_rate)} | "
            f"{_fmt_rate(runbook_rate)} | {mttr_text} | {len(ok)}/{len(result.runs)} |"
        )

    if ok_runs:
        root_values = [run for run in ok_runs if run.get("root_cause_ok")]
        runbook_values = [run for run in ok_runs if run.get("runbook_ok")]
        evidence_values = [run["evidence_rate"] for run in ok_runs if run.get("evidence_rate") is not None]
        mttr_values = [run["mttr_seconds"] for run in ok_runs]
        summary["aggregate"] = {
            "root_cause_accuracy": round(len(root_values) / len(ok_runs) * 100, 1),
            "runbook_coverage": round(len(runbook_values) / len(ok_runs) * 100, 1),
            "evidence_completeness": round(sum(evidence_values) / len(evidence_values) * 100, 1) if evidence_values else None,
            "avg_mttr_seconds": round(sum(mttr_values) / len(mttr_values), 1) if mttr_values else None,
        }

    (result_dir / "stats.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (result_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pod abnormal E2E cases")
    parser.add_argument("--case", "-s", default="all", help="case id, comma-separated ids, or all")
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE), help="cases.yaml path")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="AIOps base URL")
    parser.add_argument("-n", "--repeat", type=int, default=1, help="repeat count per case")
    parser.add_argument("-c", "--concurrency", type=int, default=1, help="concurrency per case")
    parser.add_argument("--timeout", type=int, default=900, help="request timeout seconds")
    parser.add_argument("--include-disabled", action="store_true", help="include disabled/manual cases")
    parser.add_argument("--question", default=None, help="override question for all cases")
    parser.add_argument("--output-dir", default=None, help="result directory")
    args = parser.parse_args()

    _, cases = load_cases(Path(args.cases_file))
    if args.question:
        for case in cases:
            case.question = args.question

    selected_ids = {item.strip() for item in args.case.split(",") if item.strip()}
    if args.case == "all":
        selected = [case for case in cases if case.enabled or args.include_disabled]
    else:
        selected = [case for case in cases if case.id in selected_ids]
    missing = selected_ids - {case.id for case in cases}
    if missing and args.case != "all":
        print(f"Unknown case(s): {', '.join(sorted(missing))}", file=sys.stderr)
        sys.exit(2)
    if not selected:
        print("No cases selected", file=sys.stderr)
        sys.exit(2)

    print("=" * 72)
    print("Pod Abnormal E2E")
    print("=" * 72)
    print(f"URL: {args.url}")
    print(f"Cases: {', '.join(case.id for case in selected)}")
    print(f"Repeat: {args.repeat} | concurrency: {args.concurrency} | timeout: {args.timeout}s")
    check_health(args.url)
    print("Health: OK")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = Path(args.output_dir) if args.output_dir else Path("testreports") / f"pod_abnormal_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    results = [
        run_case(args.url, case, args.repeat, args.concurrency, args.timeout, result_dir)
        for case in selected
    ]
    total_elapsed = time.time() - started
    write_reports(results, result_dir, total_elapsed)
    print(f"\nReport: {result_dir}")


if __name__ == "__main__":
    main()
