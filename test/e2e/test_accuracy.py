#!/usr/bin/env python3
"""
AIOps Copilot 质量指标测试工具

测试指标：
  1. MTTR（平均修复时间）— 从请求到响应的端到端耗时
  2. 根因定位准确率 — 定位到正确层级的比例
  3. Runbook 覆盖率 — 诊断追踪中引用了正确 Runbook 的比例
  4. 证据采集率 — 实际采集证据数 / 计划采集数

用法:
    python test_accuracy.py -n 50 -c 5                    # 50 次请求，5 并发
    python test_accuracy.py -n 3 -c 2 --expect-layer L0   # 指定期望层级
    python test_accuracy.py -n 10 -c 3 --expect-layer L3 --expect-runbook "ImagePull"
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import httpx
except ImportError:
    print("需要 httpx: pip install httpx")
    sys.exit(1)


# ── 指标提取函数 ──────────────────────────────────────────────

def extract_layer(text: str) -> str:
    """提取诊断层级"""
    # 方法1: 表格 "| **问题层级** | L0 ..."
    m = re.search(r'\|\s*\*{0,2}问题层级\*{0,2}\s*\|\s*\*{0,2}\s*(L[0-4]|QUERY|HEALTHY)', text, re.I)
    if m:
        return m.group(1).upper()
    # 方法2: "**层级**: L0" 或 "层级: L0"
    m = re.search(r'(?:层级|layer)[：:\s]*\*{0,2}\s*(L[0-4](?:\s*\+\s*L[0-4])*|QUERY|HEALTHY)', text, re.I)
    if m:
        val = m.group(1).upper()
        first = re.match(r'(L[0-4]|QUERY|HEALTHY)', val)
        return first.group(1) if first else val
    # 方法3: 频率统计
    counts = {}
    for lm in re.finditer(r'\b(L[0-4])\b', text):
        counts[lm.group(1)] = counts.get(lm.group(1), 0) + 1
    return max(counts, key=counts.get) if counts else "UNKNOWN"


def extract_mttr(text: str, wall_clock: float) -> float:
    """提取 MTTR（秒）。优先从报告中提取，回退到 wall clock"""
    # 从 "总耗时: 2.2m" 或 "总耗时: 45.3s" 提取
    m = re.search(r'总耗时[：:\s]*([\d.]+)(s|m|h)', text)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit == 'm':
            return val * 60
        elif unit == 'h':
            return val * 3600
        return val
    return wall_clock


def extract_evidence_rate(text: str) -> Optional[float]:
    """提取证据采集率。返回 0.0-1.0 或 None"""
    # 方法1: 从 "证据完整率 | > 90% | 80% (4/5) | ✅" 表格提取
    m = re.search(r'证据完整率.*?\|\s*(\d+)%\s*\((\d+)/(\d+)\)', text)
    if m:
        collected = int(m.group(2))
        planned = int(m.group(3))
        return collected / planned if planned > 0 else None
    # 方法2: 从 "证据: 2/3 项" 提取
    m = re.search(r'证据[：:\s]*(\d+)/(\d+)\s*项', text)
    if m:
        collected = int(m.group(1))
        planned = int(m.group(2))
        return collected / planned if planned > 0 else None
    # 方法3: 从 "证据完整度 | 67%" 提取
    m = re.search(r'证据完整[度率][：:\s|]*(\d+)%', text)
    if m:
        return int(m.group(1)) / 100.0
    return None


def extract_evidence_details(text: str) -> List[Dict]:
    """提取证据采集清单详情（每项证据的名称、级别、状态）"""
    details = []
    # 匹配表格行: | 1 | 磁盘使用率（df -h 输出） | CRITICAL | ✅ |
    for m in re.finditer(
        r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*(CRITICAL|IMPORTANT|OPTIONAL)\s*\|\s*(✅|❌)\s*\|',
        text
    ):
        details.append({
            "description": m.group(1).strip(),
            "level": m.group(2).strip(),
            "collected": m.group(3) == "✅",
        })
    return details


def extract_runbook(text: str) -> Dict[str, Optional[str]]:
    """提取核心 Runbook 和参考 Runbook"""
    core = None
    refs = None
    m = re.search(r'\*{0,2}核心\s*Runbook\*{0,2}[：:\s]*(.*?)(?:\n|$)', text)
    if m:
        core = m.group(1).strip().strip('*')
    m = re.search(r'\*{0,2}参考\s*Runbook\*{0,2}[：:\s]*(.*?)(?:\n|$)', text)
    if m:
        refs = m.group(1).strip().strip('*')
    return {"core": core, "refs": refs}


def extract_tool_calls(text: str) -> int:
    """提取工具调用次数"""
    m = re.search(r'\*{0,2}工具调用\*{0,2}[：:\s]*(\d+)\s*次', text)
    return int(m.group(1)) if m else 0


def extract_llm_calls(text: str) -> int:
    """提取 LLM 调用次数"""
    m = re.search(r'\*{0,2}LLM\s*调用\*{0,2}[：:\s]*(\d+)\s*次', text)
    return int(m.group(1)) if m else 0


def extract_all_metrics(text: str, wall_clock: float) -> Dict:
    """从响应文本中提取所有质量指标"""
    runbook = extract_runbook(text)
    ev_details = extract_evidence_details(text)
    return {
        "layer": extract_layer(text),
        "mttr_seconds": extract_mttr(text, wall_clock),
        "evidence_rate": extract_evidence_rate(text),
        "evidence_details": ev_details,
        "evidence_collected": sum(1 for e in ev_details if e["collected"]),
        "evidence_planned": len(ev_details),
        "runbook_core": runbook["core"],
        "runbook_refs": runbook["refs"],
        "tool_calls": extract_tool_calls(text),
        "llm_calls": extract_llm_calls(text),
        "response_length": len(text),
    }


# ── 测试运行器 ──────────────────────────────────────────────

class TestRunner:
    def __init__(self, base_url: str, question: str, total: int,
                 concurrency: int, max_steps: int, timeout: int,
                 expect_layer: Optional[str] = None,
                 expect_runbook: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.question = question
        self.total = total
        self.concurrency = concurrency
        self.max_steps = max_steps
        self.timeout = timeout
        self.expect_layer = expect_layer
        self.expect_runbook = expect_runbook

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.result_dir = Path("testreports") / ts
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # 每次请求的指标
        self.metrics: List[Dict] = []
        self.failed = 0
        self.errors: List[str] = []
        self.lock = asyncio.Lock()

    async def check_health(self):
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get(f"{self.base_url}/health")
                r.raise_for_status()
                print("✅ 服务健康检查通过\n")
            except Exception as e:
                print(f"❌ 服务不可用: {e}")
                sys.exit(1)

    async def run_single(self, idx: int, semaphore: asyncio.Semaphore):
        async with semaphore:
            start = time.time()
            print(f"  🚀 #{idx} 开始请求...")

            filepath = self.result_dir / f"response_{idx}.txt"
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    chunks = []
                    async with client.stream(
                        "GET",
                        f"{self.base_url}/ask",
                        params={
                            "q": self.question,
                            "stream": "true",
                            "format": "text",
                            "max_steps": str(self.max_steps),
                        },
                    ) as r:
                        if r.status_code != 200:
                            body = await r.aread()
                            raise Exception(f"HTTP {r.status_code}: {body.decode()[:200]}")
                        async for chunk in r.aiter_text():
                            chunks.append(chunk)

                body = "".join(chunks)
                elapsed = time.time() - start
                filepath.write_text(body, encoding="utf-8")

                if len(body) > 50:
                    m = extract_all_metrics(body, elapsed)
                    m["idx"] = idx
                    m["elapsed"] = elapsed
                    m["success"] = True

                    async with self.lock:
                        self.metrics.append(m)

                    ev_str = f"{m['evidence_rate']:.0%}" if m['evidence_rate'] is not None else "N/A"
                    rb_str = m['runbook_core'][:30] if m['runbook_core'] else "无"
                    print(
                        f"  ✅ #{idx} 完成 ({elapsed:.0f}s) "
                        f"→ {m['layer']} | MTTR={m['mttr_seconds']:.0f}s | "
                        f"证据={ev_str} | Runbook={rb_str}"
                    )
                else:
                    async with self.lock:
                        self.failed += 1
                        self.errors.append(f"#{idx}: 空响应")
                    print(f"  ❌ #{idx} 失败 ({elapsed:.0f}s): 空响应")

            except httpx.TimeoutException:
                elapsed = time.time() - start
                async with self.lock:
                    self.failed += 1
                    self.errors.append(f"#{idx}: 超时 ({elapsed:.0f}s)")
                filepath.write_text(f"TIMEOUT after {elapsed:.0f}s", encoding="utf-8")
                print(f"  ❌ #{idx} 超时 ({elapsed:.0f}s)")

            except Exception as e:
                elapsed = time.time() - start
                async with self.lock:
                    self.failed += 1
                    self.errors.append(f"#{idx}: {type(e).__name__}: {e}")
                filepath.write_text(f"ERROR: {e}", encoding="utf-8")
                print(f"  ❌ #{idx} 错误 ({elapsed:.0f}s): {e}")

    async def run_all(self):
        await self.check_health()
        print(f"📡 开始 {self.total} 次请求（并发 {self.concurrency}）...\n")

        semaphore = asyncio.Semaphore(self.concurrency)
        start = time.time()
        tasks = [self.run_single(i, semaphore) for i in range(1, self.total + 1)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        self.print_report(elapsed)
        self.save_report(elapsed)

    def print_report(self, total_elapsed: float):
        ok = [m for m in self.metrics if m["success"]]
        n = len(ok)

        print(f"\n{'=' * 60}")
        print(f"  AIOps Copilot 质量指标报告")
        print(f"{'=' * 60}")
        print(f"总请求: {self.total} | 成功: {n} | 失败: {self.failed} | 总耗时: {total_elapsed:.0f}s")
        if self.expect_layer:
            print(f"期望层级: {self.expect_layer}")
        if self.expect_runbook:
            print(f"期望 Runbook 关键词: {self.expect_runbook}")
        print()

        if not ok:
            print("❌ 无成功请求，无法计算指标")
            return

        # ── 指标 1: MTTR ──
        mttrs = [m["mttr_seconds"] for m in ok]
        avg_mttr = sum(mttrs) / len(mttrs)
        max_mttr = max(mttrs)
        min_mttr = min(mttrs)
        p95_mttr = sorted(mttrs)[int(len(mttrs) * 0.95)] if len(mttrs) >= 2 else max_mttr
        mttr_pass = avg_mttr < 900  # 15 分钟

        print(f"📊 指标 1: MTTR（平均修复时间）")
        print(f"   阈值: < 15 分钟")
        print(f"   平均: {avg_mttr:.1f}s ({avg_mttr/60:.1f}m)")
        print(f"   最小: {min_mttr:.1f}s | 最大: {max_mttr:.1f}s | P95: {p95_mttr:.1f}s")
        print(f"   结果: {'✅ 达标' if mttr_pass else '❌ 未达标'}")
        print()

        # ── 指标 2: 根因定位准确率 ──
        layers = [m["layer"] for m in ok]
        layer_counts = Counter(layers)

        if self.expect_layer:
            correct = sum(1 for l in layers if l == self.expect_layer)
            accuracy = correct / n * 100
            accuracy_pass = accuracy >= 80
            print(f"📊 指标 2: 根因定位准确率")
            print(f"   阈值: >= 80%")
            print(f"   期望: {self.expect_layer} | 正确: {correct}/{n} = {accuracy:.1f}%")
            print(f"   结果: {'✅ 达标' if accuracy_pass else '❌ 未达标'}")
        else:
            accuracy = None
            accuracy_pass = None
            print(f"📊 指标 2: 根因定位分布（未指定期望层级，仅展示分布）")

        print(f"   {'层级':<10} {'次数':<8} {'占比':<8}")
        print(f"   {'-'*26}")
        for layer, count in layer_counts.most_common():
            pct = count / n * 100
            print(f"   {layer:<10} {count:<8} {pct:.1f}%")
        print()

        # ── 指标 3: Runbook 覆盖率 ──
        # 只统计故障诊断模式（排除 QUERY/HEALTHY）
        diag_metrics = [m for m in ok if m["layer"] not in ("QUERY", "HEALTHY", "UNKNOWN")]
        if diag_metrics:
            has_runbook = sum(1 for m in diag_metrics if m["runbook_core"] and m["runbook_core"] != "无")
            rb_coverage = has_runbook / len(diag_metrics) * 100
            rb_pass = rb_coverage >= 80

            # 如果指定了期望 Runbook 关键词
            if self.expect_runbook:
                correct_rb = sum(
                    1 for m in diag_metrics
                    if m["runbook_core"] and self.expect_runbook.lower() in m["runbook_core"].lower()
                )
                rb_accuracy = correct_rb / len(diag_metrics) * 100
            else:
                rb_accuracy = None

            print(f"📊 指标 3: Runbook 覆盖率（仅故障诊断模式，{len(diag_metrics)} 次）")
            print(f"   阈值: >= 80%")
            print(f"   有核心 Runbook: {has_runbook}/{len(diag_metrics)} = {rb_coverage:.1f}%")
            if rb_accuracy is not None:
                print(f"   匹配期望 Runbook: {correct_rb}/{len(diag_metrics)} = {rb_accuracy:.1f}%")
            print(f"   结果: {'✅ 达标' if rb_pass else '❌ 未达标'}")

            # Runbook 分布
            rb_counts = Counter(m.get("runbook_core", "无") for m in diag_metrics)
            print(f"   核心 Runbook 分布:")
            for rb, count in rb_counts.most_common(5):
                print(f"     {rb[:50]}: {count} 次")
        else:
            rb_coverage = None
            rb_pass = None
            print(f"📊 指标 3: Runbook 覆盖率（无故障诊断请求，跳过）")
        print()

        # ── 指标 4: 证据采集率 ──
        ev_rates = [m["evidence_rate"] for m in diag_metrics if m.get("evidence_rate") is not None]
        if ev_rates:
            avg_ev = sum(ev_rates) / len(ev_rates) * 100
            min_ev = min(ev_rates) * 100
            ev_pass = avg_ev >= 80
            print(f"📊 指标 4: 证据采集率（{len(ev_rates)} 次有数据）")
            print(f"   阈值: >= 80%")
            print(f"   平均: {avg_ev:.1f}% | 最低: {min_ev:.1f}%")
            print(f"   结果: {'✅ 达标' if ev_pass else '❌ 未达标'}")

            # 展示证据采集详情（取第一个有详情的请求作为示例）
            for m in diag_metrics:
                details = m.get("evidence_details", [])
                if details:
                    print(f"   证据清单示例（请求 #{m.get('idx', '?')}）:")
                    for ev in details:
                        icon = "✅" if ev["collected"] else "❌"
                        print(f"     {icon} [{ev['level']}] {ev['description']}")
                    break
        else:
            avg_ev = None
            ev_pass = None
            print(f"📊 指标 4: 证据采集率（无数据，跳过）")
        print()

        # ── 汇总 ──
        print(f"{'=' * 60}")
        print(f"  质量指标汇总")
        print(f"{'=' * 60}")
        print(f"| {'指标':<20} | {'阈值':<12} | {'实际':<12} | {'状态':<8} |")
        print(f"|{'-'*22}|{'-'*14}|{'-'*14}|{'-'*10}|")
        print(f"| {'MTTR':<20} | {'< 15m':<12} | {f'{avg_mttr/60:.1f}m':<12} | {'✅' if mttr_pass else '❌':<8} |")
        if accuracy is not None:
            print(f"| {'根因定位准确率':<16} | {'>= 80%':<12} | {f'{accuracy:.1f}%':<12} | {'✅' if accuracy_pass else '❌':<8} |")
        if rb_coverage is not None:
            print(f"| {'Runbook 覆盖率':<17} | {'>= 80%':<12} | {f'{rb_coverage:.1f}%':<12} | {'✅' if rb_pass else '❌':<8} |")
        if avg_ev is not None:
            print(f"| {'证据采集率':<18} | {'>= 80%':<12} | {f'{avg_ev:.1f}%':<12} | {'✅' if ev_pass else '❌':<8} |")
        print()

        # 错误详情
        if self.errors:
            print(f"❌ 错误详情 (前5条):")
            for err in self.errors[:5]:
                print(f"  {err}")
            print()

        print(f"📁 结果目录: {self.result_dir}/")

    def save_report(self, total_elapsed: float):
        ok = [m for m in self.metrics if m["success"]]
        n = len(ok)

        mttrs = [m["mttr_seconds"] for m in ok] if ok else []
        layers = [m["layer"] for m in ok]
        diag = [m for m in ok if m["layer"] not in ("QUERY", "HEALTHY", "UNKNOWN")]
        ev_rates = [m["evidence_rate"] for m in diag if m.get("evidence_rate") is not None]

        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "total": self.total,
                "concurrency": self.concurrency,
                "question": self.question,
                "base_url": self.base_url,
                "expect_layer": self.expect_layer,
                "expect_runbook": self.expect_runbook,
            },
            "summary": {
                "success": n,
                "failed": self.failed,
                "total_elapsed_seconds": round(total_elapsed, 1),
            },
            "metrics": {
                "mttr": {
                    "avg_seconds": round(sum(mttrs) / len(mttrs), 1) if mttrs else None,
                    "min_seconds": round(min(mttrs), 1) if mttrs else None,
                    "max_seconds": round(max(mttrs), 1) if mttrs else None,
                    "p95_seconds": round(sorted(mttrs)[int(len(mttrs)*0.95)], 1) if len(mttrs) >= 2 else None,
                    "pass": (sum(mttrs)/len(mttrs) < 900) if mttrs else None,
                },
                "accuracy": {
                    "expect_layer": self.expect_layer,
                    "correct": sum(1 for l in layers if l == self.expect_layer) if self.expect_layer else None,
                    "total": n,
                    "rate": round(sum(1 for l in layers if l == self.expect_layer) / n * 100, 1) if self.expect_layer and n else None,
                    "layer_distribution": dict(Counter(layers).most_common()),
                    "pass": (sum(1 for l in layers if l == self.expect_layer) / n >= 0.8) if self.expect_layer and n else None,
                },
                "runbook_coverage": {
                    "diag_count": len(diag),
                    "has_runbook": sum(1 for m in diag if m.get("runbook_core") and m["runbook_core"] != "无"),
                    "rate": round(sum(1 for m in diag if m.get("runbook_core") and m["runbook_core"] != "无") / len(diag) * 100, 1) if diag else None,
                    "pass": (sum(1 for m in diag if m.get("runbook_core") and m["runbook_core"] != "无") / len(diag) >= 0.8) if diag else None,
                },
                "evidence_rate": {
                    "avg": round(sum(ev_rates) / len(ev_rates) * 100, 1) if ev_rates else None,
                    "min": round(min(ev_rates) * 100, 1) if ev_rates else None,
                    "count": len(ev_rates),
                    "pass": (sum(ev_rates) / len(ev_rates) >= 0.8) if ev_rates else None,
                },
            },
            "raw_metrics": [m for m in self.metrics],
            "errors": self.errors,
        }

        (self.result_dir / "stats.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )


def main():
    parser = argparse.ArgumentParser(description="AIOps Copilot 质量指标测试")
    parser.add_argument("-n", "--total", type=int, default=10, help="总请求数")
    parser.add_argument("-c", "--concurrency", type=int, default=5, help="并发数")
    parser.add_argument("-q", "--question", default="我的集群有什么问题？", help="测试问题")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="服务地址")
    parser.add_argument("--max-steps", type=int, default=20, help="LLM 最大步数")
    parser.add_argument("--timeout", type=int, default=900, help="单请求超时秒数")
    parser.add_argument("--expect-layer", default=None, help="期望的正确层级 (如 L0/L3)")
    parser.add_argument("--expect-runbook", default=None, help="期望的 Runbook 关键词 (如 ImagePull)")
    args = parser.parse_args()

    print("=" * 60)
    print("  AIOps Copilot 质量指标测试")
    print("=" * 60)
    print(f"总请求: {args.total} | 并发: {args.concurrency}")
    print(f"服务:   {args.url}")
    print(f"问题:   {args.question}")
    if args.expect_layer:
        print(f"期望层级: {args.expect_layer}")
    if args.expect_runbook:
        print(f"期望 Runbook: {args.expect_runbook}")
    print("=" * 60)
    print()

    runner = TestRunner(
        base_url=args.url,
        question=args.question,
        total=args.total,
        concurrency=args.concurrency,
        max_steps=args.max_steps,
        timeout=args.timeout,
        expect_layer=args.expect_layer,
        expect_runbook=args.expect_runbook,
    )
    asyncio.run(runner.run_all())


if __name__ == "__main__":
    main()
