#!/usr/bin/env python3
"""
联邦查询 - 子集群 HTTP 客户端

封装对子集群 /ask 端点的异步调用，超时安全，返回结构化结果。
每次调用创建独立的 httpx.AsyncClient（因为 asyncio.run 会关闭事件循环，
共享 client 会导致 'Event loop is closed' 错误）。
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

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
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=10.0)
            ) as client:
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

    async def batch_query(
        self,
        queries: List[dict],
        timeout: float = 300.0,
    ) -> List[SubAgentResult]:
        """
        在同一个事件循环中并发查询多个子集群（asyncio.gather）。

        比每个查询单独 asyncio.run() 更高效：
        - 共享 httpx.AsyncClient 连接池
        - 单个事件循环，无线程开销

        Args:
            queries: [{"agent": SubAgentConfig, "question": str, "max_steps": int, "conclusion_max_tokens": int}, ...]
            timeout: 超时秒数

        Returns:
            SubAgentResult 列表（与输入顺序一致）
        """
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0)
        ) as client:
            tasks = [
                self._query_with_client(
                    client,
                    q["agent"],
                    q["question"],
                    q.get("max_steps", 30),
                    q.get("conclusion_max_tokens", 8192),
                )
                for q in queries
            ]
            return list(await asyncio.gather(*tasks))

    async def _query_with_client(
        self,
        client: httpx.AsyncClient,
        agent: SubAgentConfig,
        question: str,
        max_steps: int,
        conclusion_max_tokens: int,
    ) -> SubAgentResult:
        """使用已有的 httpx.AsyncClient 查询单个子集群"""
        url = f"{agent.url}/ask"
        start = time.monotonic()
        logger.info(f"[FEDERATION] 开始查询子集群 {agent.name}: {url}")

        try:
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
            err = f"请求超时"
            logger.error(f"[FEDERATION] {agent.name} {err}")
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - start
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            logger.error(f"[FEDERATION] {agent.name} 请求失败: {err}")
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )
        except Exception as exc:
            elapsed = time.monotonic() - start
            err = str(exc)
            logger.error(f"[FEDERATION] {agent.name} 请求异常: {err}", exc_info=True)
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )
