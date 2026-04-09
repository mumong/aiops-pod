# tests/unit/aicall/test_types.py
from app.core.aicall.types import AICallResult, ThinkingEvent


def test_aicall_result_defaults():
    r = AICallResult()
    assert r.result == ""
    assert r.tool_calls == []
    assert r.iterations == 0


def test_aicall_result_with_data():
    r = AICallResult(result="hello", tool_call_count=3, duration_ms=1500.0)
    assert r.result == "hello"
    assert r.tool_call_count == 3


def test_thinking_event():
    e = ThinkingEvent(type="tool_start", node="layer", data={"tool_name": "kubectl"})
    assert e.type == "tool_start"
    assert e.node == "layer"
