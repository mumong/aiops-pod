#!/usr/bin/env python3
"""
AIOps Copilot E2E 场景准确率测试（盲测模式）

所有场景使用统一问题（默认 "我的集群有什么问题"），不向 LLM 泄露故障提示。
--scenario 仅提供期望值（层级、Runbook）用于结果比对。

四项质量指标：
  1. MTTR（平均修复时间）— < 15 分钟
  2. 层级准确率 — >= 80%
  3. Runbook 覆盖率 — >= 80%
  4. 证据采集率 — >= 80%

用法:
    # 运行单个场景（推荐：先手动部署 manifest，再运行测试）
    python test_accuracy.py --scenario l2-oomkilled

    # 运行所有场景
    python test_accuracy.py --scenario all

    # 单场景重复 N 次，5 并发（稳定性/压力测试）
    python test_accuracy.py --scenario l3-imagepull -n 50 -c 5

    # 自定义问题覆盖默认
    python test_accuracy.py --scenario l3-imagepull -q "查看集群 CPU 和内存使用情况"
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("需要 requests: pip install requests")
    sys.exit(1)


# ── 盲测默认问题（不含任何故障提示） ─────────────────────────
DEFAULT_QUESTION = "我的集群有什么问题"

# ── 内置场景矩阵（仅期望值，不含 query） ─────────────────────

SCENARIOS: Dict[str, Dict] = {
    "l0-volume-limit": {
        "name": "L0 存储卷超限驱逐",
        "expect_layer": "L0",
        "expect_runbook": "l0-volume-limit",
        "runbook_keywords": ["存储卷", "volume", "驱逐", "evict", "ephemeral"],
    },
    "l1-taint-node": {
        "name": "L1 节点 NotReady/Taint",
        "expect_layer": "L1",
        "expect_runbook": "l1-taint-node",
        "runbook_keywords": ["taint", "notready", "节点", "调度"],
    },
    "l2-oomkilled": {
        "name": "L2 OOMKilled",
        "expect_layer": "L2",
        "expect_runbook": "l2-oomkilled",
        "runbook_keywords": ["oomkill", "内存", "exit code 137"],
    },
    "l3-imagepull": {
        "name": "L3 镜像拉取失败",
        "expect_layer": "L3",
        "expect_runbook": "l3-imagepull-failed",
        "runbook_keywords": ["镜像拉取", "imagepull", "imagepullbackoff"],
    },
    "l4-app-health": {
        "name": "L4 应用健康检查失败",
        "expect_layer": "L4",
        "expect_runbook": "l4-app-health-fail",
        "runbook_keywords": ["健康检查", "health", "探针", "probe"],
    },
}

# ── 指标提取函数（仅从工作流系统统计提取，不使用 AI 自评） ─────

def extract_layer(text: str) -> str:
    """从报告文本中提取诊断层级（仅使用系统数据）

    数据来源优先级：
      1. 下游数据日志: "📤 → 下游数据: layer=Layer.L3"
      2. 节点输出: "层级: Layer.L3"
      3. layer_analysis JSON: '"layer": "L3"'
      4. 频率统计（纯计算兜底，非 AI 自评）
    """
    # 优先级1: 下游数据日志 — "layer=Layer.L3" 或 "layer=L3"
    m = re.search(r'📤.*?layer=(?:Layer\.)?(L[0-4])', text)
    if m:
        return m.group(1).upper()
    # 优先级2: 节点输出 — "层级: Layer.L3"
    m = re.search(r'层级[：:\s]*Layer\.(L[0-4])', text)
    if m:
        return m.group(1).upper()
    # 优先级3: layer_analysis JSON — '"layer": "L3"'
    m = re.search(r'layer_analysis=\{.*?"layer":\s*"(L[0-4])"', text)
    if m:
        return m.group(1).upper()
    # 优先级4: 频率统计（纯计算兜底）
    counts: Dict[str, int] = {}
    for lm in re.finditer(r'\b(L[0-4])\b', text):
        counts[lm.group(1)] = counts.get(lm.group(1), 0) + 1
    return max(counts, key=counts.get) if counts else "UNKNOWN"


def extract_mttr(text: str, wall_clock: float) -> float:
    """提取 MTTR（秒）。仅从 stats_block 系统统计提取，回退到 wall clock

    数据来源：
      1. stats_block: "├─ 总耗时: 4.5m" — format_stats_block() 精确输出
      2. wall clock — HTTP 请求实际耗时（兜底）
    """
    # stats_block 格式 "├─ 总耗时: X.Xm"
    m = re.search(r'[├└─]+\s*总耗时[：:\s]*([\d.]+)(s|m|h)', text)
    if m:
        val, unit = float(m.group(1)), m.group(2)
        if unit == 'm':
            return val * 60
        elif unit == 'h':
            return val * 3600
        return val
    return wall_clock


def extract_evidence_rate(text: str) -> Tuple[Optional[float], int, int]:
    """提取证据采集率。返回 (rate, collected, planned)

    仅使用系统数据（工作流内部统计），不使用 AI 自评。
    数据来源优先级：
      1. stats_block: "证据: 9/12 项, 完整度: 67%" — service.py 输出
      2. 下游数据日志: "📤 → 下游数据: evidence_items=6/9" — 节点间传递
      3. collection_summary: '"collection_summary": "计划 6 项，实际采集 6 项"' — evidence_collector
    """
    # 优先级1: stats_block — "证据: N/M 项, 完整度: XX%"
    m = re.search(r'证据[：:]\s*(\d+)/(\d+)\s*项.*?完整度[：:]\s*(\d+)%', text)
    if m:
        collected, planned = int(m.group(1)), int(m.group(2))
        rate = collected / planned if planned > 0 else None
        return rate, collected, planned
    # 优先级2: 下游数据日志 — "evidence_items=N/M"
    m = re.search(r'evidence_items=(\d+)/(\d+)', text)
    if m:
        collected, planned = int(m.group(1)), int(m.group(2))
        rate = collected / planned if planned > 0 else None
        return rate, collected, planned
    # 优先级3: collection_summary — "计划 N 项，实际采集 M 项"
    m = re.search(r'计划\s*(\d+)\s*项.*?实际采集\s*(\d+)\s*项', text)
    if m:
        planned, collected = int(m.group(1)), int(m.group(2))
        rate = collected / planned if planned > 0 else None
        return rate, collected, planned
    return None, 0, 0


def extract_runbook(text: str) -> Dict[str, Optional[str]]:
    """提取 Runbook 信息（仅系统数据）

    数据来源：
      1. rca_analysis JSON: "primary_runbooks": ["L3 镜像拉取失败 (ImagePullBackOff)"]
      2. <runbook> 标签标题: "<runbook># L3 镜像拉取失败 (ImagePullBackOff)"
      3. fetch_runbook 日志: "fetch_runbook...找到...xxx.md"
    """
    core = None
    runbook_ids = set()
    # 优先级1: rca_analysis JSON 中的 primary_runbooks
    m = re.search(r'"primary_runbooks"\s*:\s*\[([^\]]+)\]', text)
    if m:
        rm = re.search(r'"([^"]+)"', m.group(1))
        if rm:
            core = rm.group(1)
    # 优先级2: <runbook> 标签标题
    if not core:
        m = re.search(r'<runbook>\s*#\s+(.+?)(?:\n|$)', text)
        if m:
            core = m.group(1).strip()
    # 从 fetch_runbook 日志提取 .md 文件名
    for fm in re.finditer(r'fetch_runbook.*?找到.*?([\w][\w.-]*\.md)', text):
        fname = fm.group(1)
        if fname not in ("README.md", "CLAUDE.md"):
            runbook_ids.add(fname.replace(".md", ""))
    return {"core": core, "refs": None, "runbook_ids": list(runbook_ids)}


def extract_tool_calls(text: str) -> int:
    """提取工具调用次数（从 stats_block 系统统计或实际日志计数）"""
    m = re.search(r'[├└─]+\s*工具调用[：:\s]*(\d+)\s*次', text)
    if m:
        return int(m.group(1))
    # 回退: 计算实际工具调用日志行数
    return len(re.findall(r'🔧\s*调用工具:', text))


def extract_llm_calls(text: str) -> int:
    """提取 LLM 调用次数（从 stats_block 系统统计）"""
    m = re.search(r'[├└─]+\s*LLM\s*调用[：:\s]*(\d+)\s*次', text)
    if m:
        return int(m.group(1))
    return 0


def extract_all(text: str, wall_clock: float) -> Dict:
    """从响应文本中提取所有质量指标"""
    runbook = extract_runbook(text)
    ev_rate, ev_collected, ev_planned = extract_evidence_rate(text)
    return {
        "layer": extract_layer(text),
        "mttr_seconds": extract_mttr(text, wall_clock),
        "evidence_rate": ev_rate,
        "evidence_collected": ev_collected,
        "evidence_planned": ev_planned,
        "runbook_core": runbook["core"],
        "runbook_refs": runbook["refs"],
        "runbook_ids": runbook.get("runbook_ids", []),
        "tool_calls": extract_tool_calls(text),
        "llm_calls": extract_llm_calls(text),
        "response_length": len(text),
    }


# ── 单次请求 ──────────────────────────────────────────────

def run_single_request(
    base_url: str, query: str, timeout: int, idx: int, save_dir: Path
) -> Dict:
    """发送流式请求，收集完整报告文本，返回提取的指标

    使用 stream=true（默认）走 AICall + Workflow 路径，
    通过流式响应逐块收集完整文本，效果等同于 stream=false 但走正确的代码路径。
    """
    url = f"{base_url}/ask"
    params = {"q": query, "stream": "true", "format": "text"}
    chunks = []
    filepath = save_dir / f"response_{idx}.md"

    start = time.time()
    try:
        resp = requests.get(url, params=params, timeout=timeout, stream=True)
        if resp.status_code != 200:
            elapsed = time.time() - start
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")

        # 流式收集完整文本
        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                chunks.append(chunk)
        elapsed = time.time() - start

        body = "".join(chunks)
        filepath.write_text(body, encoding="utf-8")

        if len(body) < 50:
            return {"idx": idx, "success": False, "error": "空响应", "elapsed": elapsed}

        metrics = extract_all(body, elapsed)
        metrics["idx"] = idx
        metrics["success"] = True
        metrics["elapsed"] = elapsed
        return metrics

    except requests.Timeout:
        elapsed = time.time() - start
        partial = "".join(chunks)
        timeout_note = f"\n\nTIMEOUT after {elapsed:.0f}s"
        filepath.write_text((partial + timeout_note).lstrip("\n"), encoding="utf-8")
        return {"idx": idx, "success": False, "error": f"超时 ({elapsed:.0f}s)", "elapsed": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        partial = "".join(chunks)
        error_text = str(e)
        is_read_timeout = "read timed out" in error_text.lower()
        error_prefix = f"超时 ({elapsed:.0f}s)" if is_read_timeout else error_text
        error_note = f"\n\nERROR: {error_text}"
        filepath.write_text((partial + error_note).lstrip("\n"), encoding="utf-8")
        return {"idx": idx, "success": False, "error": error_prefix, "elapsed": elapsed}


def check_health(base_url: str):
    """健康检查"""
    try:
        r = requests.get(f"{base_url}/health", timeout=10)
        r.raise_for_status()
        print("✅ 服务健康检查通过\n")
    except Exception as e:
        print(f"❌ 服务不可用: {e}")
        sys.exit(1)


# ── 场景测试 ──────────────────────────────────────────────

class ScenarioResult:
    """单个场景的测试结果"""
    def __init__(self, scenario_id: str, scenario: Dict):
        self.scenario_id = scenario_id
        self.name = scenario["name"]
        self.expect_layer = scenario["expect_layer"]
        self.expect_runbook = scenario["expect_runbook"]
        self.runbook_keywords = scenario.get("runbook_keywords", [])
        self.runs: List[Dict] = []  # 每次运行的 metrics

    @property
    def ok_runs(self) -> List[Dict]:
        return [r for r in self.runs if r.get("success")]

    @property
    def layer_correct(self) -> int:
        return sum(1 for r in self.ok_runs if r["layer"] == self.expect_layer)

    @property
    def layer_accuracy(self) -> Optional[float]:
        n = len(self.ok_runs)
        return self.layer_correct / n if n > 0 else None

    def _is_runbook_match(self, run: Dict) -> bool:
        """多策略 Runbook 匹配：
        1. runbook_ids 精确匹配（从 fetch_runbook 日志提取的 .md 文件名）
        2. 核心 Runbook 中文名包含 expect_runbook 关键词
        3. runbook_keywords 模糊匹配核心 Runbook 中文名
        """
        expect = self.expect_runbook.lower()
        # 策略1: 从 thinking 中提取的 .md 文件 ID 精确匹配
        runbook_ids = run.get("runbook_ids", [])
        for rid in runbook_ids:
            if expect in rid.lower() or rid.lower() in expect:
                return True
        # 策略2: 核心 Runbook 中文名包含 expect_runbook 关键词片段
        core = (run.get("runbook_core") or "").lower()
        if core:
            # 将 expect_runbook 拆分为片段匹配（如 "l3-imagepull-failed" → ["l3", "imagepull", "failed"]）
            parts = [p for p in expect.replace("-", " ").replace("_", " ").split() if len(p) > 1]
            if parts and sum(1 for p in parts if p in core) >= len(parts) * 0.5:
                return True
        # 策略3: runbook_keywords 模糊匹配
        if self.runbook_keywords and core:
            matched = sum(1 for kw in self.runbook_keywords if kw.lower() in core)
            if matched >= 1:
                return True
        return False

    @property
    def runbook_matched(self) -> int:
        return sum(1 for r in self.ok_runs if self._is_runbook_match(r))

    @property
    def runbook_rate(self) -> Optional[float]:
        n = len(self.ok_runs)
        return self.runbook_matched / n if n > 0 else None

    @property
    def avg_mttr(self) -> Optional[float]:
        mttrs = [r["mttr_seconds"] for r in self.ok_runs]
        return sum(mttrs) / len(mttrs) if mttrs else None

    @property
    def avg_evidence_rate(self) -> Optional[float]:
        rates = [r["evidence_rate"] for r in self.ok_runs if r.get("evidence_rate") is not None]
        return sum(rates) / len(rates) if rates else None


def run_scenario(
    base_url: str, scenario_id: str, scenario: Dict,
    repeat: int, concurrency: int, timeout: int, result_dir: Path,
    question: str = DEFAULT_QUESTION,
) -> ScenarioResult:
    """运行单个场景 N 次（支持并发）。question 为统一盲测问题。"""
    sr = ScenarioResult(scenario_id, scenario)
    save_dir = result_dir / scenario_id
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'─' * 60}")
    print(f"  场景: {scenario['name']} ({scenario_id})")
    print(f"  问题: {question}")
    print(f"  期望: 层级={scenario['expect_layer']} | Runbook={scenario['expect_runbook']}")
    print(f"  运行: {repeat} 次 | 并发: {concurrency}")
    print(f"{'─' * 60}")

    print_lock = threading.Lock()

    def _run_one(i: int) -> Dict:
        with print_lock:
            print(f"  🚀 #{i}/{repeat} 请求中...")
        m = run_single_request(base_url, question, timeout, i, save_dir)
        with print_lock:
            if m.get("success"):
                layer_ok = "✅" if m["layer"] == scenario["expect_layer"] else "❌"
                rb_ok = "✅" if sr._is_runbook_match(m) else "❌"
                ev_str = f"{m['evidence_rate']:.0%}" if m.get("evidence_rate") is not None else "N/A"
                print(
                    f"  ✅ #{i} 完成 ({m['elapsed']:.0f}s) "
                    f"→ 层级={m['layer']}{layer_ok} | MTTR={m['mttr_seconds']:.0f}s | "
                    f"证据={ev_str} | Runbook={rb_ok}"
                )
            else:
                print(f"  ❌ #{i} 失败: {m.get('error', '未知')}")
        return m

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_run_one, i): i for i in range(1, repeat + 1)}
        for future in concurrent.futures.as_completed(futures):
            sr.runs.append(future.result())

    return sr


def print_report(results: List[ScenarioResult], total_elapsed: float, result_dir: Path):
    """打印汇总报告（含每次运行明细）"""
    all_ok = [r for sr in results for r in sr.ok_runs]
    all_runs = [r for sr in results for r in sr.runs]
    n_ok = len(all_ok)
    n_fail = len(all_runs) - n_ok

    print(f"\n{'=' * 70}")
    print(f"  AIOps Copilot E2E 准确率报告（盲测模式）")
    print(f"{'=' * 70}")
    print(f"场景数: {len(results)} | 总运行: {len(all_runs)} | 成功: {n_ok} | 失败: {n_fail}")
    print(f"总耗时: {total_elapsed:.0f}s ({total_elapsed/60:.1f}m)")
    print()

    if not n_ok:
        print("❌ 无成功请求，无法计算指标")
        return

    # ── 每次运行明细 ──
    print(f"{'─' * 70}")
    print(f"  运行明细")
    print(f"{'─' * 70}")
    print(f"| {'场景':<18} | {'#':<3} | {'层级':<6} | {'期望':<6} | {'Runbook':<5} | {'MTTR':<7} | {'证据':<7} | {'耗时':<7} |")
    print(f"|{'-'*20}|{'-'*5}|{'-'*8}|{'-'*8}|{'-'*7}|{'-'*9}|{'-'*9}|{'-'*9}|")

    for sr in results:
        for r in sr.runs:
            if not r.get("success"):
                print(f"| {sr.name[:18]:<18} | {r.get('idx',0):<3} | {'FAIL':<6} | {sr.expect_layer:<6} | {'—':<5} | {'—':<7} | {'—':<7} | {r.get('elapsed',0):.0f}s{'':<3} |")
                continue
            layer_mark = "✅" if r["layer"] == sr.expect_layer else "❌"
            rb_mark = "✅" if sr._is_runbook_match(r) else "❌"
            ev_str = f"{r['evidence_rate']:.0%}" if r.get("evidence_rate") is not None else "N/A"
            print(f"| {sr.name[:18]:<18} | {r.get('idx',0):<3} | {r['layer']:<4}{layer_mark} | {sr.expect_layer:<6} | {rb_mark:<5} | {r['mttr_seconds']:.0f}s{'':<4} | {ev_str:<7} | {r['elapsed']:.0f}s{'':<4} |")
    print()

    # ── 每场景汇总 ──
    print(f"{'─' * 70}")
    print(f"  场景汇总")
    print(f"{'─' * 70}")
    print(f"| {'场景':<22} | {'层级准确':<10} | {'Runbook':<10} | {'MTTR':<10} | {'证据率':<10} |")
    print(f"|{'-'*24}|{'-'*12}|{'-'*12}|{'-'*12}|{'-'*12}|")

    for sr in results:
        n = len(sr.ok_runs)
        if n == 0:
            print(f"| {sr.name:<20} | {'N/A':<10} | {'N/A':<10} | {'N/A':<10} | {'N/A':<10} |")
            continue
        la = f"{sr.layer_correct}/{n}" if sr.layer_accuracy is not None else "N/A"
        rb = f"{sr.runbook_matched}/{n}" if sr.runbook_rate is not None else "N/A"
        mt = f"{sr.avg_mttr:.0f}s" if sr.avg_mttr is not None else "N/A"
        ev = f"{sr.avg_evidence_rate:.0%}" if sr.avg_evidence_rate is not None else "N/A"
        print(f"| {sr.name:<20} | {la:<10} | {rb:<10} | {mt:<10} | {ev:<10} |")
    print()

    # ── 汇总四项指标 ──
    # 1. MTTR
    mttrs = [r["mttr_seconds"] for r in all_ok]
    avg_mttr = sum(mttrs) / len(mttrs)
    mttr_pass = avg_mttr < 900

    # 2. 层级准确率
    total_correct = sum(sr.layer_correct for sr in results)
    layer_acc = total_correct / n_ok * 100
    layer_pass = layer_acc >= 80

    # 3. Runbook 覆盖率
    total_rb = sum(sr.runbook_matched for sr in results)
    rb_rate = total_rb / n_ok * 100
    rb_pass = rb_rate >= 80

    # 4. 证据采集率
    ev_rates = [r["evidence_rate"] for r in all_ok if r.get("evidence_rate") is not None]
    avg_ev = sum(ev_rates) / len(ev_rates) * 100 if ev_rates else None
    ev_pass = avg_ev is not None and avg_ev >= 80

    print(f"{'=' * 60}")
    print(f"  质量指标汇总")
    print(f"{'=' * 60}")
    print(f"| {'指标':<20} | {'阈值':<12} | {'实际':<12} | {'状态':<8} |")
    print(f"|{'-'*22}|{'-'*14}|{'-'*14}|{'-'*10}|")
    print(f"| {'MTTR':<20} | {'< 15m':<12} | {f'{avg_mttr/60:.1f}m':<12} | {'✅' if mttr_pass else '❌':<8} |")
    print(f"| {'层级准确率':<16} | {'>= 80%':<12} | {f'{layer_acc:.1f}%':<12} | {'✅' if layer_pass else '❌':<8} |")
    print(f"| {'Runbook 覆盖率':<17} | {'>= 80%':<12} | {f'{rb_rate:.1f}%':<12} | {'✅' if rb_pass else '❌':<8} |")
    ev_str = f"{avg_ev:.1f}%" if avg_ev is not None else "N/A"
    print(f"| {'证据采集率':<18} | {'>= 80%':<12} | {ev_str:<12} | {'✅' if ev_pass else '❌':<8} |")
    print()
    print(f"📁 报告目录: {result_dir}/")


def save_report(results: List[ScenarioResult], total_elapsed: float, result_dir: Path):
    """保存 JSON 汇总报告（含计算过程）"""
    all_ok = [r for sr in results for r in sr.ok_runs]
    all_runs = [r for sr in results for r in sr.runs]
    n_ok = len(all_ok)
    n_fail = len(all_runs) - n_ok

    mttrs = [r["mttr_seconds"] for r in all_ok]
    ev_rates = [r["evidence_rate"] for r in all_ok if r.get("evidence_rate") is not None]

    # ── 汇总指标（含计算过程）──
    aggregate = {}

    # 1. MTTR
    if mttrs:
        avg_mttr = sum(mttrs) / len(mttrs)
        aggregate["mttr"] = {
            "threshold": "< 900s (15m)",
            "values": [round(v, 1) for v in mttrs],
            "calculation": f"sum({'+'.join(f'{v:.1f}' for v in mttrs)}) / {len(mttrs)}",
            "result_seconds": round(avg_mttr, 1),
            "result_formatted": f"{avg_mttr/60:.1f}m",
            "pass": avg_mttr < 900,
        }

    # 2. 层级准确率
    if n_ok:
        total_correct = sum(sr.layer_correct for sr in results)
        layer_acc = total_correct / n_ok * 100
        per_scenario = {sr.scenario_id: f"{sr.layer_correct}/{len(sr.ok_runs)}" for sr in results}
        aggregate["layer_accuracy"] = {
            "threshold": ">= 80%",
            "per_scenario": per_scenario,
            "calculation": f"{total_correct} / {n_ok} × 100%",
            "result_percent": round(layer_acc, 1),
            "pass": layer_acc >= 80,
        }

    # 3. Runbook 覆盖率
    if n_ok:
        total_rb = sum(sr.runbook_matched for sr in results)
        rb_rate = total_rb / n_ok * 100
        per_scenario = {sr.scenario_id: f"{sr.runbook_matched}/{len(sr.ok_runs)}" for sr in results}
        aggregate["runbook_coverage"] = {
            "threshold": ">= 80%",
            "per_scenario": per_scenario,
            "calculation": f"{total_rb} / {n_ok} × 100%",
            "result_percent": round(rb_rate, 1),
            "pass": rb_rate >= 80,
        }

    # 4. 证据采集率
    if ev_rates:
        avg_ev = sum(ev_rates) / len(ev_rates) * 100
        aggregate["evidence_completeness"] = {
            "threshold": ">= 80%",
            "values": [round(v * 100, 1) for v in ev_rates],
            "samples": len(ev_rates),
            "missing": n_ok - len(ev_rates),
            "calculation": f"avg({len(ev_rates)} samples)",
            "result_percent": round(avg_ev, 1),
            "pass": avg_ev >= 80,
        }
    else:
        aggregate["evidence_completeness"] = {
            "threshold": ">= 80%",
            "values": [],
            "samples": 0,
            "missing": n_ok,
            "result_percent": None,
            "pass": False,
            "note": "无法从报告中提取证据完整率",
        }

    # ── 场景明细 ──
    scenarios = {}
    for sr in results:
        n = len(sr.ok_runs)
        scenarios[sr.scenario_id] = {
            "name": sr.name,
            "expect_layer": sr.expect_layer,
            "expect_runbook": sr.expect_runbook,
            "total_runs": len(sr.runs),
            "success": n,
            "failed": len(sr.runs) - n,
            "layer_accuracy": round(sr.layer_accuracy * 100, 1) if sr.layer_accuracy is not None else None,
            "layer_detail": f"{sr.layer_correct}/{n}",
            "runbook_rate": round(sr.runbook_rate * 100, 1) if sr.runbook_rate is not None else None,
            "runbook_detail": f"{sr.runbook_matched}/{n}",
            "avg_mttr_seconds": round(sr.avg_mttr, 1) if sr.avg_mttr is not None else None,
            "avg_evidence_rate": round(sr.avg_evidence_rate * 100, 1) if sr.avg_evidence_rate is not None else None,
            "runs": [
                {
                    "idx": r.get("idx"),
                    "success": r.get("success"),
                    "elapsed": round(r.get("elapsed", 0), 1),
                    "layer": r.get("layer"),
                    "layer_correct": r.get("layer") == sr.expect_layer,
                    "mttr_seconds": round(r.get("mttr_seconds", 0), 1),
                    "evidence_rate": round(r["evidence_rate"] * 100, 1) if r.get("evidence_rate") is not None else None,
                    "evidence_detail": f"{r.get('evidence_collected', 0)}/{r.get('evidence_planned', 0)}",
                    "runbook_core": r.get("runbook_core"),
                    "runbook_matched": sr._is_runbook_match(r),
                    "tool_calls": r.get("tool_calls", 0),
                    "llm_calls": r.get("llm_calls", 0),
                }
                for r in sr.runs if r.get("success")
            ],
        }

    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_elapsed_seconds": round(total_elapsed, 1),
            "total_elapsed_formatted": f"{total_elapsed/60:.1f}m",
            "total_runs": len(all_runs),
            "success": n_ok,
            "failed": n_fail,
            "success_rate": f"{n_ok}/{len(all_runs)}",
        },
        "quality_metrics": aggregate,
        "scenarios": scenarios,
    }

    (result_dir / "stats.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(
        description="AIOps Copilot E2E 场景准确率测试（盲测模式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
内置场景:
  l0-volume-limit   L0 存储卷超限驱逐
  l1-taint-node     L1 节点 NotReady/Taint
  l2-oomkilled      L2 OOMKilled
  l3-imagepull      L3 镜像拉取失败
  l4-app-health     L4 应用健康检查失败
  all               运行所有场景

盲测说明:
  所有场景使用统一问题，不向 LLM 泄露故障提示。
  --scenario 仅提供期望值用于结果比对。

示例:
  python test_accuracy.py --scenario l2-oomkilled
  python test_accuracy.py --scenario all -n 3 -c 2
  python test_accuracy.py --scenario l3-imagepull -q "查询我集群的cpu和memory"
  python test_accuracy.py -q "自定义问题" --expect-layer L3 --expect-runbook l3-imagepull-failed
        """,
    )
    parser.add_argument("--scenario", "-s", default=None,
                        help="场景 ID（如 l2-oomkilled）或 'all' 运行全部")
    parser.add_argument("-n", "--repeat", type=int, default=1,
                        help="每个场景重复次数（默认 1）")
    parser.add_argument("-c", "--concurrency", type=int, default=1,
                        help="并发数（默认 1，串行执行）")
    parser.add_argument("-q", "--question", default=DEFAULT_QUESTION,
                        help=f"盲测问题（默认: '{DEFAULT_QUESTION}'）")
    parser.add_argument("--expect-layer", default=None,
                        help="期望层级（无 --scenario 时用于自定义比对）")
    parser.add_argument("--expect-runbook", default=None,
                        help="期望 Runbook ID（无 --scenario 时用于自定义比对）")
    parser.add_argument("--url", default="http://10.2.0.48:30800",
                        help="服务地址（默认 http://10.2.0.48:30800）")
    parser.add_argument("--timeout", type=int, default=900,
                        help="单请求超时秒数（默认 900）")
    args = parser.parse_args()

    # 确定要运行的场景列表
    scenarios_to_run: List[Tuple[str, Dict]] = []
    question = args.question  # 盲测问题（默认或 -q 覆盖）

    if args.scenario:
        if args.scenario == "all":
            scenarios_to_run = list(SCENARIOS.items())
        elif args.scenario in SCENARIOS:
            scenarios_to_run = [(args.scenario, SCENARIOS[args.scenario])]
        else:
            print(f"❌ 未知场景: {args.scenario}")
            print(f"可用场景: {', '.join(SCENARIOS.keys())}, all")
            sys.exit(1)
    elif args.expect_layer or args.expect_runbook:
        # 无 --scenario 但有期望值：自定义比对模式
        custom = {
            "name": "自定义场景",
            "expect_layer": args.expect_layer or "UNKNOWN",
            "expect_runbook": args.expect_runbook or "",
        }
        scenarios_to_run = [("custom", custom)]
    else:
        # 纯盲测：无场景、无期望值，只发问题看结果
        custom = {
            "name": "自由盲测",
            "expect_layer": "UNKNOWN",
            "expect_runbook": "",
        }
        scenarios_to_run = [("freeform", custom)]

    # 创建结果目录
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = Path("testreports") / ts
    result_dir.mkdir(parents=True, exist_ok=True)

    # 打印配置
    print("=" * 60)
    print("  AIOps Copilot E2E 准确率测试（盲测模式）")
    print("=" * 60)
    print(f"服务:   {args.url}")
    print(f"问题:   {question}")
    print(f"场景:   {', '.join(s[0] for s in scenarios_to_run)}")
    print(f"重复:   {args.repeat} 次/场景 | 并发: {args.concurrency}")
    print(f"超时:   {args.timeout}s")
    print("=" * 60)

    # 健康检查
    check_health(args.url)

    # 逐场景运行
    start = time.time()
    results: List[ScenarioResult] = []
    for sid, scenario in scenarios_to_run:
        sr = run_scenario(
            args.url, sid, scenario, args.repeat, args.concurrency,
            args.timeout, result_dir, question=question,
        )
        results.append(sr)

    total_elapsed = time.time() - start

    # 输出报告
    print_report(results, total_elapsed, result_dir)
    save_report(results, total_elapsed, result_dir)


if __name__ == "__main__":
    main()
