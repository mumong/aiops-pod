#!/usr/bin/env python3
"""
联邦查询 Agent - 使用 HolmesGPT Tool Calling 实现真正的 Agent-to-Agent

主 Agent 能够：
1. 理解用户的多集群查询意图
2. 智能决定查询哪些子集群
3. 针对不同集群发送不同问题
4. 汇总并合成统一报告
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List, Optional

import litellm

from app.core.federation.registry import AgentRegistry
from app.core.federation.toolset import FederationToolset
from app.core.prompts import FEDERATION_AGENT_PROMPT

logger = logging.getLogger(__name__)


class FederationAgent:
    """联邦查询 Agent - 使用 HolmesGPT Tool Calling"""

    def __init__(
        self,
        registry: AgentRegistry,
        model: str,
        api_key: str,
        max_steps: int = 30
    ):
        self.registry = registry
        self.toolset = FederationToolset(registry)
        self.model = model
        self.api_key = api_key
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
                # 调用 LLM
                response = litellm.completion(
                    model=self.model,
                    api_key=self.api_key,
                    messages=messages,
                    tools=self._get_tools_schema(),
                    tool_choice="auto",
                    stream=False
                )

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

                    # 执行工具调用
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = eval(tool_call.function.arguments)  # JSON string to dict

                        logger.info(f"[FEDERATION AGENT] 调用工具: {tool_name}({tool_args})")

                        # 执行工具
                        tool_result = self._execute_tool(tool_name, tool_args)

                        # 添加工具结果消息
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(tool_result)
                        })

                        logger.info(f"[FEDERATION AGENT] 工具结果: {str(tool_result)[:200]}...")

                else:
                    # 没有工具调用，返回最终答案
                    final_answer = message.content or ""
                    logger.info(f"[FEDERATION AGENT] 完成，共 {step + 1} 步")
                    yield final_answer
                    return

            except Exception as exc:
                logger.error(f"[FEDERATION AGENT] 错误: {exc}", exc_info=True)
                yield f"\n❌ Agent 执行错误: {str(exc)}\n"
                return

        # 达到最大步数
        yield f"\n⚠️ 达到最大步数 ({self.max_steps})，Agent 未完成任务\n"

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
        """执行工具调用"""
        tool = self.toolset.get_tool_by_name(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        context = self.toolset.get_context()
        return tool._invoke(params, context)
