#!/usr/bin/env python3
"""
联邦查询真实集成测试

测试策略：用本机运行的 AIOps 服务（localhost:8000）模拟"子集群"，
执行完整的 联邦查询链路：
  1. SubAgentClient 向 localhost:8000/ask 发起真实 HTTP 请求
  2. FederationAggregator 并发聚合（此处只有1个"子集群"）
  3. 调用真实 LLM（DeepSeek）合成多集群报告
  4. 流式输出到控制台

运行方式（在 robusta 目录下）：
  .venv/bin/python test/test_federation_real.py
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

# federation 模块导入（service.py 会触发 MCP 补丁，不影响测试）
from app.core.federation.registry import AgentRegistry, SubAgentConfig
from app.core.federation.client import SubAgentClient, SubAgentResult
from app.core.federation.aggregator import FederationAggregator
from app.core.federation import FederationCoordinator


SUB_CLUSTER_URL = os.getenv("TEST_SUB_CLUSTER_URL", "http://localhost:8000")
QUESTION = os.getenv("TEST_QUESTION", "集群当前有哪些异常问题？请给出总结")
MAX_STEPS = int(os.getenv("TEST_MAX_STEPS", "8"))


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# 阶段 1：SubAgentClient 单独测试
# ============================================================
async def test_client_query():
    separator("阶段1：SubAgentClient 真实 HTTP 调用")
    agent = SubAgentConfig(name="local-self", url=SUB_CLUSTER_URL)
    client = SubAgentClient()

    print(f"目标: {agent.url}/ask")
    print(f"问题: {QUESTION}")
    print(f"max_steps: {MAX_STEPS}")
    print("-" * 60)

    t0 = time.monotonic()
    result = await client.query(agent=agent, question=QUESTION, max_steps=MAX_STEPS, timeout=300)
    elapsed = time.monotonic() - t0

    if result.success:
        print(f"✅ 成功！耗时: {elapsed:.1f}s，响应长度: {len(result.text)} chars")
        print("\n--- 响应前 500 chars ---")
        print(result.text[:500])
        if len(result.text) > 500:
            print(f"... (共 {len(result.text)} chars)")
    else:
        print(f"❌ 失败: {result.error}")
        return None

    return result


# ============================================================
# 阶段 2：FederationCoordinator 完整链路
# ============================================================
def test_federation_coordinator(sub_result: SubAgentResult):
    separator("阶段2：FederationCoordinator 完整合成")

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    if model and not model.startswith("deepseek/") and "deepseek" in model.lower():
        model = f"deepseek/{model}"

    print(f"LLM 模型: {model}")
    print(f"子集群数: 1（local-self → {SUB_CLUSTER_URL}）")
    print("-" * 60)

    cfg = {
        "enabled": True,
        "max_tokens_per_agent": 12000,
        "synthesis_timeout": 300,
        "sub_agents": [
            {"name": "local-self", "url": SUB_CLUSTER_URL, "enabled": True}
        ],
    }
    coordinator = FederationCoordinator.from_config(cfg, model=model, api_key=api_key)

    print(f"\n🌐 调用 ask_stream（将并发查询子集群 + LLM 合成）\n")
    t0 = time.monotonic()
    chunks = []
    for chunk in coordinator.ask_stream(question=QUESTION, max_steps=MAX_STEPS):
        print(chunk, end="", flush=True)
        chunks.append(chunk)

    elapsed = time.monotonic() - t0
    full_output = "".join(chunks)

    separator("阶段2 完成")
    print(f"总耗时: {elapsed:.1f}s")
    print(f"总输出: {len(full_output)} chars")
    return full_output


# ============================================================
# 主入口
# ============================================================
async def main():
    print("\n" + "🚀 " * 20)
    print("  联邦查询真实集成测试")
    print("🚀 " * 20)
    print(f"\n子集群地址: {SUB_CLUSTER_URL}")
    print(f"测试问题:   {QUESTION}\n")

    # 阶段1：测试 HTTP 客户端
    sub_result = await test_client_query()
    if sub_result is None:
        print("\n❌ 阶段1失败，请确认服务在 localhost:8000 正常运行")
        print("  启动命令: cd robusta && python run.py")
        sys.exit(1)

    # 阶段2：完整联邦链路
    output = test_federation_coordinator(sub_result)

    separator("测试完成")
    print("✅ 全部阶段通过！")
    print(f"  - SubAgentClient 真实 HTTP 调用: ✅")
    print(f"  - FederationCoordinator 完整合成: ✅")


if __name__ == "__main__":
    asyncio.run(main())
