import json

from app.core.workflow.diagnosis_state import (
    DiagnosisSubmission,
    EvidenceSlotDiagnosisSubmission,
    LaneDiagnosisState,
    authoritative_entity_ids_from_ledgers,
    bind_evidence_slots,
)
from app.core.workflow.fact_contract import _canonical_fact_id


def _ledger(
    *,
    namespace: str,
    pod: str,
    uid: str,
    dimension: str,
    fact_type: str,
    attribute: str,
    value: object,
    source_system: str,
) -> tuple[dict, str]:
    entity_id = f"k8s.pod:{namespace}/{pod}:{uid}"
    record = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": namespace,
        "entity_name": pod,
        "dimension": dimension,
        "fact_type": fact_type,
        "attribute": attribute,
        "value": value,
        "source_system": source_system,
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": [f"archive://{dimension}/{attribute}"],
    }
    record["fact_id"] = _canonical_fact_id(record)
    return {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": f"{dimension}-{attribute}",
        "scope_entity_ids": [entity_id],
        "records": [record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }, record["fact_id"]


def _group_state(ledger: dict, *, tool: str, dimension: str) -> dict:
    return {
        "evidence_analysis": json.dumps({
            "collection_summary": f"collected {dimension}",
            "tool_data": [{
                "tool": tool,
                "status": "success",
                "semantic_success": True,
                "fact_ledger": ledger,
            }],
        }),
        "thinking_events": [{
            "type": "tool_result",
            "tool_name": tool,
            "tool_args": {"namespace": "demo", "pod": "api"},
            "status": "success",
            "semantic_success": True,
            "result": f"source-backed {dimension}",
            "structured": {
                "dimension": dimension,
                "coverage": "present",
                "fact_ledger": ledger,
            },
        }],
    }


def test_authoritative_entity_scope_prefers_one_source_backed_pod_uid():
    ledger, _fact_id = _ledger(
        namespace="demo",
        pod="api",
        uid="uid-current",
        dimension="kubernetes",
        fact_type="event",
        attribute="event.reason",
        value="Failed",
        source_system="kubernetes",
    )
    ledger["scope_entity_ids"] = ["k8s.pod:demo/api"]

    assert authoritative_entity_ids_from_ledgers([ledger]) == [
        "k8s.pod:demo/api:uid-current"
    ]


def test_authoritative_entity_scope_keeps_name_only_when_uid_is_ambiguous():
    first, _fact_id = _ledger(
        namespace="demo",
        pod="api",
        uid="uid-old",
        dimension="kubernetes",
        fact_type="event",
        attribute="event.reason",
        value="Failed",
        source_system="kubernetes",
    )
    second, _fact_id = _ledger(
        namespace="demo",
        pod="api",
        uid="uid-current",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value="failed",
        source_system="elasticsearch",
    )
    first["scope_entity_ids"] = ["k8s.pod:demo/api"]
    second["scope_entity_ids"] = ["k8s.pod:demo/api"]

    assert authoritative_entity_ids_from_ledgers([first, second]) == [
        "k8s.pod:demo/api"
    ]


def test_lane_diagnosis_state_preserves_first_attempt_facts_on_retry():
    metrics_ledger, metrics_fact = _ledger(
        namespace="demo",
        pod="api",
        uid="uid-api",
        dimension="metrics",
        fact_type="measurement",
        attribute="memory.current_bytes",
        value=734003200,
        source_system="prometheus",
    )
    logs_ledger, logs_fact = _ledger(
        namespace="demo",
        pod="api",
        uid="uid-api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value="allocator failed after memory limit was reached",
        source_system="elasticsearch",
    )
    state = LaneDiagnosisState(
        group_id="g1",
        entities=[{
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-api",
        }],
        status_keywords=["Restarting"],
    )

    state.record_attempt(
        attempt=1,
        group_state=_group_state(
            metrics_ledger,
            tool="execute_pod_promql",
            dimension="metrics",
        ),
        submission=None,
        collector_archive_run_id="run-g1",
    )
    state.record_attempt(
        attempt=2,
        group_state=_group_state(
            logs_ledger,
            tool="query_pod_logs",
            dimension="logging",
        ),
        submission=DiagnosisSubmission(
            diagnostic_status="diagnosed",
            phenomenon="container restarts",
            root_cause="process allocation failed at the configured memory boundary",
            causal_chain=[
                "memory boundary reached",
                "allocation failed",
                "container restarted",
            ],
            supporting_fact_ids=[logs_fact],
            confidence=0.9,
            confidence_reason="direct source-backed failure log",
        ),
        collector_archive_run_id="run-g1-retry2",
    )

    snapshot = state.snapshot_handoff
    assert set(snapshot["fact_index"]) == {metrics_fact, logs_fact}
    assert state.attempt_count == 2
    assert len(state.tool_events) == 2
    assert state.selected_rca["diagnostic_status"] == "diagnosed"
    assert state.selected_rca["claim_validation"]["diagnosis_supported"] is True
    assert state.selected_rca["supporting_fact_ids"] == [logs_fact]


def test_lane_diagnosis_state_rejects_unknown_fact_reference_without_guessing():
    ledger, _fact_id = _ledger(
        namespace="demo",
        pod="api",
        uid="uid-api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value="source-backed failure",
        source_system="elasticsearch",
    )
    state = LaneDiagnosisState(
        group_id="g1",
        entities=[{
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-api",
        }],
    )

    state.record_attempt(
        attempt=1,
        group_state=_group_state(
            ledger,
            tool="query_pod_logs",
            dimension="logging",
        ),
        submission=DiagnosisSubmission(
            diagnostic_status="diagnosed",
            phenomenon="Pod failed",
            root_cause="invented claim",
            supporting_fact_ids=["fact-unknown0001"],
            confidence=0.9,
            confidence_reason="model claim",
        ),
    )

    assert state.selected_rca["diagnostic_status"] == "inconclusive"
    assert state.selected_rca["supporting_fact_ids"] == []
    assert "fact-unknown0001" in state.selected_rca["claim_validation"][
        "invalid_fact_ids"
    ]


def test_evidence_slots_are_bound_to_authoritative_fact_ids_in_code():
    submission = EvidenceSlotDiagnosisSubmission(
        diagnostic_status="diagnosed",
        phenomenon="Pod restarts",
        root_cause="memory boundary was exceeded",
        causal_chain=["memory boundary", "OOM kill", "Pod restart"],
        supporting_evidence_slots=[2, 1, 2],
        contradicting_evidence_slots=[3],
        confidence="高",
    )

    bound = bind_evidence_slots(
        submission,
        slot_fact_ids=["fact-oom", "fact-limit", "fact-negative"],
    )

    assert bound.supporting_fact_ids == ["fact-limit", "fact-oom"]
    assert bound.contradicting_fact_ids == ["fact-negative"]
    assert bound.confidence == 0.9


def test_evidence_slot_binding_rejects_out_of_catalogue_reference():
    submission = EvidenceSlotDiagnosisSubmission(
        diagnostic_status="diagnosed",
        supporting_evidence_slots=[4],
    )

    try:
        bind_evidence_slots(submission, slot_fact_ids=["fact-only"])
    except ValueError as exc:
        assert "outside catalogue" in str(exc)
    else:
        raise AssertionError("out-of-range evidence slot must fail closed")
