"""Window-relative compaction policy: what a compaction keeps verbatim and how much it summarizes.

The model window has one source (``MODEL_CONTEXT_WINDOW`` / ``llm.context_window``, see
``ModelContextResolver``). Everything here is a share of that window or a count of
interactions, so changing the gateway window (30K / 54K / 70K) needs no other edit.

Front-loaded by design (2026-10-19): decisive facts (state, reasons, exit codes,
configuration, error lines, metric values) are usually collected early and mid-run,
while the recent tail is the current step. When compaction triggers, the verbatim tail
is only the last ``recent_keep_interactions`` complete interactions (also capped by
``recent_keep_ratio`` of the window) and the working memory that carries the older
facts gets the larger ``summary_output_ratio`` of the window.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

# Config key -> (environment override, default, lower bound, upper bound)
_FIELDS = {
    "recent_keep_interactions": ("AICALL_RECENT_KEEP_INTERACTIONS", 2, 1, 10),
    "recent_keep_ratio": ("AICALL_RECENT_KEEP_RATIO", 0.06, 0.01, 0.5),
    "summary_output_ratio": ("AICALL_SUMMARY_OUTPUT_RATIO", 0.08, 0.01, 0.3),
}
SUMMARY_FLOOR_TOKENS = 600
# The newest interaction is what the model acts on next; it stays verbatim up to this
# share of the window even when it alone exceeds ``recent_keep_ratio``.
LATEST_MAX_RATIO = 0.15


@dataclass(frozen=True)
class WindowPolicy:
    """``recent_keep_interactions``: most complete interactions kept verbatim.
    ``recent_keep_ratio``: their token cap as a share of the window (the stricter wins).
    ``summary_output_ratio``: working-memory output budget as a share of the window."""

    recent_keep_interactions: int = _FIELDS["recent_keep_interactions"][1]
    recent_keep_ratio: float = _FIELDS["recent_keep_ratio"][1]
    summary_output_ratio: float = _FIELDS["summary_output_ratio"][1]

    @classmethod
    def from_config(
        cls,
        config: Optional[Mapping[str, Any]] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> "WindowPolicy":
        env = os.environ if environ is None else environ
        source = config if isinstance(config, Mapping) else {}
        values: dict[str, Any] = {}
        for name, (env_name, default, low, high) in _FIELDS.items():
            raw = env.get(env_name)
            if raw in (None, ""):
                raw = source.get(name, default)
            try:
                value = type(default)(raw)
            except (TypeError, ValueError):
                value = default
            values[name] = min(high, max(low, value))
        return cls(**values)

    def recent_budget(self, window: int) -> int:
        """Token cap of the verbatim recent tail."""
        return int(int(window or 0) * self.recent_keep_ratio)

    def latest_budget(self, window: int) -> int:
        """Token cap for keeping the newest interaction verbatim."""
        return max(self.recent_budget(window), int(int(window or 0) * LATEST_MAX_RATIO))

    def summary_budget(self, window: int) -> int:
        """Output budget of the working memory that carries the older facts."""
        return max(SUMMARY_FLOOR_TOKENS, int(int(window or 0) * self.summary_output_ratio))


_current = WindowPolicy.from_config()


def configure(policy: WindowPolicy) -> None:
    global _current
    _current = policy


def current() -> WindowPolicy:
    return _current
