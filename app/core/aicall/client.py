"""AICall — 统一 LLM 调用层，基于 litellm + LangChain tools

用法:
    ai = AICall(model="deepseek/deepseek-chat", api_key="sk-xxx")
    result, events = ai.call(system_prompt, question, tools=tools, max_steps=10)
    text = ai.call_simple(system_prompt, question)
"""
import json
import logging
import queue
import time
from typing import Any, Dict, List, Optional, Tuple

import litellm

from .streaming import push_event
from .types import AICallResult

logger = logging.getLogger(__name__)

# litellm 日志太吵，默认压到 WARNING
litellm.suppress_debug_info = True


class AICall:
    """LLM 调用核心类，支持 tool calling ReAct 循环"""

    def __init__(self, model: str, api_key: str, api_base: str = ""):
        """
        Args:
            model: litellm 格式模型名，如 "deepseek/deepseek-chat"
            api_key: API Key
            api_base: 可选代理地址（覆盖默认 endpoint）
        """
        self.model = model
        self.api_key = api_key
        self.api_base = api_base or None
        logger.info("[AICall] init model=%s api_base=%s", model, api_base or "(default)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call_simple(self, system_prompt: str, question: str) -> str:
        """直接 LLM 调用（不带工具）"""
        messages = self._build_messages(system_prompt, question)
        resp = litellm.completion(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            api_base=self.api_base,
        )
        return resp.choices[0].message.content or ""

    def call(
        self,
        system_prompt: str,
        question: str,
        tools: Optional[List] = None,
        max_steps: int = 10,
        stream_queue: Optional[queue.Queue] = None,
        node_id: str = "",
    ) -> Tuple[AICallResult, List[Dict]]:
        """ReAct agent loop with tool calling

        Args:
            system_prompt: 系统提示词
            question: 用户问题
            tools: LangChain BaseTool 列表（来自 load_mcp_tools）
            max_steps: 最大迭代次数
            stream_queue: 实时事件队列
            node_id: 节点 ID（用于事件标记）

        Returns:
            (AICallResult, thinking_events)
        """
        messages = self._build_messages(system_prompt, question)
        thinking_events: List[Dict] = []
        all_tool_calls: List[Dict] = []
        tool_call_count = 0
        call_start = time.time()

        # Build tool schemas + lookup map
        tool_schemas = None
        tools_by_name: Dict[str, Any] = {}
        if tools:
            tool_schemas = [self._tool_to_schema(t) for t in tools]
            tools_by_name = {t.name: t for t in tools}

        for iteration in range(1, max_steps + 1):
            # LLM call
            kwargs: Dict[str, Any] = dict(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                api_base=self.api_base,
            )
            if tool_schemas:
                kwargs["tools"] = tool_schemas
            resp = litellm.completion(**kwargs)
            choice = resp.choices[0].message

            # Append assistant message
            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": choice.content or ""}
            if choice.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.tool_calls
                ]
            messages.append(assistant_msg)

            # AI message event
            if choice.content:
                evt = {"type": "ai_message", "content": choice.content[:500],
                       "iteration": iteration}
                self._push(stream_queue, node_id, thinking_events, **evt)

            # No tool calls → done
            if not choice.tool_calls:
                break

            # Execute tool calls
            for tc in choice.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    fn_args = {}

                tool_call_count += 1
                push_event(stream_queue, "tool_start", node_id,
                           tool_name=fn_name, iteration=iteration)
                self._record(thinking_events, "tool_start", node_id,
                             tool_name=fn_name, iteration=iteration)

                # Execute
                tool_start = time.time()
                result_str, error_str = self._execute_tool(tools_by_name, fn_name, fn_args)
                tool_duration = time.time() - tool_start

                status = "error" if error_str else "success"
                logger.info("[AICall] tool #%d %s | %s | %.1fs",
                            tool_call_count, fn_name, status, tool_duration)

                all_tool_calls.append({
                    "tool_name": fn_name,
                    "result": result_str,
                    "error": error_str,
                })

                evt = {
                    "type": "tool_result", "tool_name": fn_name,
                    "status": status,
                    "result_preview": (result_str or "")[:200],
                    "result": result_str or "",
                    "duration_seconds": round(tool_duration, 2),
                    "iteration": iteration,
                }
                push_event(stream_queue, "tool_result", node_id, **evt)
                self._record(thinking_events, "tool_result", node_id, **evt)

                # Append tool message for next LLM turn
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str or error_str or "",
                })

            # Iteration end event
            elapsed = time.time() - call_start
            evt = {"type": "iteration_end", "iteration": iteration,
                   "tool_calls_in_iteration": len(choice.tool_calls),
                   "elapsed_seconds": round(elapsed, 2)}
            push_event(stream_queue, "iteration_end", node_id, **evt)
            self._record(thinking_events, "iteration_end", node_id, **evt)

        # Build result
        total_ms = (time.time() - call_start) * 1000
        final_content = messages[-1].get("content", "") if messages else ""
        # Walk back to find last assistant content
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                final_content = msg["content"]
                break

        result = AICallResult(
            result=final_content,
            tool_calls=all_tool_calls,
            iterations=min(iteration, max_steps) if tools else 1,
            tool_call_count=tool_call_count,
            duration_ms=total_ms,
            intermediate_events=thinking_events,
        )
        logger.info("[AICall] done | %.1fs | iterations=%d | tools=%d",
                    total_ms / 1000, result.iterations, tool_call_count)
        return result, thinking_events

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(system_prompt: str, question: str) -> List[Dict]:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": question})
        return msgs

    @staticmethod
    def _tool_to_schema(tool) -> Dict:
        """Convert LangChain BaseTool to OpenAI function-calling schema."""
        schema = tool.args_schema.schema() if tool.args_schema else {"type": "object", "properties": {}}
        # Remove title if present (not part of OpenAI spec)
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": schema,
            },
        }

    @staticmethod
    def _execute_tool(tools_by_name: Dict, name: str, args: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Execute a LangChain tool, return (result, error)."""
        tool = tools_by_name.get(name)
        if not tool:
            err = f"Tool not found: {name}"
            logger.warning("[AICall] %s", err)
            return None, err
        try:
            result = tool.invoke(args)
            return str(result), None
        except Exception as e:
            logger.error("[AICall] Tool %s failed: %s", name, e, exc_info=True)
            return None, str(e)

    @staticmethod
    def _push(q: Optional[queue.Queue], node_id: str, events: List[Dict], **data):
        """Push to queue + record locally."""
        evt = {"node": node_id, "timestamp": time.time(), **data}
        events.append(evt)
        push_event(q, data.get("type", ""), node_id, **data)

    @staticmethod
    def _record(events: List[Dict], event_type: str, node_id: str, **data):
        """Record event locally (no queue push)."""
        events.append({"type": event_type, "node": node_id, "timestamp": time.time(), **data})
