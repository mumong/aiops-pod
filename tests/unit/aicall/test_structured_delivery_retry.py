"""Empty structured delivery is retried once without thinking (live: 3/4 RCA lanes partial)."""

from pydantic import BaseModel

from app.core.aicall.client import AICall


class _Out(BaseModel):
    ok: bool


class _Structured:
    def __init__(self, result):
        self._result = result

    def invoke(self, messages, config=None):
        return self._result


class _Model:
    def __init__(self, internal, calls):
        self._internal = internal
        self._calls = calls

    def with_structured_output(self, schema, method=None):
        self._calls.append("internal" if self._internal else "thinking")
        # With thinking enabled the gateway returned no function call at all.
        return _Structured(_Out(ok=True) if self._internal else None)


def _client(monkeypatch, calls, internal_extra_body):
    ai = AICall(
        model="openai/x",
        api_key="sk-test",
        api_base="http://gateway/v1",
        internal_extra_body=internal_extra_body,
    )
    monkeypatch.setattr(ai, "_create_chat_model", lambda **kw: _Model(kw.get("internal"), calls))
    monkeypatch.setattr(ai, "_bind_session_metadata", lambda model, *a, **k: model)
    monkeypatch.setattr(
        ai,
        "_prepare_structured_call_context",
        lambda **kw: (kw["system_prompt"], kw["question"], {}, {}, {}),
    )
    return ai


def test_empty_native_output_retries_once_as_internal_call(monkeypatch):
    calls = []
    ai = _client(monkeypatch, calls, {"chat_template_kwargs": {"enable_thinking": False}})
    parsed, raw = ai.call_structured("sys", "q", _Out, node_id="rca")
    assert parsed == _Out(ok=True) and raw == '{"ok":true}'
    assert calls == ["thinking", "internal"]


def test_internal_delivery_calls_are_not_retried_and_no_internal_config_means_no_retry(
    monkeypatch,
):
    calls = []
    ai = _client(monkeypatch, calls, {"chat_template_kwargs": {"enable_thinking": False}})
    assert ai.call_structured("sys", "q", _Out, node_id="rca", internal_model=True)[0] == _Out(
        ok=True
    )
    assert calls == ["internal"]
    calls.clear()
    ai = _client(monkeypatch, calls, None)
    assert ai.call_structured("sys", "q", _Out, node_id="rca")[0] is None
    assert calls == ["thinking"]


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
    assert calls == ["internal"]
