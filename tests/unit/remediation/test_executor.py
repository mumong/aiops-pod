from app.core.remediation.approval import ApprovalStore
from app.core.remediation.executor import RemediationExecutor
from app.core.remediation.plans import extract_remediation_plan


def _plan():
    return extract_remediation_plan(
        """
```json
{
  "remediation_available": true,
  "fix_type": "create_missing_configmap",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["ConfigMap missing"],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_apply",
      "description": "创建缺失 ConfigMap",
      "risk": "medium",
      "dry_run_command": "kubectl apply --dry-run=server -f /tmp/cm.yaml",
      "execute_command": "kubectl apply -f /tmp/cm.yaml",
      "verify_command": "kubectl get configmap missing -n aiops-e2e"
    }
  ]
}
```
"""
    )


def test_executor_stops_when_plan_rejected():
    store = ApprovalStore()
    executor = RemediationExecutor(approval_store=store, command_runner=lambda command: "unused")
    events = executor.run(run_id="run1", plan=_plan(), approval_timeout_seconds=0.01)

    first = next(events)
    assert first["type"] == "remediation_approval_required"
    store.resolve("run1", first["approval_id"], approved=False, reviewer="tester")

    remaining = list(events)
    assert remaining[-1]["type"] == "remediation_finished"
    assert remaining[-1]["status"] == "rejected"


def test_executor_requires_action_approval_and_runs_dry_run_execute_verify():
    calls = []

    def runner(command):
        calls.append(command)
        return f"ok: {command}"

    store = ApprovalStore()
    executor = RemediationExecutor(approval_store=store, command_runner=runner)
    events = executor.run(run_id="run1", plan=_plan(), approval_timeout_seconds=1)

    plan_approval = next(events)
    store.resolve("run1", plan_approval["approval_id"], approved=True, reviewer="tester")

    action_approval = next(events)
    assert action_approval["type"] == "remediation_approval_required"
    assert action_approval["approval_kind"] == "action"
    store.resolve("run1", action_approval["approval_id"], approved=True, reviewer="tester")

    remaining = list(events)

    assert calls == [
        "kubectl apply --dry-run=server -f /tmp/cm.yaml",
        "kubectl apply -f /tmp/cm.yaml",
        "kubectl get configmap missing -n aiops-e2e",
    ]
    assert [event["type"] for event in remaining] == [
        "remediation_tool_result",
        "remediation_tool_result",
        "remediation_tool_result",
        "remediation_finished",
    ]
    assert remaining[-1]["status"] == "success"


def test_executor_auto_mode_runs_without_approval():
    calls = []

    def runner(command):
        calls.append(command)
        return "ok"

    executor = RemediationExecutor(approval_store=ApprovalStore(), command_runner=runner)

    events = list(executor.run(run_id="run1", plan=_plan(), approval_mode="auto"))

    assert calls == [
        "kubectl apply --dry-run=server -f /tmp/cm.yaml",
        "kubectl apply -f /tmp/cm.yaml",
        "kubectl get configmap missing -n aiops-e2e",
    ]
    assert all(event["type"] != "remediation_approval_required" for event in events)
    assert events[-1]["status"] == "success"


def test_executor_marks_unhealthy_verify_as_needs_followup():
    def runner(command):
        if command.startswith("kubectl get"):
            return "memhog-8c5ddbd59-mxb8x 0/1 CrashLoopBackOff OOMKilled"
        return "ok"

    executor = RemediationExecutor(approval_store=ApprovalStore(), command_runner=runner)

    events = list(executor.run(run_id="run1", plan=_plan(), approval_mode="auto"))

    assert events[-1]["type"] == "remediation_finished"
    assert events[-1]["status"] == "needs_followup"
    assert "OOMKilled" in events[-1]["reason"]
