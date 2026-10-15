#!/usr/bin/env python3
"""
联邦查询 - 并发聚合器

职责：
1. 并发调用所有已启用的子集群
2. Token 估算与单报告压缩
3. 调用 LLM 合成多集群统一报告（流式输出）
4. 保存子集群报告到本地
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

import litellm

from app.core.federation.client import SubAgentClient, SubAgentResult
from app.core.federation.registry import AgentRegistry
from app.core.prompts import (
    FEDERATION_COMPRESSION_PROMPT,
    FEDERATION_SYNTHESIS_PROMPT,
)

logger = logging.getLogger(__name__)

# 多集群协调者合成提示词（独立常量，不影响单集群 prompts.py）


COMPRESS_PROMPT = FEDERATION_COMPRESSION_PROMPT


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
        api_base: Optional[str] = None,
    ):
        self._registry = registry
        self._max_tokens_per_agent = max_tokens_per_agent
        self._synthesis_timeout = synthesis_timeout
        self._client = SubAgentClient()
        self._model = model
        self._api_key = api_key
        self._api_base = api_base

    async def query_all(
        self,
        question: str,
        max_steps: int,
        conclusion_max_tokens: int = 8192,
        endpoint_path: str = "/ask",
    ) -> List[SubAgentResult]:
        """并发查询所有已启用的子集群"""
        agents = self._registry.get_enabled_agents()
        if not agents:
            logger.warning("[FEDERATION] 没有已启用的子集群，跳过联邦查询")
            return []

        logger.info(
            "[FEDERATION] 开始并发查询 %s 个子集群，问题: %s...", len(agents), question[:60]
        )

        tasks = [
            self._client.query(
                agent=agent,
                question=question,
                max_steps=max_steps,
                conclusion_max_tokens=conclusion_max_tokens,
                timeout=self._synthesis_timeout,
                endpoint_path=endpoint_path,
            )
            for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # 保存子集群报告到本地
        self._save_reports(results)

        return list(results)

    def _save_reports(self, results: List[SubAgentResult]) -> None:
        """保存子集群报告到本地目录"""
        try:
            # 创建 reports 目录
            reports_dir = Path(os.environ.get("REPORTS_DIR", "/tmp/aiops/reports"))
            reports_dir.mkdir(parents=True, exist_ok=True)

            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for result in results:
                if not result.success:
                    continue

                # 文件名格式：{cluster_name}_{timestamp}.md
                filename = f"{result.name}_{timestamp}.md"
                filepath = reports_dir / filename

                # 写入报告
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# 子集群诊断报告 - {result.name}\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**集群 URL**: {result.url}\n")
                    f.write(f"**耗时**: {result.elapsed_seconds:.1f} 秒\n\n")
                    f.write("---\n\n")
                    f.write(result.text)

                logger.info("[FEDERATION] 已保存 %s 报告到: %s", result.name, filepath)

        except Exception as exc:
            logger.error("[FEDERATION] 保存报告失败: %s", exc, exc_info=True)

    def _compress_single(self, result: SubAgentResult) -> str:
        """调用 LLM 将单个子集群报告压缩为关键摘要"""
        before_tokens = _estimate_tokens(result.text)
        logger.info(
            "[FEDERATION] %s 报告超出阈值（约 %s tokens），开始压缩...", result.name, before_tokens
        )
        prompt = COMPRESS_PROMPT + result.text
        try:
            _completion_kwargs = dict(
                model=self._model,
                api_key=self._api_key,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                max_tokens=1200,
            )
            if self._api_base:
                _completion_kwargs["base_url"] = self._api_base
            resp = litellm.completion(**_completion_kwargs)
            compressed = resp.choices[0].message.content or result.text
            after_tokens = _estimate_tokens(compressed)
            logger.info(
                "[FEDERATION] %s 压缩完成: %s %s tokens", result.name, before_tokens, after_tokens
            )
            return compressed
        except Exception as exc:
            logger.error("[FEDERATION] %s 压缩失败，使用原始文本: %s", result.name, exc)
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
        # max_tokens_per_agent=0 表示不设限，但需检测模型上下文限制
        MODEL_CONTEXT_LIMIT = 60000  # DeepSeek 上下文限制约 64K tokens，预留 4K
        contents: List[str] = []
        total_tokens = 0

        for r in successful:
            text = r.text
            token_count = _estimate_tokens(text)

            # 如果设置了单个子集群限制（非0），则按限制压缩
            if self._max_tokens_per_agent > 0 and token_count > self._max_tokens_per_agent:
                text = self._compress_single(r)
                token_count = _estimate_tokens(text)

            contents.append((r.name, r.url, text, token_count))
            total_tokens += token_count

        # 如果总 token 数超过模型上下文限制，强制压缩
        if total_tokens > MODEL_CONTEXT_LIMIT:
            logger.warning(
                "[FEDERATION] 总 tokens (%s) 超过模型限制 (%s)，开始强制压缩...", total_tokens, MODEL_CONTEXT_LIMIT
            )
            compressed_contents = []
            total_tokens = 0
            for name, url, text, _ in contents:
                # 重新创建 SubAgentResult 用于压缩
                temp_result = SubAgentResult(
                    name=name, url=url, success=True, text=text, error=None, elapsed_seconds=0
                )
                compressed_text = self._compress_single(temp_result)
                compressed_tokens = _estimate_tokens(compressed_text)
                compressed_contents.append((name, url, compressed_text, compressed_tokens))
                total_tokens += compressed_tokens
            contents = compressed_contents

        logger.info(
            "[FEDERATION] 开始 LLM 合成，总输入 tokens 约: %s，集群数: %s", total_tokens, len(contents)
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
            _completion_kwargs = dict(
                model=self._model,
                api_key=self._api_key,
                messages=messages,
                stream=True,
            )
            if self._api_base:
                _completion_kwargs["base_url"] = self._api_base
            stream = litellm.completion(**_completion_kwargs)
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            logger.error("[FEDERATION] LLM 合成失败: %s", exc, exc_info=True)
            yield f"\n\n❌ LLM 合成失败: {exc}\n"
            yield "\n**各子集群原始报告（未合成）：**\n\n"
            for name, _url, text, _ in contents:
                yield f"---\n### 集群: {name}\n\n{text}\n\n"
