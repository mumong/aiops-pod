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

    @staticmethod
    def _build_url(agent: SubAgentConfig, endpoint_path: str) -> str:
        path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        return f"{agent.url}{path}"

    async def query(
        self,
        agent: SubAgentConfig,
        question: str,
        max_steps: int = 30,
        conclusion_max_tokens: int = 8192,
        timeout: float = 300.0,
        endpoint_path: str = "/ask",
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
        url = self._build_url(agent, endpoint_path)
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
                    q.get("endpoint_path", "/ask"),
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
        endpoint_path: str,
    ) -> SubAgentResult:
        """使用已有的 httpx.AsyncClient 查询单个子集群"""
        url = self._build_url(agent, endpoint_path)
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

    # ------------------------------------------------------------------
    # 实时流式查询（逐 chunk yield，用于联邦查询实时输出）
    # ------------------------------------------------------------------

    async def query_stream_realtime(
        self,
        agent: SubAgentConfig,
        question: str,
        max_steps: int = 30,
        conclusion_max_tokens: int = 8192,
        timeout: float = 1800.0,
        endpoint_path: str = "/ask",
    ):
        """
        流式查询子集群，逐 chunk yield (cluster_name, chunk_text)。
        用于联邦查询的实时输出：主集群边收边转发给用户。
        """
        url = self._build_url(agent, endpoint_path)
        logger.info(f"[FEDERATION] 开始实时流式查询 {agent.name}: {url}")

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=10.0)
            ) as client:
                async with client.stream(
                    "POST", url,
                    data={
                        "q": question,
                        "stream": "true",
                        "format": "text",
                        "max_steps": str(max_steps),
                        "conclusion_max_tokens": str(conclusion_max_tokens),
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_text():
                        if chunk:
                            yield (agent.name, chunk)
        except Exception as exc:
            logger.error(f"[FEDERATION] {agent.name} 实时流式异常: {exc}")
            yield (agent.name, f"\n❌ {agent.name} 查询失败: {exc}\n")

    # ------------------------------------------------------------------
    # 流式查询方法（获取完整的结构化报告）
    # ------------------------------------------------------------------

    async def query_stream(
        self,
        agent: SubAgentConfig,
        question: str,
        max_steps: int = 30,
        conclusion_max_tokens: int = 8192,
        timeout: float = 1800.0,
        endpoint_path: str = "/ask",
    ) -> SubAgentResult:
        """
        向子集群发起流式（stream=true, format=text）查询请求。

        流式模式会触发 evaluate_deterministic_decision 等后处理，
        返回包含因果链、证据表格等完整结构化报告。

        Args:
            agent: 子集群配置
            question: 用户问题
            max_steps: 最大执行步数
            conclusion_max_tokens: 诊断结论最大 token 数
            timeout: 超时秒数（流式模式需要更长，默认 600s）

        Returns:
            SubAgentResult（text 为完整的流式文本拼接）
        """
        start = time.monotonic()
        logger.info(f"[FEDERATION] 开始流式查询子集群 {agent.name}: {self._build_url(agent, endpoint_path)}")

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=10.0)
            ) as client:
                return await self._query_stream_with_client(
                    client, agent, question, max_steps, conclusion_max_tokens, endpoint_path
                )
        except httpx.TimeoutException:
            elapsed = time.monotonic() - start
            err = f"流式请求超时（{timeout}s）"
            logger.error(f"[FEDERATION] {agent.name} {err}")
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )
        except Exception as exc:
            elapsed = time.monotonic() - start
            err = str(exc)
            logger.error(f"[FEDERATION] {agent.name} 流式请求异常: {err}", exc_info=True)
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )

    async def _query_stream_with_client(
        self,
        client: httpx.AsyncClient,
        agent: SubAgentConfig,
        question: str,
        max_steps: int,
        conclusion_max_tokens: int,
        endpoint_path: str,
    ) -> SubAgentResult:
        """使用已有的 httpx.AsyncClient 流式查询单个子集群"""
        url = self._build_url(agent, endpoint_path)
        start = time.monotonic()
        # batch 场景下此方法直接被调用，需要日志
        logger.debug(f"[FEDERATION] 流式请求子集群 {agent.name}: {url}")

        try:
            async with client.stream(
                "POST",
                url,
                data={
                    "q": question,
                    "stream": "true",
                    "format": "text",
                    "max_steps": str(max_steps),
                    "conclusion_max_tokens": str(conclusion_max_tokens),
                },
            ) as resp:
                resp.raise_for_status()
                chunks: List[str] = []
                async for chunk in resp.aiter_text():
                    chunks.append(chunk)

            text = "".join(chunks)
            elapsed = time.monotonic() - start
            logger.info(
                f"[FEDERATION] {agent.name} 流式响应成功，"
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
            err = "流式请求超时"
            logger.error(f"[FEDERATION] {agent.name} {err}")
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - start
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            logger.error(f"[FEDERATION] {agent.name} 流式请求失败: {err}")
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )
        except Exception as exc:
            elapsed = time.monotonic() - start
            err = str(exc)
            logger.error(f"[FEDERATION] {agent.name} 流式请求异常: {err}", exc_info=True)
            return SubAgentResult(
                name=agent.name, url=agent.url, success=False,
                error=err, elapsed_seconds=elapsed,
            )

    async def batch_query_stream(
        self,
        queries: List[dict],
        timeout: float = 1800.0,
    ) -> List[SubAgentResult]:
        """
        在同一个事件循环中并发流式查询多个子集群（asyncio.gather）。

        与 batch_query() 结构对称，内部调用 _query_stream_with_client()。

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
                self._query_stream_with_client(
                    client,
                    q["agent"],
                    q["question"],
                    q.get("max_steps", 30),
                    q.get("conclusion_max_tokens", 8192),
                    q.get("endpoint_path", "/ask"),
                )
                for q in queries
            ]
            return list(await asyncio.gather(*tasks))
