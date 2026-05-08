import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.workflow.schemas import (
    EvidenceCollectionOutput,
    EvidenceMatchOutput,
    EvidencePlanOutput,
    LayerHandoff,
    LayerOutput,
    QueryResult,
    RCAOutput,
)
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode


def test_evidence_plan_output_validates_required_fields():
    parsed = EvidencePlanOutput.model_validate({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认镜像拉取失败原因",
            }
        ],
        "collection_strategy": "先确认当前异常 Pod，再验证事件。",
    })

    assert parsed.evidence_plan[0].id == "e1"
    assert parsed.evidence_plan[0].level == "critical"


def test_evidence_plan_output_rejects_unknown_tool_name():
    with pytest.raises(ValidationError):
        EvidencePlanOutput.model_validate({
            "layer": "L3",
            "evidence_plan": [
                {
                    "id": "e1",
                    "description": "获取 Pod YAML",
                    "level": "critical",
                    "tool": "kubectl_get_pod",
                    "command": "kubectl get pod redis-0 -n aaa -o yaml",
                    "purpose": "确认 Pod 配置",
                }
            ],
            "collection_strategy": "非法工具名应被 Pydantic 拒绝。",
        })


def test_layer_output_normalizes_pods_entities_and_scenarios():
    parsed = LayerOutput.model_validate({
        "layer": "L3",
        "derived_layer": "L3",
        "layers": ["L3"],
        "confidence": "0.92",
        "reasoning": "发现镜像拉取失败",
        "primary_pod": {"name": "redis-0", "namespace": "aaa"},
        "abnormal_pods": [
            {"name": "redis-0", "namespace": "aaa", "status": "ImagePullBackOff"},
            "aiops-e2e/terminating-stuck",
        ],
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
        "key_entities": [
            {"type": "Pod", "value": "redis-0"},
            {"kind": "Namespace", "name": "aaa"},
        ],
        "possible_scenarios": [
            "节点到镜像仓库网络不可达",
            {"scenario": "镜像 tag 不存在", "probability": "中", "reason": "需要验证"},
        ],
    })

    assert parsed.confidence == 0.92
    assert parsed.abnormal_pods[0].name == "redis-0"
    assert parsed.abnormal_pods[1].namespace == "aiops-e2e"
    assert parsed.key_entities[1].type == "Namespace"
    assert parsed.possible_scenarios[0].scenario == "节点到镜像仓库网络不可达"


def test_layer_parse_json_extracts_payload_after_think_text():
    text = """</think>

{
  "layer": "L3",
  "derived_layer": "L3",
  "layers": ["L3"],
  "confidence": 0.95,
  "reasoning": "发现 ImagePullBackOff",
  "primary_pod": {"name": "redis-0", "namespace": "aaa"},
  "abnormal_pods": [{"name": "redis-0", "namespace": "aaa", "status": "ImagePullBackOff"}],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed"
}
"""

    parsed = LayerClassifierNode._try_parse_json(text)

    assert parsed["layer"] == "L3"
    assert parsed["primary_pod"] == {"name": "redis-0", "namespace": "aaa"}


def test_layer_lite_extract_uses_pydantic_structured_output():
    captured = {}

    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            captured["schema"] = schema
            captured["node_id"] = kwargs.get("node_id")
            return schema.model_validate({
                "layer": "L1",
                "derived_layer": "L1",
                "layers": ["L1"],
                "confidence": 0.91,
                "reasoning": "发现 Terminating 卡住",
                "primary_pod": {"name": "terminating-stuck", "namespace": "aiops-e2e"},
                "abnormal_pods": [
                    {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"}
                ],
                "pod_status_keyword": "Terminating",
                "pod_abnormal_type": "TerminatingStuck",
            }), "{}"

    node = LayerClassifierNode()
    node.ai_call = _StructuredAICall()

    result = node._extract_with_lite_llm(
        question="我的集群有什么问题",
        full_analysis_text="status_counts={'Terminating': 1}",
        failure_reason="测试",
    )

    assert captured["schema"] is LayerOutput
    assert captured["node_id"] == "layer_extract"
    assert result["layer"] == "L1"
    assert result["abnormal_pods"][0]["status"] == "Terminating"


def test_layer_handoff_requires_issue_groups_and_group_scenarios():
    parsed = LayerHandoff.model_validate({
        "layer": "L3",
        "derived_layer": "L3",
        "layers": ["L3", "L1"],
        "confidence": 0.92,
        "primary_problem": "发现 ImagePull 和 Terminating",
        "primary_pod": {"name": "redis-0", "namespace": "aaa"},
        "abnormal_pods": [
            {"name": "redis-0", "namespace": "aaa", "status": "ImagePullBackOff"},
            {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"},
        ],
        "issue_groups": [
            {
                "group_id": "g1",
                "status_keywords": ["ImagePullBackOff"],
                "pod_abnormal_type": "ImagePullFailed",
                "compatible_layers": ["L3"],
                "primary_entities": [{"kind": "Pod", "namespace": "aaa", "name": "redis-0"}],
                "is_primary": True,
                "possible_scenarios": ["节点到镜像仓库网络不可达"],
            },
            {
                "group_id": "g2",
                "status_keywords": ["Terminating"],
                "pod_abnormal_type": "TerminatingStuck",
                "compatible_layers": ["L1"],
                "primary_entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"}],
                "is_primary": False,
                "possible_scenarios": ["finalizer 未清理"],
            },
        ],
        "current_abnormal_summary": {
            "status_counts": {"ImagePullBackOff": 1, "Terminating": 1},
            "total_abnormal": 2,
            "selected_rows": [],
        },
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
    })

    assert len(parsed.issue_groups) == 2
    assert parsed.issue_groups[1].possible_scenarios[0].scenario == "finalizer 未清理"


