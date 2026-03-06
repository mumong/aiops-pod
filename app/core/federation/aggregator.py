#!/usr/bin/env python3
"""
联邦查询 - 并发聚合器

职责：
1. 并发调用所有已启用的子集群
2. Token 估算与单报告压缩
3. 调用 LLM 合成多集群统一报告（流式输出）
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Generator, List, Optional

import litellm

from app.core.federation.client import SubAgentClient, SubAgentResult
from app.core.federation.registry import AgentRegistry

logger = logging.getLogger(__name__)

# 多集群协调者合成提示词（独立常量，不影响单集群 prompts.py）
FEDERATION_SYNTHESIS_PROMPT = """\
你是多集群 Kubernetes 运维协调专家。
以下是各子集群独立执行诊断后的报告，每份报告都由子集群的 AIOps Agent 生成。

请综合分析所有子集群的报告，输出一份多集群统一诊断报告，格式要求如下：

1. **各集群问题概览对比表**（Markdown 表格，含集群名称、主要问题、严重程度、状态）
2. **共性问题**（多个集群都存在的问题，按优先级排序）
3. **差异化问题**（仅个别集群存在的特有问题）
4. **跨集群优先级排序**（最需要立即处理的问题，不分集群）
5. **分集群修复建议**（按集群分节，给出具体操作步骤）

规范：
- 严格基于各子集群报告中的证据，不要臆测
- 保留原始报告中的关键数据（Pod 名称、错误信息、指标值等）
- 如某子集群查询失败，在报告中注明并跳过
"""

COMPRESS_PROMPT = """\
以下是某 Kubernetes 集群的诊断报告，请压缩为简洁摘要，保留：
- 集群名称/标识
- 主要问题列表（按严重程度排序）
- 根因分析（如有）
- 关键证据（Pod 名称、错误信息、关键指标）
- 修复建议摘要

输出长度控制在 800 字以内，使用中文 Markdown 格式。

原始报告：
"""


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数（英文约 4 char/token，中文约 2 char/token）"""
    return max(len(text) // 3, 1)


class FederationAggregator:
    """联邦查询并发聚合器"""

    def __init__(
        self,
        registry: AgentRegistry,
        max_tokens_per_agent: int = 12000,
        synthesis_timeout: float = 300.0,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._registry = registry
        self._max_tokens_per_agent = max_tokens_per_agent
        self._synthesis_timeout = synthesis_timeout
        self._client = SubAgentClient()
        self._model = model or os.getenv("DEEPSEEK_MODEL") or "deepseek/deepseek-chat"
        if self._model and not self._model.startswith("deepseek/") and "deepseek" in self._model.lower():
            self._model = f"deepseek/{self._model}"
        self._api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

    async def query_all(self, question: str, max_steps: int) -> List[SubAgentResult]:
        """并发查询所有已启用的子集群"""
        agents = self._registry.get_enabled_agents()
        if not agents:
            logger.warning("[FEDERATION] 没有已启用的子集群，跳过联邦查询")
            return []

        logger.info(
            f"[FEDERATION] 开始并发查询 {len(agents)} 个子集群，"
            f"问题: {question[:60]}..."
        )

        tasks = [
            self._client.query(
                agent=agent,
                question=question,
                max_steps=max_steps,
                timeout=self._synthesis_timeout,
            )
            for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    def _compress_single(self, result: SubAgentResult) -> str:
        """调用 LLM 将单个子集群报告压缩为关键摘要"""
        before_tokens = _estimate_tokens(result.text)
        logger.info(
            f"[FEDERATION] {result.name} 报告超出阈值"
            f"（约 {before_tokens} tokens），开始压缩..."
        )
        prompt = COMPRESS_PROMPT + result.text
        try:
            resp = litellm.completion(
                model=self._model,
                api_key=self._api_key,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                max_tokens=1200,
            )
            compressed = resp.choices[0].message.content or result.text
            after_tokens = _estimate_tokens(compressed)
            logger.info(
                f"[FEDERATION] {result.name} 压缩完成: "
                f"{before_tokens} → {after_tokens} tokens"
            )
            return compressed
        except Exception as exc:
            logger.error(f"[FEDERATION] {result.name} 压缩失败，使用原始文本: {exc}")
            return result.text

    def synthesize(
        self,
        question: str,
        results: List[SubAgentResult],
    ) -> Generator[str, None, None]:
        """
        合成多集群统一报告，以流式文本 yield。

        Args:
            question: 原始用户问题
            results: 各子集群的查询结果列表
        """
        # 过滤成功结果
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if not successful:
            yield "❌ 所有子集群查询均失败，无法生成联邦报告。\n\n"
            if failed:
                yield "**失败详情：**\n"
                for r in failed:
                    yield f"- `{r.name}` ({r.url}): {r.error}\n"
            return

        # 失败集群提示
        if failed:
            yield f"⚠️ 以下 {len(failed)} 个子集群查询失败，已从合成中排除：\n"
            for r in failed:
                yield f"- `{r.name}` ({r.url}): {r.error}\n"
            yield "\n"

        # Token 估算与压缩
        contents: List[str] = []
        total_tokens = 0
        for r in successful:
            text = r.text
            token_count = _estimate_tokens(text)
            if token_count > self._max_tokens_per_agent:
                text = self._compress_single(r)
                token_count = _estimate_tokens(text)
            contents.append((r.name, r.url, text, token_count))
            total_tokens += token_count

        logger.info(
            f"[FEDERATION] 开始 LLM 合成，总输入 tokens 约: {total_tokens}，"
            f"集群数: {len(contents)}"
        )

        # 构建 synthesis 消息
        sub_reports = "\n\n".join(
            f"---\n## 集群: {name} ({url})\n\n{text}"
            for name, url, text, _ in contents
        )
        user_message = (
            f"用户原始问题：{question}\n\n"
            f"以下是 {len(contents)} 个子集群的诊断报告：\n\n"
            f"{sub_reports}"
        )

        messages = [
            {"role": "system", "content": FEDERATION_SYNTHESIS_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # 流式 LLM 合成
        try:
            stream = litellm.completion(
                model=self._model,
                api_key=self._api_key,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            logger.error(f"[FEDERATION] LLM 合成失败: {exc}", exc_info=True)
            yield f"\n\n❌ LLM 合成失败: {exc}\n"
            yield "\n**各子集群原始报告（未合成）：**\n\n"
            for name, url, text, _ in contents:
                yield f"---\n### 集群: {name}\n\n{text}\n\n"
