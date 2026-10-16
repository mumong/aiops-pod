"""Per-call ledger built from an agent call's events and tool records."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional

GUARD_FLAGS = (
    ("aiops_turn_cap", "turn_cap"),
    ("aiops_repeat_page", "repeat_page"),
    ("aiops_repeat_notice", "repeat_notice"),
    ("aiops_tool_error", "tool_error"),
)


def guard_of(additional_kwargs: Optional[Dict[str, Any]]) -> Optional[str]:
    kwargs = additional_kwargs or {}
    for key, name in GUARD_FLAGS:
        if kwargs.get(key):
            return name
    return None


def _args_digest(args: Any) -> str:
    try:
        text = json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        text = str(args)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def build_call_ledger(
    *,
    run_id: str,
    node_id: str,
    events: Iterable[Dict[str, Any]],
    tool_calls: Iterable[Dict[str, Any]],
    duration_ms: float,
    incomplete_reason: str = "",
    structured_delivered: Optional[bool] = None,
) -> Dict[str, Any]:
    events = list(events)
    tools = list(tool_calls)
    rounds: List[Dict[str, Any]] = []
    for event in events:
        if event.get("type") == "ai_usage":
            usage = event.get("usage") or {}
            rounds.append(
                {
                    "iteration": event.get("iteration"),
                    "model_ms": round(float(event.get("model_duration_ms") or 0)),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "tool_calls": 0,
                    "at": event.get("timestamp"),
                }
            )
    # Tool starts are attributed to the most recent model round that preceded them.
    starts = [e for e in events if e.get("type") == "tool_start"]
    for start in starts:
        when = start.get("timestamp") or 0
        owner = None
        for item in rounds:
            if (item.get("at") or 0) <= when:
                owner = item
        if owner is not None:
            owner["tool_calls"] += 1
    tool_rows = []
    for record in tools:
        tool_rows.append(
            {
                "tool": record.get("tool_name"),
                "args_digest": _args_digest(record.get("tool_args")),
                "status": record.get("status"),
                "semantic_success": record.get("semantic_success", True),
                "guard": record.get("guard"),
                "raw_chars": record.get("raw_chars"),
                "summary_chars": record.get("summary_chars"),
                "raw_ref": record.get("raw_ref"),
                "error_head": (
                    str(record.get("result") or "")[:160]
                    if record.get("status") == "error" or record.get("semantic_success") is False
                    else None
                ),
            }
        )
    counts = {
        "tool_calls": len(tool_rows),
        "executed": sum(1 for t in tool_rows if not t["guard"]),
        "repeat_notices": sum(1 for t in tool_rows if t["guard"] == "repeat_notice"),
        "repeat_pages": sum(1 for t in tool_rows if t["guard"] == "repeat_page"),
        "turn_capped": sum(1 for t in tool_rows if t["guard"] == "turn_cap"),
        "tool_errors": sum(
            1
            for t in tool_rows
            if t["guard"] == "tool_error"
            or t["status"] == "error"
            or t["semantic_success"] is False
        ),
        "bounded_outputs": sum(
            1
            for t in tool_rows
            if (t["raw_chars"] or 0) > (t["summary_chars"] or 0) and not t["guard"]
        ),
    }
    by_tool: Dict[str, int] = {}
    for t in tool_rows:
        if not t["guard"]:
            by_tool[t["tool"] or "?"] = by_tool.get(t["tool"] or "?", 0) + 1
    guards = {
        "args_repaired": sum(
            int(e.get("count") or 0) for e in events if e.get("type") == "tool_call_args_repaired"
        ),
        "compactions": sum(1 for e in events if e.get("type") == "context_compacted"),
        "finalization": next(
            (e for e in reversed(events) if e.get("type") == "structured_finalization"), None
        ),
        "incomplete": [e.get("reason") for e in events if e.get("type") == "execution_incomplete"],
    }
    return {
        "contract_version": "run-ledger.v1",
        "run_id": run_id,
        "node": node_id,
        "duration_ms": round(float(duration_ms or 0)),
        "model_ms": sum(r["model_ms"] for r in rounds),
        "rounds": rounds,
        "tools": tool_rows,
        "tools_by_name": by_tool,
        "counts": counts,
        "guards": guards,
        "incomplete_reason": incomplete_reason or "",
        "structured_delivered": structured_delivered,
    }
