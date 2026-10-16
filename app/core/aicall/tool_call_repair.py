"""Repair assistant tool calls before the history goes back to the provider.

Streaming tool-call deltas from small models sometimes merge two calls into one
arguments string (``{"a":1}{"b":2}``) or leave an unparsable fragment. LangChain
still executes what it could parse, but the raw ``additional_kwargs.tool_calls``
keeps the broken string, and vLLM rejects the whole next request with HTTP 400
("Extra data") while rendering the chat template. One bad delta must not end the
run: arguments are rewritten to the single JSON object that was actually
executed, and calls that never received a tool result are dropped.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, List, Tuple

from langchain_core.messages import AIMessage, ToolMessage

_DROPPED_NOTE = "（上一条工具调用的参数不是合法 JSON，已丢弃；请重新发起调用）"


def _single_json_object(text: str) -> Tuple[str, bool]:
    """Return (arguments, changed). Unchanged when ``text`` already is one JSON object."""
    try:
        if isinstance(json.loads(text), dict):
            return text, False
    except (TypeError, ValueError):
        pass
    try:
        obj, _ = json.JSONDecoder().raw_decode(str(text).strip())
        if isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False), True
    except (TypeError, ValueError):
        pass
    return "{}", True


def repair_tool_call_arguments(messages: Iterable[Any]) -> Tuple[List[Any], int]:
    """Return (messages, repaired_message_count)."""
    messages = list(messages)
    answered = {
        str(m.tool_call_id) for m in messages if isinstance(m, ToolMessage) and m.tool_call_id
    }
    out: List[Any] = []
    repaired = 0
    for message in messages:
        if not isinstance(message, AIMessage):
            out.append(message)
            continue
        raw_calls = list((message.additional_kwargs or {}).get("tool_calls") or [])
        invalid = list(getattr(message, "invalid_tool_calls", None) or [])
        if not raw_calls and not invalid:
            out.append(message)
            continue
        parsed = {str(tc.get("id")): tc.get("args") for tc in (message.tool_calls or [])}
        changed = bool(invalid)
        kept = []
        for call in raw_calls:
            call_id = str(call.get("id") or "")
            function = dict(call.get("function") or {})
            arguments = function.get("arguments")
            if isinstance(arguments, str):
                fixed, was_fixed = _single_json_object(arguments)
                if was_fixed:
                    changed = True
                    if call_id not in answered and call_id not in parsed:
                        continue  # never executed: nothing for the provider to pair it with
                    if isinstance(parsed.get(call_id), dict):
                        fixed = json.dumps(parsed[call_id], ensure_ascii=False)
                    function["arguments"] = fixed
            kept.append({**call, "function": function})
        if not changed:
            out.append(message)
            continue
        repaired += 1
        kwargs = dict(message.additional_kwargs or {})
        if kept:
            kwargs["tool_calls"] = kept
        else:
            kwargs.pop("tool_calls", None)
        update = {"additional_kwargs": kwargs, "invalid_tool_calls": []}
        if not kept and not (message.content or "").strip() and not message.tool_calls:
            update["content"] = _DROPPED_NOTE
        out.append(message.model_copy(update=update))
    return out, repaired
