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
    ConclusionOutput,
    QueryResult,
    RCAOutput,
)
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.context.observation import ObservationProcessor


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


def test_evidence_plan_output_accepts_aiops_case_mcp_tools():
    parsed = EvidencePlanOutput.model_validate({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "case-collector",
                "description": "采集异常 Pod 的多模态可观测 case",
                "level": "critical",
                "tool": "collect_aiops_case",
                "command": "collect_aiops_case namespace=aiops-temp pod=aiops-oom-business",
                "tool_args": {"namespace": "aiops-temp", "pod": "aiops-oom-business"},
                "purpose": "一次性采集 Kubernetes、metrics、logs、traces 和 topology 摘要",
                "acceptable_tools": ["collect_aiops_case", "get_aiops_case_evidence"],
            }
        ],
        "collection_strategy": "先采集实时 case summary，再按 evidence_ref 读取必要原始证据。",
    })

    assert parsed.evidence_plan[0].tool == "collect_aiops_case"
    assert parsed.evidence_plan[0].acceptable_tools == [
        "collect_aiops_case",
        "get_aiops_case_evidence",
    ]


def test_conclusion_output_schema_accepts_report_payload():
    parsed = ConclusionOutput.model_validate({
        "title": "诊断报告",
        "diagnosis_overview": {"layer": "L3"},
        "evidence_chain": [],
        "root_cause": "节点无法访问 Docker Hub",
        "recommendations": ["配置镜像代理"],
        "limitations": [],
        "markdown_report": "## 诊断报告\n节点无法访问 Docker Hub",
    })

    assert parsed.title == "诊断报告"
    assert parsed.markdown_report.startswith("## 诊断报告")


def test_conclusion_output_normalizes_flattened_markdown_report():
    parsed = ConclusionOutput.model_validate({
        "title": "诊断报告",
        "diagnosis_overview": {"layer": "L3"},
        "evidence_chain": [],
        "root_cause": "节点无法访问 Docker Hub",
        "recommendations": ["配置镜像代理"],
        "limitations": [],
        "markdown_report": "---## 📊 诊断概览| 项目 | 内容 ||------|------|| **Pod异常状态** | ImagePullBackOff |",
    })

    assert parsed.markdown_report.startswith("---\n## 📊 诊断概览")
    assert "| 项目 | 内容 |" in parsed.markdown_report
    assert "\n|------|------|" in parsed.markdown_report


def test_conclusion_output_repairs_flattened_adjacent_table_rows():
    parsed = ConclusionOutput.model_validate({
        "markdown_report": (
            "## 📊 诊断概览 | 项目 | 内容 | |------|------| "
            "| **Pod异常状态** | ImagePullBackOff (4), Terminating (1) | "
            "| **兼容归因层** | L1, L3 |"
        ),
    })

    assert "## 📊 诊断概览\n| 项目 | 内容 |" in parsed.markdown_report
    assert "\n|------|------|" in parsed.markdown_report
    assert "\n| **Pod异常状态** | ImagePullBackOff (4), Terminating (1) |" in parsed.markdown_report
    assert "| |------" not in parsed.markdown_report


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
    assert "primary_pod" not in parsed.model_dump(exclude_none=True)


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
                "entities": [{"kind": "Pod", "namespace": "aaa", "name": "redis-0"}],
                "possible_scenarios": ["节点到镜像仓库网络不可达"],
            },
            {
                "group_id": "g2",
                "status_keywords": ["Terminating"],
                "pod_abnormal_type": "TerminatingStuck",
                "compatible_layers": ["L1"],
                "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"}],
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
    dumped = parsed.model_dump(exclude_none=True)
    assert "primary_pod" not in dumped
    assert "primary_entities" not in dumped["issue_groups"][0]
    assert "is_primary" not in dumped["issue_groups"][0]


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


