"""Output reservations come from config/env, never from literals in the call path."""

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import MINIMUM_OUTPUT_TOKENS, OutputBudget


def test_defaults_config_and_env_precedence():
    assert OutputBudget.from_config(None, environ={}) == OutputBudget(
        agent=6000, delivery=10000, compaction=3000, router=1200, retry_multiplier=2
    )
    configured = OutputBudget.from_config(
        {"agent": 4000, "delivery": 8000, "compaction": 2000, "retry_multiplier": 3}, environ={}
    )
    assert configured == OutputBudget(
        agent=4000, delivery=8000, compaction=2000, router=1200, retry_multiplier=3
    )
    overridden = OutputBudget.from_config(
        {"agent": 4000},
        environ={"AICALL_MAX_OUTPUT_TOKENS": "7000", "AICALL_DELIVERY_MAX_OUTPUT_TOKENS": ""},
    )
    assert overridden.agent == 7000 and overridden.delivery == 10000


def test_invalid_and_tiny_values_fall_back_safely():
    budget = OutputBudget.from_config(
        {"agent": "lots", "delivery": 10, "retry_multiplier": 0},
        environ={"AICALL_COMPACTION_MAX_OUTPUT_TOKENS": "x"},
    )
    assert budget.agent == 6000 and budget.delivery == MINIMUM_OUTPUT_TOKENS
    assert budget.compaction == 3000 and budget.retry_multiplier == 1


def test_retry_budget_grows_within_the_window_only():
    budget = OutputBudget(agent=6000, delivery=10000, compaction=3000, retry_multiplier=2)
    assert (
        budget.retry_budget(6000, context_window=54000, input_tokens=14000, safety_tokens=2000)
        == 12000
    )
    assert (
        budget.retry_budget(30000, context_window=54000, input_tokens=14000, safety_tokens=2000)
        == 38000
    )
    assert (
        budget.retry_budget(40000, context_window=54000, input_tokens=14000, safety_tokens=2000)
        is None
    )
    assert budget.retry_budget(6000, context_window=None, input_tokens=14000) is None


def test_aicall_uses_the_injected_budget_everywhere(monkeypatch):
    budget = OutputBudget(agent=5000, delivery=9000, compaction=2500, retry_multiplier=2)
    ai = AICall(
        model="openai/x", api_key="sk-test", api_base="http://gateway/v1", output_budget=budget
    )
    assert ai.create_compaction_model().kwargs["max_tokens"] == 2500
    components = ai._default_call_context_components("sys", "q", [])
    assert next(c for c in components if c["name"] == "output_reserved")["tokens"] == 5000

    class _Request:
        model_settings = {}

        def override(self, model_settings):
            self.model_settings = model_settings
            return self

    guard = {
        "hard_guard": {"context_window": 54000, "final_input_tokens": 50000, "safety_tokens": 2000}
    }
    bounded = AICall._bound_request_output(_Request(), guard, budget)
    assert bounded.model_settings["max_tokens"] == 2000  # window-bounded below the 5000 reserve
    assert AICall._agent_request_output_reserved(_Request(), budget) == 5000