def test_query_result_normalizes_string_missing_items():
    parsed = QueryResult.model_validate({
        "query_target": "查询 CPU",
        "collection_summary": "计划 1 项，实际采集 0 项",
        "columns": ["node", {"key": "cpu", "label": "CPU"}],
        "rows": [{"node": "node1", "cpu": "10%"}],
        "missing": ["prometheus 返回空"],
        "sources": ["execute_prometheus_instant_query"],
    })

    assert parsed.columns[0].key == "node"
    assert parsed.missing[0].field == "result"
    assert parsed.missing[0].reason == "prometheus 返回空"


def test_evidence_plan_output_rejects_missing_command():
    with pytest.raises(ValidationError):
        EvidencePlanOutput.model_validate({
            "layer": "L3",
            "evidence_plan": [
                {
                    "id": "e1",
                    "description": "获取 Pod 事件",
                    "level": "critical",
                    "tool": "kubectl_events",
                    "purpose": "确认镜像拉取失败原因",
                }
            ],
            "collection_strategy": "先确认当前异常 Pod。",
        })


def test_evidence_match_output_validates_match_decisions():
    parsed = EvidenceMatchOutput.model_validate({
        "matches": [
            {
                "plan_id": "e1",
                "tool_result_index": 0,
                "matched": True,
                "confidence": 0.91,
                "reason": "对象、namespace、工具意图一致",
            },
            {
                "plan_id": "e2",
                "tool_result_index": None,
                "matched": False,
                "confidence": 0.93,
                "reason": "计划查询 NetworkPolicy，但结果是 Secret 表",
            },
        ],
        "unmatched_plan_ids": ["e2"],
        "unplanned_tool_result_indexes": [3],
    })

    assert parsed.matches[0].matched is True
    assert parsed.matches[1].tool_result_index is None


def test_evidence_collection_output_validates_summary_counts():
    parsed = EvidenceCollectionOutput.model_validate({
        "evidence_plan": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认镜像拉取失败原因",
            }
        ],
        "tool_results": [],
        "tool_data": [],
        "llm_analysis": "已完成采集",
        "collection_summary": "计划 1 项，实际采集 1 项，完整度 100%",
        "plan_total": 1,
        "plan_collected": 1,
        "plan_completeness": 1.0,
        "environment_evidence_total": 1,
        "environment_evidence_collected": 1,
        "environment_evidence_completeness": 1.0,
        "evidence_inventory": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认镜像拉取失败原因",
                "collected": True,
                "source": "thinking_match",
            }
        ],
        "missing_reasons": [],
        "early_stop": {"triggered": True, "reason": "完成", "required_levels": ["critical"]},
    })

    assert parsed.plan_total == 1
    assert parsed.evidence_inventory[0]["collected"] is True


def test_evidence_collection_output_rejects_invalid_completeness():
    with pytest.raises(ValidationError):
        EvidenceCollectionOutput.model_validate({
            "evidence_plan": [],
            "collection_summary": "invalid",
            "plan_total": 1,
            "plan_collected": 2,
            "plan_completeness": 1.5,
            "environment_evidence_total": 0,
            "environment_evidence_collected": 0,
            "environment_evidence_completeness": 0,
        })


def test_rca_output_normalizes_root_cause_from_summary():
    parsed = RCAOutput.model_validate({
        "phenomenon": "Pod ImagePullBackOff",
        "evidence_inventory": [
            {"id": "e1", "content": "Failed to pull image", "source": "kubectl_events", "reliability": "高"}
        ],
        "evidence_analysis": [
            {"evidence_id": "e1", "raw_data": "i/o timeout", "interpretation": "节点无法访问镜像仓库"}
        ],
        "causal_chain": {
            "root_cause": "节点访问 Docker Hub 超时",
            "propagation": "镜像无法下载",
            "direct_cause": "容器无法创建",
            "manifestation": "Pod ImagePullBackOff",
        },
        "root_cause_summary": "节点访问 Docker Hub 超时，导致镜像拉取失败",
        "confidence": 0.86,
        "primary_runbooks": ["l3-imagepull-failed.md"],
        "alternative_causes": [],
        "limitations": "未验证节点出口网络",
    })

    assert parsed.root_cause == "节点访问 Docker Hub 超时，导致镜像拉取失败"
    assert parsed.confidence == 0.86
    assert parsed.primary_runbooks == ["l3-imagepull-failed.md"]


def test_rca_output_rejects_empty_root_cause():
    with pytest.raises(ValidationError):
        RCAOutput.model_validate({
            "phenomenon": "Pod 异常",
            "causal_chain": {},
            "confidence": 0.9,
        })
