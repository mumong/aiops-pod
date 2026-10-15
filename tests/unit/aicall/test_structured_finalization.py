"""Bounded protocol recovery: one tool-free structured delivery after the agent stops early."""
import threading
from types import SimpleNamespace

from pydantic import BaseModel

from app.core.aicall.client import AICall
from app.core.aicall.errors import ModelStreamInterrupted


class _Out(BaseModel):
    targets: list


def _run(**overrides):
    base = dict(
        response_schema=_Out, structured_response=None, incomplete_reason="step_limit",
        cancel_event=None, node_id="layer", run_id="r1", stream_queue=None, thinking_events=[],
        emitted_ai_messages=[(None, "<think>private reasoning</think>发现 4 个异常 Pod")],
        tool_observation_contents=["query_pod_lifecycle: 72 pods, 4 abnormal"],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _ai(calls, result):
    ai = AICall(model="openai/x", api_key="sk-test", api_base="http://gw/v1")

    def fake_call_structured(system_prompt, question, schema, **kwargs):
        calls.append({"system": system_prompt, "question": question, "schema": schema, **kwargs})
        return result, ""

    ai.call_structured = fake_call_structured
    return ai


def test_step_limit_triggers_one_tool_free_structured_delivery_from_own_material():
    calls = []
    run = _run()
    _ai(calls, _Out(targets=["a", "b"]))._finalize_structured_delivery(run, system_prompt="SYS", question="Q")

    assert len(calls) == 1
    call = calls[0]
    assert call["system"] == "SYS" and call["schema"] is _Out and call["internal_model"] is True
    assert call["question"].startswith("Q")
    assert "query_pod_lifecycle: 72 pods, 4 abnormal" in call["question"]
    assert "发现 4 个异常 Pod" in call["question"]
    assert "private reasoning" not in call["question"]  # reasoning blocks are not results
    assert "不要再调用任何工具" in call["question"]
    assert run.structured_response == _Out(targets=["a", "b"])
    assert run.thinking_events[-1]["type"] == "structured_finalization"
    assert run.thinking_events[-1]["status"] == "success"


def test_failed_finalization_keeps_existing_invalid_delivery_path():
    run = _run()
    _ai([], None)._finalize_structured_delivery(run, system_prompt="SYS", question="Q")
    assert run.structured_response is None
    assert run.thinking_events[-1]["status"] == "failed"


def test_not_triggered_when_delivered_cancelled_unstructured_or_completed():
    for overrides in (
        {"structured_response": _Out(targets=[])},
        {"cancel_event": (lambda e: (e.set(), e)[1])(threading.Event())},
        {"response_schema": None},
        {"incomplete_reason": ""},
        {"emitted_ai_messages": [], "tool_observation_contents": []},
    ):
        calls = []
        _ai(calls, _Out(targets=["x"]))._finalize_structured_delivery(_run(**overrides), system_prompt="S", question="Q")
        assert calls == [], overrides


def test_model_transport_failure_during_finalization_stays_fatal():
    ai = AICall(model="openai/x", api_key="sk-test", api_base="http://gw/v1")

    def boom(*a, **k):
        raise ModelStreamInterrupted("LLM API 服务连接中断")

    ai.call_structured = boom
    try:
        ai._finalize_structured_delivery(_run(), system_prompt="S", question="Q")
    except ModelStreamInterrupted:
        pass
    else:
        raise AssertionError("transport failure must propagate")


def test_oversized_material_is_compacted_once_then_delivered(monkeypatch):
    from app.core.aicall.client import StructuredContextBudgetError
    import app.core.aicall.working_context as working_context

    calls, compacted_inputs = [], []
    ai = AICall(model="openai/x", api_key="sk-test", api_base="http://gw/v1")

    def fake_call_structured(system_prompt, question, schema, **kwargs):
        calls.append(question)
        if len(calls) == 1:
            raise StructuredContextBudgetError("working_context_compaction_required")
        return _Out(targets=["t1"]), ""

    async def fake_compact(model, material, progress=None, **kwargs):
        compacted_inputs.append(material)
        return {"question": material["question"], "working_summary": "4 个异常 Pod 摘要", "observations": []}

    ai.call_structured = fake_call_structured
    ai.create_compaction_model = lambda **kw: object()
    monkeypatch.setattr(working_context, "compact_working_material", fake_compact)
    run = _run()
    ai._finalize_structured_delivery(run, system_prompt="S", question="Q")

    assert len(calls) == 2 and "4 个异常 Pod 摘要" in calls[1]
    assert compacted_inputs[0]["observations"][0]["result"].startswith("query_pod_lifecycle")
    assert run.structured_response == _Out(targets=["t1"])
