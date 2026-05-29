from types import SimpleNamespace

from app.core.service import HolmesService
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.nodes.base import WorkflowNode


class _PromptCaptureAI:
    model = "fake"
    api_base = ""
    api_key = ""

    def __init__(self):
        self.system_prompt = ""

    def call(self, **kwargs):
        self.system_prompt = kwargs["system_prompt"]
        return SimpleNamespace(result="ok", duration_ms=1, tool_call_count=0), []


class _PromptNode(WorkflowNode):
    node_id = "demo"
    node_name = "demo"

    def execute(self, state):
        return {}


def test_workflow_prompt_review_mode_allows_planning_write_actions(monkeypatch):
    monkeypatch.setenv("AUTO_REMEDIATE", "false")
    ai = _PromptCaptureAI()
    node = _PromptNode()
    node.ai_call = ai
    node.workflow_config_override = {
        "remediation": {
            "enabled": True,
            "mode": "review",
        }
    }

    node._call_llm("q", "system prompt")

    assert "禁止执行 kubectl apply/patch/delete/rollout/taint/scale" not in ai.system_prompt
    assert "人工审批" in ai.system_prompt
    assert "patch" in ai.system_prompt


def test_workflow_prompt_does_not_read_auto_remediate_env(monkeypatch):
    monkeypatch.setenv("AUTO_REMEDIATE", "true")
    ai = _PromptCaptureAI()
    node = _PromptNode()
    node.ai_call = ai
    node.workflow_config_override = {
        "remediation": {
            "enabled": True,
            "mode": "review",
        }
    }

    node._call_llm("q", "system prompt")

    assert "修复操作已授权" not in ai.system_prompt
    assert "人工审批" in ai.system_prompt


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
    assert remediation_events[-1]["status"] == "invalid_plan"
    assert "invalid remediation plan" in remediation_events[-1]["reason"]
    assert "unsafe remediation command" in remediation_events[-1]["reason"]
    assert events[-1]["type"] == "run_end"


def test_repair_advice_with_empty_structured_actions_yields_invalid_plan(monkeypatch):
    report = """
## 修复建议
确认 Pod 当前仍存在且 finalizers 非空后执行：
```bash
kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["deletionTimestamp exists", "finalizers: aiops.e2e/hold"],
  "actions": []
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
                            "conclusion_formatted": report,
                        }
                    }
                ]
            )

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda *args, **kwargs: (_DummyWorkflow(), []),
    )

    executor = WorkflowExecutor(
        holmes_service=SimpleNamespace(
            workflow_config={
                "nodes": {"conclusion": True},
                "remediation": {
                    "enabled": True,
                    "executor": "react",
                    "mode": "review",
                    "approval_timeout_seconds": 1,
                },
            },
            merged_catalog=None,
        )
    )

    events = list(executor.execute_stream("我的集群有什么问题？", run_id="run-empty-actions"))

    remediation_events = [event for event in events if event["type"] == "remediation_finished"]
    assert remediation_events
    assert remediation_events[-1]["status"] == "invalid_plan"
    assert "structured remediation actions" in remediation_events[-1]["reason"]


def test_workflow_text_preserves_complete_ai_message_after_token_stream(monkeypatch):
    monkeypatch.delenv("AIOPS_THINK_STREAM_MODE", raising=False)
    monkeypatch.delenv("THINK_STREAM_MODE", raising=False)

    class _Executor:
        def execute_stream(self, question, cancel_event=None, workflow_overrides=None):
            yield {
                "type": "thinking",
                "node": "evidence",
                "node_name": "证据采集",
                "thinking_type": "ai_token",
                "content": "<think>正在判断证据</think>",
            }
            yield {
                "type": "thinking",
                "node": "evidence",
                "node_name": "证据采集",
                "thinking_type": "ai_message",
                "full_content": "<think>正在判断证据</think>当前 Pod 存在 finalizer。",
            }

    service = HolmesService()
    service.workflow_config = {"think_stream": {"mode": "full"}}

    output = "".join(service._workflow_to_text(_Executor(), "q"))

    assert "正在判断证据" in output
    assert "当前 Pod 存在 finalizer" in output


def test_workflow_text_renders_progress_fallback_and_remediation_events(monkeypatch):
    monkeypatch.delenv("AIOPS_THINK_STREAM_MODE", raising=False)
    monkeypatch.delenv("THINK_STREAM_MODE", raising=False)

    class _Executor:
        def execute_stream(self, question, cancel_event=None, workflow_overrides=None):
            yield {"type": "heartbeat", "node": "conclusion", "node_name": "汇总总结"}
            yield {
                "type": "remediation_approval_required",
                "run_id": "run1",
                "approval_kind": "plan",
                "approval_id": "approval-1",
                "title": "是否执行 finalizer patch",
            }
            yield {
                "type": "remediation_tool_result",
                "stage": "execute",
                "command": "kubectl patch pod terminating-stuck -n aiops-e2e",
                "status": "success",
                "result_preview": "pod patched",
            }
            yield {
                "type": "remediation_finished",
                "status": "success",
                "reason": "verified",
            }

    service = HolmesService()
    service.workflow_config = {}

    output = "".join(service._workflow_to_text(_Executor(), "q"))

    assert "仍在处理" in output
    assert "修复审批中断" in output
    assert "kubectl patch pod terminating-stuck" in output
    assert "修复流程结束: success" in output
