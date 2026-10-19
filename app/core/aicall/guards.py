"""Deterministic guards on the agent tool loop (``llm.agent_guards``)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

# Config key -> (environment override, default)
_FIELDS = {
    "max_tool_calls_per_turn": ("AICALL_MAX_TOOL_CALLS_PER_TURN", 16),
    "max_identical_calls": ("AICALL_MAX_IDENTICAL_CALLS", 3),
    "repeat_page_chars": ("AICALL_REPEAT_PAGE_CHARS", 3000),
    "idle_round_min_calls": ("AICALL_IDLE_ROUND_MIN_CALLS", 2),
    "structured_validation_retries": ("AICALL_STRUCTURED_VALIDATION_RETRIES", 2),
    "runaway_round_retries": ("AICALL_RUNAWAY_ROUND_RETRIES", 1),
}
_FLAGS = {
    "finalize_on_idle_round": ("AICALL_FINALIZE_ON_IDLE_ROUND", True),
}
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class AgentGuards:
    """``max_tool_calls_per_turn``: tool calls executed per model message (0 = no cap).
    ``max_identical_calls``: how often the same call (tool + arguments) may be repeated
    in one stage before the repeat notice tells the model to stop and deliver.
    ``repeat_page_chars``: when the first result was bounded, each repeat of the same
    call serves the next slice of the archived raw output of this size (0 disables)."""

    max_tool_calls_per_turn: int = _FIELDS["max_tool_calls_per_turn"][1]
    max_identical_calls: int = _FIELDS["max_identical_calls"][1]
    repeat_page_chars: int = _FIELDS["repeat_page_chars"][1]
    # Minimum calls in a round before "all repeats" counts as idle. One repeated call
    # is a normal re-check (live: a layer node was cut after 2 rounds); whole rounds of
    # 4-7 stale calls are the degenerate pattern this guard targets.
    idle_round_min_calls: int = _FIELDS["idle_round_min_calls"][1]
    # Tool-free structured deliveries that fail schema validation are retried this many
    # times, each retry carrying the validation error (live: the model fixed a piped
    # command on retry 1 and broke the group_id binding instead; one retry was not enough).
    structured_validation_retries: int = _FIELDS["structured_validation_retries"][1]
    # A round whose every tool call repeats an already answered call carries no new
    # request: end the loop and deliver from material (the model was done anyway).
    finalize_on_idle_round: bool = _FLAGS["finalize_on_idle_round"][1]
    # A round that spends the whole output reserve on reasoning and emits no tool call
    # (or no delivery) is retried this many times with a short "act now" note. Live
    # 2026-10-19: such rounds cost 70-100 s and ended layer/evidence/repair stages early
    # (runs 1bbfc5ea, 7e55538b, 3c052423-g1, 4285ef7a). 0 disables.
    runaway_round_retries: int = _FIELDS["runaway_round_retries"][1]

    @classmethod
    def from_config(
        cls,
        config: Optional[Mapping[str, Any]] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> "AgentGuards":
        env = os.environ if environ is None else environ
        source = config if isinstance(config, Mapping) else {}
        values = {}
        for name, (env_name, default) in _FIELDS.items():
            raw = env.get(env_name)
            if raw in (None, ""):
                raw = source.get(name, default)
            try:
                values[name] = max(0, int(raw))
            except (TypeError, ValueError):
                values[name] = default
        for name, (env_name, default) in _FLAGS.items():
            raw = env.get(env_name)
            if raw in (None, ""):
                raw = source.get(name, default)
            if isinstance(raw, bool):
                values[name] = raw
            else:
                text = str(raw).strip().lower()
                values[name] = True if text in _TRUE else False if text in _FALSE else default
        return cls(**values)
