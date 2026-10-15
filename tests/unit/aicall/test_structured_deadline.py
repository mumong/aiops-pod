"""Non-streaming structured calls get an absolute deadline (live: RCA lane silent >13 min)."""
import time

import pytest
from pydantic import BaseModel

from app.core.aicall import client as client_module
from app.core.aicall.client import AICall, _call_with_deadline


def test_deadline_releases_the_caller():
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="模型响应超过"):
        _call_with_deadline(lambda: time.sleep(3), 0.2, what="test")
    assert time.monotonic() - started < 1


def test_no_deadline_when_disabled_and_value_passthrough():
    assert _call_with_deadline(lambda: 42, None, what="test") == 42
    assert _call_with_deadline(lambda: 7, 5, what="test") == 7


class _Out(BaseModel):
    ok: bool


class _SlowStructuredModel:
    def invoke(self, messages, config=None):
        time.sleep(3)
        return _Out(ok=True)


class _Model:
    def bind(self, **kwargs):
        return self

    def with_structured_output(self, schema, method=None):
        return _SlowStructuredModel()


def test_timed_out_structured_call_degrades_to_no_result_not_a_fatal_error(monkeypatch):
    monkeypatch.setenv("AICALL_STRUCTURED_CALL_TIMEOUT_SECONDS", "0.2")
    ai = AICall(model="openai/x", api_key="sk-test", api_base="http://gw/v1")
    monkeypatch.setattr(ai, "_create_chat_model", lambda **kw: _Model())
    monkeypatch.setattr(ai, "_bind_session_metadata", lambda model, *a, **k: model)
    started = time.monotonic()
    parsed, raw = ai._call_native_structured("sys", "q", _Out, node_id="rca")
    assert parsed is None and raw == ""
    assert time.monotonic() - started < 2.5  # the blocked call itself takes 3s
    assert client_module._structured_call_timeout_seconds() == 0.2
