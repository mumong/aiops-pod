#!/usr/bin/env python3
"""
联邦查询 - 子集群 HTTP 客户端

封装对子集群 /ask 端点的异步调用，超时安全，返回结构化结果。
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.core.federation.registry import SubAgentConfig

logger = logging.getLogger(__name__)


@dataclass
class SubAgentResult:
    """子集群查询结果"""
    name: str
    url: str
    success: bool
    text: str = ""
    error: str = ""
    elapsed_seconds: float = 0.0


class SubAgentClient:
    """异步 HTTP 客户端，调用单个子集群的 /ask 端点"""

    async def query(
        self,
        agent: SubAgentConfig,
        question: str,
        max_steps: int = 30,
        conclusion_max_tokens: int = 8192,
        timeout: float = 300.0,
    ) -> SubAgentResult:
        """
        向子集群发起同步（stream=false）查询请求。

        Args:
            agent: 子集群配置
            question: 用户问题
            max_steps: 最大执行步数
            conclusion_max_tokens: 诊断结论最大 token 数
            timeout: 超时秒数

        Returns:
            SubAgentResult
        """
        url = f"{agent.url}/ask"
        start = time.monotonic()
        logger.info(f"[FEDERATION] 开始查询子集群 {agent.name}: {url}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    url,
                    data={
                        "q": question,
                        "stream": "false",
                        "max_steps": str(max_steps),
                        "conclusion_max_tokens": str(conclusion_max_tokens),
                    },
                )
                resp.raise_for_status()
                text = resp.text
                elapsed = time.monotonic() - start
                logger.info(
                    f"[FEDERATION] {agent.name} 响应成功，"
                    f"长度: {len(text)} chars，耗时: {elapsed:.1f}s"
                )
                return SubAgentResult(
                    name=agent.name,
                    url=agent.url,
                    success=True,
                    text=text,
                    elapsed_seconds=elapsed,
                )
        except httpx.TimeoutException:
            elapsed = time.monotonic() - start
            err = f"请求超时（{timeout}s）"
            logger.error(f"[FEDERATION] {agent.name} {err}")
            return SubAgentResult(
                name=agent.name,
                url=agent.url,
                success=False,
                error=err,
                elapsed_seconds=elapsed,
            )
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - start
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            logger.error(f"[FEDERATION] {agent.name} 请求失败: {err}")
            return SubAgentResult(
                name=agent.name,
                url=agent.url,
                success=False,
                error=err,
                elapsed_seconds=elapsed,
            )
        except Exception as exc:
            elapsed = time.monotonic() - start
            err = str(exc)
            logger.error(f"[FEDERATION] {agent.name} 请求异常: {err}", exc_info=True)
            return SubAgentResult(
                name=agent.name,
                url=agent.url,
                success=False,
                error=err,
                elapsed_seconds=elapsed,
            )
