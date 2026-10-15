"""Model output reservations per call kind.

One place decides how many output tokens a request may generate; nothing else in
the call path hardcodes a number. Source of truth is ``llm.output_tokens`` in the
service config; environment variables override individual values for operations.
The context budget guard still bounds every request to the model window.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

MINIMUM_OUTPUT_TOKENS = 512

# Config key -> (environment override, default)
_FIELDS = {
    "agent": ("AICALL_MAX_OUTPUT_TOKENS", 6000),
    "delivery": ("AICALL_DELIVERY_MAX_OUTPUT_TOKENS", 10000),
    "compaction": ("AICALL_COMPACTION_MAX_OUTPUT_TOKENS", 3000),
    "retry_multiplier": ("AICALL_DELIVERY_RETRY_MULTIPLIER", 2),
}


@dataclass(frozen=True)
class OutputBudget:
    """Output token reservations.

    ``agent``: one tool-loop model turn (reasoning + answer + tool call).
    ``delivery``: a tool-free structured delivery (RCA / conclusion report).
    ``compaction``: context compaction and summaries.
    ``retry_multiplier``: growth of the reserve when a delivery returns nothing.
    """

    agent: int = _FIELDS["agent"][1]
    delivery: int = _FIELDS["delivery"][1]
    compaction: int = _FIELDS["compaction"][1]
    retry_multiplier: int = _FIELDS["retry_multiplier"][1]

    @classmethod
    def from_config(
        cls,
        config: Optional[Mapping[str, Any]] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> "OutputBudget":
        """Config values first, environment overrides second, defaults last."""
        env = os.environ if environ is None else environ
        source = config if isinstance(config, Mapping) else {}
        values = {}
        for name, (env_name, default) in _FIELDS.items():
            raw = env.get(env_name)
            if raw in (None, ""):
                raw = source.get(name, default)
            values[name] = _bounded_int(raw, default)
        return cls(**values)

    def retry_budget(
        self,
        current: int,
        *,
        context_window: Optional[int],
        input_tokens: Optional[int],
        safety_tokens: int = 0,
    ) -> Optional[int]:
        """Larger reserve for one retry, or ``None`` when the window allows no growth."""
        if not context_window or not input_tokens:
            return None
        room = int(context_window) - int(input_tokens) - int(safety_tokens or 0)
        larger = min(int(current) * self.retry_multiplier, room)
        return larger if larger > int(current) else None


def _bounded_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    if default == _FIELDS["retry_multiplier"][1]:
        return max(1, number)
    return max(MINIMUM_OUTPUT_TOKENS, number)
