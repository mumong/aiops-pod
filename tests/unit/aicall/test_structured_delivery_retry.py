"""Empty structured delivery is retried once without thinking (live: 3/4 RCA lanes partial)."""

from pydantic import BaseModel

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import OutputBudget


class _Out(BaseModel):
    ok: bool


class _Structured:
    def __init__(self, result):
        self._result = result

    def invoke(self, messages, config=None):
        return self._result


class _Model:
    def __init__(self, internal, max_tokens, calls):
        self._internal = internal
        self._max_tokens = max_tokens
        self._calls = calls

    def with_structured_output(self, schema, method=None):
        self._calls.append(("internal" if self._internal else "thinking", self._max_tokens))
        # Thinking: no function call at all. Internal but 6000 tokens: cut mid-JSON.
        return _Structured(_Out(ok=True) if self._internal and self._max_tokens > 6000 else None)


def _client(monkeypatch, calls, internal_extra_body):
    ai = AICall(
        model="openai/x",
        api_key="sk-test",
        api_base="http://gateway/v1",
        internal_extra_body=internal_extra_body,
        output_budget=OutputBudget(
            agent=6000, delivery=10000, compaction=3000, retry_multiplier=2
        ),
    )
    monkeypatch.setattr(
        ai,
        "_create_chat_model",
        lambda **kw: _Model(kw.get("internal"), kw.get("max_tokens"), calls),
    )
    monkeypatch.setattr(ai, "_bind_session_metadata", lambda model, *a, **k: model)
    guard = {"context_window": 54000, "final_input_tokens": 14000, "safety_tokens": 2000}
    monkeypatch.setattr(
        ai,
        "_prepare_structured_call_context",
        lambda **kw: (kw["system_prompt"], kw["question"], guard, {}, {}),
    )
    return ai


def test_empty_native_output_retries_once_internal_with_doubled_budget(monkeypatch):
    calls = []
    ai = _client(monkeypatch, calls, {"chat_template_kwargs": {"enable_thinking": False}})
    parsed, raw = ai.call_structured("sys", "q", _Out, node_id="rca", max_tokens=6000)
    assert parsed == _Out(ok=True) and raw == '{"ok":true}'
    assert calls == [("thinking", 6000), ("internal", 12000)]


def test_retry_budget_is_bounded_by_the_window(monkeypatch):
    calls = []
    ai = _client(monkeypatch, calls, {"chat_template_kwargs": {"enable_thinking": False}})
    ai.call_structured("sys", "q", _Out, node_id="rca", max_tokens=30000)
    # 54000 - 14000 input - 2000 safety = 38000 < 2 * 30000
    assert calls == [("thinking", 30000), ("internal", 38000)]


def test_internal_delivery_retries_budget_only_and_no_change_means_no_retry(monkeypatch):
    calls = []
    ai = _client(monkeypatch, calls, {"chat_template_kwargs": {"enable_thinking": False}})
    # Already internal: the only thing left to change is the budget -> one retry.
    parsed, _ = ai.call_structured(
        "sys", "q", _Out, node_id="rca", internal_model=True, max_tokens=6000
    )
    assert parsed == _Out(ok=True)
    assert calls == [("internal", 6000), ("internal", 12000)]
    calls.clear()
    ai = _client(monkeypatch, calls, None)
    ai._prepare_structured_call_context = lambda **kw: (
        kw["system_prompt"],
        kw["question"],
        {},
        {},
        {},
    )
    assert ai.call_structured("sys", "q", _Out, node_id="rca", max_tokens=6000)[0] is None
    assert calls == [("thinking", 6000)]


def test_tool_free_stage_delivery_uses_internal_settings(monkeypatch):
    calls = []
    ai = _client(monkeypatch, calls, {"chat_template_kwargs": {"enable_thinking": False}})
    result, _events = ai._call_without_agent_loop(
        system_prompt="sys",
        question="q",
        max_steps=0,
        stream_queue=None,
        node_id="rca",
        run_id="",
        static_context_components=[],
        response_schema=_Out,
        thinking_events=[],
        call_start=0.0,
    )
    assert result.result == '{"ok":true}'
    assert calls == [("internal", 10000)]
