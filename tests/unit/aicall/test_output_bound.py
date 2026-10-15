"""Every agent model request carries max_tokens; input + output must fit the context window."""
from dataclasses import dataclass, field, replace

from app.core.aicall.client import AICall


@dataclass
class _Request:
    model_settings: dict = field(default_factory=dict)

    def override(self, **kw):
        return replace(self, **kw)


def _budget(window=54000, used=17222, reserved=6000, safety=2000):
    return {"hard_guard": {"context_window": window, "final_input_tokens": used,
                           "output_reserved": reserved, "safety_tokens": safety}}


def test_small_input_gets_the_configured_output_budget():
    req = AICall._bound_request_output(_Request(), _budget(used=17222))
    assert req.model_settings["max_tokens"] == 6000


def test_large_input_gets_only_what_fits_in_the_window():
    req = AICall._bound_request_output(_Request(), _budget(used=49000))
    assert req.model_settings["max_tokens"] == 54000 - 49000 - 2000
    assert 49000 + req.model_settings["max_tokens"] <= 54000


def test_explicit_max_tokens_is_kept():
    req = AICall._bound_request_output(_Request(model_settings={"max_tokens": 1234}), _budget())
    assert req.model_settings["max_tokens"] == 1234


def test_env_configures_the_output_budget(monkeypatch):
    monkeypatch.setenv("AICALL_MAX_OUTPUT_TOKENS", "3000")
    req = AICall._bound_request_output(_Request(), {"hard_guard": {}})
    assert req.model_settings["max_tokens"] == 3000
