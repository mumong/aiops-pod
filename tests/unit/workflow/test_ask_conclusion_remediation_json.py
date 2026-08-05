import hashlib
import json
import os
import re
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import app.core.workflow.fact_contract as fact_contract_module
from app.core.remediation.plans import extract_remediation_plan
from app.core.prompts import REMEDIATION_PLAN_PROMPT
from app.core.skills.models import Layer
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.schemas import FactLedger, FactRecord


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


_OPTIONAL_FACT_FIELDS = {
    "namespace",
    "entity_name",
    "strength",
    "unit",
    "timestamp",
    "start",
    "end",
    "metadata",
}


_ACTION_SPECIFIC_FACT_CASES = [
    (
        "delete",
        "kubectl delete deployment api -n demo",
        "lifecycle.desired_state",
        "absent",
    ),
    (
        "patch",
        (
            "kubectl patch deployment api -n demo "
            "-p '{\"spec\":{\"replicas\":2}}' --type=merge"
        ),
        "spec.replicas",
        2,
    ),
    (
        "scale",
        "kubectl scale deployment api -n demo --replicas=2",
        "spec.replicas",
        2,
    ),
    (
        "set_resources",
        (
            "kubectl set resources deployment/api -n demo "
            "--containers=api --limits=memory=128Mi "
            "--requests=memory=64Mi"
        ),
        "spec.template.spec.containers",
        [
            {
                "name": "api",
                "resources": {
                    "limits": {"memory": "128Mi"},
                    "requests": {"memory": "64Mi"},
                },
            }
        ],
    ),
    (
        "set_image",
        (
            "kubectl set image deployment/api "
            "api=example.invalid/api:v2 -n demo"
        ),
        "spec.template.spec.containers",
        {
            "name": "api",
            "image": "example.invalid/api:v2",
        },
    ),
    (
        "set_env",
        (
            "kubectl set env deployment/api "
            "FEATURE_FLAG=enabled --containers=api -n demo"
        ),
        "spec.template.spec.containers",
        [
            {
                "name": "api",
                "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
            }
        ],
    ),
    (
        "rollout_restart",
        "kubectl rollout restart deployment/api -n demo",
        "status.rollout.restart_required",
        True,
    ),
]


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


