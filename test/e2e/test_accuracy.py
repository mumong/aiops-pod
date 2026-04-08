#!/usr/bin/env python3
"""
AIOps Copilot 准确率测试工具

用法:
    python test_accuracy.py                          # 默认 10 并发
    python test_accuracy.py -n 100                   # 100 次请求
    python test_accuracy.py -n 100 -c 5              # 100 次请求，5 并发
    python test_accuracy.py -n 100 -c 10 -q "集群有什么问题"
    python test_accuracy.py -n 3 --url http://10.2.0.48:30800
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import httpx
except ImportError:
    print("需要 httpx: pip install httpx")
    sys.exit(1)

LAYER_PATTERN = re.compile(
    r'(?:层级|layer)[：:\s]*\*{0,2}\s*(L[0-4](?:\s*\+\s*L[0-4])*|QUERY)\b',
    re.IGNORECASE
)
LAYER_TABLE_PATTERN = re.compile(
    r'\|\s*\*{0,2}问题层级\*{0,2}\s*\|\s*\*{0,2}\s*(L[0-4])',
    re.IGNORECASE
)


def extract_layer_from_response(text: str) -> str:
    """从完整 API 响应文本中提取 layer（支持多层级如 L0+L1）"""
    # 方法1: 从诊断报告表格提取 "| **问题层级** | L0 ..."
    m = LAYER_TABLE_PATTERN.search(text)
    if m:
        return m.group(1).upper()
    # 方法2: "层级: L0 + L1（主层级: L0）" 或 "**层级**: L0"
    m = LAYER_PATTERN.search(text)
    if m:
        # 可能是 "L0 + L1"，取第一个（主层级）
        val = m.group(1).upper()
        first = re.match(r'(L[0-4]|QUERY)', val)
        return first.group(1) if first else val
    # 方法3: 扫描所有行找 L0-L4，按出现频率
    layer_counts = {}
    for line in text.split('\n'):
        for lm in re.finditer(r'\b(L[0-4])\b', line):
            layer_counts[lm.group(1)] = layer_counts.get(lm.group(1), 0) + 1
    if layer_counts:
        return max(layer_counts, key=layer_counts.get)
    return "UNKNOWN"


def extract_all_layers_from_response(text: str) -> list:
    """提取所有检测到的层级（用于多层级统计）"""
    # 从 "层级: L0 + L1（主层级: L0）" 提取
    m = re.search(r'层级[：:\s]*\*{0,2}\s*(L[0-4](?:\s*\+\s*L[0-4])+)', text)
    if m:
        return re.findall(r'L[0-4]', m.group(1))
    # 单层级
    single = extract_layer_from_response(text)
    return [single] if single != "UNKNOWN" else []


class TestRunner:
    def __init__(self, base_url: str, question: str, total: int,
                 concurrency: int, max_steps: int, timeout: int):
        self.base_url = base_url.rstrip('/')
        self.question = question
        self.total = total
        self.concurrency = concurrency
        self.max_steps = max_steps
        self.timeout = timeout

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.result_dir = Path("testreports") / ts
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # 统计
        self.success = 0
        self.failed = 0
        self.errors: list[str] = []
        self.layers: list[str] = []
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
                # 用流式接口，保存完整原始输出（和 curl 看到的一致）
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

                # 保存完整原始响应
                filepath.write_text(body, encoding="utf-8")

                if len(body) > 50:
                    layer = extract_layer_from_response(body)
                    async with self.lock:
                        self.success += 1
                        self.layers.append(layer)
                    print(f"  ✅ #{idx} 完成 ({elapsed:.0f}s) → {layer} [{len(body)}字符]")
                else:
                    reason = body[:200] if body else "空响应"
                    async with self.lock:
                        self.failed += 1
                        self.errors.append(f"#{idx}: HTTP {r.status_code} - {reason}")
                    print(f"  ❌ #{idx} 失败 ({elapsed:.0f}s) HTTP {r.status_code}: {reason[:80]}")

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
        self.print_stats(elapsed)
        self.save_stats(elapsed)

    def print_stats(self, elapsed: float):
        print(f"\n{'=' * 50}")
        print(f"  测试结果统计")
        print(f"{'=' * 50}")
        print(f"总请求:  {self.total}")
        print(f"成功:    {self.success}")
        print(f"失败:    {self.failed}")
        print(f"耗时:    {elapsed:.0f}s")
        print(f"并发:    {self.concurrency}")
        print()

        if self.layers:
            from collections import Counter
            counts = Counter(self.layers)
            print("📊 层级分布:")
            print(f"{'层级':<10} {'次数':<8} {'占比':<8}")
            print("-" * 26)
            for layer, count in counts.most_common():
                pct = count / len(self.layers) * 100
                print(f"{layer:<10} {count:<8} {pct:.1f}%")
            print()

        if self.errors:
            print(f"❌ 错误详情 (前10条):")
            for err in self.errors[:10]:
                print(f"  {err}")
            if len(self.errors) > 10:
                print(f"  ... 还有 {len(self.errors) - 10} 条")
            print()

        print(f"📁 结果目录: {self.result_dir}/")

    def save_stats(self, elapsed: float):
        from collections import Counter
        counts = Counter(self.layers)

        stats = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "total": self.total,
                "concurrency": self.concurrency,
                "question": self.question,
                "base_url": self.base_url,
                "max_steps": self.max_steps,
                "timeout": self.timeout,
            },
            "results": {
                "success": self.success,
                "failed": self.failed,
                "elapsed_seconds": round(elapsed, 1),
                "layer_distribution": dict(counts.most_common()),
                "layers": self.layers,
            },
            "errors": self.errors,
        }
        (self.result_dir / "stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main():
    parser = argparse.ArgumentParser(description="AIOps Copilot 准确率测试")
    parser.add_argument("-n", "--total", type=int, default=10, help="总请求数 (默认 10)")
    parser.add_argument("-c", "--concurrency", type=int, default=5, help="并发数 (默认 5)")
    parser.add_argument("-q", "--question", default="我的集群有什么问题？", help="测试问题")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="服务地址")
    parser.add_argument("--max-steps", type=int, default=20, help="LLM 最大步数")
    parser.add_argument("--timeout", type=int, default=900, help="单请求超时秒数 (默认 900)")
    args = parser.parse_args()

    print("=" * 50)
    print("  AIOps Copilot 准确率测试")
    print("=" * 50)
    print(f"总请求:  {args.total}")
    print(f"并发:    {args.concurrency}")
    print(f"服务:    {args.url}")
    print(f"问题:    {args.question}")
    print(f"超时:    {args.timeout}s")
    print("=" * 50)
    print()

    runner = TestRunner(
        base_url=args.url,
        question=args.question,
        total=args.total,
        concurrency=args.concurrency,
        max_steps=args.max_steps,
        timeout=args.timeout,
    )
    asyncio.run(runner.run_all())


if __name__ == "__main__":
    main()