def test_query_result_normalizes_legacy_llm_shapes():
    parsed = QueryResult.model_validate({
        "query_target": "查询 CPU 和内存",
        "collection_summary": {"collected": "100%", "missing": "0%"},
        "columns": [
            {"name": "节点", "type": "string"},
            {"name": "CPU 使用率 (%)", "type": "float"},
        ],
        "rows": [{"节点": "node1", "CPU 使用率 (%)": "12.3"}],
        "notes": "指标来自 Prometheus node exporter",
        "missing": "没有缺失数据",
        "sources": {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
    })

    assert parsed.collection_summary == "collected=100%; missing=0%"
    assert parsed.columns[0].key == "节点"
    assert parsed.notes == ["指标来自 Prometheus node exporter"]
    assert parsed.missing[0].reason == "没有缺失数据"
    assert parsed.sources[0].tool == "execute_prometheus_instant_query"


def test_query_result_normalizes_source_type_to_tool():
    parsed = QueryResult.model_validate({
        "query_target": "查询 CPU",
        "collection_summary": {"collected_nodes": 3, "missing_nodes": 0},
        "columns": [{"name": "节点", "type": "string"}],
        "rows": [{"节点": "10.2.0.48"}],
        "sources": {
            "type": "prometheus_instant_query",
            "query": "cpu_query",
            "timestamp": "2026-05-09T03:20:12Z",
        },
    })

    assert parsed.sources[0].tool == "prometheus_instant_query"
    assert parsed.sources[0].query == "cpu_query"


def test_prometheus_http_error_is_semantic_failure():
    processor = ObservationProcessor()

    observation = processor.process(
        run_id="test-prometheus-error",
        node_id="layer",
        sequence=1,
        tool_name="execute_prometheus_instant_query",
        raw_content='{"error": "400 Client Error: Bad Request for url: http://prometheus/api/v1/query?query=bad"}',
    )

    assert observation["semantic_success"] is False
    assert observation["structured"]["status"] == "prometheus_error"
    assert "400 Client Error" in observation["summary"]


def test_prometheus_api_error_preserves_parse_error_and_query():
    processor = ObservationProcessor()

    observation = processor.process(
        run_id="test-prometheus-api-error",
        node_id="layer",
        sequence=1,
        tool_name="execute_prometheus_instant_query",
        raw_content=(
            '{"status":"error","errorType":"bad_data",'
            '"error":"invalid parameter \\"query\\": 1:49: parse error: unexpected character inside braces: \'/\'",'
            '"query":"1 - (node_filesystem_avail_bytes{mountpoint=\\"/\\" / node_filesystem_size_bytes{mountpoint=\\"/\\"})",'
            '"url":"http://prometheus/api/v1/query"}'
        ),
    )

    assert observation["semantic_success"] is False
    assert observation["structured"]["status"] == "prometheus_error"
    assert observation["structured"]["error_type"] == "bad_data"
    assert "unexpected character inside braces" in observation["structured"]["error"]
    assert "node_filesystem_avail_bytes" in observation["structured"]["query"]
    assert "Prometheus errorType: bad_data" in observation["summary"]
    assert "unexpected character inside braces" in observation["summary"]
    assert "PromQL:" in observation["summary"]


def test_prometheus_empty_vector_is_semantic_miss():
    processor = ObservationProcessor()

    observation = processor.process(
        run_id="test-prometheus-empty",
        node_id="layer",
        sequence=1,
        tool_name="execute_prometheus_instant_query",
        raw_content='{"status":"success","data":{"resultType":"vector","result":[]}}',
    )

    assert observation["semantic_success"] is False
    assert observation["structured"]["status"] == "prometheus_empty"
    assert observation["structured"]["result_count"] == 0
    assert "结果为空" in observation["summary"]


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
        "primary_runbooks": ["pod-imagepull-failed.md"],
        "alternative_causes": [],
        "limitations": "未验证节点出口网络",
    })

    assert parsed.root_cause == "节点访问 Docker Hub 超时，导致镜像拉取失败"
    assert parsed.confidence == 0.86
    assert parsed.primary_runbooks == ["pod-imagepull-failed.md"]


def test_rca_output_rejects_empty_root_cause():
    with pytest.raises(ValidationError):
        RCAOutput.model_validate({
            "phenomenon": "Pod 异常",
            "causal_chain": {},
            "confidence": 0.9,
        })
