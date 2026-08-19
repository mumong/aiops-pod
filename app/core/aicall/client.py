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
import asyncio
import json
import logging
import os
import queue
import re
import time
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager, nullcontext
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple

import anyio
from pydantic import BaseModel, ValidationError
from langgraph.errors import GraphRecursionError
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from openai import (
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
)

from app.core.context.archive import ContextArchive
from app.core.context.budget import (
    ContextBudgetEstimator,
    ModelContextResolver,
    calculate_hard_input_limit,
    compact_text_to_token_budget,
    count_tokens,
    serialize_tool_schema,
)
from app.core.context.observation import ObservationProcessor
from app.core.prompts import get_workflow_prompt
from app.core.workflow.schemas import ContextCompactionSummary, ToolObservationSummary
from .streaming import push_event
from .types import AICallResult

logger = logging.getLogger(__name__)

# 已知模型提供商 → base_url 映射
_PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "openai": None,  # 默认
}

_PROVIDER_REQUEST_OVERHEAD_TOKENS = 64
_ESTIMATOR_DRIFT_RESERVE_TOKENS = 256
_RETRYABLE_STREAM_INTERRUPTION_SIGNATURES = (
    "unexpected eof",
    "empty_stream",
    "closed before first payload",
)


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


class StructuredContextBudgetError(RuntimeError):
    """Structured request rejected locally before a provider invocation."""

    def __init__(
        self,
        message: str,
        *,
        pre_budget: Optional[Dict[str, Any]] = None,
        final_budget: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.pre_budget = pre_budget
        self.final_budget = final_budget


class AICall:
    """LLM 调用核心类，基于 LangChain ChatModel + LangChain Agent (create_agent)"""

    def __init__(
        self,
        model: str,
        api_key: str,
        api_base: str = "",
        observation_summary_mode: str = "rule",
        observation_summary_max_chars: int = 3000,
        context_compaction_config: Optional[Dict[str, Any]] = None,
        chat_model_extra_body: Optional[Dict[str, Any]] = None,
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
        self.api_base = api_base.strip() if api_base and api_base.strip() else None
        normalized_mode = (observation_summary_mode or "rule").strip().lower()
        self.observation_summary_mode = normalized_mode if normalized_mode in {"rule", "ai"} else "rule"
        self.observation_summary_max_chars = max(200, int(observation_summary_max_chars or 3000))
        self.context_compaction_config = dict(context_compaction_config or {})
        self.chat_model_extra_body = deepcopy(chat_model_extra_body or {})

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

    def _create_chat_model(
        self,
        session_id: Optional[str] = None,
        node_id: str = "",
        disable_streaming: bool = False,
    ):
        """按次创建 ChatOpenAI，避免跨 asyncio event loop 复用底层 async client。"""
        kwargs = dict(self._chat_model_kwargs)
        if disable_streaming:
            kwargs["streaming"] = False
            kwargs["disable_streaming"] = True
        metadata = self._session_metadata(session_id, node_id)
        extra_body = self._build_extra_body(session_id, node_id, metadata)
        if extra_body:
            kwargs["extra_body"] = extra_body
        return ChatOpenAI(**kwargs)

    @staticmethod
    def _is_retryable_stream_eof(exc: Exception) -> bool:
        """Recognize the SDK's incomplete streamed-response failure."""
        if not isinstance(exc, APIError):
            return False
        if isinstance(exc, (APITimeoutError, APIResponseValidationError)):
            return False
        if isinstance(exc, APIStatusError) and not isinstance(
            exc,
            InternalServerError,
        ):
            return False
        current: Optional[BaseException] = exc
        seen = set()
        for _ in range(5):
            if current is None or id(current) in seen:
                break
            seen.add(id(current))
            message = str(current).strip().lower()
            if any(
                signature in message
                for signature in _RETRYABLE_STREAM_INTERRUPTION_SIGNATURES
            ):
                return True
            current = current.__cause__ or current.__context__
        return False

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
        try:
            (
                system_prompt,
                question,
                hard_guard,
                pre_guard_budget,
                budget,
            ) = self._prepare_structured_call_context(
                system_prompt=system_prompt,
                question=question,
                schema=None,
                node_id=node_id or "simple",
                output_reserved=output_reserved,
            )
        except StructuredContextBudgetError as exc:
            if run_id:
                try:
                    archive = ContextArchive(run_id=run_id)
                    if isinstance(exc.pre_budget, dict):
                        archive.write_budget(
                            f"{node_id or 'simple'}_pre_guard",
                            exc.pre_budget,
                        )
                    if isinstance(exc.final_budget, dict):
                        archive.write_budget(
                            node_id or "simple",
                            exc.final_budget,
                        )
                except Exception as archive_exc:
                    logger.warning(
                        "⚠️ [AICall] simple hard guard 失败归档写入失败: %s",
                        archive_exc,
                    )
            raise
        if static_context_components is None:
            static_context_components = [
                {
                    "name": "node_system_prompt",
                    "category": "static_input",
                    "content": system_prompt,
                },
                {
                    "name": "user_message",
                    "category": "static_input",
                    "content": question,
                },
                {
                    "name": "output_reserved",
                    "category": "reserved",
                    "tokens": output_reserved,
                },
                {
                    "name": "safety_margin",
                    "category": "reserved",
                    "tokens": hard_guard.get("safety_tokens", 0),
                },
                {
                    "name": "provider_request_overhead",
                    "category": "static_input",
                    "tokens": _PROVIDER_REQUEST_OVERHEAD_TOKENS,
                    "token_accuracy": "estimated",
                },
            ]
        ContextBudgetEstimator().log(budget)
        if run_id:
            try:
                archive = ContextArchive(run_id=run_id)
                archive.write_budget(
                    f"{node_id or 'simple'}_pre_guard",
                    pre_guard_budget,
                )
                archive.write_budget(node_id or "simple", budget)
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
        invoke_config = self._build_langchain_config(session_id, node_id=node_id or "simple")

        def _invoke(*, disable_streaming: bool = False):
            model = self._create_chat_model(
                session_id=session_id,
                node_id=node_id or "simple",
                disable_streaming=disable_streaming,
            )
            if kwargs:
                model = model.bind(**kwargs)
            model = self._bind_session_metadata(
                model,
                session_id,
                node_id=node_id or "simple",
            )
            with self._langfuse_session_scope(session_id, node_id or "simple"):
                if invoke_config:
                    return model.invoke(messages, config=invoke_config)
                return model.invoke(messages)

        try:
            result = _invoke()
        except Exception as exc:
            if not self._is_retryable_stream_eof(exc):
                raise
            logger.warning(
                "⚠️ [AICall] streamed response ended unexpectedly; "
                "retrying once without streaming | node=%s",
                node_id or "simple",
            )
            result = _invoke(disable_streaming=True)
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
                enable_usage_probe=False,
            )
            final_budget["hard_guard"] = hard_guard
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
        """Call the model with Pydantic structured output.

        Native structured output is the default and the workflow boundary.
        Text parsing fallback is disabled unless explicitly requested by a
        legacy caller via allow_text_fallback=True.
        """
        use_native = bool(kwargs.pop("use_native_structured", True))
        allow_text_fallback = bool(kwargs.pop("allow_text_fallback", False))
        context_compactor = kwargs.pop("context_compactor", None)
        node_id = str(kwargs.get("node_id") or "structured")
        run_id = str(kwargs.get("run_id") or "")
        output_reserved = int(kwargs.get("max_tokens", 6000) or 6000)
        try:
            (
                system_prompt,
                question,
                hard_guard,
                pre_guard_budget,
                final_guard_budget,
            ) = self._prepare_structured_call_context(
                system_prompt=system_prompt,
                question=question,
                schema=schema,
                node_id=node_id,
                output_reserved=output_reserved,
                context_compactor=context_compactor,
            )
        except StructuredContextBudgetError as exc:
            if run_id:
                try:
                    archive = ContextArchive(run_id=run_id)
                    if isinstance(exc.pre_budget, dict):
                        archive.write_budget(
                            f"{node_id}_pre_guard",
                            exc.pre_budget,
                        )
                    if isinstance(exc.final_budget, dict):
                        archive.write_budget(node_id, exc.final_budget)
                except Exception as archive_exc:
                    logger.warning(
                        "⚠️ [AICall] structured hard guard 失败归档写入失败: %s",
                        archive_exc,
                    )
            raise
        if run_id:
            try:
                archive = ContextArchive(run_id=run_id)
                archive.write_budget(f"{node_id}_pre_guard", pre_guard_budget)
                archive.write_budget(node_id, final_guard_budget)
            except Exception as exc:
                logger.warning(
                    "⚠️ [AICall] structured hard guard 写入 context budget 失败: %s",
                    exc,
                )
        if use_native:
            native, raw = self._call_native_structured(
                system_prompt,
                question,
                schema,
                hard_guard_metadata=hard_guard,
                hard_guard_budget=final_guard_budget,
                **kwargs,
            )
            if native is not None:
                return native, raw

        if not allow_text_fallback:
            logger.warning(
                "⚠️ [AICall] native structured output unavailable for schema=%s; text fallback disabled",
                schema.__name__,
            )
            return None, raw if 'raw' in locals() else ""

        # Compatibility fallback for OpenAI-compatible gateways that do not
        # support native structured output. The schema is still enforced by
        # Pydantic; invalid JSON is treated as no result.
        raw = self.call_simple(system_prompt, question, **kwargs)
        if run_id:
            try:
                ContextArchive(run_id=run_id).write_budget(
                    node_id,
                    final_guard_budget,
                )
            except Exception as exc:
                logger.warning(
                    "⚠️ [AICall] structured JSON fallback 写回 hard guard budget 失败: %s",
                    exc,
                )
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

    def _call_native_structured(
        self,
        system_prompt: str,
        question: str,
        schema: type[BaseModel],
        **kwargs,
    ) -> Tuple[Optional[BaseModel], str]:
        node_id = kwargs.pop("node_id", "")
        run_id = kwargs.pop("run_id", "")
        static_context_components = kwargs.pop("static_context_components", None)
        structured_method = kwargs.pop("structured_method", "function_calling")
        hard_guard_metadata = kwargs.pop("hard_guard_metadata", None)
        hard_guard_budget = kwargs.pop("hard_guard_budget", None)
        output_reserved = int(kwargs.get("max_tokens", 6000) or 6000)
        try:
            schema_payload = schema.model_json_schema()
        except Exception:
            schema_payload = {"schema": getattr(schema, "__name__", str(schema))}
        if static_context_components is None:
            static_context_components = [
                {"name": "node_system_prompt", "category": "static_input", "content": system_prompt},
                {"name": "user_message", "category": "static_input", "content": question},
                {"name": "structured_schema", "category": "static_input", "content": schema_payload},
                {"name": "output_reserved", "category": "reserved", "tokens": output_reserved},
            ]
        elif not any(
            component.get("name") == "structured_schema"
            for component in static_context_components
        ):
            static_context_components = [
                *static_context_components,
                {
                    "name": "structured_schema",
                    "category": "static_input",
                    "content": schema_payload,
                },
            ]
        if isinstance(hard_guard_budget, dict):
            budget = deepcopy(hard_guard_budget)
        else:
            budget = ContextBudgetEstimator().estimate(
                node_id=node_id or "structured",
                model=self.model_str,
                system_prompt=system_prompt,
                user_message=question,
                tool_count=0,
                components=static_context_components,
                api_base=self.api_base or "",
                api_key=self.api_key or "",
                enable_usage_probe=False,
            )
        if isinstance(hard_guard_metadata, dict):
            budget["hard_guard"] = hard_guard_metadata
        ContextBudgetEstimator().log(budget)
        if run_id:
            try:
                ContextArchive(run_id=run_id).write_budget(node_id or "structured", budget)
            except Exception as exc:
                logger.warning("⚠️ [AICall] call_structured 写入 context budget 失败: %s", exc)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=question))

        session_id = self._normalize_langfuse_session_id(run_id)
        try:
            model = self._create_chat_model(
                session_id=session_id,
                node_id=node_id or "structured",
                disable_streaming=True,
            )
            if kwargs:
                model = model.bind(**kwargs)
            model = self._bind_session_metadata(model, session_id, node_id=node_id or "structured")
            if not hasattr(model, "with_structured_output"):
                return None, ""
            structured_model = model.with_structured_output(schema, method=structured_method)
            invoke_config = self._build_langchain_config(session_id, node_id=node_id or "structured")
            with self._langfuse_session_scope(session_id, node_id or "structured"):
                result = (
                    structured_model.invoke(messages, config=invoke_config)
                    if invoke_config
                    else structured_model.invoke(messages)
                )
            if isinstance(result, schema):
                raw = result.model_dump_json()
                return result, raw
            if isinstance(result, dict):
                parsed = schema.model_validate(result)
                return parsed, json.dumps(parsed.model_dump(), ensure_ascii=False, default=str)
            logger.warning(
                "⚠️ [AICall] native structured output returned unsupported type=%s schema=%s",
                type(result).__name__,
                schema.__name__,
            )
            return None, str(result)
        except Exception as exc:
            logger.warning(
                "⚠️ [AICall] native structured output failed for schema=%s, fallback to JSON: %s",
                schema.__name__,
                exc,
            )
            return None, ""

    def _prepare_structured_call_context(
        self,
        *,
        system_prompt: str,
        question: str,
        schema: Optional[type[BaseModel]],
        node_id: str,
        output_reserved: int,
        context_compactor: Optional[Callable[..., str]] = None,
    ) -> Tuple[str, str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Apply a deterministic hard budget before any provider call."""
        config = self._structured_hard_guard_config()
        resolved = ModelContextResolver().resolve(
            self.model_str,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
        )
        context_window = resolved.get("context_window")
        schema_payload: Any = None
        if schema is not None:
            try:
                schema_payload = schema.model_json_schema()
            except Exception:
                schema_payload = {
                    "schema": getattr(schema, "__name__", str(schema))
                }

        safety_margin = int(config["safety_tokens"])
        components = [
            {
                "name": "node_system_prompt",
                "category": "static_input",
                "content": system_prompt,
            },
            {
                "name": "user_message",
                "category": "static_input",
                "content": question,
            },
            {
                "name": "output_reserved",
                "category": "reserved",
                "tokens": output_reserved,
            },
            {
                "name": "safety_margin",
                "category": "reserved",
                "tokens": safety_margin,
            },
            {
                "name": "provider_request_overhead",
                "category": "static_input",
                "tokens": _PROVIDER_REQUEST_OVERHEAD_TOKENS,
                "token_accuracy": "estimated",
            },
        ]
        if schema_payload is not None:
            components.insert(2, {
                "name": "structured_schema",
                "category": "static_input",
                "content": schema_payload,
            })
        estimator = ContextBudgetEstimator()
        pre_budget = estimator.estimate(
            node_id=node_id,
            model=self.model_str,
            system_prompt=system_prompt,
            user_message=question,
            components=components,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
            enable_usage_probe=False,
        )
        schema_tokens = (
            count_tokens(schema_payload, model=self.model_str)["tokens"]
            if schema_payload is not None
            else 0
        )
        local_input_tokens = int(pre_budget.get("actual_context_tokens") or 0)
        original_input_tokens = local_input_tokens
        token_count_accuracy = str(
            pre_budget.get("token_count_accuracy") or "estimated"
        ).strip().lower()
        metadata: Dict[str, Any] = {
            "enabled": bool(config["enabled"]),
            "triggered": False,
            "strategy": "none",
            "context_window": context_window,
            "input_ratio": config["input_ratio"],
            "output_reserved": output_reserved,
            "safety_tokens": safety_margin,
            "original_input_tokens": original_input_tokens,
            "final_input_tokens": original_input_tokens,
            "max_input_tokens": None,
            "effective_input_target": None,
            "estimator_drift_reserve": 0,
            "token_count_accuracy": token_count_accuracy,
            "original_question_chars": len(question),
            "final_question_chars": len(question),
        }
        pre_budget["hard_guard"] = dict(metadata)

        if not config["enabled"]:
            final_budget = dict(pre_budget)
            return system_prompt, question, metadata, pre_budget, final_budget
        if not isinstance(context_window, int) or context_window <= 0:
            metadata["error"] = "context_window_unavailable"
            pre_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} context window is unavailable",
                pre_budget=pre_budget,
            )

        max_input_tokens = calculate_hard_input_limit(
            context_window=context_window,
            output_reserved=output_reserved,
            safety_margin=safety_margin,
            input_ratio=float(config["input_ratio"]),
        )
        metadata["max_input_tokens"] = max_input_tokens
        estimator_drift_reserve = (
            0
            if token_count_accuracy == "exact"
            else min(
                max_input_tokens,
                int(config["estimator_drift_reserve"]),
            )
        )
        effective_input_target = max(
            0,
            max_input_tokens - estimator_drift_reserve,
        )
        metadata["effective_input_target"] = effective_input_target
        metadata["estimator_drift_reserve"] = estimator_drift_reserve
        pre_budget["hard_guard"] = dict(metadata)
        if effective_input_target <= 0:
            metadata["error"] = "input_budget_unavailable"
            pre_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} has no input budget after "
                f"output_reserved={output_reserved} safety={safety_margin} "
                f"estimator_drift_reserve={estimator_drift_reserve}",
                pre_budget=pre_budget,
            )

        final_question = question
        strategies: List[str] = []
        system_tokens = count_tokens(
            system_prompt,
            model=self.model_str,
        )["tokens"]
        local_question_budget = (
            effective_input_target
            - system_tokens
            - schema_tokens
            - _PROVIDER_REQUEST_OVERHEAD_TOKENS
        )
        if local_question_budget <= 0:
            metadata["error"] = "static_contract_exceeds_input_budget"
            pre_budget["hard_guard"] = dict(metadata)
            contract_name = (
                "system prompt and structured schema"
                if schema_payload is not None
                else "system prompt"
            )
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} {contract_name} exceed "
                f"hard input budget {max_input_tokens} "
                f"(effective target {effective_input_target})",
                pre_budget=pre_budget,
            )

        if original_input_tokens > effective_input_target:
            metadata["triggered"] = True
            if callable(context_compactor):
                try:
                    compacted = context_compactor(
                        final_question,
                        max_tokens=local_question_budget,
                        model=self.model_str,
                    )
                    if isinstance(compacted, str) and compacted.strip():
                        final_question = compacted
                        strategies.append("node_compactor")
                except Exception as exc:
                    logger.warning(
                        "⚠️ [AICall] node-specific context compactor failed "
                        "node=%s: %s",
                        node_id,
                        exc,
                    )

            if (
                count_tokens(final_question, model=self.model_str)["tokens"]
                > local_question_budget
            ):
                final_question = compact_text_to_token_budget(
                    final_question,
                    max_tokens=local_question_budget,
                    model=self.model_str,
                    preserve_tail_tokens=int(config["preserve_tail_tokens"]),
                )
                strategies.append("deterministic_head_tail")

        def _estimate_candidate(candidate_question: str) -> Dict[str, Any]:
            candidate_components = [
                {
                    "name": "node_system_prompt",
                    "category": "static_input",
                    "content": system_prompt,
                },
                {
                    "name": "user_message",
                    "category": "static_input",
                    "content": candidate_question,
                },
                {
                    "name": "output_reserved",
                    "category": "reserved",
                    "tokens": output_reserved,
                },
                {
                    "name": "safety_margin",
                    "category": "reserved",
                    "tokens": safety_margin,
                },
                {
                    "name": "provider_request_overhead",
                    "category": "static_input",
                    "tokens": _PROVIDER_REQUEST_OVERHEAD_TOKENS,
                    "token_accuracy": "estimated",
                },
            ]
            if schema_payload is not None:
                candidate_components.insert(2, {
                    "name": "structured_schema",
                    "category": "static_input",
                    "content": schema_payload,
                })
            return estimator.estimate(
                node_id=node_id,
                model=self.model_str,
                system_prompt=system_prompt,
                user_message=candidate_question,
                components=candidate_components,
                api_base=self.api_base or "",
                api_key=self.api_key or "",
                enable_usage_probe=False,
            )

        final_budget = _estimate_candidate(final_question)
        final_input_tokens = int(
            final_budget.get("actual_context_tokens") or 0
        )

        if final_input_tokens > effective_input_target:
            metadata["error"] = "deterministic_compaction_failed"
            metadata["final_input_tokens"] = final_input_tokens
            metadata["final_question_chars"] = len(final_question)
            pre_budget["hard_guard"] = dict(metadata)
            final_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} deterministic compaction failed: "
                f"input={final_input_tokens} target={effective_input_target} "
                f"limit={max_input_tokens}",
                pre_budget=pre_budget,
                final_budget=final_budget,
            )

        metadata.update({
            "strategy": "+".join(strategies) if strategies else "none",
            "final_input_tokens": final_input_tokens,
            "final_question_chars": len(final_question),
        })
        pre_budget["hard_guard"] = dict(metadata)
        final_budget["hard_guard"] = dict(metadata)
        if metadata["triggered"]:
            logger.warning(
                "🧯 [AICall] structured hard context guard | node=%s "
                "input=%d→%d target=%d limit=%d chars=%d→%d strategy=%s",
                node_id,
                original_input_tokens,
                final_input_tokens,
                effective_input_target,
                max_input_tokens,
                len(question),
                len(final_question),
                metadata["strategy"],
            )
        return (
            system_prompt,
            final_question,
            metadata,
            pre_budget,
            final_budget,
        )

    def _structured_hard_guard_config(self) -> Dict[str, Any]:
        config = self.context_compaction_config
        enabled = bool(config.get("hard_guard_enabled", True))
        try:
            input_ratio = float(config.get("hard_guard_input_ratio", 0.72))
        except (TypeError, ValueError):
            input_ratio = 0.72
        try:
            safety_tokens = int(config.get("hard_guard_safety_tokens", 2000))
        except (TypeError, ValueError):
            safety_tokens = 2000
        try:
            preserve_tail_tokens = int(
                config.get("hard_guard_preserve_tail_tokens", 1200)
            )
        except (TypeError, ValueError):
            preserve_tail_tokens = 1200
        try:
            estimator_drift_reserve = int(
                config.get(
                    "hard_guard_estimator_drift_reserve",
                    _ESTIMATOR_DRIFT_RESERVE_TOKENS,
                )
            )
        except (TypeError, ValueError):
            estimator_drift_reserve = _ESTIMATOR_DRIFT_RESERVE_TOKENS
        return {
            "enabled": enabled,
            "input_ratio": min(max(input_ratio, 0.05), 0.95),
            "safety_tokens": max(0, safety_tokens),
            "preserve_tail_tokens": max(0, preserve_tail_tokens),
            "estimator_drift_reserve": max(
                _ESTIMATOR_DRIFT_RESERVE_TOKENS,
                estimator_drift_reserve,
            ),
        }

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
        response_schema: Optional[type[BaseModel]] = None,
        tool_result_sequence_start: int = 0,
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
            response_schema: 可选 Pydantic schema。传入时使用 LangChain
                create_agent(response_format=ToolStrategy(schema))，在同一次
                agent 工具循环内生成结构化结果。

        Returns:
            (AICallResult, thinking_events)
        """
        call_start = time.time()
        thinking_events: List[Dict] = []
        all_tool_calls: List[Dict] = []
        tool_call_count = 0
        tool_result_sequence = max(0, int(tool_result_sequence_start or 0))
        iteration = 0
        seen_tool_call_signatures = set()
        seen_tool_result_signatures = set()
        tool_args_by_call_id: Dict[str, Dict[str, Any]] = {}
        tool_sequence_by_call_id: Dict[str, int] = {}
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

        # 无工具且不需要 agent structured_response 时直接调用 call_simple。
        if not tools and response_schema is None:
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
        response_format = None
        structured_output_tool_names = set()
        if response_schema is not None:
            from langchain.agents.structured_output import ToolStrategy

            response_format = ToolStrategy(
                schema=response_schema,
                tool_message_content="结构化结果已生成。",
            )
            structured_output_tool_names = {
                str(getattr(spec, "name", ""))
                for spec in getattr(response_format, "schema_specs", [])
                if str(getattr(spec, "name", "")).strip()
            }

        def _create_agent_instance(*, disable_streaming: bool = False):
            agent_model = self._bind_session_metadata(
                self._create_chat_model(
                    session_id=session_id,
                    node_id=node_id or "agent",
                    disable_streaming=disable_streaming,
                ),
                session_id,
                node_id=node_id or "agent",
            )
            create_agent_kwargs = {
                "model": agent_model,
                "tools": tools,
                "system_prompt": system_prompt,
                "middleware": [
                    self._build_context_hard_guard_middleware(
                        node_id=node_id or "agent",
                        run_id=run_id,
                    ),
                    self._build_tool_dedup_middleware(),
                ],
            }
            if response_format is not None:
                create_agent_kwargs["response_format"] = response_format
            return create_agent(**create_agent_kwargs)

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
        structured_response = None
        _content_buffer = []  # 收集 token 级别的文本片段
        tool_observation_contents: List[str] = []
        compaction_count = 0
        try:
            max_compactions = max(
                0,
                int(
                    self._runtime_compaction_config().get(
                        "max_compactions_per_call",
                        1,
                    )
                    or 0
                ),
            )
        except (TypeError, ValueError):
            max_compactions = 1
        emitted_ai_messages: List[Tuple[Any, str]] = []
        emitted_tool_messages: List[Tuple[Any, Dict[str, Any]]] = []
        agent = None

        async def _run_agent():
            nonlocal final_content, structured_response, iteration, tool_call_count, tool_result_sequence, compaction_count
            model_request_started_at = time.time()
            async for chunk in agent.astream(
                input_messages, config=config,
                stream_mode=["updates", "messages"],
                version="v2",
            ):
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

                if (
                    chunk_type != "updates"
                    and cancel_event
                    and cancel_event.is_set()
                ):
                    logger.info("🛑 [AICall] 收到取消信号，停止 agent (node=%s)", node_id)
                    break

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
                    if isinstance(update, dict) and update.get("structured_response") is not None:
                        structured_response = update.get("structured_response")
                        final_content = self._serialize_structured_response(structured_response)
                        self._record(
                            thinking_events,
                            "structured_response",
                            node_id,
                            schema=getattr(response_schema, "__name__", "") if response_schema else "",
                            content=final_content[:1000],
                        )
                    messages = update.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            usage = self._extract_usage_metadata(msg)
                            if usage:
                                model_duration_ms = max(
                                    0.0,
                                    (time.time() - model_request_started_at) * 1000,
                                )
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
                                    model_duration_ms=model_duration_ms,
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
                            should_track_ai_message = (
                                bool(full_msg_text) or bool(new_tool_calls)
                            ) and (
                                not msg_tool_calls or bool(new_tool_calls)
                            )
                            if should_track_ai_message:
                                emitted_ai_messages.append(
                                    (msg, full_msg_text)
                                )
                                if compaction_count > 0:
                                    self._compact_langgraph_ai_messages_in_place(
                                        emitted_ai_messages
                                    )

                            should_emit_ai_message = (
                                bool(full_msg_text)
                                and should_track_ai_message
                            )
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
                                    if tc.get("name") in structured_output_tool_names:
                                        logger.info(
                                            "🧾 [AICall] structured response emitted | node=%s schema=%s",
                                            node_id or "?",
                                            tc.get("name"),
                                        )
                                        continue
                                    tool_call_count += 1
                                    tool_sequence = tool_call_count
                                    logger.debug("   🔧 [AICall] tool_call #%d %s | args=%s",
                                                tool_sequence, tc["name"],
                                                str(tc.get("args", {}))[:300])
                                    push_event(stream_queue, "tool_start", node_id,
                                               tool_name=tc["name"],
                                               tool_args=tc.get("args", {}),
                                               tool_call_id=tc.get("id"),
                                               tool_sequence=tool_sequence,
                                               iteration=iteration)
                                    if tc.get("id"):
                                        call_id = str(tc.get("id"))
                                        tool_args_by_call_id[call_id] = dict(tc.get("args") or {})
                                        tool_sequence_by_call_id[call_id] = tool_sequence
                                    self._record(thinking_events, "tool_start", node_id,
                                                 tool_name=tc["name"],
                                                 tool_args=tc.get("args", {}),
                                                 tool_call_id=tc.get("id"),
                                                 tool_sequence=tool_sequence,
                                                 iteration=iteration)

                        elif hasattr(msg, 'type') and msg.type == 'tool':
                            # 工具执行结果
                            tool_name = getattr(msg, 'name', '') or ''
                            if tool_name in structured_output_tool_names:
                                logger.debug(
                                    "🧾 [AICall] 跳过结构化输出 tool_result 统计 | node=%s schema=%s",
                                    node_id or "?",
                                    tool_name,
                                )
                                continue
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
                                tool_args=tool_args_by_call_id.get(str(getattr(msg, "tool_call_id", None)), {}),
                            )
                            bounded_content = observation.get("summary", tool_content)
                            tool_observation_contents.append(bounded_content)
                            try:
                                msg.content = bounded_content
                                additional_kwargs = dict(
                                    getattr(msg, "additional_kwargs", None) or {}
                                )
                                additional_kwargs.update({
                                    "aiops_raw_ref": observation.get("raw_ref"),
                                    "aiops_structured_ref": observation.get(
                                        "structured_ref"
                                    ),
                                    "aiops_summary_ref": observation.get(
                                        "summary_ref"
                                    ),
                                    "aiops_semantic_success": observation.get(
                                        "semantic_success",
                                        True,
                                    ),
                                })
                                msg.additional_kwargs = additional_kwargs
                            except Exception as exc:
                                logger.warning("⚠️ [AICall] ToolMessage 内容压缩回写失败: %s", exc)
                            status = str(
                                getattr(msg, "status", "success") or "success"
                            ).strip().lower()
                            if status not in {"success", "error"}:
                                status = "success"
                            if status == "error":
                                observation["semantic_success"] = False
                            tool_call_id = getattr(msg, "tool_call_id", None)
                            tool_args = tool_args_by_call_id.get(str(tool_call_id), {}) if tool_call_id else {}
                            tool_sequence = tool_sequence_by_call_id.get(
                                str(tool_call_id),
                                tool_result_sequence,
                            )
                            additional_kwargs = getattr(msg, "additional_kwargs", None) or {}
                            deduplicated = bool(additional_kwargs.get("aiops_deduplicated"))
                            original_tool_call_id = additional_kwargs.get(
                                "aiops_original_tool_call_id"
                            )
                            all_tool_calls.append({
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "status": status,
                                "result": bounded_content,
                                "raw_ref": observation.get("raw_ref"),
                                "structured_ref": observation.get("structured_ref"),
                                "summary_ref": observation.get("summary_ref"),
                                "raw_chars": observation.get("raw_chars", len(tool_content)),
                                "summary_chars": observation.get("summary_chars", len(bounded_content)),
                                "semantic_success": observation.get("semantic_success", True),
                                "structured": observation.get("structured"),
                                "deduplicated": deduplicated,
                                "original_tool_call_id": original_tool_call_id,
                            })
                            emitted_tool_messages.append((msg, {
                                "tool_name": tool_name,
                                "semantic_success": observation.get(
                                    "semantic_success",
                                    True,
                                ),
                                "result_preview": bounded_content[:500],
                                "raw_ref": observation.get("raw_ref"),
                                "structured_ref": observation.get("structured_ref"),
                                "summary_ref": observation.get("summary_ref"),
                                "summary_chars": observation.get("summary_chars", len(bounded_content)),
                            }))
                            logger.info("   ✅ [AICall] tool #%d %s | %s | raw=%d summary=%d processor=%s",
                                        tool_sequence, tool_name, status,
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
                                        tool_sequence, tool_name,
                                        bounded_content[:2000])
                            evt = {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "tool_call_id": tool_call_id,
                                "tool_sequence": tool_sequence,
                                "tool_args": tool_args,
                                "status": status,
                                "deduplicated": deduplicated,
                                "original_tool_call_id": original_tool_call_id,
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
                                "context_usage_ratio": observation.get("context_usage_ratio"),
                                "iteration": iteration,
                            }
                            push_event(stream_queue, "tool_result", node_id, **evt)
                            self._record(thinking_events, "tool_result", node_id, **evt)
                            model_request_started_at = time.time()

                            if compaction_count < max_compactions:
                                compacted = await anyio.to_thread.run_sync(
                                    partial(
                                        self._maybe_compact_runtime_context,
                                        node_id=node_id or "unknown",
                                        run_id=run_id,
                                        static_context_components=static_context_components,
                                        thinking_events=thinking_events,
                                        tool_observation_contents=tool_observation_contents,
                                    ),
                                )
                                if compacted:
                                    compaction_count += 1
                                    self._compact_langgraph_ai_messages_in_place(emitted_ai_messages)
                                    self._compact_langgraph_tool_messages_in_place(emitted_tool_messages)

                if cancel_event and cancel_event.is_set():
                    logger.info("🛑 [AICall] 收到取消信号，停止 agent (node=%s)", node_id)
                    break
                if stop_checker:
                    try:
                        if stop_checker(thinking_events):
                            logger.info("🛑 [AICall] stop_checker 触发，提前结束 agent (node=%s)", node_id)
                            self._record(
                                thinking_events,
                                "early_stop",
                                node_id,
                                reason="stop_checker",
                                iteration=iteration,
                            )
                            return
                    except Exception as exc:
                        logger.warning("⚠️ [AICall] stop_checker 执行失败: %s", exc)

        # 在新线程中运行异步 agent（避免与 uvicorn event loop 冲突）
        def _run_agent_thread():
            with self._langfuse_session_scope(session_id, node_id or "agent"):
                asyncio.run(_run_agent())

        def _agent_has_progress() -> bool:
            return bool(
                tool_call_count
                or iteration
                or _content_buffer
                or final_content
                or structured_response is not None
                or seen_tool_call_signatures
                or seen_tool_result_signatures
                or all_tool_calls
                or emitted_ai_messages
                or emitted_tool_messages
            )

        for attempt in range(2):
            try:
                agent = _create_agent_instance(
                    disable_streaming=attempt == 1,
                )
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(_run_agent_thread).result(timeout=max_steps * 30)
                break
            except concurrent.futures.TimeoutError:
                logger.warning("⚠️ [AICall] agent 执行超时 (%ds)", max_steps * 30)
                if not final_content:
                    final_content = "Agent 执行超时"
                break
            except GraphRecursionError as e:
                recursion_msg = str(e).splitlines()[0].strip()
                logger.warning("⚠️ [AICall] agent 达到递归/步数上限 (%d): %s", max_steps, recursion_msg)
                if not final_content:
                    final_content = f"达到最大工具执行步数限制: {recursion_msg}"
                break
            except Exception as e:
                if (
                    attempt == 0
                    and self._is_retryable_stream_eof(e)
                    and not _agent_has_progress()
                ):
                    logger.warning(
                        "⚠️ [AICall] agent stream ended before first payload; "
                        "retrying once without streaming | node=%s",
                        node_id or "agent",
                    )
                    continue
                logger.error("❌ [AICall] agent 执行异常: %s", e, exc_info=True)
                if not final_content:
                    final_content = f"Agent 执行异常: {e}"
                break

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
            structured_response=structured_response,
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

    def execute_tool_batch(
        self,
        *,
        tool_requests: List[Dict[str, Any]],
        tools: List[Any],
        stream_queue: Optional[queue.Queue] = None,
        node_id: str = "",
        run_id: str = "",
        cancel_event: Optional[Any] = None,
        max_workers: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a bounded, code-owned read-only tool baseline in parallel.

        This method deliberately does not ask a model to choose or schedule the
        supplied calls.  It still sends every raw result through the same
        ObservationProcessor and ContextArchive path as a normal ReAct tool
        call, so baseline evidence has identical source refs and structured
        semantics.  Returned events are ordered by request order even though
        the underlying I/O runs concurrently.
        """
        requests = [
            dict(request)
            for request in (tool_requests or [])
            if isinstance(request, dict)
            and str(request.get("tool_name") or "").strip()
        ]
        if not requests:
            return []

        tool_index = {
            str(getattr(tool, "name", "") or "").strip(): tool
            for tool in (tools or [])
            if str(getattr(tool, "name", "") or "").strip()
        }
        events: List[Dict[str, Any]] = []
        for sequence, request in enumerate(requests, start=1):
            self._push(
                stream_queue,
                node_id,
                events,
                type="tool_start",
                tool_name=str(request["tool_name"]),
                tool_args=dict(request.get("tool_args") or {}),
                tool_call_id=f"baseline-{sequence}-{request['tool_name']}",
                tool_sequence=sequence,
                iteration=0,
                execution_phase="pre_react_baseline",
            )

        def invoke(request: Dict[str, Any]) -> Dict[str, Any]:
            started_at = time.time()
            tool_name = str(request.get("tool_name") or "")
            tool = tool_index.get(tool_name)
            if cancel_event is not None and cancel_event.is_set():
                return {
                    "status": "error",
                    "content": json.dumps({
                        "status": "cancelled",
                        "semantic_success": False,
                        "error": "diagnosis cancelled before baseline tool execution",
                    }, ensure_ascii=False),
                    "duration_seconds": 0.0,
                }
            if tool is None:
                return {
                    "status": "error",
                    "content": json.dumps({
                        "status": "tool_unavailable",
                        "semantic_success": False,
                        "error": f"tool not loaded: {tool_name}",
                    }, ensure_ascii=False),
                    "duration_seconds": 0.0,
                }
            try:
                args = dict(request.get("tool_args") or {})
                if hasattr(tool, "invoke"):
                    try:
                        value = tool.invoke(args)
                    except NotImplementedError:
                        if not hasattr(tool, "ainvoke"):
                            raise
                        # MCP StructuredTools are commonly async-only.  Each
                        # baseline request owns a worker thread, so it is safe
                        # to run its coroutine in a private event loop here.
                        value = asyncio.run(tool.ainvoke(args))
                elif hasattr(tool, "ainvoke"):
                    value = asyncio.run(tool.ainvoke(args))
                elif callable(tool):
                    value = tool(**args)
                else:
                    raise TypeError(f"tool is not invokable: {tool_name}")
                if hasattr(value, "content"):
                    value = value.content
                content = (
                    value
                    if isinstance(value, str)
                    else json.dumps(value, ensure_ascii=False, default=str)
                )
                return {
                    "status": "success",
                    "content": content,
                    "duration_seconds": time.time() - started_at,
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "error",
                    "content": json.dumps({
                        "status": "tool_error",
                        "semantic_success": False,
                        "error": {
                            "type": type(exc).__name__,
                            "message": str(exc) or type(exc).__name__,
                        },
                    }, ensure_ascii=False),
                    "duration_seconds": time.time() - started_at,
                }

        worker_count = max(1, min(
            int(max_workers or len(requests)),
            len(requests),
        ))
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(invoke, request) for request in requests]
            outcomes = [future.result() for future in futures]

        processor = self._build_observation_processor()
        prior_observations: List[str] = []
        for sequence, (request, outcome) in enumerate(
            zip(requests, outcomes),
            start=1,
        ):
            tool_name = str(request["tool_name"])
            tool_args = dict(request.get("tool_args") or {})
            observation = self._process_tool_observation(
                processor=processor,
                run_id=run_id,
                node_id=node_id,
                sequence=sequence,
                tool_name=tool_name,
                tool_content=str(outcome["content"]),
                prior_tool_observations=prior_observations,
                tool_args=tool_args,
            )
            summary = str(observation.get("summary") or outcome["content"])
            prior_observations.append(summary)
            if outcome["status"] == "error":
                observation["semantic_success"] = False
            event = {
                "type": "tool_result",
                "tool_name": tool_name,
                "tool_call_id": f"baseline-{sequence}-{tool_name}",
                "tool_sequence": sequence,
                "tool_args": tool_args,
                "status": outcome["status"],
                "result_preview": summary[:200],
                "result": summary,
                "raw_ref": observation.get("raw_ref"),
                "structured_ref": observation.get("structured_ref"),
                "summary_ref": observation.get("summary_ref"),
                "raw_chars": observation.get(
                    "raw_chars", len(str(outcome["content"]))
                ),
                "summary_chars": observation.get(
                    "summary_chars", len(summary)
                ),
                "semantic_success": observation.get("semantic_success", True),
                "structured": observation.get("structured"),
                "observation_processed": observation.get("processed", False),
                "observation_processor": observation.get("processor", ""),
                "context_usage_ratio": observation.get("context_usage_ratio"),
                "duration_seconds": outcome["duration_seconds"],
                "iteration": 0,
                "execution_phase": "pre_react_baseline",
            }
            self._push(stream_queue, node_id, events, **event)
        return events

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

        if reasoning:
            reasoning_text = AICall._normalize_reasoning_text(str(reasoning))
        else:
            reasoning_text = ""

        if reasoning_text and content:
            return f"{reasoning_text}{content}"
        if reasoning_text:
            return reasoning_text
        return str(content or "")

    @staticmethod
    def _normalize_reasoning_text(reasoning: str) -> str:
        """Wrap provider reasoning as `<think>` so stream filters can apply."""
        text = str(reasoning or "")
        if not text.strip():
            return ""
        if "<think>" in text.lower() and "</think>" in text.lower():
            return text
        return f"<think>{text}</think>"

    @staticmethod
    def _serialize_structured_response(value: Any) -> str:
        """Serialize a LangChain structured_response without text parsing."""
        if value is None:
            return ""
        if hasattr(value, "model_dump_json"):
            try:
                return value.model_dump_json()
            except Exception:
                pass
        if hasattr(value, "model_dump"):
            try:
                return json.dumps(value.model_dump(), ensure_ascii=False, default=str)
            except Exception:
                pass
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)

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
                extra_body=self._build_extra_body(session_id, node_id, metadata),
            )
        except Exception as exc:
            logger.debug("📉 [AICall] 绑定 session metadata 失败，继续原模型调用: %s", exc)
            return model

    def _build_extra_body(
        self,
        session_id: Optional[str],
        node_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Merge model-provider options with trace metadata.

        `extra_body` is also used for provider-specific controls such as local
        Qwen chat-template options. Keep this merge centralized so tracing
        cannot accidentally overwrite model controls, and model controls cannot
        remove run/session provenance.
        """
        extra_body = deepcopy(self.chat_model_extra_body or {})
        if not session_id:
            return extra_body

        trace_metadata = metadata or self._session_metadata(session_id, node_id)
        existing_metadata = extra_body.get("metadata")
        if isinstance(existing_metadata, dict):
            merged_metadata = {**existing_metadata, **trace_metadata}
        else:
            merged_metadata = trace_metadata
        extra_body["metadata"] = merged_metadata
        extra_body["trace_id"] = self._trace_id(session_id, node_id)
        extra_body["generation_name"] = self._generation_name(node_id)
        extra_body["user"] = session_id
        return extra_body

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

    def _build_context_hard_guard_middleware(
        self,
        *,
        node_id: str,
        run_id: str,
    ):
        """Bound every LangGraph model request before it reaches the provider."""
        from langchain.agents.middleware import wrap_model_call

        request_sequence = 0

        @wrap_model_call
        async def guard_model_request(request, handler):
            nonlocal request_sequence
            request_sequence += 1
            try:
                guarded_request, budget = self._guard_agent_model_request(
                    request,
                    node_id=node_id,
                )
            except StructuredContextBudgetError as exc:
                if run_id and isinstance(exc.pre_budget, dict):
                    try:
                        ContextArchive(run_id=run_id).write_budget(
                            f"{node_id}_agent_guard_{request_sequence:03d}",
                            exc.pre_budget,
                        )
                    except Exception as archive_exc:
                        logger.warning(
                            "⚠️ [AICall] agent hard guard 失败归档写入失败: %s",
                            archive_exc,
                        )
                raise

            if run_id:
                try:
                    ContextArchive(run_id=run_id).write_budget(
                        f"{node_id}_agent_guard_{request_sequence:03d}",
                        budget,
                    )
                except Exception as exc:
                    logger.warning(
                        "⚠️ [AICall] agent hard guard budget 写入失败: %s",
                        exc,
                    )
            return await handler(guarded_request)

        return guard_model_request

    def _guard_agent_model_request(
        self,
        request: Any,
        *,
        node_id: str,
    ) -> Tuple[Any, Dict[str, Any]]:
        config = self._structured_hard_guard_config()
        resolved = ModelContextResolver().resolve(
            self.model_str,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
        )
        context_window = resolved.get("context_window")
        output_reserved = 6000
        model_settings = getattr(request, "model_settings", None)
        if isinstance(model_settings, dict):
            try:
                output_reserved = int(
                    model_settings.get("max_tokens")
                    or model_settings.get("max_completion_tokens")
                    or output_reserved
                )
            except (TypeError, ValueError):
                output_reserved = 6000
        safety_margin = int(config["safety_tokens"])

        system_content = (
            getattr(getattr(request, "system_message", None), "content", "")
            or ""
        )
        messages = list(getattr(request, "messages", None) or [])
        messages_payload = [
            self._serialize_agent_message(message)
            for message in messages
        ]
        tool_schema_payload = serialize_tool_schema(
            getattr(request, "tools", None) or []
        )
        response_schema_payload = self._serialize_agent_response_format(
            getattr(request, "response_format", None)
        )

        def _components(message_content: Any) -> List[Dict[str, Any]]:
            return [
                {
                    "name": "node_system_prompt",
                    "category": "static_input",
                    "content": system_content,
                },
                {
                    "name": "agent_message_history",
                    "category": "dynamic_runtime",
                    "content": message_content,
                },
                {
                    "name": "tool_schema",
                    "category": "static_input",
                    "content": tool_schema_payload,
                },
                {
                    "name": "structured_schema",
                    "category": "static_input",
                    "content": response_schema_payload,
                },
                {
                    "name": "output_reserved",
                    "category": "reserved",
                    "tokens": output_reserved,
                },
                {
                    "name": "safety_margin",
                    "category": "reserved",
                    "tokens": safety_margin,
                },
                {
                    "name": "provider_request_overhead",
                    "category": "static_input",
                    "tokens": _PROVIDER_REQUEST_OVERHEAD_TOKENS,
                    "token_accuracy": "estimated",
                },
            ]

        estimator = ContextBudgetEstimator()
        pre_budget = estimator.estimate(
            node_id=f"{node_id}_agent_guard",
            model=self.model_str,
            system_prompt=system_content,
            user_message="",
            components=_components(messages_payload),
            api_base=self.api_base or "",
            api_key=self.api_key or "",
            enable_usage_probe=False,
        )
        original_input_tokens = int(
            pre_budget.get("actual_context_tokens") or 0
        )
        token_count_accuracy = str(
            pre_budget.get("token_count_accuracy") or "estimated"
        ).strip().lower()
        metadata: Dict[str, Any] = {
            "enabled": bool(config["enabled"]),
            "triggered": False,
            "strategy": "none",
            "context_window": context_window,
            "input_ratio": config["input_ratio"],
            "output_reserved": output_reserved,
            "safety_tokens": safety_margin,
            "original_input_tokens": original_input_tokens,
            "final_input_tokens": original_input_tokens,
            "max_input_tokens": None,
            "effective_input_target": None,
            "estimator_drift_reserve": 0,
            "token_count_accuracy": token_count_accuracy,
            "original_message_count": len(messages),
            "final_message_count": len(messages),
        }
        pre_budget["hard_guard"] = dict(metadata)
        if not config["enabled"]:
            return request, pre_budget
        if not isinstance(context_window, int) or context_window <= 0:
            metadata["error"] = "context_window_unavailable"
            pre_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} agent context window is unavailable",
                pre_budget=pre_budget,
            )

        max_input_tokens = calculate_hard_input_limit(
            context_window=context_window,
            output_reserved=output_reserved,
            safety_margin=safety_margin,
            input_ratio=float(config["input_ratio"]),
        )
        metadata["max_input_tokens"] = max_input_tokens
        estimator_drift_reserve = (
            0
            if token_count_accuracy == "exact"
            else min(
                max_input_tokens,
                int(config["estimator_drift_reserve"]),
            )
        )
        effective_input_target = max(
            0,
            max_input_tokens - estimator_drift_reserve,
        )
        metadata["effective_input_target"] = effective_input_target
        metadata["estimator_drift_reserve"] = estimator_drift_reserve
        pre_budget["hard_guard"] = dict(metadata)
        if effective_input_target <= 0:
            metadata["error"] = "input_budget_unavailable"
            pre_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} agent has no input budget",
                pre_budget=pre_budget,
            )
        if original_input_tokens <= effective_input_target:
            return request, pre_budget

        fixed_tokens = sum(
            int(component.get("tokens") or 0)
            for component in pre_budget.get("components", [])
            if component.get("name") != "agent_message_history"
            and component.get("category") != "reserved"
        )
        message_budget = effective_input_target - fixed_tokens
        if message_budget <= 0:
            metadata["error"] = "static_contract_exceeds_input_budget"
            pre_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} agent system prompt, tools, "
                f"and response schema exceed hard input budget "
                f"{max_input_tokens} (effective target "
                f"{effective_input_target})",
                pre_budget=pre_budget,
            )

        compacted_history = self._build_agent_request_compaction_summary(
            messages,
            max_tokens=message_budget,
        )
        compacted_messages = [HumanMessage(content=compacted_history)]
        final_budget = estimator.estimate(
            node_id=f"{node_id}_agent_guard",
            model=self.model_str,
            system_prompt=system_content,
            user_message="",
            components=_components([
                self._serialize_agent_message(compacted_messages[0])
            ]),
            api_base=self.api_base or "",
            api_key=self.api_key or "",
            enable_usage_probe=False,
        )
        final_input_tokens = int(
            final_budget.get("actual_context_tokens") or 0
        )
        if final_input_tokens > effective_input_target:
            overflow = final_input_tokens - effective_input_target
            tighter_budget = max(1, message_budget - overflow - 64)
            compacted_history = compact_text_to_token_budget(
                compacted_history,
                max_tokens=tighter_budget,
                model=self.model_str,
                preserve_tail_tokens=int(config["preserve_tail_tokens"]),
            )
            compacted_messages = [HumanMessage(content=compacted_history)]
            final_budget = estimator.estimate(
                node_id=f"{node_id}_agent_guard",
                model=self.model_str,
                system_prompt=system_content,
                user_message="",
                components=_components([
                    self._serialize_agent_message(compacted_messages[0])
                ]),
                api_base=self.api_base or "",
                api_key=self.api_key or "",
                enable_usage_probe=False,
            )
            final_input_tokens = int(
                final_budget.get("actual_context_tokens") or 0
            )
        if final_input_tokens > effective_input_target:
            metadata.update({
                "triggered": True,
                "strategy": "deterministic_agent_summary",
                "error": "deterministic_compaction_failed",
                "final_input_tokens": final_input_tokens,
                "final_message_count": 1,
            })
            pre_budget["hard_guard"] = dict(metadata)
            final_budget["hard_guard"] = dict(metadata)
            raise StructuredContextBudgetError(
                f"[context_budget] node={node_id} agent deterministic "
                f"compaction failed: input={final_input_tokens} "
                f"target={effective_input_target} limit={max_input_tokens}",
                pre_budget=pre_budget,
                final_budget=final_budget,
            )

        metadata.update({
            "triggered": True,
            "strategy": "deterministic_agent_summary",
            "final_input_tokens": final_input_tokens,
            "final_message_count": 1,
        })
        pre_budget["hard_guard"] = dict(metadata)
        final_budget["hard_guard"] = dict(metadata)
        logger.warning(
            "🧯 [AICall] agent hard context guard | node=%s "
            "input=%d→%d target=%d limit=%d messages=%d→1",
            node_id,
            original_input_tokens,
            final_input_tokens,
            effective_input_target,
            max_input_tokens,
            len(messages),
        )
        return request.override(messages=compacted_messages), final_budget

    @staticmethod
    def _serialize_agent_message(message: Any) -> Dict[str, Any]:
        if isinstance(message, dict):
            return dict(message)
        if hasattr(message, "model_dump"):
            try:
                return message.model_dump(exclude_none=True)
            except Exception:
                pass
        return {
            "type": getattr(message, "type", type(message).__name__),
            "content": getattr(message, "content", str(message)),
        }

    @staticmethod
    def _serialize_agent_response_format(response_format: Any) -> Any:
        if response_format is None:
            return {}
        specs = getattr(response_format, "schema_specs", None)
        if isinstance(specs, list):
            payload = []
            for spec in specs:
                json_schema = getattr(spec, "json_schema", None)
                if json_schema:
                    payload.append({
                        "name": getattr(spec, "name", ""),
                        "json_schema": json_schema,
                    })
            if payload:
                return payload
        schema = getattr(response_format, "schema", None)
        if hasattr(schema, "model_json_schema"):
            try:
                return schema.model_json_schema()
            except Exception:
                pass
        return str(response_format)

    def _build_agent_request_compaction_summary(
        self,
        messages: List[Any],
        *,
        max_tokens: int,
    ) -> str:
        user_requests: List[str] = []
        assistant_messages: List[str] = []
        tool_calls: List[Dict[str, Any]] = []
        tool_results: List[Tuple[int, int, Dict[str, Any]]] = []

        def _bounded(value: Any, max_value_tokens: int) -> str:
            return compact_text_to_token_budget(
                value,
                max_tokens=max_value_tokens,
                model=self.model_str,
                preserve_tail_tokens=max(16, max_value_tokens // 4),
            )

        for index, message in enumerate(messages):
            content = str(getattr(message, "content", "") or "")
            if isinstance(message, HumanMessage):
                if content:
                    user_requests.append(_bounded(content, 320))
                continue
            if isinstance(message, AIMessage):
                if content:
                    assistant_messages.append(_bounded(content, 240))
                for tool_call in list(message.tool_calls or []):
                    tool_calls.append({
                        "tool_name": str(
                            tool_call.get("name") or "unknown"
                        ),
                        "tool_args": _bounded(
                            json.dumps(
                                tool_call.get("args") or {},
                                ensure_ascii=False,
                                default=str,
                            ),
                            240,
                        ),
                    })
                continue
            if isinstance(message, ToolMessage):
                additional = dict(message.additional_kwargs or {})
                item: Dict[str, Any] = {
                    "tool_name": str(message.name or "unknown"),
                    "semantic_success": additional.get(
                        "aiops_semantic_success"
                    ),
                    "result_preview": _bounded(content, 480),
                }
                refs_available = False
                for field, key in (
                    ("raw_ref", "aiops_raw_ref"),
                    ("structured_ref", "aiops_structured_ref"),
                    ("summary_ref", "aiops_summary_ref"),
                ):
                    value = additional.get(key)
                    if value:
                        item[field] = str(value)
                        refs_available = True
                item["refs_available"] = refs_available
                priority = (
                    0
                    if item.get("semantic_success") is False
                    else 1
                    if refs_available
                    else 2
                )
                tool_results.append((priority, -index, item))

        tool_results.sort(key=lambda candidate: (candidate[0], candidate[1]))
        summary: Dict[str, Any] = {
            "context_compacted": True,
            "compaction_strategy": "deterministic_agent_request",
            "original_message_count": len(messages),
            "user_requests": user_requests[:2],
            "tool_results": [
                item for _, _, item in tool_results[:12]
            ],
            "tool_calls": tool_calls[-12:],
            "assistant_messages": assistant_messages[-4:],
        }

        def _serialized() -> str:
            return json.dumps(
                summary,
                ensure_ascii=False,
                default=str,
            )

        serialized = _serialized()
        if count_tokens(serialized, model=self.model_str)["tokens"] <= max_tokens:
            return serialized

        summary["assistant_messages"] = []
        for text_budget in (240, 120, 64):
            for item in summary["tool_results"]:
                item["result_preview"] = _bounded(
                    item.get("result_preview") or "",
                    text_budget,
                )
            for item in summary["tool_calls"]:
                item["tool_args"] = _bounded(
                    item.get("tool_args") or "",
                    text_budget,
                )
            serialized = _serialized()
            if count_tokens(
                serialized,
                model=self.model_str,
            )["tokens"] <= max_tokens:
                return serialized

        while (
            count_tokens(_serialized(), model=self.model_str)["tokens"]
            > max_tokens
            and len(summary["tool_results"]) > 1
        ):
            summary["tool_results"].pop()
        while (
            count_tokens(_serialized(), model=self.model_str)["tokens"]
            > max_tokens
            and len(summary["tool_calls"]) > 1
        ):
            summary["tool_calls"].pop(0)
        serialized = _serialized()
        if count_tokens(serialized, model=self.model_str)["tokens"] <= max_tokens:
            return serialized
        return compact_text_to_token_budget(
            serialized,
            max_tokens=max_tokens,
            model=self.model_str,
            preserve_tail_tokens=max(32, max_tokens // 5),
        )

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
    def _tool_execution_signature(tool_call: Dict[str, Any]) -> str:
        """Return a stable execution key independent of provider call IDs."""
        name = str(tool_call.get("name") or "unknown")
        args = tool_call.get("args", {})
        try:
            args_str = json.dumps(
                args,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
        except Exception:
            args_str = str(args)
        return f"name:{name}|args:{args_str}"

    @staticmethod
    def _build_tool_dedup_middleware():
        """Deduplicate identical tool executions within one agent call."""
        import asyncio
        from langchain.agents.middleware import wrap_tool_call

        cache: Dict[str, Tuple[ToolMessage, str]] = {}
        in_flight: Dict[str, Tuple[Any, str]] = {}
        lock = asyncio.Lock()

        def _clone_for_call(
            source: ToolMessage,
            current_call_id: str,
            original_call_id: str,
        ) -> ToolMessage:
            additional_kwargs = dict(source.additional_kwargs or {})
            additional_kwargs.update({
                "aiops_deduplicated": True,
                "aiops_original_tool_call_id": original_call_id,
            })
            return source.model_copy(update={
                "id": None,
                "tool_call_id": current_call_id,
                "additional_kwargs": additional_kwargs,
            })

        @wrap_tool_call
        async def deduplicate_tool_call(request, handler):
            tool_call = dict(request.tool_call or {})
            signature = AICall._tool_execution_signature(tool_call)
            current_call_id = str(tool_call.get("id") or "")

            async with lock:
                cached = cache.get(signature)
                if cached is not None:
                    source, original_call_id = cached
                    return _clone_for_call(
                        source,
                        current_call_id,
                        original_call_id,
                    )

                pending = in_flight.get(signature)
                if pending is None:
                    task = asyncio.create_task(handler(request))
                    original_call_id = current_call_id
                    in_flight[signature] = (task, original_call_id)
                    owner = True
                else:
                    task, original_call_id = pending
                    owner = False

            try:
                result = await task
            except Exception as exc:
                error_message = compact_text_to_token_budget(
                    str(exc) or type(exc).__name__,
                    max_tokens=240,
                    model="",
                    preserve_tail_tokens=48,
                )
                logger.warning(
                    "⚠️ [AICall] isolated tool failure | tool=%s "
                    "call_id=%s error=%s: %s",
                    tool_call.get("name") or "unknown",
                    current_call_id,
                    type(exc).__name__,
                    error_message,
                )
                return ToolMessage(
                    content=json.dumps(
                        {
                            "status": "tool_error",
                            "semantic_success": False,
                            "error": {
                                "type": type(exc).__name__,
                                "message": error_message,
                            },
                        },
                        ensure_ascii=False,
                    ),
                    tool_call_id=current_call_id,
                    name=str(tool_call.get("name") or "unknown"),
                    status="error",
                    additional_kwargs={
                        "aiops_tool_error": True,
                        "aiops_error_type": type(exc).__name__,
                    },
                )
            finally:
                if owner:
                    async with lock:
                        in_flight.pop(signature, None)

            if not isinstance(result, ToolMessage):
                return result

            if owner:
                if getattr(result, "status", "success") == "success":
                    async with lock:
                        cache[signature] = (result, original_call_id)
                return result

            return _clone_for_call(
                result,
                current_call_id,
                original_call_id,
            )

        return deduplicate_tool_call

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
        tool_args: Optional[Dict[str, Any]] = None,
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
                tool_args=tool_args or {},
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
            enable_usage_probe=False,
        )
        context_window = budget.get("context_window")
        if not isinstance(context_window, int) or context_window <= 0:
            return None
        return float(budget.get("actual_context_tokens", 0)) / float(context_window)

    def _maybe_compact_runtime_context(
        self,
        node_id: str,
        run_id: str,
        static_context_components: List[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
        tool_observation_contents: List[str],
    ) -> bool:
        config = self._runtime_compaction_config()
        if not config.get("enabled"):
            return False

        node_text = str(node_id or "").strip()
        nodes = {str(item) for item in config.get("nodes", [])}
        if nodes and node_text not in nodes:
            return False

        resolved = ModelContextResolver().resolve(
            self.model_str,
            api_base=self.api_base or "",
            api_key=self.api_key or "",
        )
        context_window = resolved.get("context_window")
        if not isinstance(context_window, int) or context_window <= 0:
            return False
        max_window = int(config.get("max_context_window") or 35000)
        if context_window > max_window:
            return False

        dynamic_components = self._runtime_dynamic_components(thinking_events)
        budget = ContextBudgetEstimator().estimate(
            node_id=f"{node_text or 'unknown'}_runtime_compaction_check",
            model=self.model_str,
            system_prompt="",
            user_message="",
            components=[
                *[c for c in static_context_components if c.get("category") != "reserved"],
                *dynamic_components,
            ],
            api_base=self.api_base or "",
            api_key=self.api_key or "",
            scratchpad_reserved=0,
            output_reserved=0,
            enable_usage_probe=False,
        )
        actual_tokens = int(budget.get("actual_context_tokens") or 0)
        usage_ratio = actual_tokens / context_window
        trigger_ratio = float(config.get("trigger_ratio") or 0.7)
        if usage_ratio < trigger_ratio:
            return False

        payload = self._build_runtime_compaction_payload(
            node_id=node_text,
            usage_ratio=usage_ratio,
            context_window=context_window,
            thinking_events=thinking_events,
            tool_observation_contents=tool_observation_contents,
            model=self.model_str,
            max_events=24,
            max_tokens=6000,
        )
        try:
            configured_summary_max_tokens = max(
                1,
                int(config.get("summary_max_tokens") or 1200),
            )
        except (TypeError, ValueError):
            configured_summary_max_tokens = 1200
        source_summary = self._build_deterministic_runtime_compaction_summary(
            thinking_events,
            max_tokens=max(1200, configured_summary_max_tokens),
        )
        minimum_contract = self._minimum_runtime_summary_contract(
            source_summary
        )
        minimum_contract = self._fit_minimum_runtime_contract_to_budget(
            minimum_contract,
            max_tokens=configured_summary_max_tokens,
        )
        minimum_contract_tokens = count_tokens(
            json.dumps(
                minimum_contract,
                ensure_ascii=False,
                default=str,
            ),
            model=self.model_str,
        )["tokens"]
        summary_max_tokens = max(
            configured_summary_max_tokens,
            minimum_contract_tokens,
        )
        summary = self._compact_context_with_lite_llm(
            payload,
            node_id=node_text,
            run_id=run_id,
            max_tokens=summary_max_tokens,
        )
        validated_summary = None
        if isinstance(summary, dict):
            try:
                candidate = ContextCompactionSummary.model_validate(summary).model_dump()
                if self._runtime_compaction_summary_has_evidence_contract(
                    candidate,
                    thinking_events,
                ):
                    validated_summary = (
                        self._sanitize_runtime_compaction_summary(
                            candidate,
                            source_summary=source_summary,
                            max_tokens=summary_max_tokens,
                        )
                    )
            except Exception:
                validated_summary = None
        if validated_summary is None:
            summary = self._fit_deterministic_runtime_summary_to_token_budget(
                source_summary,
                max_tokens=summary_max_tokens,
            )
        else:
            summary = validated_summary

        compact_text = json.dumps(summary, ensure_ascii=False, default=str)
        if not compact_text.strip():
            return False

        compact_event = {
            "type": "context_summary",
            "node": node_text,
            "timestamp": time.time(),
            "content": compact_text[:500],
            "full_content": compact_text,
            "iteration": "compaction",
            "context_compacted": True,
            "context_usage_ratio_before": usage_ratio,
        }
        self._compact_thinking_events_in_place(thinking_events, compact_event)
        tool_observation_contents[:] = [compact_text]
        logger.info(
            "🧯 [AICall] runtime context compacted | node=%s usage=%.0f%% window=%s",
            node_text or "unknown",
            usage_ratio * 100,
            context_window,
        )
        return True

    @staticmethod
    def _runtime_compaction_summary_has_evidence_contract(
        candidate: Dict[str, Any],
        thinking_events: List[Dict[str, Any]],
    ) -> bool:
        plan_items = candidate.get("evidence_plan")
        has_plan = isinstance(plan_items, list) and any(
            isinstance(item, dict)
            and any(value not in (None, "", [], {}) for value in item.values())
            for item in plan_items
        )
        completed_items = candidate.get("completed_items")
        completed_evidence_keys = {
            "tool_name",
            "tool",
            "semantic_success",
            "outcome",
            "fact",
            "result_preview",
            "error",
            "raw_ref",
            "structured_ref",
            "summary_ref",
        }
        has_completed_tool_evidence = (
            isinstance(completed_items, list)
            and any(
                isinstance(item, dict)
                and any(
                    key in item and item.get(key) not in (None, "", [], {})
                    for key in completed_evidence_keys
                )
                for item in completed_items
            )
        )

        def _has_archive_ref(value: Any) -> bool:
            if isinstance(value, dict):
                for key in ("raw_ref", "structured_ref", "summary_ref"):
                    if str(value.get(key) or "").strip():
                        return True
                return any(_has_archive_ref(item) for item in value.values())
            if isinstance(value, list):
                return any(_has_archive_ref(item) for item in value)
            return False

        has_candidate_ref = _has_archive_ref(candidate)
        source_tool_events = [
            event
            for event in thinking_events
            if event.get("type") == "tool_result"
        ]
        source_has_tool_result = bool(source_tool_events)
        if source_has_tool_result:
            source_tool_names = {
                str(event.get("tool_name") or "").strip()
                for event in source_tool_events
                if str(event.get("tool_name") or "").strip()
            }
            source_refs = {
                str(event.get(key)).strip()
                for event in source_tool_events
                for key in ("raw_ref", "structured_ref", "summary_ref")
                if str(event.get(key) or "").strip()
            }
            candidate_tool_names = {
                str(item.get("tool_name") or item.get("tool") or "").strip()
                for item in (completed_items or [])
                if isinstance(item, dict)
                and str(
                    item.get("tool_name") or item.get("tool") or ""
                ).strip()
            }

            def _collect_refs(value: Any) -> set[str]:
                refs: set[str] = set()
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key in {
                            "raw_ref",
                            "structured_ref",
                            "summary_ref",
                        } and str(item or "").strip():
                            refs.add(str(item).strip())
                        else:
                            refs.update(_collect_refs(item))
                elif isinstance(value, list):
                    for item in value:
                        refs.update(_collect_refs(item))
                return refs

            candidate_refs = _collect_refs(candidate)
            if candidate_tool_names and not candidate_tool_names.issubset(
                source_tool_names
            ):
                return False
            if candidate_refs and not candidate_refs.issubset(source_refs):
                return False

            source_by_tool: Dict[str, List[Dict[str, Any]]] = {}
            source_corpus_parts: List[str] = []
            for event in source_tool_events:
                tool_name = str(event.get("tool_name") or "").strip()
                source_by_tool.setdefault(tool_name, []).append(event)
                source_corpus_parts.append(
                    json.dumps(event, ensure_ascii=False, default=str)
                )
            source_corpus = "\n".join(source_corpus_parts).lower()
            has_bound_candidate = False
            for item in completed_items or []:
                if not isinstance(item, dict):
                    continue
                item_tool = str(
                    item.get("tool_name") or item.get("tool") or ""
                ).strip()
                item_refs = {
                    str(item.get(key)).strip()
                    for key in ("raw_ref", "structured_ref", "summary_ref")
                    if str(item.get(key) or "").strip()
                }
                if not item_tool and not item_refs:
                    continue
                has_bound_candidate = True
                matching_events = source_by_tool.get(item_tool, [])
                if item_refs:
                    matching_events = [
                        event
                        for event in matching_events
                        if item_refs.issubset({
                            str(event.get(key)).strip()
                            for key in (
                                "raw_ref",
                                "structured_ref",
                                "summary_ref",
                            )
                            if str(event.get(key) or "").strip()
                        })
                    ]
                if not matching_events:
                    return False
                matched = False
                for event in matching_events:
                    event_corpus = json.dumps(
                        event,
                        ensure_ascii=False,
                        default=str,
                    ).lower()
                    if (
                        item.get("semantic_success") is not None
                        and item.get("semantic_success")
                        != event.get("semantic_success")
                    ):
                        continue
                    if any(
                        str(item.get(key) or "").strip()
                        and str(item.get(key)).strip().lower()
                        not in event_corpus
                        for key in (
                            "result_preview",
                            "fact",
                            "error",
                            "outcome",
                        )
                    ):
                        continue
                    matched = True
                    break
                if not matched:
                    return False

            if has_bound_candidate:
                for key in ("key_facts", "negative_facts", "conflicts"):
                    for value in candidate.get(key) or []:
                        text = str(value or "").strip().lower()
                        if text and text not in source_corpus:
                            return False
            return has_completed_tool_evidence or has_candidate_ref
        return has_plan or has_completed_tool_evidence or has_candidate_ref

    def _sanitize_runtime_compaction_summary(
        self,
        candidate: Dict[str, Any],
        *,
        source_summary: Dict[str, Any],
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Rebuild every evidence-bearing field from deterministic source events."""
        sanitized = {
            "compaction_strategy": "validated_llm_shape_source_evidence",
            "process_summary": deepcopy(
                source_summary.get("process_summary") or []
            ),
            "evidence_plan": deepcopy(
                source_summary.get("evidence_plan") or []
            ),
            "completed_items": deepcopy(
                source_summary.get("completed_items") or []
            ),
            "open_items": deepcopy(
                source_summary.get("open_items") or []
            ),
            "key_facts": deepcopy(
                source_summary.get("key_facts") or []
            ),
            "negative_facts": deepcopy(
                source_summary.get("negative_facts") or []
            ),
            "conflicts": deepcopy(
                source_summary.get("conflicts") or []
            ),
            "discarded_noise": deepcopy(
                source_summary.get("discarded_noise") or []
            ),
            "next_focus": deepcopy(
                source_summary.get("next_focus") or []
            ),
        }
        return self._fit_deterministic_runtime_summary_to_token_budget(
            sanitized,
            max_tokens=max_tokens,
        )

    def _build_deterministic_runtime_compaction_summary(
        self,
        thinking_events: List[Dict[str, Any]],
        *,
        max_tokens: int,
    ) -> Dict[str, Any]:
        evidence_plan: List[Dict[str, Any]] = []
        completed_items: List[Dict[str, Any]] = []
        seen_plan_items = set()
        seen_tool_items = set()
        plan_limit = max(1, min(8, max_tokens // 160 or 1))
        tool_limit = max(1, min(8, max_tokens // 110 or 1))

        def _bounded_text(value: Any, limit: int) -> str:
            text = (
                value
                if isinstance(value, str)
                else json.dumps(value, ensure_ascii=False, default=str)
            )
            return text if len(text) <= limit else text[:limit] + "...[truncated]"

        for event in thinking_events:
            if event.get("type") != "ai_message":
                continue
            text = str(event.get("full_content") or event.get("content") or "")
            if "evidence_plan" not in text:
                continue
            parsed = self.extract_json_payload(text)
            if not isinstance(parsed, dict):
                continue
            plan_items = parsed.get("evidence_plan")
            if isinstance(plan_items, list):
                for item in plan_items:
                    if not isinstance(item, dict):
                        continue
                    bounded_item = {
                        key: _bounded_text(item.get(key), 180)
                        for key in (
                            "id",
                            "description",
                            "tool",
                            "purpose",
                            "level",
                            "command",
                        )
                        if item.get(key) not in (None, "", [], {})
                    }
                    if not bounded_item:
                        continue
                    signature = json.dumps(
                        bounded_item,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    if signature in seen_plan_items:
                        continue
                    seen_plan_items.add(signature)
                    evidence_plan.append(bounded_item)
                    if len(evidence_plan) >= plan_limit:
                        break
            if len(evidence_plan) >= plan_limit:
                break

        tool_candidates: List[Tuple[int, int, Dict[str, Any]]] = []
        for event in thinking_events:
            if event.get("type") != "tool_result":
                continue
            result_preview = _bounded_text(
                event.get("result_preview") or event.get("result") or "",
                260,
            )
            error = event.get("error")
            structured = event.get("structured")
            if error is None and isinstance(structured, dict):
                error = structured.get("error")
            item = {
                "tool_name": str(event.get("tool_name") or "unknown"),
                "semantic_success": event.get("semantic_success"),
                "result_preview": result_preview,
            }
            if error not in (None, "", {}, []):
                item["error"] = _bounded_text(error, 260)
            refs_available = False
            for ref_name in ("raw_ref", "structured_ref", "summary_ref"):
                ref_value = event.get(ref_name)
                if ref_value:
                    item[ref_name] = str(ref_value)
                    refs_available = True
            item["refs_available"] = refs_available
            signature = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if signature in seen_tool_items:
                continue
            seen_tool_items.add(signature)
            priority = (
                0
                if event.get("semantic_success") is False or "error" in item
                else 1
                if refs_available
                else 2
            )
            tool_candidates.append((priority, len(tool_candidates), item))

        tool_candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
        completed_items = [
            item for _, _, item in tool_candidates[:tool_limit]
        ]
        summary = {
            "compaction_strategy": "deterministic_fallback",
            "deterministic_fallback": True,
            "process_summary": [
                "Invalid LLM compaction output was replaced by bounded "
                "deterministic evidence."
            ],
            "evidence_plan": evidence_plan,
            "completed_items": completed_items,
            "discarded_noise": [
                f"omitted_plan_items={max(0, len(seen_plan_items) - len(evidence_plan))}; "
                f"omitted_tool_items={max(0, len(tool_candidates) - len(completed_items))}"
            ],
        }
        return self._fit_deterministic_runtime_summary_to_token_budget(
            summary,
            max_tokens=max_tokens,
        )

    def _fit_deterministic_runtime_summary_to_token_budget(
        self,
        summary: Dict[str, Any],
        *,
        max_tokens: int,
    ) -> Dict[str, Any]:
        def _token_count(value: Dict[str, Any]) -> int:
            return count_tokens(
                json.dumps(value, ensure_ascii=False, default=str),
                model=self.model_str,
            )["tokens"]

        def _shrink(value: Any, limit: int) -> str:
            text = str(value or "")
            return text if len(text) <= limit else text[:limit] + "..."

        minimum_contract = self._fit_minimum_runtime_contract_to_budget(
            self._minimum_runtime_summary_contract(summary),
            max_tokens=max_tokens,
        )
        effective_max_tokens = max(
            int(max_tokens),
            _token_count(minimum_contract),
        )

        if _token_count(summary) <= effective_max_tokens:
            return summary

        summary["process_summary"] = []
        summary["discarded_noise"] = ["bounded deterministic evidence"]
        for text_limit in (120, 72, 40):
            for item in summary.get("evidence_plan", []):
                for key in ("description", "purpose", "command"):
                    if key in item:
                        item[key] = _shrink(item[key], text_limit)
            for item in summary.get("completed_items", []):
                for key in (
                    "result_preview",
                    "error",
                ):
                    if key in item:
                        item[key] = _shrink(item[key], text_limit)
            if _token_count(summary) <= effective_max_tokens:
                return summary

        for item in summary.get("evidence_plan", []):
            for key in tuple(item):
                if key not in {"id", "tool"}:
                    item.pop(key, None)
        for item in summary.get("completed_items", []):
            if item.get("error"):
                item.pop("result_preview", None)
            for key in ("error", "result_preview"):
                if key in item:
                    item[key] = _shrink(item[key], 32)
        summary.pop("process_summary", None)
        summary.pop("discarded_noise", None)
        if _token_count(summary) <= effective_max_tokens:
            return summary
        return minimum_contract

    @staticmethod
    def _minimum_runtime_summary_contract(
        summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        evidence_plan = []
        for item in summary.get("evidence_plan") or []:
            if not isinstance(item, dict):
                continue
            minimum_item = {
                key: item[key]
                for key in ("id", "tool")
                if item.get(key) not in (None, "", [], {})
            }
            if not minimum_item:
                for key, value in item.items():
                    if value not in (None, "", [], {}):
                        minimum_item[key] = value
                        break
            if minimum_item:
                evidence_plan.append(minimum_item)

        completed_items = []
        for item in summary.get("completed_items") or []:
            if not isinstance(item, dict):
                continue
            minimum_item = {
                key: item[key]
                for key in (
                    "tool_name",
                    "semantic_success",
                    "error",
                    "raw_ref",
                    "structured_ref",
                    "summary_ref",
                    "refs_available",
                )
                if key in item
                and item.get(key) not in (None, "", [], {})
            }
            if minimum_item:
                completed_items.append(minimum_item)

        return {
            "compaction_strategy": "minimum_evidence_contract",
            "deterministic_fallback": True,
            "evidence_plan": evidence_plan,
            "completed_items": completed_items,
        }

    def _fit_minimum_runtime_contract_to_budget(
        self,
        minimum: Dict[str, Any],
        *,
        max_tokens: int,
    ) -> Dict[str, Any]:
        bounded = deepcopy(minimum)

        def _tokens() -> int:
            return count_tokens(
                json.dumps(bounded, ensure_ascii=False, default=str),
                model=self.model_str,
            )["tokens"]

        while (
            _tokens() > max_tokens
            and len(bounded.get("completed_items") or []) > 1
        ):
            bounded["completed_items"].pop()
        while (
            _tokens() > max_tokens
            and len(bounded.get("evidence_plan") or []) > 1
        ):
            bounded["evidence_plan"].pop()
        return bounded

    @staticmethod
    def _bounded_evidence_plan_text(
        text: str,
        *,
        max_chars: int = 1600,
    ) -> str:
        parsed = AICall.extract_json_payload(text)
        plan_items = (
            parsed.get("evidence_plan")
            if isinstance(parsed, dict)
            else None
        )
        bounded_items: List[Dict[str, Any]] = []

        def _short(value: Any, limit: int) -> str:
            value_text = str(value or "")
            return (
                value_text
                if len(value_text) <= limit
                else value_text[:limit] + "..."
            )

        if isinstance(plan_items, list):
            for item in plan_items[:8]:
                if not isinstance(item, dict):
                    continue
                bounded_item = {
                    key: _short(item.get(key), 140)
                    for key in (
                        "id",
                        "tool",
                        "description",
                        "purpose",
                        "level",
                    )
                    if item.get(key) not in (None, "", [], {})
                }
                if bounded_item:
                    bounded_items.append(bounded_item)

        payload: Dict[str, Any] = {
            "context_compacted": True,
            "bounded_evidence_plan": True,
            "evidence_plan": bounded_items,
        }
        if isinstance(plan_items, list):
            payload["source_plan_count"] = len(plan_items)
            payload["omitted_plan_count"] = max(
                0,
                len(plan_items) - len(bounded_items),
            )
        else:
            payload["plan_preview"] = _short(text, 600)
            payload["plan_parse_status"] = "unavailable"

        serialized = json.dumps(payload, ensure_ascii=False)
        while len(serialized) > max_chars and len(bounded_items) > 1:
            bounded_items.pop()
            payload["evidence_plan"] = bounded_items
            if isinstance(plan_items, list):
                payload["omitted_plan_count"] = (
                    len(plan_items) - len(bounded_items)
                )
            serialized = json.dumps(payload, ensure_ascii=False)
        if len(serialized) <= max_chars:
            return serialized

        for item in bounded_items:
            for key in ("description", "purpose"):
                if key in item:
                    item[key] = _short(item[key], 48)
        serialized = json.dumps(payload, ensure_ascii=False)
        if len(serialized) <= max_chars:
            return serialized

        payload["evidence_plan"] = [
            {
                key: item[key]
                for key in ("id", "tool")
                if key in item
            }
            for item in bounded_items[:1]
        ]
        payload.pop("plan_preview", None)
        serialized = json.dumps(payload, ensure_ascii=False)
        if len(serialized) <= max_chars:
            return serialized
        return json.dumps(
            {
                "context_compacted": True,
                "bounded_evidence_plan": True,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _compact_thinking_events_in_place(
        thinking_events: List[Dict[str, Any]],
        compact_event: Dict[str, Any],
    ) -> None:
        """Keep event topology for downstream consumers while removing long text."""
        compacted_events: List[Dict[str, Any]] = [compact_event]
        for ev in thinking_events:
            ev_type = ev.get("type")
            if ev_type == "ai_message":
                text = ev.get("full_content") or ev.get("content") or ""
                if "evidence_plan" in text:
                    if len(text) <= 1200:
                        compacted_events.append(ev)
                        continue
                    compacted = dict(ev)
                    bounded_plan = AICall._bounded_evidence_plan_text(text)
                    compacted["full_content"] = bounded_plan
                    compacted["content"] = bounded_plan[:500]
                    compacted["context_compacted"] = True
                    compacted["original_chars"] = len(text)
                    compacted_events.append(compacted)
                    continue
                compacted = dict(ev)
                compacted["full_content"] = ""
                compacted["content"] = f"[compacted ai_message: original_chars={len(text)}]"
                compacted["context_compacted"] = True
                compacted_events.append(compacted)
                continue

            if ev_type == "tool_result":
                compacted = dict(ev)
                result = str(compacted.get("result") or compacted.get("result_preview") or "")
                result_preview = str(compacted.get("result_preview") or result)
                raw_ref = compacted.get("raw_ref")
                structured_ref = compacted.get("structured_ref")
                summary_ref = compacted.get("summary_ref")
                if len(result) > 1200:
                    marker = (
                        "see raw_ref/structured_ref/summary_ref"
                        if raw_ref or structured_ref or summary_ref
                        else "refs unavailable"
                    )
                    compacted["result"] = (
                        result_preview[:1200]
                        + f"\n...[compacted: {marker}]"
                    )
                    compacted["result_preview"] = result_preview[:200]
                    compacted["context_compacted"] = True
                compacted_events.append(compacted)
                continue

            compacted_events.append(ev)
        thinking_events[:] = compacted_events

    @staticmethod
    def _compact_langgraph_ai_messages_in_place(messages: List[Tuple[Any, str]]) -> None:
        """Compact emitted AI text and provider-bound historical tool arguments."""
        for msg, original_text in messages:
            text = str(original_text or "")
            try:
                tool_calls = list(getattr(msg, "tool_calls", None) or [])
                if tool_calls:
                    compacted_tool_calls = []
                    for tool_call in tool_calls:
                        compacted = dict(tool_call)
                        compacted["args"] = AICall._bounded_tool_call_args(
                            tool_call.get("args") or {}
                        )
                        compacted_tool_calls.append(compacted)
                    msg.tool_calls = compacted_tool_calls
                    additional_kwargs = dict(
                        getattr(msg, "additional_kwargs", None) or {}
                    )
                    if isinstance(additional_kwargs.get("tool_calls"), list):
                        additional_kwargs["tool_calls"] = compacted_tool_calls
                        msg.additional_kwargs = additional_kwargs

                if text:
                    if "evidence_plan" in text:
                        if len(text) > 1200:
                            msg.content = AICall._bounded_evidence_plan_text(
                                text
                            )
                    else:
                        msg.content = (
                            f"[compacted ai_message: original_chars={len(text)}]"
                        )
            except Exception:
                continue

    @staticmethod
    def _bounded_tool_call_args(
        args: Any,
        *,
        max_chars: int = 1200,
    ) -> Dict[str, Any]:
        if not isinstance(args, dict):
            args = {"value": args}
        serialized = json.dumps(
            args,
            ensure_ascii=False,
            default=str,
        )
        if len(serialized) <= max_chars:
            return dict(args)

        compacted: Dict[str, Any] = {"context_compacted": True}
        for key, value in args.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                text = str(value or "")
                compacted[str(key)] = (
                    value
                    if len(text) <= 160
                    else text[:160] + "...[truncated]"
                )
            else:
                value_text = json.dumps(
                    value,
                    ensure_ascii=False,
                    default=str,
                )
                compacted[str(key)] = (
                    value
                    if len(value_text) <= 240
                    else value_text[:240] + "...[truncated]"
                )

        while (
            len(json.dumps(compacted, ensure_ascii=False, default=str))
            > max_chars
            and len(compacted) > 2
        ):
            removable = [
                key
                for key in compacted
                if key != "context_compacted"
            ]
            if not removable:
                break
            compacted.pop(removable[-1], None)
        return compacted

    @staticmethod
    def _compact_langgraph_tool_messages_in_place(messages: List[Tuple[Any, Dict[str, Any]]]) -> None:
        """Compact tool observations already stored in the agent message list."""
        for msg, metadata in messages:
            current = str(getattr(msg, "content", "") or "")
            if len(current) <= 1200:
                continue
            raw_ref = metadata.get("raw_ref")
            structured_ref = metadata.get("structured_ref")
            summary_ref = metadata.get("summary_ref")
            semantic_success = metadata.get("semantic_success")
            result_preview = str(metadata.get("result_preview") or current)
            ref_text = ", ".join(str(v) for v in (raw_ref, structured_ref, summary_ref) if v)
            replacement = (
                f"[compacted tool_result: tool={metadata.get('tool_name') or 'unknown'} "
                f"semantic_success={semantic_success} "
                f"original_chars={len(current)} "
                f"preview={result_preview[:500]}"
            )
            if ref_text:
                replacement += f" refs={ref_text}"
            else:
                replacement += " refs unavailable"
            replacement += "]"
            try:
                msg.content = replacement
            except Exception:
                continue

    def _runtime_compaction_config(self) -> Dict[str, Any]:
        defaults = {
            "enabled": True,
            "nodes": ["evidence"],
            "max_context_window": 35000,
            "trigger_ratio": 0.70,
            "max_compactions_per_call": 1,
            "summary_max_tokens": 1200,
        }
        cfg = dict(defaults)
        user_cfg = self.context_compaction_config if isinstance(self.context_compaction_config, dict) else {}
        cfg.update({k: v for k, v in user_cfg.items() if v is not None})
        if isinstance(cfg.get("nodes"), str):
            cfg["nodes"] = [cfg["nodes"]]
        return cfg

    @staticmethod
    def _runtime_dynamic_components(thinking_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
        tool_call_text = "\n".join(
            json.dumps(
                {
                    "tool_name": ev.get("tool_name"),
                    "tool_args": ev.get("tool_args") or {},
                },
                ensure_ascii=False,
                default=str,
            )
            for ev in thinking_events
            if ev.get("type") == "tool_start"
        )
        return [
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
                "name": "tool_calls",
                "category": "dynamic_runtime",
                "content": tool_call_text,
                "preview": tool_call_text[:200],
            },
        ]

    @staticmethod
    def _build_runtime_compaction_payload(
        node_id: str,
        usage_ratio: float,
        context_window: int,
        thinking_events: List[Dict[str, Any]],
        tool_observation_contents: List[str],
        model: str = "",
        max_events: int = 24,
        max_tokens: int = 6000,
    ) -> Dict[str, Any]:
        bounded_event_count = max(1, int(max_events or 1))
        selected_events = [
            ev
            for ev in thinking_events
            if ev.get("type") in {"ai_message", "tool_result"}
        ][-bounded_event_count:]
        ai_messages = [
            (ev.get("full_content") or ev.get("content") or "")[:2000]
            for ev in selected_events
            if ev.get("type") == "ai_message"
        ]
        tool_results: List[Dict[str, Any]] = []
        for ev in selected_events:
            if ev.get("type") != "tool_result":
                continue
            tool_results.append({
                "tool_name": ev.get("tool_name"),
                "semantic_success": ev.get("semantic_success"),
                "result": (
                    ev.get("result") or ev.get("result_preview") or ""
                )[:1600],
                "raw_ref": ev.get("raw_ref"),
                "structured_ref": ev.get("structured_ref"),
                "summary_ref": ev.get("summary_ref"),
            })
        payload = {
            "node_id": node_id,
            "usage_ratio": round(usage_ratio, 4),
            "context_window": context_window,
            "instruction": (
                "压缩 evidence 运行上下文。保留关键过程、计划、已完成/未完成证据、"
                "正向事实、负向事实、冲突和下一步焦点。若模型陷入重复工具或钻牛角尖，"
                "请抓大放小，把重复/无关节点容量、长 JSON、重复 describe 归入 discarded_noise。"
            ),
            "ai_messages": ai_messages,
            "tool_results": tool_results,
            "tool_observation_tail": [
                str(item)[:1200]
                for item in tool_observation_contents[-3:]
            ],
        }
        token_limit = max(1, int(max_tokens or 1))

        def _tokens() -> int:
            return count_tokens(
                json.dumps(payload, ensure_ascii=False, default=str),
                model=model,
            )["tokens"]

        for text_limit in (900, 480, 240):
            if _tokens() <= token_limit:
                return payload
            payload["ai_messages"] = [
                compact_text_to_token_budget(
                    item,
                    max_tokens=max(16, text_limit // 3),
                    model=model,
                    preserve_tail_tokens=max(4, text_limit // 12),
                )
                for item in payload["ai_messages"]
            ]
            for item in payload["tool_results"]:
                item["result"] = compact_text_to_token_budget(
                    item.get("result") or "",
                    max_tokens=max(24, text_limit // 3),
                    model=model,
                    preserve_tail_tokens=max(6, text_limit // 12),
                )
            payload["tool_observation_tail"] = [
                compact_text_to_token_budget(
                    item,
                    max_tokens=max(16, text_limit // 4),
                    model=model,
                    preserve_tail_tokens=max(4, text_limit // 16),
                )
                for item in payload["tool_observation_tail"]
            ]

        while _tokens() > token_limit and len(payload["ai_messages"]) > 1:
            payload["ai_messages"].pop(0)
        while _tokens() > token_limit and len(payload["tool_results"]) > 1:
            payload["tool_results"].pop(0)
        while (
            _tokens() > token_limit
            and len(payload["tool_observation_tail"]) > 1
        ):
            payload["tool_observation_tail"].pop(0)
        if _tokens() <= token_limit:
            return payload

        payload["instruction"] = (
            "压缩 evidence 上下文，保留计划、工具事实、错误和证据引用。"
        )
        while _tokens() > token_limit and payload["ai_messages"]:
            payload["ai_messages"].pop(0)
        while _tokens() > token_limit and payload["tool_observation_tail"]:
            payload["tool_observation_tail"].pop(0)
        while _tokens() > token_limit and len(payload["tool_results"]) > 1:
            payload["tool_results"].pop()
        if _tokens() <= token_limit:
            return payload

        serialized = compact_text_to_token_budget(
            json.dumps(payload, ensure_ascii=False, default=str),
            max_tokens=max(1, token_limit - 32),
            model=model,
            preserve_tail_tokens=max(16, token_limit // 5),
        )
        bounded = {
            "node_id": node_id,
            "bounded_payload": serialized,
        }
        for _attempt in range(8):
            bounded_tokens = count_tokens(
                json.dumps(bounded, ensure_ascii=False, default=str),
                model=model,
            )["tokens"]
            if bounded_tokens <= token_limit:
                return bounded
            serialized_tokens = count_tokens(
                bounded.get("bounded_payload") or "",
                model=model,
            )["tokens"]
            serialized = compact_text_to_token_budget(
                bounded.get("bounded_payload") or "",
                max_tokens=max(
                    1,
                    serialized_tokens
                    - (bounded_tokens - token_limit)
                    - 8,
                ),
                model=model,
                preserve_tail_tokens=max(4, token_limit // 8),
            )
            bounded["bounded_payload"] = serialized
        if count_tokens(
            json.dumps(bounded, ensure_ascii=False, default=str),
            model=model,
        )["tokens"] <= token_limit:
            return bounded
        return {}

    def _compact_context_with_lite_llm(
        self,
        payload: Dict[str, Any],
        node_id: str,
        run_id: str,
        max_tokens: int = 1200,
    ) -> Optional[Dict[str, Any]]:
        prompt = """你是 K8s AIOps evidence 上下文压缩器。
任务：把冗长的中间思考和工具输出压缩成结构化摘要，帮助后续模型继续诊断。
要求：
- 保留重要事实，不编造。
- 体现过程顺序，用“先...随后...最后...”描述。
- 负向结果也是事实，例如 timeout、connection reset、NotFound、空事件。
- 如果工具调用重复、跑偏或钻牛角尖，抓大放小，把噪声放入 discarded_noise。
"""
        try:
            parsed, raw = self.call_structured(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False, default=str),
                schema=ContextCompactionSummary,
                node_id=f"{node_id}_context_compaction",
                run_id=run_id,
                max_tokens=max_tokens,
            )
            if parsed is None:
                return None
            return parsed.model_dump()
        except Exception as exc:
            logger.warning("⚠️ [AICall] runtime context compaction failed: %s", exc)
            return None

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
        context_summary_text = "\n".join(
            ev.get("full_content", "") or ev.get("content", "")
            for ev in thinking_events
            if ev.get("type") == "context_summary"
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
                "name": "context_summaries",
                "category": "dynamic_runtime",
                "content": context_summary_text,
                "preview": context_summary_text[:200],
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
            enable_usage_probe=False,
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
            parsed, text = self.call_structured(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False),
                schema=ToolObservationSummary,
                node_id="tool_observation_summarizer",
                max_tokens=2048,
            )
            if parsed is not None and parsed.summary:
                facts = parsed.key_facts or []
                conflicts = parsed.conflicts or []
                missing = parsed.missing or []
                lines = [str(parsed.summary)]
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
