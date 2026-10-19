"""Structured delivery over an ordinary tool call (``tool_choice=auto``).

Why not ``with_structured_output(method="function_calling")``: that sends a *named*
``tool_choice``, and vLLM then decodes the arguments under a JSON grammar. Under
that grammar Qwen3.6 emits the double quotes inside string values unescaped, so
the first inner quote terminates the string and every later field is lost
(live 2026-10-19, run ``6ec40015e1024f8a``: three attempts all ended at
``-p='[{"`` with ``actions`` missing; gateway probe reproduced it with
``tool_choice`` named/required and not with ``auto``). The same defect produced
the earlier "command in prose, actions empty" and "malformed patch JSON" cases.

With ``tool_choice=auto`` the model writes the tool call in its native format,
escapes correctly, and the schema is still enforced here by Pydantic. What the
model actually returned is kept (``finish_reason``, usage, raw arguments) so a
rejected delivery can be read back instead of guessed at.
"""

from __future__ import annotations

import json
import typing
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, ValidationError

TOOL_CHOICE_MODES = ("auto", "named")


def normalize_tool_choice(value: Any, default: str = "auto") -> str:
    text = str(value or "").strip().lower()
    return text if text in TOOL_CHOICE_MODES else default


def _is_container_annotation(annotation: Any) -> bool:
    origin = typing.get_origin(annotation)
    if origin in (list, dict, tuple, set):
        return True
    if annotation in (list, dict, tuple, set):
        return True
    if origin is typing.Union or str(origin) == "types.UnionType":
        return any(_is_container_annotation(arg) for arg in typing.get_args(annotation))
    return False


def coerce_json_strings(
    args: Dict[str, Any], schema: type[BaseModel]
) -> Tuple[Dict[str, Any], list]:
    """Decode list/dict fields the model serialised as a JSON *string*.

    Small models sometimes write ``"actions": "[{...}]"``. Only well-formed JSON of
    the right container type is accepted; anything else is left for validation to
    report, never silently invented.
    """
    coerced = dict(args)
    changed = []
    for name, field in schema.model_fields.items():
        value = coerced.get(name)
        if not isinstance(value, str) or not _is_container_annotation(field.annotation):
            continue
        text = value.strip()
        if not text or text[0] not in "[{":
            continue
        try:
            decoded = json.loads(text)
        except ValueError:
            continue
        if isinstance(decoded, (list, dict)):
            coerced[name] = decoded
            changed.append(name)
    return coerced, changed


def _finish_reason(message: Any) -> str:
    metadata = getattr(message, "response_metadata", None) or {}
    return str(metadata.get("finish_reason") or "").lower()


def _usage(message: Any) -> Dict[str, Any]:
    usage = getattr(message, "usage_metadata", None) or {}
    return dict(usage) if isinstance(usage, dict) else {}


def _raw_arguments(message: Any) -> Optional[str]:
    extra = getattr(message, "additional_kwargs", None) or {}
    for call in extra.get("tool_calls") or []:
        function = (call or {}).get("function") or {}
        arguments = function.get("arguments")
        if isinstance(arguments, str):
            return arguments
    return None


def parse_structured_tool_message(
    message: Any,
    schema: type[BaseModel],
    *,
    text_fallback: Optional[typing.Callable[[str], Any]] = None,
) -> Tuple[Optional[BaseModel], str, Dict[str, Any]]:
    """``(parsed, error, record)`` for one model reply to a single-tool request.

    ``error`` is the sentence fed back to the model on retry; ``record`` is what
    gets archived when the reply is rejected (never the whole prompt).
    """
    finish = _finish_reason(message)
    record: Dict[str, Any] = {
        "schema": schema.__name__,
        "finish_reason": finish or None,
        "usage": _usage(message),
        "content_chars": len(str(getattr(message, "content", "") or "")),
    }
    raw_arguments = _raw_arguments(message)
    if raw_arguments is not None:
        record["arguments"] = raw_arguments
    invalid = list(getattr(message, "invalid_tool_calls", None) or [])
    calls = list(getattr(message, "tool_calls", None) or [])

    if finish == "length":
        # A truncated reply parses as *partial* JSON (LangChain repairs the fragment),
        # so a tool call here would carry missing or cut fields. Reject it as what it is.
        error = (
            "输出在 max_tokens 处被截断（finish_reason=length），JSON 不完整："
            "请压缩正文与说明，只保留必要字段，重新输出完整 JSON"
        )
        record["error"] = error
        return None, error, record

    if invalid and not calls:
        detail = str((invalid[0] or {}).get("error") or "")[:300]
        error = f'函数参数不是合法 JSON（{detail or "解析失败"}）：字符串内的双引号必须写成 \\"，重新输出完整 JSON'
        record["error"] = error
        record["invalid_tool_calls"] = [str((i or {}).get("args") or "")[:2000] for i in invalid]
        return None, error, record

    if calls:
        args = (calls[0] or {}).get("args")
        if not isinstance(args, dict):
            error = "函数参数不是 JSON 对象"
            record["error"] = error
            return None, error, record
        coerced, changed = coerce_json_strings(args, schema)
        if changed:
            record["coerced_fields"] = changed
        try:
            return schema.model_validate(coerced), "", record
        except ValidationError as exc:
            error = str(exc)[:800]
            record["error"] = error
            record["parsed_arguments"] = coerced
            return None, error, record

    content = getattr(message, "content", "")
    text = (
        content
        if isinstance(content, str)
        else json.dumps(content, ensure_ascii=False, default=str)
    )
    if text.strip() and text_fallback is not None:
        payload = text_fallback(text)
        if isinstance(payload, dict):
            coerced, changed = coerce_json_strings(payload, schema)
            if changed:
                record["coerced_fields"] = changed
            try:
                return schema.model_validate(coerced), "", record
            except ValidationError as exc:
                error = str(exc)[:800]
                record["error"] = error
                record["content_head"] = text[:2000]
                return None, error, record
    error = (
        f"没有调用函数 {schema.__name__}，而是返回了文本：结果必须通过调用该函数提交，"
        "正文只放在函数参数里"
        if text.strip()
        else f"模型没有返回任何内容（未调用函数 {schema.__name__}）"
    )
    record["error"] = error
    if text.strip():
        record["content_head"] = text[:2000]
    return None, error, record
