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
