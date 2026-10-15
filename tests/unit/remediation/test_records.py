import json

import pytest

from app.core.remediation.approval import ApprovalStore
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.records import (
    PlanConflict,
    RecordUnavailable,
    RepairRecordStore,
    diagnosis_payload,
)
from tests.unit.remediation.test_pod_executor import fixture


def test_record_survives_new_store_and_is_owner_bound(tmp_path):
    store = RepairRecordStore(tmp_path)
    record = store.save("diagnosis-1", "alice", "session", "diagnosis", {"report": "evidence"})
    assert "owner" not in record
    restored = RepairRecordStore(tmp_path)
    assert restored.load("diagnosis-1", "alice")["payload"]["report"] == "evidence"
    assert restored.latest("alice", "session")["run_id"] == "diagnosis-1"
    with pytest.raises(RecordUnavailable):
        restored.load("diagnosis-1", "bob")
    with pytest.raises(RecordUnavailable):
        restored.load("../outside", "alice")
    with pytest.raises(RecordUnavailable):
        restored.load("diagnosis-1", "alice", "plan")
    with pytest.raises(PlanConflict):
        restored.save("diagnosis-1", "alice", "session", "diagnosis", {})


def test_supersession_and_execution_claim_are_mutually_exclusive(tmp_path):
    store = RepairRecordStore(tmp_path)
    store.save("p", "alice", "s", "plan", {})
    store.transition("p", "alice", "awaiting_approval")
    old = store.supersede("p", "alice")
    assert old["execution_status"] == "awaiting_approval"
    assert not store.transition("p", "alice", "executing")
    assert not store.current("p", "alice")
    store.save("p2", "alice", "s", "plan", {}, previous_plan_id="p")
    store.transition("p2", "alice", "executing")
    with pytest.raises(PlanConflict):
        store.supersede("p2", "alice")


def test_superseded_approval_never_runs_command(tmp_path):
    draft, _, _, _ = fixture()
    store = RepairRecordStore(tmp_path)
    store.save("plan", "alice", "s", "plan", {"draft": draft})
    approvals = ApprovalStore()
    calls = []
    executor = PodRepairExecutor(approvals, lambda args: calls.append(args) or "ok")
    stream = executor.run("plan", draft, owner="alice", record_store=store)
    first = next(stream)
    assert first["type"] == "remediation_approval_required"
    store.supersede("plan", "alice")
    approvals.resolve("plan", first["approval_id"], True, owner="alice")
    events = list(stream)
    assert events[-1]["status"] == "superseded"
    assert calls == []


def test_auto_execution_stores_exact_commands_and_results(tmp_path):
    draft, _, _, _ = fixture()
    store = RepairRecordStore(tmp_path)
    store.save("plan", "alice", "s", "plan", {"draft": draft})
    calls = []
    stream = PodRepairExecutor(ApprovalStore(), lambda args: calls.append(args) or "observed").run(
        "plan", draft, owner="alice", mode="auto", record_store=store
    )
    events = list(stream)
    assert calls
    assert not any(e["type"] == "remediation_approval_required" for e in events)
    record = store.load("plan", "alice")
    assert record["execution_status"] == "needs_followup"
    assert any(
        e.get("command") == draft["actions"][0]["execute_command"]
        for e in record["execution_events"]
    )


def test_evidence_projection_preserves_actual_body_and_ownership_with_budget():
    state = {
        "question": "diagnose",
        "conclusion": "report",
        "autonomous_group_results": [
            {"group_id": "g1", "target": {"name": "one"}, "material": {}},
            {"group_id": "g2", "target": {"name": "two"}, "material": {}},
        ],
        "thinking_events": [
            {
                "type": "tool_result",
                "tool_name": "generic",
                "lane_id": "g1",
                "raw_ref": "/raw/1",
                "result": "A" * 6000,
            },
            {
                "type": "tool_result",
                "tool_name": "generic",
                "lane_id": "g2",
                "raw_ref": "/raw/2",
                "result": "B" * 6000,
            },
            {
                "type": "tool_result",
                "tool_name": "fetch_runbook",
                "raw_ref": "/book",
                "result": "BOOK",
            },
        ],
    }
    result = diagnosis_payload(state, evidence_chars=5000)
    records = [e for g in result["groups"] for e in g["evidence"]]
    assert sum(len(e["result_excerpt"]) for e in records) == 5000
    assert result["groups"][1]["evidence"][0]["result_excerpt"] == "B" * 1000
    assert all(e["excerpt_truncated"] for e in records)
    assert result["shared_evidence"]["evidence"][0]["raw_ref"] == "/book"
    assert "BOOK" not in json.dumps(result)
