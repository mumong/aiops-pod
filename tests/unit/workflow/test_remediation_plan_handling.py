from types import SimpleNamespace

from app.core.workflow.executor import WorkflowExecutor


def test_invalid_remediation_plan_yields_failure_event_and_run_end(monkeypatch):
    invalid_report = """
## 🧩 结构化修复计划
```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_resources",
  "risk_level": "low",
  "requires_human_approval": true,
  "basis": ["kubectl_get_yaml: resources.limits.memory: <unset>"],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_patch",
      "description": "设置内存限制",
      "risk": "low",
      "dry_run_command": "kubectl patch deployment <name> -n aiops-e2e --dry-run=server",
      "execute_command": "kubectl patch deployment <name> -n aiops-e2e",
      "verify_command": "kubectl get deployment <name> -n aiops-e2e"
    }
  ]
}
```
"""

    class _DummyWorkflow:
        def stream(self, initial_state):
            return iter(
                [
                    {
                        "conclusion": {
                            "layer": "L1",
                            "conclusion_formatted": invalid_report,
                        }
                    }
                ]
            )

    def _fake_build_workflow(*args, **kwargs):
        return _DummyWorkflow(), []

    monkeypatch.setattr("app.core.workflow.executor.build_diagnosis_workflow", _fake_build_workflow)

    executor = WorkflowExecutor(
        holmes_service=SimpleNamespace(
            workflow_config={
                "nodes": {"conclusion": True},
                "remediation": {
                    "enabled": True,
                    "executor": "react",
                    "mode": "review",
                },
            },
            merged_catalog=None,
        )
    )

    events = list(executor.execute_stream("我的集群有什么问题？", run_id="run-invalid-plan"))

    remediation_events = [event for event in events if event["type"] == "remediation_finished"]
    assert remediation_events
    assert remediation_events[-1]["status"] == "failed"
    assert "invalid remediation plan" in remediation_events[-1]["reason"]
    assert "unsafe remediation command" in remediation_events[-1]["reason"]
    assert events[-1]["type"] == "run_end"
