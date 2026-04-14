"""AICall — 统一 LLM 调用层，基于 LangChain Agent + LangGraph

核心能力：
- call(): LangChain create_agent loop（支持 tool calling、middleware、interrupt）
- call_simple(): LangChain ChatModel 直接调用（无工具）
- 完全控制 system prompt，无框架注入

用法:
    ai = AICall(model="deepseek/deepseek-chat", api_key="sk-xxx")
    result, events = ai.call(system_prompt, question, tools=tools, max_steps=10)
    text = ai.call_simple(system_prompt, question)
"""
import logging
import queue
import time
from typing import Any, Dict, List, Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .streaming import push_event
from .types import AICallResult

logger = logging.getLogger(__name__)

# 已知模型提供商 → base_url 映射
_PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "openai": None,  # 默认
}


def _parse_model(model_str: str, api_base: str = "") -> Tuple[str, Optional[str]]:
    """解析 litellm 格式模型名为 (model_name, base_url)

    'deepseek/deepseek-chat' → ('deepseek-chat', 'https://api.deepseek.com/v1')
    'openai/gpt-4o' → ('gpt-4o', None)
    'anthropic/claude-sonnet-4-6' → ('claude-sonnet-4-6', api_base)
    """
    if api_base and api_base.strip():
        # 用户指定了 api_base，直接用
        parts = model_str.split("/", 1)
        model_name = parts[-1] if len(parts) > 1 else model_str
        return model_name, api_base.strip()

    if "/" in model_str:
        provider, model_name = model_str.split("/", 1)
        base_url = _PROVIDER_BASE_URLS.get(provider.lower())
        return model_name, base_url
    return model_str, None


