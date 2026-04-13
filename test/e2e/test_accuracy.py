#!/usr/bin/env python3
"""
AIOps Copilot E2E 场景准确率测试

内置 L0-L4 场景矩阵，每个场景有预定义的 query、期望层级、期望 Runbook。
使用 stream=false 纯文本 API，保存完整可读 Markdown 报告供人工排查。

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

    # 自定义问题（不使用内置场景）
    python test_accuracy.py -q "namespace=aiops-e2e pod xxx 异常" --expect-layer L2 --expect-runbook l2-oomkilled
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


# ── 内置场景矩阵 ──────────────────────────────────────────────

SCENARIOS: Dict[str, Dict] = {
    "l0-volume-limit": {
        "name": "L0 存储卷超限驱逐",
        "query": "namespace=aiops-e2e Pod logfill 被驱逐 Evicted ephemeral-storage 超限",
        "expect_layer": "L0",
        "expect_runbook": "l0-volume-limit",
    },
    "l1-taint-node": {
        "name": "L1 节点 NotReady/Taint",
        "query": "namespace=aiops-e2e 节点 NotReady Taint 导致 Pod 无法调度",
        "expect_layer": "L1",
        "expect_runbook": "l1-taint-node",
    },
    "l2-oomkilled": {
        "name": "L2 OOMKilled",
        "query": "namespace=aiops-e2e pod memhog 一直重启 OOMKilled",
        "expect_layer": "L2",
        "expect_runbook": "l2-oomkilled",
    },
    "l3-imagepull": {
        "name": "L3 镜像拉取失败",
        "query": "namespace=aiops-e2e Pod imagepull-fail-victim 镜像拉取失败 ImagePullBackOff",
        "expect_layer": "L3",
        "expect_runbook": "l3-imagepull-failed",
    },
    "l4-app-health": {
        "name": "L4 应用健康检查失败",
        "query": "namespace=aiops-e2e 应用 apphealth 健康检查失败",
        "expect_layer": "L4",
        "expect_runbook": "l4-app-health-fail",
    },
}

# ── 指标提取函数 ──────────────────────────────────────────────

def extract_layer(text: str) -> str:
    """从报告文本中提取诊断层级"""
    # 方法1: 表格 "| **问题层级** | L0 ..."
    m = re.search(r'\|\s*\*{0,2}问题层级\*{0,2}\s*\|\s*\*{0,2}\s*(L[0-4]|QUERY|HEALTHY)', text, re.I)
    if m:
        return m.group(1).upper()
    # 方法2: "**层级**: L0" 或 "层级: L0"
    m = re.search(r'(?:层级|layer)[：:\s]*\*{0,2}\s*(L[0-4]|QUERY|HEALTHY)', text, re.I)
    if m:
        return m.group(1).upper()
    # 方法3: 频率统计
    counts: Dict[str, int] = {}
    for lm in re.finditer(r'\b(L[0-4])\b', text):
        counts[lm.group(1)] = counts.get(lm.group(1), 0) + 1
    return max(counts, key=counts.get) if counts else "UNKNOWN"


def extract_mttr(text: str, wall_clock: float) -> float:
    """提取 MTTR（秒）。优先从报告 format_stats_block 提取，回退到 wall clock"""
    # 从 "总耗时: 2.2m" 或 "总耗时: 45.3s"
    m = re.search(r'总耗时[：:\s]*([\d.]+)(s|m|h)', text)
    if m:
        val, unit = float(m.group(1)), m.group(2)
        if unit == 'm':
            return val * 60
        elif unit == 'h':
            return val * 3600
        return val
    return wall_clock


def extract_evidence_rate(text: str) -> Tuple[Optional[float], int, int]:
    """提取证据采集率。返回 (rate, collected, planned)"""
    # 从 format_metrics_block: "| **证据完整率** | > 90% | 80% (4/5) | ✅ 达标 |"
    m = re.search(r'证据完整率.*?\|\s*(\d+)%\s*\((\d+)/(\d+)\)', text)
    if m:
        collected, planned = int(m.group(2)), int(m.group(3))
        rate = collected / planned if planned > 0 else None
        return rate, collected, planned
    return None, 0, 0


def extract_runbook(text: str) -> Dict[str, Optional[str]]:
    """提取核心 Runbook 和参考 Runbook"""
    core = refs = None
    m = re.search(r'\*{0,2}核心\s*Runbook\*{0,2}[：:\s]*(.*?)(?:\n|$)', text)
    if m:
        val = m.group(1).strip().strip('*')
        if val and val != "无":
            core = val
    m = re.search(r'\*{0,2}参考\s*Runbook\*{0,2}[：:\s]*(.*?)(?:\n|$)', text)
    if m:
        val = m.group(1).strip().strip('*')
        if val and val != "无":
            refs = val
    return {"core": core, "refs": refs}


def extract_tool_calls(text: str) -> int:
    m = re.search(r'\*{0,2}工具调用\*{0,2}[：:\s]*(\d+)\s*次', text)
    return int(m.group(1)) if m else 0


def extract_llm_calls(text: str) -> int:
    m = re.search(r'\*{0,2}LLM\s*调用\*{0,2}[：:\s]*(\d+)\s*次', text)
    return int(m.group(1)) if m else 0


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
        "tool_calls": extract_tool_calls(text),
        "llm_calls": extract_llm_calls(text),
        "response_length": len(text),
    }


# ── 单次请求 ──────────────────────────────────────────────

def run_single_request(
    base_url: str, query: str, timeout: int, idx: int, save_dir: Path
) -> Dict:
    """发送 stream=false 请求，保存完整报告，返回提取的指标"""
    url = f"{base_url}/ask"
    params = {"q": query, "stream": "false"}

    start = time.time()
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")

        body = resp.text
        filepath = save_dir / f"response_{idx}.md"
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
        (save_dir / f"response_{idx}.md").write_text(
            f"TIMEOUT after {elapsed:.0f}s", encoding="utf-8"
        )
        return {"idx": idx, "success": False, "error": f"超时 ({elapsed:.0f}s)", "elapsed": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        (save_dir / f"response_{idx}.md").write_text(
            f"ERROR: {e}", encoding="utf-8"
        )
        return {"idx": idx, "success": False, "error": str(e), "elapsed": elapsed}


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

    @property
    def runbook_matched(self) -> int:
        return sum(
            1 for r in self.ok_runs
            if r.get("runbook_core") and self.expect_runbook.lower() in r["runbook_core"].lower()
        )

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
    repeat: int, concurrency: int, timeout: int, result_dir: Path
) -> ScenarioResult:
    """运行单个场景 N 次（支持并发）"""
    sr = ScenarioResult(scenario_id, scenario)
    save_dir = result_dir / scenario_id
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'─' * 60}")
    print(f"  场景: {scenario['name']} ({scenario_id})")
    print(f"  期望: 层级={scenario['expect_layer']} | Runbook={scenario['expect_runbook']}")
    print(f"  运行: {repeat} 次 | 并发: {concurrency}")
    print(f"{'─' * 60}")

    print_lock = threading.Lock()

    def _run_one(i: int) -> Dict:
        with print_lock:
            print(f"  🚀 #{i}/{repeat} 请求中...")
        m = run_single_request(base_url, scenario["query"], timeout, i, save_dir)
        with print_lock:
            if m.get("success"):
                layer_ok = "✅" if m["layer"] == scenario["expect_layer"] else "❌"
                rb_ok = "✅" if m.get("runbook_core") and scenario["expect_runbook"].lower() in m["runbook_core"].lower() else "❌"
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
    """打印汇总报告"""
    all_ok = [r for sr in results for r in sr.ok_runs]
    all_runs = [r for sr in results for r in sr.runs]
    n_ok = len(all_ok)
    n_fail = len(all_runs) - n_ok

    print(f"\n{'=' * 60}")
    print(f"  AIOps Copilot E2E 准确率报告")
    print(f"{'=' * 60}")
    print(f"场景数: {len(results)} | 总运行: {len(all_runs)} | 成功: {n_ok} | 失败: {n_fail}")
    print(f"总耗时: {total_elapsed:.0f}s ({total_elapsed/60:.1f}m)")
    print()

    if not n_ok:
        print("❌ 无成功请求，无法计算指标")
        return

    # ── 每场景明细 ──
    print(f"{'─' * 60}")
    print(f"  场景明细")
    print(f"{'─' * 60}")
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
    """保存 JSON 汇总报告"""
    all_ok = [r for sr in results for r in sr.ok_runs]
    all_runs = [r for sr in results for r in sr.runs]
    n_ok = len(all_ok)

    mttrs = [r["mttr_seconds"] for r in all_ok]
    ev_rates = [r["evidence_rate"] for r in all_ok if r.get("evidence_rate") is not None]

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_elapsed_seconds": round(total_elapsed, 1),
        "total_runs": len(all_runs),
        "success": n_ok,
        "failed": len(all_runs) - n_ok,
        "scenarios": {},
        "aggregate": {
            "mttr_avg_seconds": round(sum(mttrs) / len(mttrs), 1) if mttrs else None,
            "mttr_pass": (sum(mttrs) / len(mttrs) < 900) if mttrs else None,
            "layer_accuracy": round(sum(sr.layer_correct for sr in results) / n_ok * 100, 1) if n_ok else None,
            "layer_pass": (sum(sr.layer_correct for sr in results) / n_ok >= 0.8) if n_ok else None,
            "runbook_rate": round(sum(sr.runbook_matched for sr in results) / n_ok * 100, 1) if n_ok else None,
            "runbook_pass": (sum(sr.runbook_matched for sr in results) / n_ok >= 0.8) if n_ok else None,
            "evidence_avg": round(sum(ev_rates) / len(ev_rates) * 100, 1) if ev_rates else None,
            "evidence_pass": (sum(ev_rates) / len(ev_rates) >= 0.8) if ev_rates else None,
        },
    }

    for sr in results:
        report["scenarios"][sr.scenario_id] = {
            "name": sr.name,
            "expect_layer": sr.expect_layer,
            "expect_runbook": sr.expect_runbook,
            "runs": len(sr.runs),
            "success": len(sr.ok_runs),
            "layer_accuracy": round(sr.layer_accuracy * 100, 1) if sr.layer_accuracy is not None else None,
            "runbook_rate": round(sr.runbook_rate * 100, 1) if sr.runbook_rate is not None else None,
            "avg_mttr": round(sr.avg_mttr, 1) if sr.avg_mttr is not None else None,
            "avg_evidence_rate": round(sr.avg_evidence_rate * 100, 1) if sr.avg_evidence_rate is not None else None,
            "raw_metrics": sr.ok_runs,
        }

    (result_dir / "stats.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(
        description="AIOps Copilot E2E 场景准确率测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
内置场景:
  l0-volume-limit   L0 存储卷超限驱逐
  l1-taint-node     L1 节点 NotReady/Taint
  l2-oomkilled      L2 OOMKilled
  l3-imagepull      L3 镜像拉取失败
  l4-app-health     L4 应用健康检查失败
  all               运行所有场景

示例:
  python test_accuracy.py --scenario l2-oomkilled
  python test_accuracy.py --scenario all -n 3 -c 2
  python test_accuracy.py -q "自定义问题" --expect-layer L3 --expect-runbook l3-imagepull-failed
        """,
    )
    parser.add_argument("--scenario", "-s", default=None,
                        help="场景 ID（如 l2-oomkilled）或 'all' 运行全部")
    parser.add_argument("-n", "--repeat", type=int, default=1,
                        help="每个场景重复次数（默认 1）")
    parser.add_argument("-c", "--concurrency", type=int, default=1,
                        help="并发数（默认 1，串行执行）")
    parser.add_argument("-q", "--question", default=None,
                        help="自定义问题（不使用内置场景时）")
    parser.add_argument("--expect-layer", default=None,
                        help="期望层级（自定义问题时使用）")
    parser.add_argument("--expect-runbook", default=None,
                        help="期望 Runbook ID（自定义问题时使用）")
    parser.add_argument("--url", default="http://10.2.0.48:30800",
                        help="服务地址（默认 http://10.2.0.48:30800）")
    parser.add_argument("--timeout", type=int, default=900,
                        help="单请求超时秒数（默认 900）")
    args = parser.parse_args()

    # 确定要运行的场景列表
    scenarios_to_run: List[Tuple[str, Dict]] = []

    if args.scenario:
        if args.scenario == "all":
            scenarios_to_run = list(SCENARIOS.items())
        elif args.scenario in SCENARIOS:
            scenarios_to_run = [(args.scenario, SCENARIOS[args.scenario])]
        else:
            print(f"❌ 未知场景: {args.scenario}")
            print(f"可用场景: {', '.join(SCENARIOS.keys())}, all")
            sys.exit(1)
    elif args.question:
        # 自定义问题模式
        custom = {
            "name": "自定义场景",
            "query": args.question,
            "expect_layer": args.expect_layer or "UNKNOWN",
            "expect_runbook": args.expect_runbook or "",
        }
        scenarios_to_run = [("custom", custom)]
    else:
        parser.print_help()
        print("\n❌ 请指定 --scenario 或 -q 参数")
        sys.exit(1)

    # 创建结果目录
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = Path("testreports") / ts
    result_dir.mkdir(parents=True, exist_ok=True)

    # 打印配置
    print("=" * 60)
    print("  AIOps Copilot E2E 准确率测试")
    print("=" * 60)
    print(f"服务:   {args.url}")
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
        sr = run_scenario(args.url, sid, scenario, args.repeat, args.concurrency, args.timeout, result_dir)
        results.append(sr)

    total_elapsed = time.time() - start

    # 输出报告
    print_report(results, total_elapsed, result_dir)
    save_report(results, total_elapsed, result_dir)


if __name__ == "__main__":
    main()
