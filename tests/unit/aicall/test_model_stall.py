"""A silent model stream must fail fast as a model stall, not look like a stuck workflow."""
import asyncio
from types import SimpleNamespace

import pytest

from app.core.aicall.client import AICall, _STREAM_END
from app.core.aicall.errors import ModelStreamInterrupted, ModelStreamStalled, model_error_code


class _Stream:
    def __init__(self, items, then_sleep=30.0):
        self._items = list(items)
        self._then_sleep = then_sleep
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._items:
            return self._items.pop(0)
        await asyncio.sleep(self._then_sleep)
        raise StopAsyncIteration

    async def aclose(self):
        self.closed = True


def test_silence_while_waiting_on_model_raises_stall():
    run = SimpleNamespace(pending_tool_calls=0, node_id="query_collect", iteration=2)
    stream = _Stream(["chunk"])

    async def main():
        assert await AICall._next_stream_chunk(stream, run, 0.2) == "chunk"
        with pytest.raises(ModelStreamStalled) as info:
            await AICall._next_stream_chunk(stream, run, 0.2)
        return info.value

    err = asyncio.run(main())
    assert isinstance(err, ModelStreamInterrupted)  # fatal: never a partial success
    assert "模型服务停滞" in str(err) and "不是诊断流程卡住" in str(err)
    assert model_error_code(err) == "model_stalled"


def test_no_idle_limit_while_tools_are_running_or_when_disabled():
    stream = _Stream([], then_sleep=0.4)

    async def main(pending, limit):
        run = SimpleNamespace(pending_tool_calls=pending, node_id="n", iteration=1)
        return await AICall._next_stream_chunk(stream, run, limit)

    assert asyncio.run(main(pending=1, limit=0.1)) is _STREAM_END
    assert asyncio.run(main(pending=0, limit=0)) is _STREAM_END


def test_executor_error_event_reports_model_stall():
    from app.core.workflow.executor import WorkflowExecutor
    from app.core.workflow.graph import build_diagnosis_workflow
    from tests.unit.workflow.test_executor_timing import _DummyHolmesService

    graph, nodes = build_diagnosis_workflow(query_mode="auto")
    for node in nodes:
        def execute(state, name=node.node_id):
            if name == "request_router":
                return {"request_route": "focused"}
            raise ModelStreamStalled(180)
        node.execute = execute

    import app.core.workflow.executor as executor_module
    original = executor_module.build_diagnosis_workflow
    executor_module.build_diagnosis_workflow = lambda *a, **k: (graph, nodes)
    try:
        events = list(WorkflowExecutor(holmes_service=_DummyHolmesService()).execute_stream("q"))
    finally:
        executor_module.build_diagnosis_workflow = original
    errors = [e for e in events if e["type"] == "error"]
    assert len(errors) == 1 and not any(e["type"] == "final" for e in events)
    assert errors[0]["error_code"] == "model_stalled"
    assert "模型服务停滞" in errors[0]["error"]


def test_stall_is_reported_even_if_the_stream_is_slow_to_cancel():
    import time

    class _SlowCancelStream(_Stream):
        async def __anext__(self):
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                await asyncio.sleep(3)  # cleanup waiting on an in-flight request
                raise

    run = SimpleNamespace(pending_tool_calls=0, node_id="layer", iteration=8)

    async def main():
        started = time.monotonic()
        with pytest.raises(ModelStreamStalled):
            await AICall._next_stream_chunk(_SlowCancelStream([]), run, 0.2)
        return time.monotonic() - started

    assert asyncio.run(main()) < 1.5


def test_stall_error_names_what_the_agent_was_waiting_on():
    run = SimpleNamespace(pending_tool_calls=0, node_id="layer", iteration=5,
                          waiting_on="本节点第 6 次模型请求（已发出，输入约 25096 tokens）")

    async def main():
        with pytest.raises(ModelStreamStalled) as info:
            await AICall._next_stream_chunk(_Stream([]), run, 0.1)
        return info.value

    err = asyncio.run(main())
    assert "第 6 次模型请求" in str(err) and "25096" in str(err)
    assert err.waiting_on.startswith("本节点第 6 次")
    compaction = ModelStreamStalled(180, waiting_on="上下文压缩（内部摘要模型调用，压缩早期工作历史）")
    assert "上下文压缩" in str(compaction) and model_error_code(compaction) == "model_stalled"
