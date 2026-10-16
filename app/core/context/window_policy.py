"""Window-relative context policy: how much recent history every compaction keeps.

The model window itself has one source (``MODEL_CONTEXT_WINDOW`` / ``llm.context_window``,
see ``ModelContextResolver``). Everything derived from it is a ratio or an explicit
config key under ``workflow.context_compaction`` so that a larger window needs no code
change. The service installs the configured policy at start-up; callers read it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

# Config key -> (environment override, default)
_FIELDS = {
    "recent_keep_tokens": ("AICALL_RECENT_KEEP_TOKENS", 8000),
    "recent_keep_ratio": ("AICALL_RECENT_KEEP_RATIO", 0.15),
}


@dataclass(frozen=True)
class WindowPolicy:
    """``recent_keep_tokens``: absolute cap on the recent, uncompressed tail.
    ``recent_keep_ratio``: the same cap as a share of the model window; the smaller wins."""

    recent_keep_tokens: int = _FIELDS["recent_keep_tokens"][1]
    recent_keep_ratio: float = _FIELDS["recent_keep_ratio"][1]

    @classmethod
    def from_config(
        cls,
        config: Optional[Mapping[str, Any]] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> "WindowPolicy":
        env = os.environ if environ is None else environ
        source = config if isinstance(config, Mapping) else {}
        values: dict[str, Any] = {}
        for name, (env_name, default) in _FIELDS.items():
            raw = env.get(env_name)
            if raw in (None, ""):
                raw = source.get(name, default)
            try:
                value = type(default)(raw)
            except (TypeError, ValueError):
                value = default
            values[name] = value
        tokens = max(512, int(values["recent_keep_tokens"]))
        ratio = min(0.9, max(0.01, float(values["recent_keep_ratio"])))
        return cls(recent_keep_tokens=tokens, recent_keep_ratio=ratio)

    def recent_budget(self, window: int) -> int:
        return min(self.recent_keep_tokens, int(int(window or 0) * self.recent_keep_ratio))


_current = WindowPolicy.from_config()


def configure(policy: WindowPolicy) -> None:
    global _current
    _current = policy


def current() -> WindowPolicy:
    return _current
