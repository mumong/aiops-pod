import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.remediation.plans import extract_remediation_plan
from app.core.skills.models import Layer
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode


class _PlainAICall:
    def __init__(self, response: str):
        self.response = response

    def call_simple(self, *args, **kwargs):
        return self.response


def _node_with_response(response: str) -> ConclusionFormatterNode:
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {}
    node.ai_call = _PlainAICall(response)
    return node


def _finalizer_evidence() -> str:
    return json.dumps(
        {
            "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
            "evidence_inventory": [
                {
                    "id": "pod-yaml",
                    "description": "获取 Terminating Pod YAML",
                    "tool": "kubectl_get_yaml",
                    "command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
                    "collected": True,
                    "raw_data": """
apiVersion: v1
kind: Pod
metadata:
  name: terminating-stuck
  namespace: aiops-e2e
  deletionTimestamp: "2026-06-01T01:00:00Z"
  finalizers:
  - aiops.e2e/hold
status:
  phase: Running
""",
                }
            ],
        },
        ensure_ascii=False,
    )


def test_ask_conclusion_normalizes_finalizer_patch_plan_when_actions_missing():
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前仍在 Terminating，deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
优先移除已确认阻塞的 finalizer：
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
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": _finalizer_evidence(),
            "rca_analysis": '{"root_cause":"Pod finalizer 清理卡住"}',
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.fix_type == "remove_finalizer"
    assert plan.actions[0].execute_command == (
        "kubectl patch pod terminating-stuck -n aiops-e2e "
        "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
    )
    assert plan.actions[0].verify_command == "kubectl get pod terminating-stuck -n aiops-e2e"


def test_ask_conclusion_does_not_synthesize_force_delete_without_finalizer_evidence():
    report = """
## 📊 诊断概览
Pod 删除卡住，但当前证据不足。

## 🛠️ 修复建议
```bash
kubectl delete pod terminating-stuck -n aiops-e2e --grace-period=0 --force
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "risk_level": "high",
  "requires_human_approval": true,
  "basis": ["finalizer evidence missing"],
  "actions": []
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": "{}",
            "rca_analysis": "{}",
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_ask_conclusion_requires_upstream_finalizer_evidence_not_report_claims_only():
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前 deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
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
  "basis": ["report claim only"],
  "actions": []
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": "{}",
            "rca_analysis": "{}",
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_ask_conclusion_repairs_invalid_structured_finalizer_action_when_evidence_is_safe():
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前仍在 Terminating，deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
```bash
kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": true,
  "fix_type": "remove_finalizer",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["deletionTimestamp exists", "finalizers: aiops.e2e/hold"],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_patch",
      "description": "移除 finalizer",
      "risk": "medium",
      "dry_run_command": "kubectl patch pod terminating-stuck -n aiops-e2e -p '{\\"metadata\\":{\\"finalizers\\":null}}' --type=merge --dry-run=client -o yaml",
      "execute_command": "kubectl patch pod terminating-stuck -n aiops-e2e -p '{\\"metadata\\":{\\"finalizers\\":null}}' --type=merge",
      "verify_command": "kubectl get pod terminating-stuck -n aiops-e2e 2>&1 || echo NotFound"
    }
  ]
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": _finalizer_evidence(),
            "rca_analysis": '{"root_cause":"Pod finalizer 清理卡住"}',
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.actions[0].verify_command == "kubectl get pod terminating-stuck -n aiops-e2e"


def test_query_direct_render_does_not_invoke_ask_remediation_normalization():
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}
    node.ai_call = _PlainAICall("should not be called")

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("ask remediation normalization must not run for query direct")

    node._normalize_ask_remediation_plan = _fail_if_called

    result = node.execute(
        {
            "question": "查询 CPU",
            "layer": Layer.QUERY,
            "query_result": {
                "query_target": "查询 CPU",
                "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
                "columns": [{"key": "node", "label": "节点"}, {"key": "cpu", "label": "CPU"}],
                "rows": [{"node": "node1", "cpu": "1%"}],
                "notes": [],
                "missing": [],
                "sources": [{"tool": "execute_prometheus_instant_query", "query": "cpu"}],
            },
        }
    )

    assert "## 📊 查询结果" in result["conclusion"]
    assert "node1" in result["conclusion"]


def test_normalized_finalizer_plan_reaches_remediation_approval(monkeypatch):
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前仍在 Terminating，deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
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
    node = _node_with_response(report)
    normalized = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": _finalizer_evidence(),
            "rca_analysis": '{"root_cause":"Pod finalizer 清理卡住"}',
            "thinking_events": [],
        }
    )["conclusion"]

    class _DummyWorkflow:
        def stream(self, initial_state):
            return iter(
                [
                    {
                        "conclusion": {
                            "layer": "L1",
                            "conclusion_formatted": normalized,
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
                    "executor": "deterministic",
                    "mode": "review",
                    "approval_timeout_seconds": 1,
                },
            },
            merged_catalog=None,
        )
    )

    events = list(executor.execute_stream("我的集群有什么问题？", run_id="run-normalized-plan"))

    approvals = [event for event in events if event["type"] == "remediation_approval_required"]
    assert approvals
    assert approvals[0]["approval_kind"] == "plan"
    assert approvals[0]["payload"]["actions"][0]["execute_command"].startswith(
        "kubectl patch pod terminating-stuck -n aiops-e2e"
    )