class AICall:
    """LLM 调用核心类，基于 LangChain ChatModel + LangChain Agent (create_agent)"""

    def __init__(self, model: str, api_key: str, api_base: str = ""):
        """
        Args:
            model: litellm 格式模型名，如 "deepseek/deepseek-chat"
            api_key: API Key
            api_base: 可选代理地址（覆盖默认 endpoint）
        """
        self.model_str = model
        self.api_key = api_key
        self.api_base = api_base

        model_name, base_url = _parse_model(model, api_base)
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "api_key": api_key,
            "streaming": True,  # 启用 token 级别流式输出
        }
        if base_url:
            kwargs["base_url"] = base_url

        self.chat_model = ChatOpenAI(**kwargs)
        logger.info("🔧 [AICall] 初始化 model=%s base_url=%s (LangChain ChatOpenAI)",
                     model_name, base_url or "(default)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call_simple(self, system_prompt: str, question: str, **kwargs) -> str:
        """直接 LLM 调用（不带工具）

        Args:
            system_prompt: 系统提示词（你写的就是全部，无框架注入）
            question: 用户问题
            **kwargs: 透传给 ChatModel（如 max_tokens, temperature）
        """
        logger.debug("📍 [AICall] call_simple 开始 | prompt=%d字 question=%d字 extra=%s",
                      len(system_prompt), len(question), list(kwargs.keys()) or "无")
        start = time.time()

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=question))

        # 透传 kwargs（如 max_tokens）到 model.invoke
        model = self.chat_model
        if kwargs:
            model = model.bind(**kwargs)

        result = model.invoke(messages)
        content = result.content or ""
        logger.debug("✅ [AICall] call_simple 完成 | %.1fs | 输出=%d字",
                      time.time() - start, len(content))
        return content

    def call(
        self,
        system_prompt: str,
        question: str,
        tools: Optional[List] = None,
        max_steps: int = 10,
        stream_queue: Optional[queue.Queue] = None,
        node_id: str = "",
        cancel_event: Optional[Any] = None,
    ) -> Tuple[AICallResult, List[Dict]]:
        """LangChain Agent loop with tool calling (create_agent)

        Args:
            system_prompt: 系统提示词（你写的就是全部，无框架注入）
            question: 用户问题
            tools: LangChain BaseTool 列表（来自 load_mcp_tools）
            max_steps: 最大迭代次数（LangGraph recursion_limit）
            stream_queue: 实时事件队列（thinking 事件推送）
            node_id: 节点 ID（用于事件标记）
            cancel_event: 取消信号（threading.Event），set() 后 agent 提前退出

        Returns:
            (AICallResult, thinking_events)
        """
        call_start = time.time()
        thinking_events: List[Dict] = []
        all_tool_calls: List[Dict] = []
        tool_call_count = 0
        iteration = 0

        logger.debug("📍 [AICall] call 开始 | node=%s max_steps=%d tools=%d prompt=%d字",
                      node_id or "?", max_steps, len(tools or []), len(system_prompt))

        # 无工具时直接调用 call_simple
        if not tools:
            content = self.call_simple(system_prompt, question)
            total_ms = (time.time() - call_start) * 1000
            result = AICallResult(
                result=content, iterations=1, duration_ms=total_ms,
            )
            return result, thinking_events

        # 创建 LangChain Agent (create_agent，替代已废弃的 create_react_agent)
        from langchain.agents import create_agent

        agent = create_agent(
            model=self.chat_model,
            tools=tools,
            system_prompt=system_prompt,
        )

        # 使用 async stream 模式（MCP 工具需要异步调用）
        import asyncio
        import concurrent.futures

        input_messages = {"messages": [{"role": "user", "content": question}]}
        # recursion_limit 直接使用 config 传入的 max_steps，不做任何公式转换
        config = {"recursion_limit": max_steps}
        logger.info("📍 [AICall] node=%s | max_steps(recursion_limit)=%d", node_id or "?", max_steps)

        final_content = ""
        _content_buffer = []  # 收集 token 级别的文本片段

        async def _run_agent():
            nonlocal final_content, iteration, tool_call_count
            async for chunk in agent.astream(
                input_messages, config=config,
                stream_mode=["updates", "messages"],
                version="v2",
            ):
                # 检查取消信号
                if cancel_event and cancel_event.is_set():
                    logger.info("🛑 [AICall] 收到取消信号，停止 agent (node=%s)", node_id)
                    break
                # v2 格式: chunk 是 dict {"type": "updates"|"messages", "data": ..., "ns": [...]}
                # 但某些版本可能返回 tuple (stream_mode_name, data)
                if isinstance(chunk, tuple):
                    chunk_type, chunk_data = chunk[0], chunk[1]
                elif isinstance(chunk, dict):
                    chunk_type = chunk.get("type", "")
                    chunk_data = chunk.get("data", {})
                else:
                    logger.debug("   ⚠️ [AICall] 未知 chunk 类型: %s", type(chunk))
                    continue

                # ── messages 模式：token 级别流式 ──
                if chunk_type == "messages":
                    # chunk_data 可能是 tuple (token_msg, metadata) 或 list
                    if isinstance(chunk_data, (list, tuple)) and len(chunk_data) >= 2:
                        token_msg, metadata = chunk_data[0], chunk_data[1]
                    else:
                        continue
                    if hasattr(token_msg, 'content') and token_msg.content:
                        langgraph_node = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""
                        if langgraph_node != "tools":
                            _content_buffer.append(token_msg.content)
                            push_event(stream_queue, "ai_token", node_id,
                                       content=token_msg.content, iteration=iteration)
                    continue

                # ── updates 模式：消息/工具级别（原有逻辑） ──
                if chunk_type != "updates":
                    continue
                update_data = chunk_data if isinstance(chunk_data, dict) else {}
                for node_name, update in update_data.items():
                    messages = update.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            # AI 完整消息（用于 final_content 和工具调用检测）
                            if msg.content:
                                final_content = msg.content
                                iteration += 1
                                logger.debug("   💬 [AICall] AI 消息 #%d:\n%s",
                                            iteration, msg.content[:1000])
                                evt = {"type": "ai_message",
                                       "content": msg.content[:500],
                                       "iteration": iteration}
                                self._push(stream_queue, node_id, thinking_events, **evt)

                            # AI 工具调用
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_call_count += 1
                                    logger.debug("   🔧 [AICall] tool_call #%d %s | args=%s",
                                                tool_call_count, tc["name"],
                                                str(tc.get("args", {}))[:300])
                                    push_event(stream_queue, "tool_start", node_id,
                                               tool_name=tc["name"], iteration=iteration)
                                    self._record(thinking_events, "tool_start", node_id,
                                                 tool_name=tc["name"], iteration=iteration)

                        elif hasattr(msg, 'type') and msg.type == 'tool':
                            # 工具执行结果
                            tool_name = getattr(msg, 'name', '') or ''
                            tool_content = msg.content or ''
                            status = "success"
                            all_tool_calls.append({
                                "tool_name": tool_name,
                                "result": tool_content,
                            })
                            logger.info("   ✅ [AICall] tool #%d %s | %s | len=%d",
                                        tool_call_count, tool_name, status,
                                        len(tool_content))
                            logger.debug("   📄 [AICall] tool #%d %s 完整输出:\n%s",
                                        tool_call_count, tool_name,
                                        tool_content[:2000])
                            evt = {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "status": status,
                                "result_preview": tool_content[:200],
                                "result": tool_content,
                                "iteration": iteration,
                            }
                            push_event(stream_queue, "tool_result", node_id, **evt)
                            self._record(thinking_events, "tool_result", node_id, **evt)

        # 在新线程中运行异步 agent（避免与 uvicorn event loop 冲突）
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(lambda: asyncio.run(_run_agent())).result(timeout=max_steps * 30)
        except concurrent.futures.TimeoutError:
            logger.warning("⚠️ [AICall] agent 执行超时 (%ds)", max_steps * 30)
            if not final_content:
                final_content = "Agent 执行超时"
        except Exception as e:
            logger.error("❌ [AICall] agent 执行异常: %s", e, exc_info=True)
            if not final_content:
                final_content = f"Agent 执行异常: {e}"

        total_ms = (time.time() - call_start) * 1000
        result = AICallResult(
            result=final_content,
            tool_calls=all_tool_calls,
            iterations=max(iteration, 1),
            tool_call_count=tool_call_count,
            duration_ms=total_ms,
            intermediate_events=thinking_events,
        )
        logger.info("✅ [AICall] call 完成 | node=%s | %.1fs | iterations=%d | tools=%d | 输出=%d字",
                    node_id or "?", total_ms / 1000, result.iterations, tool_call_count,
                    len(final_content))
        return result, thinking_events

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
