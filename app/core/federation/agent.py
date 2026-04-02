#!/usr/bin/env python3
"""
联邦查询 Agent - 使用 LiteLLM Tool Calling 实现真正的 Agent-to-Agent

主 Agent 能够：
1. 理解用户的多集群查询意图
2. 智能决定查询哪些子集群
3. 针对不同集群发送不同问题（多个 query_cluster 并发执行）
4. 汇总并合成统一报告（流式输出最终答案）

并发优化：
- 当 LLM 一次返回多个 query_cluster 调用时，使用 asyncio.gather 并发执行
- 所有并发查询共享同一个 httpx 连接池（单事件循环）
- 最终答案使用 stream=True 减少首 token 延迟
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import httpx
import litellm

from app.core.federation.registry import AgentRegistry
from app.core.federation.toolset import FederationToolset
from app.core.federation.client import SubAgentClient
from app.core.federation.report_parser import extract_final_answer
from app.core.prompts import FEDERATION_AGENT_PROMPT

logger = logging.getLogger(__name__)


class FederationAgent:
    """联邦查询 Agent - 使用 LiteLLM Tool Calling"""

    def __init__(
        self,
        registry: AgentRegistry,
        model: str,
        api_key: str,
        api_base: str = None,
        max_steps: int = 30
    ):
        self.registry = registry
        self.toolset = FederationToolset(registry)
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.max_steps = max_steps
        self._max_retries = 3
        self._retry_base_delay = 2  # 秒

    def _completion_with_retry(self, **kwargs) -> Any:
        """带重试的 litellm.completion 调用，处理 DeepSeek 连接中断等瞬态错误"""
        # 设置较长超时（DeepSeek 有时响应较慢）
        kwargs.setdefault("timeout", 120)

        # 可重试的异常类型
        retryable = (
            litellm.InternalServerError,
            litellm.APIConnectionError,
            litellm.Timeout,
            litellm.ServiceUnavailableError,
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            ConnectionError,
        )

        last_exc = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return litellm.completion(**kwargs)
            except retryable as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (2 ** (attempt - 1))  # 指数退避: 2s, 4s, 8s
                    logger.warning(
                        f"[FEDERATION AGENT] LLM 调用失败 (第{attempt}次), "
                        f"{delay}s 后重试: {type(exc).__name__}: {str(exc)[:120]}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"[FEDERATION AGENT] LLM 调用失败 (已重试{self._max_retries}次): {exc}")
        raise last_exc

    def ask_stream(self, question: str) -> Generator[str, None, None]:
        """
        执行联邦查询，流式返回结果。

        子集群查询时实时转发流式输出（与 /ask 一致的 thinking 效果），
        最后由 LLM 合成统一报告。
        """
        logger.info(f"[FEDERATION AGENT] 开始处理问题: {question[:60]}...")

        # 构建初始消息
        messages = [
            {"role": "system", "content": FEDERATION_AGENT_PROMPT},
            {"role": "user", "content": question}
        ]

        # 收集各子集群的完整报告文本（用于最终合成）
        cluster_reports: Dict[str, str] = {}

        # Tool Calling 循环
        for step in range(self.max_steps):
            logger.info(f"[FEDERATION AGENT] Step {step + 1}/{self.max_steps}")

            try:
                _completion_kwargs = dict(
                    model=self.model,
                    api_key=self.api_key,
                    messages=messages,
                    tools=self._get_tools_schema(),
                    tool_choice="auto",
                    stream=False,
                )
                if self.api_base:
                    _completion_kwargs["base_url"] = self.api_base
                response = self._completion_with_retry(**_completion_kwargs)

                message = response.choices[0].message

                if message.tool_calls:
                    # 添加 assistant 消息
                    messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })

                    # 执行工具调用 — 实时 yield 子集群输出
                    tool_results = yield from self._execute_tools_streaming(
                        message.tool_calls, cluster_reports
                    )

                    # 添加工具结果到消息历史
                    for tool_call, result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result)
                        })

                else:
                    # 没有工具调用 → 流式生成最终答案
                    logger.info(f"[FEDERATION AGENT] 开始生成最终答案（流式），共 {step + 1} 步")
                    yield from self._stream_final_answer(messages)
                    return

            except Exception as exc:
                logger.error(f"[FEDERATION AGENT] 错误: {exc}", exc_info=True)
                yield f"\n❌ Agent 执行错误: {str(exc)}\n"
                return

        # 达到最大步数
        yield f"\n⚠️ 达到最大步数 ({self.max_steps})，Agent 未完成任务\n"

    def _execute_tools_streaming(self, tool_calls, cluster_reports: Dict[str, str]) -> Generator[str, None, List[tuple]]:
        """
        执行工具调用，query_cluster 时并发查询 + 实时 yield 子集群输出。

        并发策略：所有 query_cluster 同时发起，按完成顺序输出。
        """
        import queue as _queue
        import threading

        parsed = []
        for tc in tool_calls:
            args = self._parse_tool_args(tc.function.arguments)
            parsed.append((tc, tc.function.name, args))

        query_calls = [(tc, args) for tc, name, args in parsed if name == "query_cluster"]
        other_calls = [(tc, name, args) for tc, name, args in parsed if name != "query_cluster"]

        results = {}

        # 先执行非查询工具
        for tc, name, args in other_calls:
            logger.info(f"[FEDERATION AGENT] 调用工具: {name}({args})")
            result = self._execute_tool(name, args)
            results[tc.id] = (tc, result)

        if not query_calls:
            return [results[tc.id] for tc in tool_calls]

        registry = self.toolset.get_context().get("federation_registry")
        enabled_agents = {a.name: a for a in registry.get_enabled_agents()} if registry else {}

        # 并发流式查询所有子集群
        # 用一个共享 queue 收集所有子集群的 chunk，带 cluster_name 标记
        chunk_queue = _queue.Queue()
        cluster_chunks: Dict[str, list] = {}  # cluster_name → [chunks]
        tc_by_cluster: Dict[str, Any] = {}  # cluster_name → tool_call

        valid_queries = []
        for tc, args in query_calls:
            cluster_name = args.get("cluster_name", "")
            agent_cfg = enabled_agents.get(cluster_name)
            if not agent_cfg:
                results[tc.id] = (tc, {
                    "error": f"Cluster '{cluster_name}' not found",
                    "available_clusters": list(enabled_agents.keys())
                })
                continue
            valid_queries.append((tc, args, cluster_name, agent_cfg))
            cluster_chunks[cluster_name] = []
            tc_by_cluster[cluster_name] = tc

        if not valid_queries:
            return [results[tc.id] for tc in tool_calls]

        # 每个子集群一个线程，并发执行
        active_count = len(valid_queries)

        def _stream_cluster(agent_cfg, cluster_name, question, max_steps, conclusion_max_tokens):
            """在独立线程中流式查询一个子集群"""
            client = SubAgentClient()
            try:
                async def _run():
                    async for name, chunk in client.query_stream_realtime(
                        agent_cfg, question, max_steps, conclusion_max_tokens
                    ):
                        chunk_queue.put((cluster_name, chunk))
                    chunk_queue.put((cluster_name, None))  # sentinel
                asyncio.run(_run())
            except Exception as exc:
                chunk_queue.put((cluster_name, f"\n❌ {cluster_name} 查询失败: {exc}\n"))
                chunk_queue.put((cluster_name, None))

        # 启动所有线程
        threads = []
        for tc, args, cluster_name, agent_cfg in valid_queries:
            t = threading.Thread(
                target=_stream_cluster,
                args=(agent_cfg, cluster_name, args.get("question", ""),
                      args.get("max_steps", 30), args.get("conclusion_max_tokens", 8192)),
                daemon=True
            )
            threads.append(t)
            t.start()

        logger.info(f"[FEDERATION AGENT] 并发启动 {len(threads)} 个子集群查询")

        # 输出所有子集群的查询开始标记
        yield f"\n{'=' * 70}\n"
        yield f"🔍 并发查询 {len(valid_queries)} 个子集群: {', '.join(c for _, _, c, _ in valid_queries)}\n"
        yield f"{'=' * 70}\n\n"

        # 按到达顺序实时输出 chunk
        finished_clusters = set()
        current_cluster = None

        while len(finished_clusters) < active_count:
            try:
                cluster_name, chunk = chunk_queue.get(timeout=1.0)
            except _queue.Empty:
                # 检查线程是否还活着
                if not any(t.is_alive() for t in threads):
                    break
                continue

            if chunk is None:
                finished_clusters.add(cluster_name)
                yield f"\n   ✅ [{cluster_name}] 查询完成\n\n"
                current_cluster = None
                continue

            # 切换集群时输出标记
            if cluster_name != current_cluster:
                if current_cluster is not None:
                    yield "\n"
                yield f"📡 [{cluster_name}] "
                current_cluster = cluster_name

            cluster_chunks[cluster_name].append(chunk)
            yield chunk

        # 等待所有线程结束
        for t in threads:
            t.join(timeout=5)

        # 组装结果
        for tc, args, cluster_name, agent_cfg in valid_queries:
            full_text = "".join(cluster_chunks.get(cluster_name, []))
            cluster_reports[cluster_name] = full_text
            self._save_report(cluster_name, type('R', (), {'text': full_text, 'elapsed_seconds': 0})())

            parsed_report = extract_final_answer(full_text)
            results[tc.id] = (tc, {
                "cluster": cluster_name,
                "success": True,
                "response": parsed_report.final_answer,
            })

        return [results[tc.id] for tc in tool_calls]

    def _execute_tools(self, tool_calls) -> List[tuple]:
        """
        执行工具调用，多个 query_cluster 调用会并发执行。

        并发策略：
        - 将 query_cluster 调用分组，使用 asyncio.gather 在单个事件循环中并发
        - 其他工具（如 list_clusters）直接同步执行
        - 总耗时 = max(单个子集群耗时) 而非 sum
        """
        # 解析所有工具调用
        parsed = []
        for tc in tool_calls:
            args = self._parse_tool_args(tc.function.arguments)
            parsed.append((tc, tc.function.name, args))

        # 分离 query_cluster 和其他工具
        query_calls = [(tc, args) for tc, name, args in parsed if name == "query_cluster"]
        other_calls = [(tc, name, args) for tc, name, args in parsed if name != "query_cluster"]

        results = {}  # tc.id → (tc, result)

        # 先执行非查询工具（如 list_clusters，通常很快）
        for tc, name, args in other_calls:
            logger.info(f"[FEDERATION AGENT] 调用工具: {name}({args})")
            result = self._execute_tool(name, args)
            logger.info(f"[FEDERATION AGENT] 工具结果: {str(result)[:200]}...")
            results[tc.id] = (tc, result)

        # 并发执行所有 query_cluster 调用
        if len(query_calls) == 1:
            # 单个查询：直接执行，无线程开销
            tc, args = query_calls[0]
            logger.info(f"[FEDERATION AGENT] 调用工具: query_cluster({args})")
            result = self._execute_tool("query_cluster", args)
            logger.info(f"[FEDERATION AGENT] 工具结果: {str(result)[:200]}...")
            results[tc.id] = (tc, result)

        elif len(query_calls) > 1:
            # 多个查询：asyncio.gather 并发执行
            batch_results = self._batch_query_clusters(query_calls)
            for tc, result in batch_results:
                results[tc.id] = (tc, result)

        # 按原始顺序返回结果
        return [results[tc.id] for tc in tool_calls]

    def _batch_query_clusters(self, query_calls: List[tuple]) -> List[tuple]:
        """
        批量并发执行多个 query_cluster 调用。

        使用单个线程 + 单个事件循环 + asyncio.gather + 共享连接池，
        比每个查询单独开线程 + 单独 asyncio.run 更高效。

        Args:
            query_calls: [(tool_call, args_dict), ...]

        Returns:
            [(tool_call, result_dict), ...]
        """
        logger.info(f"[FEDERATION AGENT] 并发执行 {len(query_calls)} 个子集群查询")

        registry = self.toolset.get_context().get("federation_registry")
        if not registry:
            return [(tc, {"error": "Federation registry not available"}) for tc, _ in query_calls]

        # 构建批量查询列表
        enabled_agents = {a.name: a for a in registry.get_enabled_agents()}
        queries = []
        tc_map = []  # 保持对应关系

        for tc, args in query_calls:
            cluster_name = args.get("cluster_name", "")
            agent = enabled_agents.get(cluster_name)
            if agent:
                queries.append({
                    "agent": agent,
                    "question": args.get("question", ""),
                    "max_steps": args.get("max_steps", 30),
                    "conclusion_max_tokens": args.get("conclusion_max_tokens", 8192),
                })
                tc_map.append((tc, cluster_name, True))
            else:
                tc_map.append((tc, cluster_name, False))

        # 在独立线程中执行异步批量流式查询
        client = SubAgentClient()

        def _run_batch():
            return asyncio.run(client.batch_query_stream(queries))

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_batch)
            batch_results = future.result()

        # 组装结果
        results = []
        batch_idx = 0
        for tc, cluster_name, found in tc_map:
            if found:
                sub_result = batch_results[batch_idx]
                batch_idx += 1

                if sub_result.success:
                    # 解析报告：提取最终答案给 LLM，完整文本保存到磁盘
                    parsed = extract_final_answer(sub_result.text)
                    self._save_report(cluster_name, sub_result)
                    result = {
                        "cluster": cluster_name,
                        "success": True,
                        "response": parsed.final_answer,
                        "elapsed_seconds": sub_result.elapsed_seconds
                    }
                else:
                    result = {
                        "cluster": cluster_name,
                        "success": False,
                        "error": sub_result.error,
                        "elapsed_seconds": sub_result.elapsed_seconds
                    }

                logger.info(
                    f"[FEDERATION AGENT] [并发] {cluster_name} 完成: "
                    f"{'成功' if sub_result.success else '失败'}, "
                    f"耗时 {sub_result.elapsed_seconds:.1f}s"
                )
            else:
                result = {
                    "error": f"Cluster '{cluster_name}' not found",
                    "available_clusters": list(enabled_agents.keys())
                }

            results.append((tc, result))

        return results

    def _save_report(self, cluster_name: str, result) -> None:
        """保存子集群报告到 reports/ 目录"""
        try:
            reports_dir = Path(os.environ.get("REPORTS_DIR", "/tmp/aiops/reports"))
            reports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{cluster_name}_{timestamp}.md"
            filepath = reports_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 子集群诊断报告 - {cluster_name}\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**来源**: Agent-to-Agent (v2)\n")
                f.write(f"**耗时**: {result.elapsed_seconds:.1f} 秒\n\n")
                f.write("---\n\n")
                f.write(result.text)

            logger.info(f"[FEDERATION A2A] 已保存 {cluster_name} 报告到: {filepath}")
        except Exception as exc:
            logger.error(f"[FEDERATION A2A] 保存报告失败 ({cluster_name}): {exc}", exc_info=True)

    def _stream_final_answer(self, messages: List[Dict]) -> Generator[str, None, None]:
        """
        流式生成最终答案（带重试）

        不带 tools 参数重新调用 LLM，使用 stream=True，
        让用户在生成过程中就能看到输出，减少等待时间。
        """
        retryable = (
            litellm.InternalServerError,
            litellm.APIConnectionError,
            litellm.Timeout,
            litellm.ServiceUnavailableError,
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
            ConnectionError,
        )

        for attempt in range(1, self._max_retries + 1):
            try:
                _completion_kwargs = dict(
                    model=self.model,
                    api_key=self.api_key,
                    messages=messages,
                    stream=True,
                    timeout=120,
                )
                if self.api_base:
                    _completion_kwargs["base_url"] = self.api_base
                stream = litellm.completion(**_completion_kwargs)
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                return  # 成功完成
            except retryable as exc:
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"[FEDERATION AGENT] 流式回答失败 (第{attempt}次), "
                        f"{delay}s 后重试: {type(exc).__name__}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"[FEDERATION AGENT] 流式回答失败 (已重试{self._max_retries}次): {exc}", exc_info=True)
                    yield f"\n❌ 生成最终报告失败: {str(exc)}\n"
            except Exception as exc:
                logger.error(f"[FEDERATION AGENT] 流式最终回答失败: {exc}", exc_info=True)
                yield f"\n❌ 生成最终报告失败: {str(exc)}\n"
                return

    def _parse_tool_args(self, arguments: str) -> Dict[str, Any]:
        """解析工具参数（优先 JSON，回退 eval）"""
        try:
            return json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return eval(arguments)

    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取工具的 OpenAI 格式 schema"""
        tools = []

        for tool in self.toolset.get_tools():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": self._get_tool_parameters(tool)
                }
            })

        return tools

    def _get_tool_parameters(self, tool) -> Dict[str, Any]:
        """获取工具参数的 JSON Schema"""
        if tool.name == "list_clusters":
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        elif tool.name == "query_cluster":
            return {
                "type": "object",
                "properties": {
                    "cluster_name": {
                        "type": "string",
                        "description": "子集群名称"
                    },
                    "question": {
                        "type": "string",
                        "description": "要查询的问题"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "最大执行步数",
                        "default": 30
                    },
                    "conclusion_max_tokens": {
                        "type": "integer",
                        "description": "结论最大 token 数",
                        "default": 8192
                    }
                },
                "required": ["cluster_name", "question"]
            }
        return {"type": "object", "properties": {}}

    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具调用"""
        tool = self.toolset.get_tool_by_name(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        context = self.toolset.get_context()
        return tool._invoke(params, context)
