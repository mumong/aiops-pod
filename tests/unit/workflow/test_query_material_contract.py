"""Characterize material projection before separating it from graph nodes."""

from copy import deepcopy

from app.core.workflow.nodes.query_answer import build_working_material, parse_query_answer
from app.core.workflow.working_material import evidence_receipts


def test_latest_compaction_and_lane_boundaries_preserve_user_scope():
    # Arrange: parent and child observations intentionally share a tool name.
    state = {
        "question": "子任务",
        "original_question": "原始任务",
        "diagnosis_target": {"pod": "p1"},
        "request_time_utc": "2026-09-24T00:00:00Z",
        "query_session_context": {"turns": [{"answer": "old"}]},
        "thinking_events": [
            {"type": "tool_result", "tool_name": "kubectl_logs", "result": "old"},
            {
                "type": "context_compacted",
                "working_summary": "retained",
                "retained_messages": [{"type": "tool", "content": "recent"}],
            },
            {"type": "tool_result", "tool_name": "kubectl_logs", "result": "new"},
            {
                "type": "tool_result",
                "tool_name": "kubectl_logs",
                "lane_id": "g2",
                "result": "other-lane",
            },
            {"type": "execution_incomplete", "lane_id": "g2", "reason": "timeout"},
        ],
    }
    original = deepcopy(state)

    # Act.
    result = build_working_material(state)

    # Assert: no older raw content or sibling results are re-injected.
    assert result["question"] == "子任务"
    assert result["original_question"] == "原始任务"
    assert result["working_summary"] == "retained"
    assert result["recent_interactions"] == [{"type": "tool", "content": "recent"}]
    assert result["session_history"] is None
    assert [item["result"] for item in result["observations"]] == ["new"]
    assert result["execution_incomplete"] == ["g2: timeout"]
    assert state == original


def test_receipts_keep_outcome_and_lane_identity_without_mutating_events():
    # Arrange: only identical acquisition outcomes should replace their references.
    base = {
        "type": "tool_result",
        "tool_name": "execute_pod_promql",
        "tool_args": {"namespace": "ns", "pod": "pod"},
        "status": "success",
        "structured": {"coverage": "present"},
    }
    events = [
        {**base, "raw_ref": "old"},
        {**base, "raw_ref": "new"},
        {**base, "raw_ref": "failed", "status": "failed"},
        {**base, "raw_ref": "sibling", "lane_id": "g2"},
    ]
    original = deepcopy(events)

    # Act.
    result = evidence_receipts(events)

    # Assert: failure and sibling evidence must not overwrite the parent success.
    assert [item["raw_ref"] for item in result] == ["new", "failed", "sibling"]
    assert events == original


def test_invalid_or_ambiguous_answer_is_not_manufactured():
    # Arrange/Act: an answer string alone is not the structured response contract.
    result, repaired = parse_query_answer('{"answer":"hello"}')

    # Assert.
    assert result is None
    assert repaired is False
