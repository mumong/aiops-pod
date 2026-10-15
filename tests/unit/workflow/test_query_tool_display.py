from app.core.prompts import QUERY_COLLECT_PROMPT, QUERY_CONCLUSION_PROMPT
from app.core.workflow.nodes import query_answer
from app.core.workflow.stream_contract import project_query_tool_event


def test_prompts_have_single_source():
    assert query_answer.QUERY_COLLECT_PROMPT is QUERY_COLLECT_PROMPT
    assert query_answer.QUERY_CONCLUSION_PROMPT is QUERY_CONCLUSION_PROMPT


def test_empty_result_and_call_identity_survive_projection():
    event = {
        "type": "tool_result",
        "tool_call_id": "cpu-1",
        "tool_args": {"promql": "rate(cpu[5m])"},
        "result": '{"coverage":"empty","facts":[]}',
        "raw_ref": "/archive/raw",
    }
    projected = project_query_tool_event(event)
    assert projected["tool_call_id"] == "cpu-1"
    assert projected["tool_args"] == event["tool_args"]
    assert projected["tool_display"]["coverage"] == "empty"
    assert projected["tool_display"]["measurements"] == []


def test_display_limit_does_not_modify_observation():
    event = {"type": "tool_result", "result": "a" * 15000}
    projected = project_query_tool_event(event)
    assert projected["tool_display"]["result_excerpt_truncated"]
    assert len(projected["tool_display"]["result_excerpt"]) == 12000
    assert len(event["result"]) == 15000
