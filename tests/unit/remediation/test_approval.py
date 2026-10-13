import threading
import time

from app.core.remediation.approval import ApprovalStore


def test_approval_store_approves_request():
    store = ApprovalStore()
    request = store.create_request(
        run_id="run1",
        kind="action",
        title="执行 kubectl patch",
        payload={"action_id": "a1"},
    )

    assert store.resolve("run1", request.approval_id, approved=True, reviewer="tester")
    decision = store.wait_for_decision("run1", request.approval_id, timeout_seconds=0.1)

    assert decision is not None
    assert decision.approved is True
    assert decision.reviewer == "tester"


def test_approval_store_waits_until_rejected():
    store = ApprovalStore()
    request = store.create_request("run1", "plan", "认可修复方案", {"plan": "x"})

    def reject_later():
        time.sleep(0.05)
        store.resolve("run1", request.approval_id, approved=False, reviewer="tester", reason="不认可")

    thread = threading.Thread(target=reject_later)
    thread.start()
    decision = store.wait_for_decision("run1", request.approval_id, timeout_seconds=1)
    thread.join()

    assert decision is not None
    assert decision.approved is False
    assert decision.reason == "不认可"


def test_approval_store_returns_none_on_timeout():
    store = ApprovalStore()
    request = store.create_request("run1", "action", "执行", {})

    assert store.wait_for_decision("run1", request.approval_id, timeout_seconds=0.01) is None
    assert not store.resolve("run1", request.approval_id, approved=True)


def test_approval_decision_is_single_use_and_cannot_be_overwritten():
    store = ApprovalStore()
    request = store.create_request("run1", "action", "execute", {})
    assert store.resolve("run1", request.approval_id, approved=False)
    assert not store.resolve("run1", request.approval_id, approved=True)
    assert store.wait_for_decision("run1", request.approval_id, 1).approved is False
    assert store.wait_for_decision("run1", request.approval_id, 1) is None


def test_unknown_approval_does_not_wait():
    assert ApprovalStore().wait_for_decision("missing", "missing", 600) is None


def test_expiry_starts_at_creation_not_when_wait_begins(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("app.core.remediation.approval.time.time", lambda: clock[0])
    store = ApprovalStore()
    request = store.create_request("run", "action", "execute", {}, timeout_seconds=5)
    assert request.expires_at == 105
    clock[0] = 106
    assert not store.resolve("run", request.approval_id, True)
    assert store.wait_for_decision("run", request.approval_id, 600) is None


def test_approval_payload_is_snapshot():
    payload = {"actions": [{"execute_command": "safe"}]}
    request = ApprovalStore().create_request("run", "action", "execute", payload)
    payload["actions"][0]["execute_command"] = "changed"
    assert request.payload["actions"][0]["execute_command"] == "safe"


def test_decision_status_does_not_consume_and_is_owner_bound():
    store = ApprovalStore()
    request = store.create_request('run', 'action', 'test', {}, owner='owner')
    assert store.decision_status('run', request.approval_id, 'other') == 'unavailable'
    assert store.decision_status('run', request.approval_id, 'owner') == 'pending'
    assert store.resolve('run', request.approval_id, True, owner='owner')
    for _ in range(3):
        assert store.decision_status('run', request.approval_id, 'owner') == 'approved'
    assert store.poll_decision('run', request.approval_id).approved
    assert store.poll_decision('run', request.approval_id) is None
    assert store.decision_status('run', request.approval_id, 'owner') == 'approved'
