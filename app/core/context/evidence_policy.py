"""Per-response and live-history limits, independent of tool names and symptoms."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class EvidencePolicy:
    enabled: bool = False
    result_tokens: int = 4096
    history_tokens: int = 24000
    recent_tokens: int = 8000

    @classmethod
    def from_env(cls):
        mode = os.getenv("AIOPS_EVIDENCE_VIEW_MODE", "legacy").strip().lower()
        if mode not in {"legacy", "compact"}:
            raise ValueError("AIOPS_EVIDENCE_VIEW_MODE must be legacy or compact")
        if mode == "legacy":
            return cls()
        result = int(os.getenv("AIOPS_EVIDENCE_RESULT_TOKENS", "4096"))
        history = int(os.getenv("AIOPS_EVIDENCE_HISTORY_TOKENS", "24000"))
        recent = int(os.getenv("AIOPS_EVIDENCE_RECENT_TOKENS", "8000"))
        if not (512 <= result <= 16384 and result <= recent and recent * 2 <= history):
            raise ValueError("Evidence budgets require 512 <= result <= 16384, result <= recent <= history/2")
        return cls(True, result, history, recent)

    def limits(self, window):
        # Small model windows still need room for prompts, schema and summaries.
        high = min(self.history_tokens, int(window * 0.45))
        low = min(self.recent_tokens, int(window * 0.15), high // 3)
        return high, low
