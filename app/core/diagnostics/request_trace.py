"""Compact per-request view of the message list sent to the model.

Answers "what did the model actually see this round" without storing full
transcripts twice: per message the role, text size, whether in-loop reasoning
was attached, and the tool calls (name + argument digest). Written next to the
budget snapshots as ``requests/<node>-NNN.json``; derived data, never read back
by the run.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def _digest(value: Any) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        text = str(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def _text_len(content: Any) -> int:
    if isinstance(content, str):
        return len(content)
    try:
        return len(json.dumps(content, ensure_ascii=False, default=str))
    except Exception:
        return len(str(content))


def describe_messages(messages: List[Any]) -> List[Dict[str, Any]]:
    """One compact dict per message, in send order."""
    rows: List[Dict[str, Any]] = []
    for index, message in enumerate(messages):
        role = str(
            getattr(message, "type", None)
            or getattr(message, "role", None)
            or type(message).__name__
        )
        row: Dict[str, Any] = {
            "index": index,
            "role": role,
            "chars": _text_len(getattr(message, "content", "")),
        }
        extra = getattr(message, "additional_kwargs", None) or {}
        reasoning = extra.get("reasoning_content") or extra.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            row["reasoning_chars"] = len(reasoning)
        calls = getattr(message, "tool_calls", None) or []
        if calls:
            row["tool_calls"] = [
                {
                    "name": call.get("name"),
                    "args": _digest(call.get("args") or {}),
                    "id": call.get("id"),
                }
                for call in calls
                if isinstance(call, dict)
            ]
        call_id = getattr(message, "tool_call_id", None)
        if call_id:
            row["tool_call_id"] = call_id
            row["name"] = getattr(message, "name", None)
            flags = [key for key in extra if str(key).startswith("aiops_") and extra.get(key)]
            if flags:
                row["guard"] = flags
        rows.append(row)
    return rows


def repeated_call_digests(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    """How many times each (name, args) pair was issued across the history."""
    counts: Dict[str, int] = {}
    for row in rows:
        for call in row.get("tool_calls") or []:
            key = f"{call.get('name')}:{call.get('args')}"
            counts[key] = counts.get(key, 0) + 1
    return {key: value for key, value in counts.items() if value > 1}
