import queue

from app.core.workflow.nodes.parallel_evidence import _ScopedParallelEventQueue
from app.core.workflow.stream_contract import (
    build_parallel_evidence_stream_context,
    project_parallel_tool_event,
)


GROUP_ENTITIES = [
    {
        "kind": "Pod",
        "namespace": "aiops-case-09",
        "name": "workload-5f4fb9ff45-nmqpr",
    }
]


def _parallel_context():
    return {"group_id": "g3", "entities": GROUP_ENTITIES}


def test_scoped_parallel_queue_attaches_authoritative_group_context_without_mutating_input():
    target = queue.Queue()
    scoped = _ScopedParallelEventQueue(
        target,
        group_id="g3",
        entities=GROUP_ENTITIES,
    )
    original = {
        "type": "tool_start",
        "tool_name": "kubectl_events",
        "tool_call_id": "call-events",
    }

    scoped.put_nowait(("thinking", original))

    tag, event = target.get_nowait()
    assert tag == "thinking"
    assert event["parallel_context"] == _parallel_context()
    assert "parallel_context" not in original


def test_scoped_parallel_queue_uses_outer_lifecycle_node_and_preserves_lane_stage():
    target = queue.Queue()
    scoped = _ScopedParallelEventQueue(
        target,
        group_id="g3",
        entities=GROUP_ENTITIES,
    )
    original = {
        "type": "ai_message",
        "node": "rca",
        "content": "lane analysis",
    }

    scoped.put_nowait(("thinking", original))

    tag, event = target.get_nowait()
    assert tag == "thinking"
    assert event["node"] == "parallel_evidence"
    assert event["lane_stage"] == "rca"
    assert event["parallel_context"] == _parallel_context()
    assert original == {
        "type": "ai_message",
        "node": "rca",
        "content": "lane analysis",
    }


def test_parallel_sse_projection_exposes_lane_stage_without_outer_node_override():
    projected = project_parallel_tool_event({
        "type": "ai_message",
        "node": "parallel_evidence",
        "lane_stage": "rca",
        "parallel_context": _parallel_context(),
    })

    assert projected == {"lane_stage": "rca"}


def test_stream_context_uses_exact_group_entity_from_tool_arguments():
    context = build_parallel_evidence_stream_context({
        "parallel_context": _parallel_context(),
        "tool_name": "kubectl_previous_logs",
        "tool_args": {
            "namespace": "aiops-case-09",
            "pod_name": "workload-5f4fb9ff45-nmqpr",
        },
    })

    assert context == {
        "contract_version": "aiops.parallel-evidence-stream.v1",
        "group_id": "g3",
        "entity": GROUP_ENTITIES[0],
        "dimension": "kubernetes",
    }


def test_stream_context_matches_pod_even_when_it_is_not_the_first_group_entity():
    pod = {
        "kind": "Pod",
        "namespace": "aiops-case-09",
        "name": "workload-5f4fb9ff45-nmqpr",
    }
    context = build_parallel_evidence_stream_context({
        "parallel_context": {
            "group_id": "g3",
            "entities": [
                {
                    "kind": "Service",
                    "namespace": "aiops-case-09",
                    "name": "workload",
                },
                pod,
            ],
        },
        "tool_name": "kubectl_previous_logs",
        "tool_args": {
            "namespace": "aiops-case-09",
            "pod_name": "workload-5f4fb9ff45-nmqpr",
        },
    })

    assert context["entity"] == pod


def test_stream_context_keeps_group_only_when_tool_has_no_unique_pod():
    context = build_parallel_evidence_stream_context({
        "parallel_context": _parallel_context(),
        "tool_name": "fetch_runbook",
        "tool_args": {"runbook_id": "pod-notready-probe-failed.md"},
    })

    assert context == {
        "contract_version": "aiops.parallel-evidence-stream.v1",
        "group_id": "g3",
        "dimension": "other",
    }
    assert "entity" not in context


def test_stream_context_rejects_tool_entity_outside_scoped_group():
    context = build_parallel_evidence_stream_context({
        "parallel_context": _parallel_context(),
        "tool_name": "query_pod_logs",
        "tool_args": {
            "namespace": "other-namespace",
            "pod": "other-pod",
        },
        "structured": {
            "dimension": "logging",
            "source_system": "elasticsearch",
        },
    })

    assert context == {
        "contract_version": "aiops.parallel-evidence-stream.v1",
        "group_id": "g3",
        "dimension": "logging",
        "source_system": "elasticsearch",
    }
    assert "entity" not in context


def test_parallel_result_projection_preserves_full_summary_and_failure_semantics():
    internal = {
        "type": "tool_result",
        "tool_name": "kubectl_previous_logs",
        "tool_call_id": "call-previous",
        "tool_sequence": 2,
        "status": "success",
        "semantic_success": False,
        "result_preview": "Command failed (exit 1)",
        "result": "Command failed (exit 1):\nfull processed result after the preview boundary",
        "raw_ref": "/tmp/archive/raw.txt",
        "structured_ref": "/tmp/archive/structured.json",
        "summary_ref": "/tmp/archive/summary.txt",
        "parallel_context": _parallel_context(),
        "tool_args": {
            "namespace": "aiops-case-09",
            "pod_name": "workload-5f4fb9ff45-nmqpr",
        },
    }

    projected = project_parallel_tool_event(internal)

    assert projected["tool_call_id"] == "call-previous"
    assert projected["tool_sequence"] == 2
    assert projected["semantic_success"] is False
    assert projected["result"] == internal["result"]
    assert projected["raw_ref"] == internal["raw_ref"]
    assert projected["structured_ref"] == internal["structured_ref"]
    assert projected["summary_ref"] == internal["summary_ref"]
    assert projected["evidence_context"]["group_id"] == "g3"
    assert projected["evidence_context"]["entity"] == GROUP_ENTITIES[0]


def test_non_parallel_projection_does_not_expand_existing_sse_payload():
    projected = project_parallel_tool_event({
        "type": "tool_result",
        "tool_name": "kubectl_previous_logs",
        "tool_call_id": "ordinary-call",
        "result": "large ordinary result",
        "semantic_success": False,
    })

    assert projected == {}
