import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.workflow.schemas import (
    EvidenceCollectionOutput,
    EvidenceMatchOutput,
    EvidencePlanOutput,
    RCAOutput,
)


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
