"""Context window resolution and token budget estimation for workflow LLM calls."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

from .usage_probe import OpenAIUsageProbe

logger = logging.getLogger(__name__)


_KNOWN_CONTEXT_WINDOWS = {
    "qwen3-next-80b": 65536,
    "qwen3-32b": 32768,
    "qwen2.5-32b": 32768,
    "deepseek-chat": 65536,
}

_CONTEXT_WINDOW_KEYS = {
    "max_model_len",
    "max_context_length",
    "context_length",
    "max_sequence_length",
    "model_max_length",
    "n_ctx",
    "max_position_embeddings",
    "max_input_tokens",
    "max_total_tokens",
}


_TOKENIZER_CACHE: Dict[str, Any] = {}


def _env_truthy(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def estimate_tokens(text: Any) -> int:
    """Cheap cross-provider estimate.

    Chinese and JSON-heavy prompts vary by tokenizer; chars/3 is a pragmatic
    estimate that errs slightly high for English and slightly low for dense CJK.
    """
    if text is None:
        return 0
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False, default=str)
    return max(1, (len(text) + 2) // 3) if text else 0


def _token_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def count_tokens(text: Any, model: str = "") -> Dict[str, Any]:
    """Count tokens using an exact tokenizer when explicitly configured.

    Exact means "exact for the configured tokenizer". If the runtime does not
    provide the same tokenizer used by the model server, we fall back to a
    clearly marked heuristic instead of pretending to be accurate.
    """
    value = _token_text(text)
    if not value:
        return {"tokens": 0, "source": "empty", "accuracy": "exact"}

    tokenizer_json = os.getenv("AIOPS_TOKENIZER_JSON_PATH", "").strip()
    if tokenizer_json:
        try:
            cache_key = f"tokenizers:{tokenizer_json}"
            tokenizer = _TOKENIZER_CACHE.get(cache_key)
            if tokenizer is None:
                from tokenizers import Tokenizer

                tokenizer = Tokenizer.from_file(tokenizer_json)
                _TOKENIZER_CACHE[cache_key] = tokenizer
            return {
                "tokens": len(tokenizer.encode(value).ids),
                "source": f"tokenizer_json:{tokenizer_json}",
                "accuracy": "exact",
            }
        except Exception as exc:
            logger.warning("⚠️ [context_budget] tokenizer_json 计数失败，回退估算: %s", exc)

    tiktoken_encoding = os.getenv("AIOPS_TIKTOKEN_ENCODING", "").strip()
    if tiktoken_encoding:
        try:
            cache_key = f"tiktoken:{tiktoken_encoding}"
            encoding = _TOKENIZER_CACHE.get(cache_key)
            if encoding is None:
                import tiktoken

                encoding = tiktoken.get_encoding(tiktoken_encoding)
                _TOKENIZER_CACHE[cache_key] = encoding
            return {
                "tokens": len(encoding.encode(value)),
                "source": f"tiktoken:{tiktoken_encoding}",
                "accuracy": "exact",
            }
        except Exception as exc:
            logger.warning("⚠️ [context_budget] tiktoken 计数失败，回退估算: %s", exc)

    short_model = _short_model_name(model)
    if short_model and re.match(r"^(gpt-|o[0-9]|chatgpt-)", short_model.lower()):
        try:
            cache_key = f"tiktoken_model:{short_model}"
            encoding = _TOKENIZER_CACHE.get(cache_key)
            if encoding is None:
                import tiktoken

                encoding = tiktoken.encoding_for_model(short_model)
                _TOKENIZER_CACHE[cache_key] = encoding
            return {
                "tokens": len(encoding.encode(value)),
                "source": f"tiktoken_model:{short_model}",
                "accuracy": "exact",
            }
        except Exception:
            pass

    return {
        "tokens": estimate_tokens(value),
        "source": "heuristic:chars/3",
        "accuracy": "estimated",
    }


def _short_model_name(model: str = "") -> str:
    return (model or "").split("/", 1)[-1]


def _extract_context_window_from_payload(payload: Any, model: str = "") -> Optional[int]:
    """Find a context window in common OpenAI-compatible metadata payloads."""
    target = _short_model_name(model).lower()

    def _walk(obj: Any, matched_model: bool = False) -> Optional[int]:
        if isinstance(obj, dict):
            current_match = matched_model
            obj_id = str(obj.get("id") or obj.get("model") or obj.get("model_name") or "").lower()
            if target and obj_id and (obj_id == target or target in obj_id or obj_id in target):
                current_match = True

            for key, value in obj.items():
                if key in _CONTEXT_WINDOW_KEYS:
                    try:
                        parsed = int(value)
                    except (TypeError, ValueError):
                        continue
                    if parsed > 0 and (current_match or not target):
                        return parsed

            for value in obj.values():
                found = _walk(value, current_match)
                if found:
                    return found

        if isinstance(obj, list):
            fallback: Optional[int] = None
            for item in obj:
                found = _walk(item, matched_model)
                if found and target:
                    return found
                if found and fallback is None:
                    fallback = found
            return fallback

        return None

    return _walk(payload)


class ModelContextResolver:
    """Resolve model context windows with explicit accuracy metadata.

    Only env/config file and model metadata endpoints are considered exact.
    Model-name mappings are kept as an estimated fallback for observability,
    but callers can distinguish them via ``accuracy=estimated``.
    """

    _metadata_cache: Dict[str, Dict[str, Any]] = {}

    def resolve(
        self,
        model: str = "",
        api_base: str = "",
        api_key: str = "",
    ) -> Dict[str, Any]:
        env_value = os.getenv("MODEL_CONTEXT_WINDOW", "").strip()
        if env_value.isdigit():
            return {
                "context_window": int(env_value),
                "source": "env:MODEL_CONTEXT_WINDOW",
                "accuracy": "exact",
            }

        file_result = self._from_metadata_file(model)
        if file_result:
            return file_result

        metadata_result = self._from_openai_compatible_metadata(model, api_base, api_key)
        if metadata_result:
            return metadata_result

        model_l = (model or "").lower()
        for key, value in _KNOWN_CONTEXT_WINDOWS.items():
            if key in model_l:
                return {
                    "context_window": value,
                    "source": f"model_name_heuristic:{key}",
                    "accuracy": "estimated",
                }

        return {
            "context_window": None,
            "source": "unavailable",
            "accuracy": "unknown",
        }

    def _from_metadata_file(self, model: str) -> Optional[Dict[str, Any]]:
        path_raw = os.getenv("AIOPS_MODEL_METADATA_FILE", "").strip()
        if not path_raw:
            return None
        try:
            payload = json.loads(Path(path_raw).read_text(encoding="utf-8"))
            window = _extract_context_window_from_payload(payload, model)
            if window:
                return {
                    "context_window": window,
                    "source": f"file:{path_raw}",
                    "accuracy": "exact",
                }
        except Exception as exc:
            logger.warning("⚠️ [context_budget] 读取模型 metadata 文件失败: %s", exc)
        return None

    def _from_openai_compatible_metadata(
        self,
        model: str,
        api_base: str,
        api_key: str,
    ) -> Optional[Dict[str, Any]]:
        if not api_base:
            return None
        cache_key = f"{api_base.rstrip('/')}|{_short_model_name(model)}"
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]

        base = api_base.rstrip("/")
        model_name = _short_model_name(model)
        endpoints = [
            f"{base}/models/{model_name}",
            f"{base}/model/info",
            f"{base}/models",
        ]
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

        for url in endpoints:
            try:
                response = requests.get(url, timeout=2, headers=headers)
                if response.status_code >= 400:
                    continue
                payload = response.json()
                window = _extract_context_window_from_payload(payload, model)
                if window:
                    result = {
                        "context_window": window,
                        "source": f"metadata:{url}",
                        "accuracy": "exact",
                    }
                    self._metadata_cache[cache_key] = result
                    return result
            except Exception:
                continue
        return None


def get_model_context_window(model: str = "") -> Optional[int]:
    resolved = ModelContextResolver().resolve(model)
    value = resolved.get("context_window")
    return int(value) if value else None


def serialize_tool_schema(tools: Optional[Iterable[Any]]) -> List[Dict[str, Any]]:
    """Serialize enough of tool schemas to estimate prompt pressure."""
    serialized: List[Dict[str, Any]] = []
    for tool in tools or []:
        item: Dict[str, Any] = {
            "name": getattr(tool, "name", tool.__class__.__name__),
            "description": getattr(tool, "description", "") or "",
        }
        args_schema = getattr(tool, "args_schema", None)
        if args_schema is not None:
            try:
                if hasattr(args_schema, "model_json_schema"):
                    item["args_schema"] = args_schema.model_json_schema()
                elif hasattr(args_schema, "schema"):
                    item["args_schema"] = args_schema.schema()
                else:
                    item["args_schema"] = str(args_schema)
            except Exception:
                item["args_schema"] = str(args_schema)
        serialized.append(item)
    return serialized


def serialize_tool_schema_for_openai(tools: Optional[Iterable[Any]]) -> List[Dict[str, Any]]:
    """Serialize LangChain tools into a minimal OpenAI-compatible tool schema."""
    serialized: List[Dict[str, Any]] = []
    for item in serialize_tool_schema(tools):
        parameters = item.get("args_schema")
        if not isinstance(parameters, dict):
            parameters = {"type": "object", "properties": {}}
        serialized.append({
            "type": "function",
            "function": {
                "name": item.get("name") or "unknown_tool",
                "description": item.get("description") or "",
                "parameters": parameters,
            },
        })
    return serialized


class ContextBudgetEstimator:
    """Builds and logs node-level context budget snapshots."""

    def estimate(
        self,
        node_id: str,
        model: str,
        system_prompt: str,
        user_message: str,
        tool_count: int = 0,
        tools: Optional[Iterable[Any]] = None,
        handoff: Any = None,
        tool_traces: Optional[Iterable[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        api_base: str = "",
        api_key: str = "",
        scratchpad_reserved: int = 4096,
        output_reserved: int = 6000,
    ) -> Dict[str, Any]:
        resolved_window = ModelContextResolver().resolve(model, api_base=api_base, api_key=api_key)
        context_window = resolved_window.get("context_window")
        provider_prompt_tokens: Optional[int] = None
        provider_total_tokens: Optional[int] = None
        provider_completion_tokens: Optional[int] = None
        provider_usage_source: Optional[str] = None
        provider_usage_error: str = ""

        if _env_truthy("AIOPS_CONTEXT_USAGE_PROBE") and api_base:
            messages: List[Dict[str, Any]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if user_message:
                messages.append({"role": "user", "content": user_message})
            if messages:
                probe = OpenAIUsageProbe(
                    api_base=api_base,
                    api_key=api_key,
                    timeout=float(os.getenv("AIOPS_CONTEXT_USAGE_PROBE_TIMEOUT", "30") or 30),
                )
                probed = probe.count_prompt_tokens(
                    model=model,
                    messages=messages,
                    tools=serialize_tool_schema_for_openai(tools) if tools else None,
                )
                provider_prompt_tokens = probed.prompt_tokens
                provider_total_tokens = probed.total_tokens
                provider_completion_tokens = probed.completion_tokens
                provider_usage_source = probed.source
                provider_usage_error = probed.error or ""

        if components is None:
            tool_schema_payload = serialize_tool_schema(tools)
            if tool_schema_payload:
                tool_schema_count = count_tokens(tool_schema_payload, model=model)
                tool_schema = tool_schema_count["tokens"]
            else:
                tool_schema_count = {
                    "source": "fallback:tool_count*280",
                    "accuracy": "estimated",
                }
                tool_schema = int(tool_count or 0) * 280
            components = [
                {"name": "startup_prompt", "category": "static_input", "content": system_prompt},
                {"name": "user_message", "category": "static_input", "content": user_message},
                {
                    "name": "tool_schema",
                    "category": "static_input",
                    "tokens": tool_schema,
                    "token_source": tool_schema_count["source"],
                    "token_accuracy": tool_schema_count["accuracy"],
                },
                {"name": "handoff", "category": "static_input", "content": handoff},
                {"name": "tool_traces", "category": "dynamic_runtime", "content": list(tool_traces or [])},
                {"name": "scratchpad_reserved", "category": "reserved", "tokens": scratchpad_reserved},
                {"name": "output_reserved", "category": "reserved", "tokens": output_reserved},
            ]

        normalized_components = self._normalize_components(components, model=model)
        estimated_total = sum(c["tokens"] for c in normalized_components)
        usage_ratio = (estimated_total / context_window) if context_window else None
        provider_input_usage_ratio = (
            provider_prompt_tokens / context_window
            if isinstance(provider_prompt_tokens, int) and isinstance(context_window, int) and context_window > 0
            else None
        )

        static_context_tokens = sum(c["tokens"] for c in normalized_components if c["category"] == "static_input")
        dynamic_context_tokens = sum(c["tokens"] for c in normalized_components if c["category"] == "dynamic_runtime")
        reserved_tokens = sum(c["tokens"] for c in normalized_components if c["category"] == "reserved")
        actual_context_tokens = static_context_tokens + dynamic_context_tokens
        token_sources = sorted({
            str(c.get("token_source"))
            for c in normalized_components
            if c.get("token_source") and c.get("category") != "reserved"
        })
        token_accuracies = {
            str(c.get("token_accuracy"))
            for c in normalized_components
            if c.get("token_accuracy") and c.get("category") != "reserved"
        }
        if token_accuracies == {"exact"}:
            token_count_accuracy = "exact"
        elif "exact" in token_accuracies:
            token_count_accuracy = "mixed"
        else:
            token_count_accuracy = "estimated"

        for component in normalized_components:
            component["total_ratio"] = round(component["tokens"] / estimated_total, 4) if estimated_total else 0.0
            component["window_ratio"] = round(component["tokens"] / context_window, 4) if context_window else None

        budget = {
            "node": node_id,
            "model": model,
            "context_window": context_window or "unknown",
            "context_window_source": resolved_window.get("source"),
            "context_window_accuracy": resolved_window.get("accuracy"),
            "components": normalized_components,
            "static_context_tokens": static_context_tokens,
            "dynamic_context_tokens": dynamic_context_tokens,
            "actual_context_tokens": actual_context_tokens,
            "reserved_tokens": reserved_tokens,
            "provider_prompt_tokens": provider_prompt_tokens,
            "provider_total_tokens": provider_total_tokens,
            "provider_completion_tokens": provider_completion_tokens,
            "provider_usage_source": provider_usage_source,
            "provider_usage_error": provider_usage_error,
            "provider_input_usage_ratio": provider_input_usage_ratio,
            "token_count_accuracy": token_count_accuracy,
            "token_count_sources": token_sources,
            # Legacy flattened keys kept for current logs/tests.
            "startup_prompt": self._component_tokens(
                normalized_components,
                "startup_prompt",
                "runbook_catalog",
                "node_system_prompt",
                "remediation_policy",
                "language_policy",
            ),
            "user": self._component_tokens(normalized_components, "user_message"),
            "tool_schema": self._component_tokens(normalized_components, "tool_schema"),
            "handoff": self._component_tokens(normalized_components, "handoff", "layer_handoff"),
            "tool_traces": self._component_tokens(normalized_components, "tool_traces", "tool_observations"),
            "scratchpad_reserved": self._component_tokens(normalized_components, "scratchpad_reserved"),
            "output_reserved": self._component_tokens(normalized_components, "output_reserved"),
            "estimated_total": estimated_total,
            "usage_ratio": usage_ratio,
        }
        return budget

    def _normalize_components(self, components: List[Dict[str, Any]], model: str = "") -> List[Dict[str, Any]]:
        normalized = []
        for component in components or []:
            name = str(component.get("name") or "unknown")
            category = str(component.get("category") or "static_input")
            tokens = component.get("tokens")
            token_source = component.get("token_source")
            token_accuracy = component.get("token_accuracy")
            if tokens is None:
                counted = count_tokens(component.get("content", ""), model=model)
                tokens = counted["tokens"]
                token_source = counted["source"]
                token_accuracy = counted["accuracy"]
            else:
                token_source = token_source or "provided"
                token_accuracy = token_accuracy or ("reserved" if category == "reserved" else "unknown")
            preview = component.get("preview")
            if preview is None and "content" in component:
                content = component.get("content")
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False, default=str)
                preview = content[:200]
            normalized.append({
                "name": name,
                "category": category,
                "tokens": int(tokens or 0),
                "token_source": token_source,
                "token_accuracy": token_accuracy,
                "chars": component.get("chars", len(str(component.get("content", ""))) if "content" in component else None),
                "preview": preview,
            })
        return normalized

    @staticmethod
    def _component_tokens(components: List[Dict[str, Any]], *names: str) -> int:
        return sum(c["tokens"] for c in components if c.get("name") in names)

    @staticmethod
    def _sum_component_tokens(components: List[Dict[str, Any]], categories: set[str]) -> int:
        return sum(
            int(component.get("tokens") or 0)
            for component in components or []
            if component.get("category") in categories
        )

    def log(self, budget: Dict[str, Any]) -> None:
        usage = budget.get("usage_ratio")
        usage_text = "unknown" if usage is None else f"{usage:.0%}"
        token_accuracy = str(budget.get("token_count_accuracy") or "estimated")
        provider_prompt_tokens = budget.get("provider_prompt_tokens")
        provider_input_usage = budget.get("provider_input_usage_ratio")
        has_provider_exact = isinstance(provider_prompt_tokens, int)
        estimated_input_tokens = self._sum_component_tokens(
            budget.get("components", []),
            {"static_input", "dynamic_runtime"},
        )
        input_tokens = provider_prompt_tokens if has_provider_exact else (
            budget.get("actual_context_tokens") if token_accuracy == "exact" else (
                f"~{estimated_input_tokens}" if estimated_input_tokens else "n/a"
            )
        )
        if isinstance(provider_input_usage, (int, float)):
            input_usage = f"{provider_input_usage:.0%}"
            input_token_source = budget.get("provider_usage_source") or "provider_usage_probe"
        elif token_accuracy == "exact" and isinstance(budget.get("context_window"), int) and budget.get("context_window"):
            input_usage = f"{budget.get('actual_context_tokens') / budget.get('context_window'):.0%}"
            input_token_source = "local_tokenizer"
        else:
            context_window = budget.get("context_window")
            if isinstance(context_window, int) and context_window > 0 and estimated_input_tokens:
                input_usage = f"{estimated_input_tokens / context_window:.0%}"
                input_token_source = "estimated_components"
            else:
                input_usage = "n/a"
                input_token_source = "n/a"
        level = logging.INFO
        ratio_for_level = provider_input_usage if isinstance(provider_input_usage, (int, float)) else usage
        if isinstance(ratio_for_level, (int, float)):
            if ratio_for_level >= 0.90:
                level = logging.ERROR
            elif ratio_for_level >= 0.75:
                level = logging.WARNING

        logger.log(
            level,
            "[context_budget] node=%s window=%s window_source=%s token=%s token_sources=%s "
            "input_tokens=%s input_usage=%s input_source=%s reserved_tokens=%s budget_tokens=%s budget_usage=%s",
            budget.get("node"),
            budget.get("context_window"),
            budget.get("context_window_source"),
            token_accuracy,
            ",".join(budget.get("token_count_sources") or []),
            input_tokens,
            input_usage,
            input_token_source,
            budget.get("reserved_tokens"),
            budget.get("estimated_total"),
            usage_text,
        )
        if budget.get("provider_usage_error") and _env_truthy("AIOPS_CONTEXT_USAGE_PROBE"):
            logger.warning(
                "[context_budget.probe] node=%s input_usage=unknown error=%s",
                budget.get("node"),
                budget.get("provider_usage_error"),
            )

        top_components = [
            c for c in budget.get("components", [])
            if c.get("category") in {"static_input", "dynamic_runtime"}
        ]
        top_components.sort(key=lambda c: int(c.get("tokens") or 0), reverse=True)
        top_parts = []
        for component in top_components[:3]:
            ratio = component.get("window_ratio")
            ratio_text = "n/a" if ratio is None else f"{ratio:.0%}"
            tokens = int(component.get("tokens") or 0)
            accuracy = str(component.get("token_accuracy") or token_accuracy or "estimated")
            token_text = str(tokens) if accuracy == "exact" else f"~{tokens}"
            top_parts.append(f"{component.get('name')}={token_text}({ratio_text},{accuracy})")
        if top_parts:
            logger.log(
                level,
                "[context_budget.top] node=%s %s",
                budget.get("node"),
                " ".join(top_parts),
            )
