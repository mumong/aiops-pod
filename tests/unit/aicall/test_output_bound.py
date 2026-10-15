"""Every agent model request carries max_tokens; input + output must fit the context window."""

from dataclasses import dataclass, field, replace

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import OutputBudget

_BUDGET = OutputBudget(agent=6000, delivery=10000, compaction=3000, retry_multiplier=2)


@dataclass
class _Request:
    model_settings: dict = field(default_factory=dict)

    def override(self, **kw):
        return replace(self, **kw)


def _budget(window=54000, used=17222, reserved=6000, safety=2000):
    return {
        "hard_guard": {
            "context_window": window,
            "final_input_tokens": used,
            "output_reserved": reserved,
            "safety_tokens": safety,
        }
    }


def test_small_input_gets_the_configured_output_budget():
    req = AICall._bound_request_output(_Request(), _budget(used=17222), _BUDGET)
    assert req.model_settings["max_tokens"] == 6000


def test_large_input_gets_only_what_fits_in_the_window():
    req = AICall._bound_request_output(_Request(), _budget(used=49000), _BUDGET)
    assert req.model_settings["max_tokens"] == 54000 - 49000 - 2000
    assert 49000 + req.model_settings["max_tokens"] <= 54000


def test_explicit_max_tokens_is_kept():
    req = AICall._bound_request_output(
        _Request(model_settings={"max_tokens": 1234}), _budget(), _BUDGET
    )
    assert req.model_settings["max_tokens"] == 1234


def test_env_configures_the_output_budget(monkeypatch):
    monkeypatch.setenv("AICALL_MAX_OUTPUT_TOKENS", "3000")
    budget = OutputBudget.from_config({"agent": 6000})  # env overrides config
    req = AICall._bound_request_output(_Request(), {"hard_guard": {}}, budget)
    assert req.model_settings["max_tokens"] == 3000


def test_structured_calls_keep_max_tokens_through_with_structured_output():
    """.bind(max_tokens=...) is dropped by with_structured_output; it must be a constructor field."""
    from pydantic import BaseModel

    class _S(BaseModel):
        ok: bool

    ai = AICall(model="openai/m", api_key="sk-test", api_base="http://gw/v1")
    captured = {}
    original = ai._create_chat_model

    def spy(**kw):
        model = original(**kw)
        captured["model"] = model
        return model

    ai._create_chat_model = spy
    ai._bind_session_metadata = lambda model, *a, **k: model
    ai._call_native_structured(
        "sys", "q", _S, node_id="rca", max_tokens=1234, raise_on_error=False
    )
    assert captured["model"].max_tokens == 1234
