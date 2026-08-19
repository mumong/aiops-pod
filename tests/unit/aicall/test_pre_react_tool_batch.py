import threading

from app.core.aicall.client import AICall


class _BarrierTool:
    def __init__(self, name: str, barrier: threading.Barrier):
        self.name = name
        self._barrier = barrier

    def invoke(self, args):
        self._barrier.wait(timeout=2)
        return {"tool": self.name, "pod": args["pod"], "value": "real"}


def test_pre_react_tool_batch_executes_in_parallel_and_keeps_request_order(
    monkeypatch,
):
    barrier = threading.Barrier(3)
    tools = [
        _BarrierTool(name, barrier)
        for name in ("metrics", "logging", "tracing")
    ]
    ai_call = AICall(model="openai/test", api_key="test")
    monkeypatch.setattr(
        ai_call,
        "_process_tool_observation",
        lambda **kwargs: {
            "summary": kwargs["tool_content"],
            "structured": {"source_backed": True},
            "semantic_success": True,
            "processed": True,
            "processor": "test",
        },
    )

    events = ai_call.execute_tool_batch(
        tool_requests=[
            {"tool_name": tool.name, "tool_args": {"pod": "api"}}
            for tool in tools
        ],
        tools=tools,
        node_id="evidence",
        run_id="run-baseline",
        max_workers=3,
    )

    results = [event for event in events if event["type"] == "tool_result"]
    assert [event["tool_name"] for event in results] == [
        "metrics",
        "logging",
        "tracing",
    ]
    assert all(event["status"] == "success" for event in results)
    assert all(event["structured"] == {"source_backed": True} for event in results)
