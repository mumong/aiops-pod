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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

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

    def ask_stream(self, question: str) -> Generator[str, None, None]:
        """
        执行联邦查询，流式返回结果

        Args:
            question: 用户问题

        Yields:
            流式文本块
        """
        logger.info(f"[FEDERATION AGENT] 开始处理问题: {question[:60]}...")

        # 构建初始消息
        messages = [
            {"role": "system", "content": FEDERATION_AGENT_PROMPT},
            {"role": "user", "content": question}
        ]

        # Tool Calling 循环
        for step in range(self.max_steps):
            logger.info(f"[FEDERATION AGENT] Step {step + 1}/{self.max_steps}")

            try:
                # 调用 LLM（中间步骤使用非流式，快速获取工具调用决策）
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
                response = litellm.completion(**_completion_kwargs)

                message = response.choices[0].message

                # 检查是否有工具调用
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

                    # 执行所有工具调用（多个 query_cluster 会并发执行）
                    tool_results = self._execute_tools(message.tool_calls)

                    # 按顺序添加工具结果到消息历史
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
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
            logger.error(f"[FEDERATION A2A] 保存报告失败: {exc}", exc_info=True)

    def _stream_final_answer(self, messages: List[Dict]) -> Generator[str, None, None]:
        """
        流式生成最终答案

        不带 tools 参数重新调用 LLM，使用 stream=True，
        让用户在生成过程中就能看到输出，减少等待时间。
        """
        try:
            _completion_kwargs = dict(
                model=self.model,
                api_key=self.api_key,
                messages=messages,
                stream=True,
            )
            if self.api_base:
                _completion_kwargs["base_url"] = self.api_base
            stream = litellm.completion(**_completion_kwargs)
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            logger.error(f"[FEDERATION AGENT] 流式最终回答失败: {exc}", exc_info=True)
            yield f"\n❌ 生成最终报告失败: {str(exc)}\n"

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
