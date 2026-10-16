"""Finalization material names the tool and arguments behind every observation.

Live run 66662a8287ce4dac: two Prometheus vectors (CPU and memory) reached the
tool-free delivery as bare result bodies; the model guessed which was which and
swapped the columns. The call identity is known at observation time and must
travel with the result.
"""

from types import SimpleNamespace

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import OutputBudget


def _ai():
    return AICall(
        model="openai/x",
        api_key="k",
        api_base="http://gw/v1",
        output_budget=OutputBudget(agent=4000, delivery=10000, compaction=3000, retry_multiplier=2),
    )


def test_observation_carries_tool_name_and_args_before_result():
    run = SimpleNamespace(
        emitted_ai_messages=[],
        tool_observation_contents=['{"data": {"result": [["1", "21.4"]]}}', '{"data": {"result": [["1", "43.1"]]}}'],
        tool_observation_calls=[
            {"tool": "execute_prometheus_instant_query", "args": {"query": "cpu_expr"}},
            {"tool": "execute_prometheus_instant_query", "args": {"query": "mem_expr"}},
        ],
    )
    material = _ai()._run_material_for_finalization(run, "q")
    first, second = material["observations"]
    assert list(first) == ["order", "tool", "args", "result"]
    assert first["tool"] == "execute_prometheus_instant_query" and first["args"] == {"query": "cpu_expr"}
    assert second["args"] == {"query": "mem_expr"} and "43.1" in second["result"]


def test_observations_without_recorded_call_identity_still_deliver():
    run = SimpleNamespace(emitted_ai_messages=[], tool_observation_contents=["ok"], tool_observation_calls=[])
    material = _ai()._run_material_for_finalization(run, "q")
    assert material["observations"] == [{"order": 1, "result": "ok"}]
