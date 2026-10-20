"""What a repair planning run is doing, kept on its job for the workspace to show.

The planning run streams the same thinking events as a diagnosis lane (tool calls,
results, model reasoning). This keeps a bounded copy - one row per tool call and the
latest reasoning text - so a person can follow the plan being made instead of a bare
"planning" status. Presentation only: nothing here feeds back into the plan.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List


class PlanningProgress:
    MAX_TOOLS = 80
    ARGS_CHARS = 300
    PREVIEW_CHARS = 600
    REASONING_CHARS = 12000
    FLUSH_SECONDS = 2.0

    def __init__(self, clock: Callable[[], float] = time.time):
        self._clock = clock
        self.tools: List[Dict[str, Any]] = []
        self.reasoning = ""
        self._flushed_at: float | None = None

    @staticmethod
    def _clip(text: Any, limit: int) -> str:
        text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        return text if len(text) <= limit else text[:limit] + "…"

    def _row(self, event: Dict[str, Any]) -> Dict[str, Any] | None:
        call_id = event.get("tool_call_id")
        for row in reversed(self.tools):
            if row["status"] != "running":
                continue
            if (call_id and row["id"] == call_id) or (
                not call_id and row["name"] == event.get("tool_name")
            ):
                return row
        return None

    def add(self, event: Dict[str, Any]) -> bool:
        """Record one stream event; True when the job record should be rewritten now."""
        if event.get("type") != "thinking":
            return False
        kind = event.get("thinking_type")
        if kind == "ai_reasoning":
            self.reasoning = (self.reasoning + str(event.get("content") or ""))[
                -self.REASONING_CHARS :
            ]
            now = self._clock()
            if self._flushed_at is None or now - self._flushed_at >= self.FLUSH_SECONDS:
                self._flushed_at = now
                return True
            return False
        if kind == "tool_start":
            if len(self.tools) < self.MAX_TOOLS:
                args = event.get("tool_args")
                self.tools.append(
                    {
                        "id": event.get("tool_call_id") or f"t{len(self.tools) + 1}",
                        "name": event.get("tool_name") or "",
                        "args": self._clip(args, self.ARGS_CHARS) if args else "",
                        "status": "running",
                    }
                )
        elif kind == "tool_result":
            row = self._row(event)
            if row is None:
                return False
            failed = event.get("status") != "success" or event.get("semantic_success") is False
            row.update(
                status="error" if failed else "success",
                preview=self._clip(str(event.get("result_preview") or ""), self.PREVIEW_CHARS),
                duration_seconds=event.get("duration_seconds"),
            )
        else:
            return False
        self._flushed_at = self._clock()
        return True

    def snapshot(self) -> Dict[str, Any]:
        return {"tools": [dict(row) for row in self.tools], "reasoning": self.reasoning}
