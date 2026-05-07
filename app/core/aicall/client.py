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
import json
import logging
import os
import queue
import re
import time
from contextlib import ExitStack, contextmanager, nullcontext
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, ValidationError
from langgraph.errors import GraphRecursionError
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.core.context.archive import ContextArchive
from app.core.context.budget import ContextBudgetEstimator, ModelContextResolver, serialize_tool_schema
from app.core.context.observation import ObservationProcessor
from app.core.prompts import get_workflow_prompt
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

    def __init__(
        self,
        model: str,
        api_key: str,
        api_base: str = "",
        observation_summary_mode: str = "rule",
        observation_summary_max_chars: int = 3000,
    ):
        """
        Args:
            model: litellm 格式模型名，如 "deepseek/deepseek-chat"
            api_key: API Key
            api_base: 可选代理地址（覆盖默认 endpoint）
        """
        self.model = model
        self.model_str = model
        self.api_key = api_key
        self.api_base = api_base
        normalized_mode = (observation_summary_mode or "rule").strip().lower()
        self.observation_summary_mode = normalized_mode if normalized_mode in {"rule", "ai"} else "rule"
        self.observation_summary_max_chars = max(200, int(observation_summary_max_chars or 3000))

        model_name, base_url = _parse_model(model, api_base)
        self._chat_model_kwargs: Dict[str, Any] = {
            "model": model_name,
            "api_key": api_key,
            "streaming": True,  # 启用 token 级别流式输出
            "stream_usage": True,  # 让 OpenAI-compatible 网关返回 usage_metadata
        }
        if base_url:
            self._chat_model_kwargs["base_url"] = base_url

        logger.info("🔧 [AICall] 初始化 model=%s base_url=%s (LangChain ChatOpenAI)",
                    model_name, base_url or "(default)")

    def _create_chat_model(self, session_id: Optional[str] = None, node_id: str = ""):
        """按次创建 ChatOpenAI，避免跨 asyncio event loop 复用底层 async client。"""
        kwargs = dict(self._chat_model_kwargs)
        metadata = self._session_metadata(session_id, node_id)
        if metadata:
            # Put session metadata on the base ChatOpenAI instance so LangChain
            # agent internals such as bind_tools keep it on actual chat
            # completion requests.
            kwargs["extra_body"] = {
                "metadata": metadata,
                "trace_id": self._trace_id(session_id, node_id),
                "generation_name": self._generation_name(node_id),
                "user": session_id,
            }
        return ChatOpenAI(**kwargs)

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
        node_id = kwargs.pop("node_id", "")
        run_id = kwargs.pop("run_id", "")
        static_context_components = kwargs.pop("static_context_components", None)
        output_reserved = int(kwargs.get("max_tokens", 6000) or 6000)
        if static_context_components is None:
            static_context_components = [
                {"name": "node_system_prompt", "category": "static_input", "content": system_prompt},
                {"name": "user_message", "category": "static_input", "content": question},
                {"name": "output_reserved", "category": "reserved", "tokens": output_reserved},
            ]
        budget = ContextBudgetEstimator().estimate(
            node_id=node_id or "simple",
            model=self.model_str,
            system_prompt=system_prompt,
            user_message=question,
            tool_count=0,
            components=static_context_components,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
        )
        ContextBudgetEstimator().log(budget)
        if run_id:
            try:
                ContextArchive(run_id=run_id).write_budget(node_id or "simple", budget)
            except Exception as exc:
                logger.warning("⚠️ [AICall] call_simple 写入 context budget 失败: %s", exc)

        logger.debug("📍 [AICall] call_simple 开始 | node=%s prompt=%d字 question=%d字 extra=%s",
                      node_id or "simple", len(system_prompt), len(question), list(kwargs.keys()) or "无")
        start = time.time()

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=question))

        session_id = self._normalize_langfuse_session_id(run_id)
        # 透传 kwargs（如 max_tokens）到 model.invoke
        model = self._create_chat_model(session_id=session_id, node_id=node_id or "simple")
        if kwargs:
            model = model.bind(**kwargs)

        model = self._bind_session_metadata(model, session_id, node_id=node_id or "simple")
        invoke_config = self._build_langchain_config(session_id, node_id=node_id or "simple")
        with self._langfuse_session_scope(session_id, node_id or "simple"):
            result = model.invoke(messages, config=invoke_config) if invoke_config else model.invoke(messages)
        content = result.content or ""
        usage = self._extract_usage_metadata(result)
        self._log_provider_usage(node_id or "simple", usage, source="provider_usage:call_simple")
        if run_id:
            final_components = [
                *static_context_components,
                {
                    "name": "final_output",
                    "category": "dynamic_runtime",
                    "content": content,
                },
            ]
            final_budget = ContextBudgetEstimator().estimate(
                node_id=node_id or "simple",
                model=self.model_str,
                system_prompt=system_prompt,
                user_message=question,
                components=final_components,
                api_base=self.api_base or "",
                api_key=self.api_key or "",
            )
            try:
                ContextArchive(run_id=run_id).write_budget(node_id or "simple", final_budget)
            except Exception as exc:
                logger.warning("⚠️ [AICall] call_simple 写入 final context budget 失败: %s", exc)
        logger.debug("✅ [AICall] call_simple 完成 | %.1fs | 输出=%d字",
                      time.time() - start, len(content))
        return content

    def call_simple_json(
        self,
        system_prompt: str,
        question: str,
        validator: Optional[Callable[[Any], bool]] = None,
        **kwargs,
    ) -> Tuple[Optional[Any], str]:
        """直接调用 LLM 并尽最大可能稳定获取 JSON。"""
        raw = self.call_simple(system_prompt, question, **kwargs)
        parsed = self.extract_json_payload(raw)
        if parsed is not None and validator is not None and not validator(parsed):
            parsed = None
        return parsed, raw

    def call_structured(
        self,
        system_prompt: str,
        question: str,
        schema: type[BaseModel],
        **kwargs,
    ) -> Tuple[Optional[BaseModel], str]:
        """Call the model and validate the JSON payload against a Pydantic schema."""
        raw = self.call_simple(system_prompt, question, **kwargs)
        parsed = self.extract_json_payload(raw)
        if parsed is None:
            logger.warning("⚠️ [AICall] structured output parse failed for schema=%s", schema.__name__)
            return None, raw

        try:
            return schema.model_validate(parsed), raw
        except ValidationError as exc:
            logger.warning(
                "⚠️ [AICall] structured output validation failed for schema=%s: %s",
                schema.__name__,
                exc,
            )
            return None, raw

    def call(
        self,
        system_prompt: str,
        question: str,
        tools: Optional[List] = None,
        max_steps: int = 10,
        stream_queue: Optional[queue.Queue] = None,
        node_id: str = "",
        run_id: str = "",
        cancel_event: Optional[Any] = None,
        stop_checker: Optional[Callable[[List[Dict]], bool]] = None,
        expect_json: bool = False,
        json_validator: Optional[Callable[[Any], bool]] = None,
        json_acceptance_guard: Optional[Callable[[Any, List[Dict]], bool]] = None,
        static_context_components: Optional[List[Dict[str, Any]]] = None,
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
        tool_result_sequence = 0
        iteration = 0
        seen_tool_call_signatures = set()
        seen_tool_result_signatures = set()
        observation_processor = self._build_observation_processor()
        if static_context_components is None:
            tool_schema_payload = serialize_tool_schema(tools or [])
            static_context_components = [
                {"name": "node_system_prompt", "category": "static_input", "content": system_prompt},
                {"name": "user_message", "category": "static_input", "content": question},
                {
                    "name": "tool_schema",
                    "category": "static_input",
                    "content": tool_schema_payload,
                },
                {"name": "scratchpad_reserved", "category": "reserved", "tokens": 4096},
                {"name": "output_reserved", "category": "reserved", "tokens": 6000},
            ]

        logger.debug("📍 [AICall] call 开始 | node=%s max_steps=%d tools=%d prompt=%d字 expect_json=%s",
                      node_id or "?", max_steps, len(tools or []), len(system_prompt), expect_json)

        # 无工具时直接调用 call_simple
        if not tools:
            content = self.call_simple(
                system_prompt,
                question,
                node_id=node_id,
                run_id=run_id,
                static_context_components=static_context_components,
            )
            total_ms = (time.time() - call_start) * 1000
            result = AICallResult(
                result=content, iterations=1, duration_ms=total_ms,
            )
            return result, thinking_events

        # 创建 LangChain Agent (create_agent，替代已废弃的 create_react_agent)
        from langchain.agents import create_agent

        session_id = self._normalize_langfuse_session_id(run_id)
        agent_model = self._bind_session_metadata(
            self._create_chat_model(session_id=session_id, node_id=node_id or "agent"),
            session_id,
            node_id=node_id or "agent",
        )
        agent = create_agent(
            model=agent_model,
            tools=tools,
            system_prompt=system_prompt,
        )

        # 使用 async stream 模式（MCP 工具需要异步调用）
        import asyncio
        import concurrent.futures

        input_messages = {"messages": [{"role": "user", "content": question}]}
        # recursion_limit 直接使用 config 传入的 max_steps，不做任何公式转换
        langfuse_config = self._build_langchain_config(session_id, node_id=node_id or "agent")
        config = {"recursion_limit": max_steps}
        if langfuse_config:
            config.update(langfuse_config)
        logger.info("📍 [AICall] node=%s | max_steps(recursion_limit)=%d", node_id or "?", max_steps)

        final_content = ""
        _content_buffer = []  # 收集 token 级别的文本片段
        tool_observation_contents: List[str] = []

        async def _run_agent():
            nonlocal final_content, iteration, tool_call_count, tool_result_sequence
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
                    token_text = self._extract_visible_ai_text(token_msg)
                    if token_text:
                        langgraph_node = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""
                        if langgraph_node != "tools":
                            _content_buffer.append(token_text)
                            push_event(stream_queue, "ai_token", node_id,
                                       content=token_text, iteration=iteration)
                    continue

                # ── updates 模式：消息/工具级别（原有逻辑） ──
                if chunk_type != "updates":
                    continue
                update_data = chunk_data if isinstance(chunk_data, dict) else {}
                for node_name, update in update_data.items():
                    messages = update.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            usage = self._extract_usage_metadata(msg)
                            if usage:
                                self._log_provider_usage(
                                    node_id or "agent",
                                    usage,
                                    source="provider_usage:agent_astream",
                                    iteration=iteration + 1,
                                )
                                self._record(
                                    thinking_events,
                                    "ai_usage",
                                    node_id,
                                    usage=usage,
                                    iteration=iteration + 1,
                                )
                            msg_tool_calls = list(msg.tool_calls or [])
                            new_tool_calls = []
                            for tc in msg_tool_calls:
                                signature = self._tool_call_signature(tc)
                                if signature in seen_tool_call_signatures:
                                    logger.debug(
                                        "   ♻️ [AICall] 跳过重复 tool_call replay | node=%s tool=%s signature=%s",
                                        node_id or "?",
                                        tc.get("name"),
                                        signature,
                                    )
                                    continue
                                seen_tool_call_signatures.add(signature)
                                new_tool_calls.append(tc)

                            if msg_tool_calls and not new_tool_calls and not msg.content:
                                continue

                            # AI 完整消息（用于 final_content 和工具调用检测）
                            full_msg_text = self._extract_visible_ai_text(msg)
                            should_emit_ai_message = bool(full_msg_text) and (not msg_tool_calls or bool(new_tool_calls))
                            if should_emit_ai_message:
                                final_content = full_msg_text
                                iteration += 1
                                logger.debug("   💬 [AICall] AI 消息 #%d:\n%s",
                                            iteration, full_msg_text[:1000])
                                evt = {"type": "ai_message",
                                       "content": full_msg_text[:500],
                                       "full_content": full_msg_text,
                                       "iteration": iteration}
                                self._push(stream_queue, node_id, thinking_events, **evt)

                                if expect_json and not msg.tool_calls:
                                    parsed = self.extract_json_payload(full_msg_text)
                                    if parsed is not None and (
                                        json_validator is None or json_validator(parsed)
                                    ):
                                        if json_acceptance_guard is not None and not json_acceptance_guard(parsed, thinking_events):
                                            logger.info(
                                                "⏭️ [AICall] JSON middleware 捕获到结构化输出，但接受条件未满足，继续 agent (node=%s)",
                                                node_id,
                                            )
                                            continue
                                        final_content = json.dumps(parsed, ensure_ascii=False)
                                        logger.info("🛑 [AICall] JSON middleware 捕获到有效结构化输出，提前结束 agent (node=%s)", node_id)
                                        return

                            # AI 工具调用
                            if new_tool_calls:
                                for tc in new_tool_calls:
                                    tool_call_count += 1
                                    logger.debug("   🔧 [AICall] tool_call #%d %s | args=%s",
                                                tool_call_count, tc["name"],
                                                str(tc.get("args", {}))[:300])
                                    push_event(stream_queue, "tool_start", node_id,
                                               tool_name=tc["name"],
                                               tool_args=tc.get("args", {}),
                                               tool_call_id=tc.get("id"),
                                               iteration=iteration)
                                    self._record(thinking_events, "tool_start", node_id,
                                                 tool_name=tc["name"],
                                                 tool_args=tc.get("args", {}),
                                                 tool_call_id=tc.get("id"),
                                                 iteration=iteration)

                        elif hasattr(msg, 'type') and msg.type == 'tool':
                            # 工具执行结果
                            tool_name = getattr(msg, 'name', '') or ''
                            tool_content = msg.content or ''
                            tool_signature = self._tool_result_signature(msg, tool_name, tool_content)
                            if tool_signature in seen_tool_result_signatures:
                                logger.debug(
                                    "   ♻️ [AICall] 跳过重复 tool_result replay | node=%s tool=%s signature=%s",
                                    node_id or "?",
                                    tool_name,
                                    tool_signature,
                                )
                                continue
                            seen_tool_result_signatures.add(tool_signature)
                            tool_result_sequence += 1
                            observation = self._process_tool_observation(
                                processor=observation_processor,
                                run_id=run_id,
                                node_id=node_id,
                                sequence=tool_result_sequence,
                                tool_name=tool_name,
                                tool_content=tool_content,
                                static_context_components=static_context_components,
                                prior_tool_observations=tool_observation_contents,
                            )
                            bounded_content = observation.get("summary", tool_content)
                            tool_observation_contents.append(bounded_content)
                            try:
                                msg.content = bounded_content
                            except Exception as exc:
                                logger.warning("⚠️ [AICall] ToolMessage 内容压缩回写失败: %s", exc)
                            status = "success"
                            all_tool_calls.append({
                                "tool_name": tool_name,
                                "result": bounded_content,
                                "raw_ref": observation.get("raw_ref"),
                                "structured_ref": observation.get("structured_ref"),
                                "summary_ref": observation.get("summary_ref"),
                                "raw_chars": observation.get("raw_chars", len(tool_content)),
                                "summary_chars": observation.get("summary_chars", len(bounded_content)),
                                "semantic_success": observation.get("semantic_success", True),
                                "structured": observation.get("structured"),
                            })
                            logger.info("   ✅ [AICall] tool #%d %s | %s | raw=%d summary=%d processor=%s",
                                        tool_call_count, tool_name, status,
                                        observation.get("raw_chars", len(tool_content)),
                                        observation.get("summary_chars", len(bounded_content)),
                                        observation.get("processor", "unknown"))
                            context_usage_ratio = observation.get("context_usage_ratio")
                            if isinstance(context_usage_ratio, (int, float)) and context_usage_ratio >= 0.8:
                                logger.warning(
                                    "   🧯 [AICall] context compression guard triggered | node=%s tool=%s usage=%.0f%% processor=%s",
                                    node_id or "?",
                                    tool_name,
                                    context_usage_ratio * 100,
                                    observation.get("processor", "unknown"),
                                )
                            logger.debug("   📄 [AICall] tool #%d %s 摘要输出:\n%s",
                                        tool_call_count, tool_name,
                                        bounded_content[:2000])
                            evt = {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "tool_call_id": getattr(msg, "tool_call_id", None),
                                "status": status,
                                "result_preview": bounded_content[:200],
                                "result": bounded_content,
                                "raw_ref": observation.get("raw_ref"),
                                "structured_ref": observation.get("structured_ref"),
                                "summary_ref": observation.get("summary_ref"),
                                "raw_chars": observation.get("raw_chars", len(tool_content)),
                                "summary_chars": observation.get("summary_chars", len(bounded_content)),
                                "semantic_success": observation.get("semantic_success", True),
                                "structured": observation.get("structured"),
                                "observation_processed": observation.get("processed", False),
                                "observation_processor": observation.get("processor", ""),
                                "iteration": iteration,
                            }
                            push_event(stream_queue, "tool_result", node_id, **evt)
                            self._record(thinking_events, "tool_result", node_id, **evt)

                            if stop_checker:
                                try:
                                    if stop_checker(thinking_events):
                                        logger.info("🛑 [AICall] stop_checker 触发，提前结束 agent (node=%s)", node_id)
                                        return
                                except Exception as exc:
                                    logger.warning("⚠️ [AICall] stop_checker 执行失败: %s", exc)

        # 在新线程中运行异步 agent（避免与 uvicorn event loop 冲突）
        def _run_agent_thread():
            with self._langfuse_session_scope(session_id, node_id or "agent"):
                asyncio.run(_run_agent())

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(_run_agent_thread).result(timeout=max_steps * 30)
        except concurrent.futures.TimeoutError:
            logger.warning("⚠️ [AICall] agent 执行超时 (%ds)", max_steps * 30)
            if not final_content:
                final_content = "Agent 执行超时"
        except GraphRecursionError as e:
            recursion_msg = str(e).splitlines()[0].strip()
            logger.warning("⚠️ [AICall] agent 达到递归/步数上限 (%d): %s", max_steps, recursion_msg)
            if not final_content:
                final_content = f"达到最大工具执行步数限制: {recursion_msg}"
        except Exception as e:
            logger.error("❌ [AICall] agent 执行异常: %s", e, exc_info=True)
            if not final_content:
                final_content = f"Agent 执行异常: {e}"

        total_ms = (time.time() - call_start) * 1000
        aggregate_usage = self._aggregate_usage_from_events(thinking_events)
        result = AICallResult(
            result=final_content,
            tool_calls=all_tool_calls,
            iterations=max(iteration, 1),
            tool_call_count=tool_call_count,
            duration_ms=total_ms,
            intermediate_events=thinking_events,
            input_tokens=aggregate_usage.get("input_tokens"),
            output_tokens=aggregate_usage.get("output_tokens"),
            total_tokens=aggregate_usage.get("total_tokens"),
        )
        self._write_final_context_budget(
            run_id=run_id,
            node_id=node_id or "unknown",
            system_prompt=system_prompt,
            question=question,
            static_context_components=static_context_components,
            thinking_events=thinking_events,
            final_content=final_content,
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

    @staticmethod
    def _extract_usage_metadata(message: Any) -> Dict[str, int]:
        usage = getattr(message, "usage_metadata", None) or {}
        if not usage:
            response_metadata = getattr(message, "response_metadata", None) or {}
            usage = response_metadata.get("token_usage") or {}
        if not isinstance(usage, dict):
            return {}
        result: Dict[str, int] = {}
        for src, dst in (
            ("input_tokens", "input_tokens"),
            ("output_tokens", "output_tokens"),
            ("total_tokens", "total_tokens"),
            ("prompt_tokens", "input_tokens"),
            ("completion_tokens", "output_tokens"),
        ):
            value = usage.get(src)
            if value is not None and dst not in result:
                try:
                    result[dst] = int(value)
                except (TypeError, ValueError):
                    pass
        if "total_tokens" not in result and "input_tokens" in result and "output_tokens" in result:
            result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
        return result

    def _log_provider_usage(
        self,
        node_id: str,
        usage: Dict[str, int],
        source: str,
        iteration: Optional[int] = None,
    ) -> None:
        input_tokens = usage.get("input_tokens")
        if input_tokens is None:
            return
        resolved = ModelContextResolver().resolve(
            self.model_str,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
        )
        window = resolved.get("context_window")
        input_usage = (
            f"{input_tokens / window:.2%}"
            if isinstance(window, int) and window > 0
            else "unknown"
        )
        iter_part = "" if iteration is None else f" iteration={iteration}"
        logger.info(
            "[context_usage.actual] node=%s%s input_tokens=%s input_usage=%s "
            "output_tokens=%s total_tokens=%s window=%s window_source=%s source=%s accuracy=exact",
            node_id or "unknown",
            iter_part,
            input_tokens,
            input_usage,
            usage.get("output_tokens", "unknown"),
            usage.get("total_tokens", "unknown"),
            window or "unknown",
            resolved.get("source"),
            source,
        )

    @staticmethod
    def _aggregate_usage_from_events(events: List[Dict[str, Any]]) -> Dict[str, int]:
        usage_events = [
            ev.get("usage") or {}
            for ev in events
            if ev.get("type") == "ai_usage" and isinstance(ev.get("usage"), dict)
        ]
        if not usage_events:
            return {}
        return {
            "input_tokens": sum(int(ev.get("input_tokens") or 0) for ev in usage_events),
            "output_tokens": sum(int(ev.get("output_tokens") or 0) for ev in usage_events),
            "total_tokens": sum(int(ev.get("total_tokens") or 0) for ev in usage_events),
        }

    @staticmethod
    def _extract_visible_ai_text(message: Any) -> str:
        """Return stream-visible AI text, including reasoning fields from compatible gateways."""
        if message is None:
            return ""

        content = getattr(message, "content", None) or ""
        additional_kwargs = getattr(message, "additional_kwargs", None) or {}
        response_metadata = getattr(message, "response_metadata", None) or {}

        reasoning = (
            additional_kwargs.get("reasoning_content")
            or additional_kwargs.get("reasoning")
            or response_metadata.get("reasoning_content")
            or response_metadata.get("reasoning")
            or ""
        )

        if reasoning and content:
            return f"{reasoning}{content}"
        if reasoning:
            return str(reasoning)
        return str(content or "")

    @staticmethod
    def _normalize_langfuse_session_id(run_id: str) -> Optional[str]:
        """Langfuse session_id must be a short US-ASCII string."""
        raw = str(run_id or "").strip()
        if not raw:
            return None
        ascii_text = raw.encode("ascii", errors="ignore").decode("ascii").strip()
        if not ascii_text:
            return None
        return ascii_text[:199]

    def _build_langchain_config(self, session_id: Optional[str], node_id: str = "") -> Dict[str, Any]:
        if not session_id:
            return {}
        # Keep this out of `metadata`: ChatOpenAI uses `metadata` both as a
        # runnable config field and as an OpenAI request field, which can cause
        # duplicate keyword errors when the model is also bound with request
        # metadata.
        tags = [f"session:{session_id}"]
        node_text = str(node_id or "").strip()
        if node_text:
            tags.append(f"node:{node_text}")
        config: Dict[str, Any] = {"tags": tags, "metadata": self._session_metadata(session_id, node_id)}
        if self._is_langfuse_sdk_configured():
            handler = self._create_langfuse_callback_handler()
            if handler is not None:
                config["callbacks"] = [handler]
        return config

    @staticmethod
    def _is_langfuse_sdk_configured() -> bool:
        return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

    @staticmethod
    def _create_langfuse_callback_handler() -> Optional[Any]:
        if not AICall._is_langfuse_sdk_configured():
            return None
        try:
            from langfuse.langchain import CallbackHandler

            return CallbackHandler()
        except Exception as exc:
            logger.debug("📉 [AICall] Langfuse CallbackHandler 不可用，跳过 callbacks: %s", exc)
            return None

    def _bind_session_metadata(self, model: Any, session_id: Optional[str], node_id: str = "") -> Any:
        if not session_id:
            return model
        metadata = self._session_metadata(session_id, node_id)
        if not metadata:
            return model
        try:
            # Keep `metadata` out of top-level bind/config. LangChain passes
            # runnable metadata internally to generate_prompt(); binding it as
            # a model kwarg causes "multiple values for keyword argument
            # metadata". OpenAI-compatible gateways still receive session data
            # through extra_body.metadata and user.
            return model.bind(
                extra_body={
                    "metadata": metadata,
                    "trace_id": self._trace_id(session_id, node_id),
                    "generation_name": self._generation_name(node_id),
                    "user": session_id,
                },
            )
        except Exception as exc:
            logger.debug("📉 [AICall] 绑定 session metadata 失败，继续原模型调用: %s", exc)
            return model

    @staticmethod
    def _session_metadata(session_id: Optional[str], node_id: str = "") -> Dict[str, str]:
        if not session_id:
            return {}
        trace_id = AICall._trace_id(session_id, node_id)
        metadata: Dict[str, str] = {
            "session_id": session_id,
            "langfuse_session_id": session_id,
            "run_id": session_id,
            "trace_id": trace_id,
        }
        node_text = str(node_id or "").strip()
        if node_text:
            metadata["node_id"] = node_text
            metadata["workflow_node"] = node_text
            metadata["generation_name"] = AICall._generation_name(node_text)
        return metadata

    @staticmethod
    def _trace_id(session_id: Optional[str], node_id: str = "") -> Optional[str]:
        if not session_id:
            return None
        node_text = str(node_id or "unknown").strip() or "unknown"
        return f"{session_id}:{node_text}"

    @staticmethod
    def _generation_name(node_id: str = "") -> str:
        node_text = str(node_id or "unknown").strip() or "unknown"
        return f"workflow-{node_text}"

    @contextmanager
    def _langfuse_session_scope(self, session_id: Optional[str], node_id: str):
        if not session_id:
            with nullcontext():
                yield
            return
        if not self._is_langfuse_sdk_configured():
            yield
            return
        try:
            from langfuse import get_client, propagate_attributes
        except Exception as exc:
            logger.debug("📉 [AICall] Langfuse session scope 不可用，直接执行: %s", exc)
            yield
            return

        logger.debug("📈 [AICall] Langfuse session_id=%s node=%s", session_id, node_id or "unknown")
        metadata = self._session_metadata(session_id, node_id)
        stack: Optional[ExitStack] = None
        try:
            langfuse = get_client()
            stack = ExitStack()
            stack.enter_context(langfuse.start_as_current_observation(
                as_type="span",
                name=f"workflow-{node_id or 'unknown'}",
                metadata=metadata,
            ))
            stack.enter_context(propagate_attributes(session_id=session_id))
        except Exception as exc:
            logger.debug("📉 [AICall] Langfuse span 创建失败，仅传播 session: %s", exc)
            with propagate_attributes(session_id=session_id):
                yield
            return

        try:
            yield
        finally:
            if stack is not None:
                stack.close()

    @staticmethod
    def _tool_call_signature(tool_call: Dict[str, Any]) -> str:
        name = tool_call.get("name") or "unknown"
        call_id = tool_call.get("id")
        if call_id:
            return f"id:{call_id}"
        args = tool_call.get("args", {})
        try:
            args_str = json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            args_str = str(args)
        return f"name:{name}|args:{args_str}"

    @staticmethod
    def _tool_result_signature(msg: Any, tool_name: str, tool_content: str) -> str:
        tool_call_id = getattr(msg, "tool_call_id", None)
        if tool_call_id:
            return f"id:{tool_call_id}"
        return f"name:{tool_name}|content:{tool_content}"

    def _build_observation_processor(self) -> ObservationProcessor:
        return ObservationProcessor(
            summarizer=self._summarize_tool_observation,
            max_observation_chars=self.observation_summary_max_chars,
            summary_mode=self.observation_summary_mode,
            context_pressure_threshold=0.8,
        )

    def _process_tool_observation(
        self,
        processor: ObservationProcessor,
        run_id: str,
        node_id: str,
        sequence: int,
        tool_name: str,
        tool_content: str,
        static_context_components: Optional[List[Dict[str, Any]]] = None,
        prior_tool_observations: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        effective_run_id = run_id or f"adhoc-{int(time.time())}"
        context_usage_ratio = self._estimate_observation_context_usage(
            static_context_components=static_context_components or [],
            prior_tool_observations=prior_tool_observations or [],
            candidate_observation=tool_content or "",
        )
        try:
            return processor.process(
                run_id=effective_run_id,
                node_id=node_id or "unknown",
                sequence=sequence,
                tool_name=tool_name or "unknown",
                raw_content=tool_content or "",
                context_usage_ratio=context_usage_ratio,
            )
        except Exception as exc:
            logger.warning("⚠️ [AICall] observation processor 失败，使用截断回退: %s", exc)
            summary = (tool_content or "")[:3000]
            refs: Dict[str, str] = {}
            try:
                refs = ContextArchive(run_id=effective_run_id).write_tool_artifact(
                    node_id=node_id or "unknown",
                    sequence=sequence,
                    tool_name=tool_name or "unknown",
                    raw=tool_content or "",
                    structured={"status": "fallback_truncate", "error": str(exc)},
                    summary=summary,
                )
            except Exception as archive_exc:
                logger.warning("⚠️ [AICall] fallback observation 归档失败: %s", archive_exc)
            return {
                "tool": tool_name,
                "status": "success",
                "semantic_success": False,
                "summary": summary,
                "raw_chars": len(tool_content or ""),
                "summary_chars": len(summary),
                "processed": False,
                "processor": "fallback_truncate",
                "context_usage_ratio": context_usage_ratio,
                **refs,
            }

    def _estimate_observation_context_usage(
        self,
        static_context_components: List[Dict[str, Any]],
        prior_tool_observations: List[str],
        candidate_observation: str,
    ) -> Optional[float]:
        components = [
            c for c in static_context_components
            if c.get("category") != "reserved"
        ]
        if prior_tool_observations or candidate_observation:
            components.append({
                "name": "tool_observations_after_candidate",
                "category": "dynamic_runtime",
                "content": "\n".join([*prior_tool_observations, candidate_observation]),
            })
        budget = ContextBudgetEstimator().estimate(
            node_id="observation_budget",
            model=self.model_str,
            system_prompt="",
            user_message="",
            components=components,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
            scratchpad_reserved=0,
            output_reserved=0,
        )
        context_window = budget.get("context_window")
        if not isinstance(context_window, int) or context_window <= 0:
            return None
        return float(budget.get("actual_context_tokens", 0)) / float(context_window)

    def _write_final_context_budget(
        self,
        run_id: str,
        node_id: str,
        system_prompt: str,
        question: str,
        static_context_components: List[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
        final_content: str,
    ) -> None:
        if not run_id:
            return
        tool_observation_text = "\n".join(
            ev.get("result", "") or ev.get("result_preview", "")
            for ev in thinking_events
            if ev.get("type") == "tool_result"
        )
        ai_message_text = "\n".join(
            ev.get("full_content", "") or ev.get("content", "")
            for ev in thinking_events
            if ev.get("type") == "ai_message"
        )
        final_components = [
            *static_context_components,
            {
                "name": "tool_observations",
                "category": "dynamic_runtime",
                "content": tool_observation_text,
                "preview": tool_observation_text[:200],
            },
            {
                "name": "ai_messages",
                "category": "dynamic_runtime",
                "content": ai_message_text,
                "preview": ai_message_text[:200],
            },
            {
                "name": "final_output",
                "category": "dynamic_runtime",
                "content": final_content or "",
                "preview": (final_content or "")[:200],
            },
        ]
        budget = ContextBudgetEstimator().estimate(
            node_id=node_id,
            model=self.model_str,
            system_prompt=system_prompt,
            user_message=question,
            components=final_components,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
        )
        ContextBudgetEstimator().log(budget)
        try:
            ContextArchive(run_id=run_id).write_budget(node_id, budget)
        except Exception as exc:
            logger.warning("⚠️ [AICall] 写入 final context budget 失败: %s", exc)

    def _summarize_tool_observation(self, tool_name: str, raw: str, current_summary: str) -> Optional[str]:
        if not raw:
            return current_summary
        try:
            prompt = get_workflow_prompt("tool_observation_summarizer")
            payload = {
                "tool": tool_name,
                "raw_chars": len(raw),
                "current_summary": current_summary[:4000],
                "raw_preview": raw[:12000],
            }
            parsed, text = self.call_simple_json(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False),
                validator=lambda data: isinstance(data, dict),
                max_tokens=2048,
            )
            if isinstance(parsed, dict) and parsed.get("summary"):
                facts = parsed.get("key_facts") or []
                conflicts = parsed.get("conflicts") or []
                missing = parsed.get("missing") or []
                lines = [str(parsed.get("summary", ""))]
                if facts:
                    lines.append("key_facts: " + json.dumps(facts, ensure_ascii=False, default=str))
                if conflicts:
                    lines.append("conflicts: " + json.dumps(conflicts, ensure_ascii=False, default=str))
                if missing:
                    lines.append("missing: " + json.dumps(missing, ensure_ascii=False, default=str))
                return "\n".join(lines)
            return text[:3000] if text else current_summary
        except Exception as exc:
            logger.warning("⚠️ [AICall] LLM observation summarizer 失败: %s", exc)
            return current_summary

    @staticmethod
    def extract_json_payload(text: str) -> Optional[Any]:
        """从模型文本中稳定提取第一个 JSON 对象/数组。"""
        if not isinstance(text, str) or not text.strip():
            return None

        candidates: List[str] = []

        fenced = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        candidates.extend(fenced)
        candidates.append(text.strip())

        balanced = AICall._extract_balanced_json_substring(text)
        if balanced:
            candidates.append(balanced)

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    @staticmethod
    def _extract_balanced_json_substring(text: str) -> Optional[str]:
        """提取文本中的第一个平衡 JSON 对象/数组。"""
        start = None
        opening = None
        closing = None
        depth = 0
        in_string = False
        escape = False

        for idx, ch in enumerate(text):
            if start is None and ch in "{[":
                start = idx
                opening = ch
                closing = "}" if ch == "{" else "]"
                depth = 1
                continue

            if start is None:
                continue

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return text[start:idx + 1]

        return None
