import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.service import HolmesService
from app.core.remediation.plans import extract_remediation_plan
from app.core.prompts import (
    CONCLUSION_FORMATTER_PROMPT,
    EVIDENCE_COLLECTOR_PROMPT,
    LAYER_CLASSIFIER_PROMPT,
    REMEDIATION_PLAN_PROMPT,
    ROOT_CAUSE_ANALYZER_PROMPT,
    get_query_evidence_normalization_prompt,
    get_conclusion_mode_instruction,
    get_workflow_prompt,
)
from app.core.skills.models import Layer
from app.core.workflow.fact_contract import (
    _canonical_fact_id,
)
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.schemas import (
    FactLedger,
    LayerOutput,
    QueryResult,
    RCAOutput,
)


class _RecordingAICall:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def call_simple(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        return self.content

    def call_structured(self, **kwargs):
        self.calls.append({"args": (), "kwargs": kwargs})
        schema = kwargs["schema"]
        structured = schema.model_validate({
            "title": "诊断报告",
            "diagnosis_overview": {},
            "evidence_chain": [],
            "root_cause": "",
            "recommendations": [],
            "limitations": [],
            "markdown_report": self.content,
        })
        return structured, structured.model_dump_json()


def test_query_conclusion_uses_llm_structured_summary():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询当前异常 Pod 列表

## 📈 数据摘要
| 项目 | 数值 |
|------|------|
| 异常 Pod 数量 | 1 |

## 🔎 详情
- default/pod-a: CrashLoopBackOff
"""
    )

    state = {
        "question": "查询当前异常 Pod 列表",
        "layer": Layer.QUERY,
        "evidence_analysis": (
            '{"collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",'
            '"tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", '
            '"data": "NAMESPACE NAME STATUS\\ndefault pod-a CrashLoopBackOff"}],'
            '"evidence_plan": [{"tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get pods -A"}]}'
        ),
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 1
    assert "查询结果" in result["conclusion"]
    assert "数据摘要" in result["conclusion"]
    assert "异常 Pod 数量" in result["conclusion"]
    assert "CrashLoopBackOff" in result["conclusion"]

def test_healthy_conclusion_uses_deterministic_fast_path():
    node = ConclusionFormatterNode()
    class _FailingAICall:
        def call_simple(self, *args, **kwargs):
            raise AssertionError("call_simple should not be called")

    node.ai_call = _FailingAICall()

    state = {
        "question": "我的集群现在健康吗",
        "layer": Layer.HEALTHY,
        "layer_full_analysis": "所有 Pod Running，节点 Ready，未发现异常事件。",
        "thinking_events": [],
    }

    result = node.execute(state)

    assert "健康检查结果" in result["conclusion"]
    assert "当前集群运行正常" in result["conclusion"]
    assert "所有 Pod Running" in result["conclusion"]


def test_single_path_inconclusive_rca_cannot_publish_narrative_diagnosis():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        "root cause is definitely unsupported, confidence 99%"
    )
    state = {
        "question": "What is wrong?",
        "layer": Layer.L2,
        "rca_analysis": json.dumps({
            "diagnostic_status": "inconclusive",
            "root_cause": "Current facts are insufficient",
            "confidence": 0.2,
            "confidence_reason": "invalid Fact reference",
            "supporting_fact_ids": [],
            "unknowns": ["source-backed cause is not established"],
            "claim_validation": {
                "valid": False,
                "reasons": ["unknown supporting fact reference"],
            },
        }),
        "rca_input_projection": {
            "authoritative_entity_ids": ["k8s.pod:demo/api:uid-a"],
            "selected_facts": [{
                "fact_id": "fact-abc12345",
                "dimension": "logging",
                "source_system": "elasticsearch",
                "value": "real observed symptom",
            }],
        },
        "entity_evidence_snapshot": {
            "contract_version": "aiops.entity-evidence-snapshot.v1",
            "dimension_evidence_by_entity": {
                "demo/api": {
                    "kubernetes": {"status": "unselected", "facts": []},
                    "metrics": {"status": "error", "facts": []},
                    "logging": {"status": "present", "facts": []},
                    "tracing": {"status": "absent", "facts": []},
                }
            },
        },
        "thinking_events": [],
    }

    report = node.execute(state)["conclusion"]

    assert "diagnostic_status: inconclusive" in report
    assert "unknown supporting fact reference" in report
    assert "real observed symptom" in report
    assert "| metrics | error |" in report
    assert "| tracing | absent |" in report
    assert "confidence 99%" not in report
    assert node.ai_call.calls == []


def test_layer_stage1_text_is_always_revalidated_with_pydantic_and_keeps_full_analysis():
    node = LayerClassifierNode()
    stage1_text = "用户在直接查询异常 Pod 列表，工具结果显示 default/pod-a CrashLoopBackOff。"

    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME STATUS\ndefault pod-a CrashLoopBackOff",
        }
    ]

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result=stage1_text), thinking_events)

    class _StructuredAICall:
        def __init__(self):
            self.calls = []

        def call_structured(self, system_prompt, question, schema, **kwargs):
            self.calls.append({"system_prompt": system_prompt, "question": question, "schema": schema})
            return schema.model_validate({
                "layer": "QUERY",
                "layers": ["QUERY"],
                "layer_name": "直接查询",
                "confidence": 0.95,
                "reasoning": "用户在直接查询异常 Pod 列表",
                "key_entities": [{"type": "Resource", "value": "Pod"}],
                "possible_scenarios": [{"scenario": "直接查询", "probability": "高", "reason": "请求状态列表"}],
            }), "{}"

    node.ai_call = _StructuredAICall()

    result, returned_events = node._analyze_with_llm("查询异常 Pod")

    assert result["layer"] == "QUERY"
    assert "full_analysis" in result
    assert "kubectl_get_by_kind_in_cluster" in result["full_analysis"]
    assert "CrashLoopBackOff" in result["full_analysis"]
    assert len(node.ai_call.calls) == 1
    assert node.ai_call.calls[0]["schema"] is LayerOutput
    assert returned_events == thinking_events


def test_layer_tool_collection_is_finalized_by_layer_extract():
    node = LayerClassifierNode()
    stage1_text = "工具结果显示 aaa/redis-0 ImagePullBackOff。"
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME STATUS\naaa redis-0 ImagePullBackOff",
            "structured": {
                "status_counts": {"ImagePullBackOff": 1},
                "selected_rows": ["aaa redis-0 ImagePullBackOff"],
            },
        }
    ]
    structured = LayerOutput.model_validate({
        "layer": "L3",
        "layers": ["L3"],
        "layer_name": "服务网络层",
        "confidence": 0.93,
        "reasoning": "当前 Pod 镜像拉取失败",
        "abnormal_pods": [
            {"name": "redis-0", "namespace": "aaa", "status": "ImagePullBackOff"}
        ],
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
        "status_category": "image_registry",
    })

    captured = {}

    def _fake_call_llm(question, prompt, **kwargs):
        captured["response_schema"] = kwargs.get("response_schema")
        return SimpleNamespace(result=stage1_text), thinking_events

    node._call_llm = _fake_call_llm

    class _ExtractAICall:
        def __init__(self):
            self.calls = []

        def call_structured(self, *args, **kwargs):
            self.calls.append(kwargs)
            return structured, structured.model_dump_json()

    node.ai_call = _ExtractAICall()

    result, returned_events = node._analyze_with_llm("我的集群有什么问题")

    assert captured["response_schema"] is None
    assert node.ai_call.calls[0]["schema"] is LayerOutput
    assert result["layer"] == "L3"
    assert result["abnormal_pods"][0]["status"] == "ImagePullBackOff"
    assert "kubectl_get_by_kind_in_cluster" in result["full_analysis"]
    assert returned_events == thinking_events


def test_layer_stage1_non_json_output_uses_lite_extraction():
    node = LayerClassifierNode()
    non_json_text = "分析结果：检测到 OOMKilled，根因更接近 L2 工作负载层。"
    thinking_events = []

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result=non_json_text), thinking_events)

    class _RecordingAICall:
        def __init__(self):
            self.calls = []

        def call_structured(self, system_prompt, question, schema, **kwargs):
            self.calls.append({"system_prompt": system_prompt, "question": question, "kwargs": kwargs})
            return schema.model_validate({
                "layer": "L2",
                "layers": ["L2"],
                "layer_name": "工作负载层",
                "confidence": 0.78,
                "reasoning": "基于已采集到的工具与分析文本，当前问题更符合 L2 工作负载层。",
                "key_entities": [{"type": "Pod", "value": "nginx-1"}],
                "possible_scenarios": [{"scenario": "OOMKilled", "probability": "高", "reason": "分析文本明确提到 OOMKilled"}],
            }), '{"layer":"L2"}'

    node.ai_call = _RecordingAICall()

    result, returned_events = node._analyze_with_llm("我的服务为什么 OOM 了")

    # 提取阶段透传 LLM 原文（legacy L2 兼容），execute 阶段统一归一化为 ABNORMAL
    assert result["layer"] == "L2"
    assert "工作负载层" == result["layer_name"]
    assert result["confidence"] == 0.78
    assert "full_analysis" in result
    assert len(node.ai_call.calls) == 1
    assert "分析文本" in node.ai_call.calls[0]["question"]
    assert returned_events == thinking_events


def test_layer_lite_extraction_enables_text_json_fallback():
    node = LayerClassifierNode()
    node._call_llm = lambda question, prompt, **kwargs: (
        SimpleNamespace(result="工具结果显示 aaa/redis-0 ImagePullBackOff。"),
        [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "kubectl_get_by_kind_in_cluster",
                "result": "NAMESPACE NAME STATUS\naaa redis-0 ImagePullBackOff",
            }
        ],
    )

    class _FallbackAICall:
        def __init__(self):
            self.calls = []

        def call_structured(self, system_prompt, question, schema, **kwargs):
            self.calls.append(kwargs)
            if not kwargs.get("allow_text_fallback"):
                return None, ""
            parsed = schema.model_validate({
                "layer": "L3",
                "layers": ["L3"],
                "layer_name": "服务网络层",
                "confidence": 0.82,
                "reasoning": "当前 Pod 镜像拉取失败",
                "abnormal_pods": [{"name": "redis-0", "namespace": "aaa", "status": "ImagePullBackOff"}],
                "pod_status_keyword": "ImagePullBackOff",
                "pod_abnormal_type": "ImagePullFailed",
            })
            return parsed, parsed.model_dump_json()

    node.ai_call = _FallbackAICall()

    result, _events = node._analyze_with_llm("我的集群有什么问题？")

    assert result["layer"] == "L3"
    assert node.ai_call.calls[0]["allow_text_fallback"] is True


def test_layer_connection_error_without_tool_evidence_fails_clear_without_extract_retry():
    node = LayerClassifierNode()
    node._call_llm = lambda question, prompt, **kwargs: (
        SimpleNamespace(result="Agent 执行异常: Connection error."),
        [],
    )

    class _UnexpectedAICall:
        def __init__(self):
            self.calls = 0

        def call_structured(self, *args, **kwargs):
            self.calls += 1
            return None, ""

    node.ai_call = _UnexpectedAICall()

    with pytest.raises(RuntimeError, match="LLM 服务不可用"):
        node._analyze_with_llm("我的集群有什么问题？")

    assert node.ai_call.calls == 0


def test_layer_execute_preserves_llm_unavailable_error_without_rescue_extract():
    node = LayerClassifierNode()
    node._analyze_with_llm = lambda question: (_ for _ in ()).throw(
        RuntimeError("LLM 服务不可用，无法完成问题定位: Agent 执行异常: Connection error.")
    )
    extract_calls = []

    def _unexpected_extract(*args, **kwargs):
        extract_calls.append(kwargs)
        return None

    node._extract_with_lite_llm = _unexpected_extract
    node.ai_call = object()

    with pytest.raises(RuntimeError, match="LLM 服务不可用"):
        node.execute({"question": "我的集群有什么问题？"})

    assert extract_calls == []


def test_layer_ignores_stage1_json_text_and_uses_pydantic_output():
    node = LayerClassifierNode()
    first_text = "terminating-stuck Pod Terminating"
    first_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "terminating-stuck Terminating",
        }
    ]
    calls = []

    def _fake_call_llm(question, prompt, **kwargs):
        calls.append({"prompt": prompt, "kwargs": kwargs})
        return SimpleNamespace(result=first_text), first_events

    node._call_llm = _fake_call_llm

    class _StructuredAICall:
        def __init__(self):
            self.calls = 0

        def call_structured(self, system_prompt, question, schema, **kwargs):
            self.calls += 1
            return schema.model_validate({
                "layer": "L1",
                "layers": ["L1"],
                "confidence": 0.8,
                "reasoning": "terminating-stuck Pod Terminating",
                "primary_pod": {"name": "terminating-stuck", "namespace": "aiops-e2e"},
                "abnormal_pods": [{"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"}],
                "pod_status_keyword": "Terminating",
                "pod_abnormal_type": "TerminatingStuck",
            }), "{}"

    node.ai_call = _StructuredAICall()

    result, returned_events = node._analyze_with_llm("我的集群有什么问题？")

    assert len(calls) == 1
    assert calls[0]["kwargs"]["expect_json"] is False
    assert node.ai_call.calls == 1
    assert result["confidence"] == 0.8
    assert result["pod_abnormal_type"] == "TerminatingStuck"
    assert returned_events == first_events


def test_layer_early_stop_disabled_does_not_enable_json_middleware():
    node = LayerClassifierNode()
    node.workflow_config_override = {"layer": {"early_stop": {"enabled": False}}}
    structured_json = """{
      "layer": "QUERY",
      "layers": ["QUERY"],
      "confidence": 0.95,
      "reasoning": "查询请求",
      "key_entities": [],
      "possible_scenarios": []
    }"""
    calls = []

    def _fake_call_llm(question, prompt, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(result=structured_json), []

    node._call_llm = _fake_call_llm

    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            return schema.model_validate({
                "layer": "QUERY",
                "layers": ["QUERY"],
                "confidence": 0.95,
                "reasoning": "查询请求",
                "key_entities": [],
                "possible_scenarios": [],
            }), "{}"

    node.ai_call = _StructuredAICall()

    result, _ = node._analyze_with_llm("查询异常 Pod")

    assert result["layer"] == "QUERY"
    assert calls[0]["expect_json"] is False
    assert "json_acceptance_guard" not in calls[0]


def test_layer_execute_keeps_llm_result_when_only_historical_events_exist():
    node = LayerClassifierNode()

    def _fake_llm(question):
        return (
            {
                "layer": "L2",
                "layers": ["L2"],
                "layer_name": "工作负载层",
                "confidence": 0.72,
                "reasoning": "发现 Warning 事件，怀疑工作负载异常",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [
                {
                    "type": "tool_result",
                    "status": "success",
                    "tool_name": "kubernetes_jq_query",
                    "result": "aiops-e2e Warning BackOff Pod/appconfigfail-123: Back-off restarting failed container app",
                },
                {
                    "type": "tool_result",
                    "status": "success",
                    "tool_name": "kubectl_get_by_kind_in_namespace",
                    "result": "No resources found in aiops-e2e namespace.",
                },
                {
                    "type": "tool_result",
                    "status": "success",
                    "tool_name": "kubectl_get_by_kind_in_cluster",
                    "result": "NAME STATUS ROLES\nmaster Ready control-plane\nnode1 Ready <none>",
                },
            ],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "我的集群有什么问题？"})

    assert result["layer"] == Layer.ABNORMAL
    assert result["layer_reasoning"] == "发现 Warning 事件，怀疑工作负载异常"


def test_layer_execute_keeps_llm_result_when_live_abnormal_signal_exists():
    node = LayerClassifierNode()

    def _fake_llm(question):
        return (
            {
                "layer": "L2",
                "layers": ["L2"],
                "layer_name": "工作负载层",
                "confidence": 0.88,
                "reasoning": "发现当前存在 CrashLoopBackOff Pod",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [
                {
                    "type": "tool_result",
                    "status": "success",
                    "tool_name": "kubectl_get_by_kind_in_namespace",
                    "result": "NAME READY STATUS RESTARTS\nappconfigfail-123 0/1 CrashLoopBackOff 5",
                }
            ],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "我的服务为什么异常"})

    assert result["layer"] == Layer.ABNORMAL
    assert result["layer_reasoning"] == "发现当前存在 CrashLoopBackOff Pod"


def test_layer_uses_llm_for_clear_query_requests():
    node = LayerClassifierNode()
    called = {"llm": False}

    def _fake_llm(question):
        called["llm"] = True
        return (
            {
                "layer": "QUERY",
                "layers": ["QUERY"],
                "layer_name": "直接查询",
                "confidence": 0.95,
                "reasoning": "LLM 判定用户在直接查询指标",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "查询集群每个节点 CPU 和内存使用率"})

    assert called["llm"] is True
    assert result["layer"] == Layer.QUERY
    assert result["layer_reasoning"]


def test_layer_does_not_lightweight_route_diagnosis_questions():
    node = LayerClassifierNode()

    called = {"llm": False}

    def _fake_llm(question):
        called["llm"] = True
        return (
            {
                "layer": "L2",
                "layers": ["L2"],
                "layer_name": "工作负载层",
                "confidence": 0.91,
                "reasoning": "用户在询问集群问题原因，属于诊断请求",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "我的集群有什么问题？分析下原因"})

    assert called["llm"] is True
    assert result["layer"] == Layer.ABNORMAL


def test_layer_does_not_lightweight_route_cluster_status_diagnosis_wording():
    node = LayerClassifierNode()

    called = {"llm": False}

    def _fake_llm(question):
        called["llm"] = True
        return (
            {
                "layer": "L1",
                "layers": ["L1"],
                "layer_name": "集群与节点层",
                "confidence": 0.83,
                "reasoning": "‘集群什么情况’属于整体状态诊断，不是明确数据查询",
                "key_entities": [],
                "possible_scenarios": [],
            },
            [],
        )

    node.ai_call = object()
    node._analyze_with_llm = _fake_llm

    result = node.execute({"question": "我的集群现在什么情况？"})

    assert called["llm"] is True
    assert result["layer"] == Layer.ABNORMAL


def test_query_conclusion_renders_locally_when_query_result_present():
    node = ConclusionFormatterNode()
    node.workflow_config_override = {"query_mode": "direct"}

    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询集群每个节点 CPU 和内存使用率

## 📈 数据摘要
| 节点 | CPU 使用率 | 内存使用率 |
|------|------------|------------|
| master | 13.7% | 26.2% |
"""
    )

    state = {
        "question": "查询集群每个节点 CPU 和内存使用率",
        "layer": Layer.QUERY,
        "query_result": {
            "query_target": "查询集群每个节点 CPU 和内存使用率",
            "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
            "columns": [
                {"key": "node", "label": "节点"},
                {"key": "cpu", "label": "CPU 使用率"},
                {"key": "memory", "label": "内存使用率"},
            ],
            "rows": [
                {"node": "master", "cpu": "13.7%", "memory": "26.2%"},
                {"node": "node1", "cpu": "9.8%", "memory": "19.3%"},
            ],
            "notes": ["数据来自 Prometheus 查询。"],
            "sources": [
                {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
                {"tool": "execute_prometheus_instant_query", "query": "mem_query"},
            ],
        },
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 0
    assert "## 📊 查询结果" in result["conclusion"]
    assert "master" in result["conclusion"]


def test_query_conclusion_falls_back_to_llm_when_query_result_missing():
    node = ConclusionFormatterNode()

    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询集群每个节点 CPU 和内存使用率

## 📈 数据摘要
| 工具 | 结果摘要 |
|------|----------|
| execute_prometheus_instant_query | master=13.7%,node1=9.8% |
"""
    )

    state = {
        "question": "查询集群每个节点 CPU 和内存使用率",
        "layer": Layer.QUERY,
        "query_result": None,
        "evidence_analysis": (
            '{"collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",'
            '"tool_data":[{"tool":"execute_prometheus_instant_query","data":"master=13.7%,node1=9.8%"}],'
            '"evidence_plan":[{"tool":"execute_prometheus_instant_query","command":"cpu_query"}],'
            '"missing_reasons":[]}'
        ),
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 1
    assert "## 📊 查询结果" in result["conclusion"]
    assert "execute_prometheus_instant_query" in result["conclusion"]


def test_query_evidence_execute_builds_structured_query_result():
    node = EvidenceCollectorNode()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._extract_tool_data_from_thinking = lambda events: [
        {"tool": "execute_prometheus_instant_query", "data": '{"status":"success"}', "duration_s": 0}
    ]
    node._plan_evidence_with_llm = lambda **kwargs: (
        [
            {"id": "e1", "description": "查询 CPU", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "cpu_query", "purpose": "cpu"},
            {"id": "e2", "description": "查询内存", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "mem_query", "purpose": "memory"},
        ],
        [
            {"type": "tool_result", "status": "success", "tool_name": "execute_prometheus_instant_query", "result_preview": '{"status":"success"}', "result": '{"status":"success"}'},
        ],
        "已完成查询",
    )

    class _NormalizeAICall:
        def __init__(self):
            self.calls = []

        def call_structured(self, system_prompt, question, schema, **kwargs):
            assert schema is QueryResult
            self.calls.append({"system_prompt": system_prompt, "question": question})
            payload = {
                "query_target": "查询集群每个节点 CPU 和内存使用率",
                "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
                "columns": [
                    {"key": "node", "label": "节点"},
                    {"key": "cpu", "label": "CPU 使用率"},
                    {"key": "memory", "label": "内存使用率"},
                ],
                "rows": [
                    {"node": "master", "cpu": "13.7%", "memory": "26.2%"},
                ],
                "notes": ["数据来自 Prometheus。"],
                "sources": [
                    {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
                ],
            }
            return schema.model_validate(payload), "{}"

    node.ai_call = _NormalizeAICall()

    result = node.execute({
        "question": "查询集群每个节点 CPU 和内存使用率",
        "layer": Layer.QUERY,
        "layer_analysis": "{}",
        "possible_scenarios": [],
        "key_entities": [],
        "thinking_events": [],
    })

    assert result["query_result"]["query_target"] == "查询集群每个节点 CPU 和内存使用率"
    assert result["query_result"]["rows"][0]["node"] == "master"
    assert len(node.ai_call.calls) == 1


def test_extract_tool_data_prefers_full_result_over_preview():
    node = EvidenceCollectorNode()

    tool_data = node._extract_tool_data_from_thinking([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "result_preview": '{"status":"success","data":"truncated"}',
            "result": '{"status":"success","data":{"result":[{"metric":{"node":"master"},"value":[1,"13.7"]}]}}',
            "duration_seconds": 1.2,
        }
    ])

    assert tool_data == [
        {
            "tool": "execute_prometheus_instant_query",
            "data": '{"status":"success","data":{"result":[{"metric":{"node":"master"},"value":[1,"13.7"]}]}}',
            "duration_s": 1.2,
            "semantic_success": True,
            "raw_ref": None,
            "structured_ref": None,
            "summary_ref": None,
        }
    ]


def test_rca_lite_mode_no_output_uses_generic_llm_fallback():
    node = RootCauseAnalyzerNode()
    node.ai_call = object()
    node._call_structured_agent = lambda *args, **kwargs: (None, SimpleNamespace(result=""), [])

    result, thinking_events = node._analyze_with_llm_lite(
        question="我的服务为什么异常",
        layer=Layer.L2,
        evidence_summary="1. [✅ 已采集] pod 重启",
    )

    assert result["confidence"] <= 0.2
    assert "不符合 RCA 结构化输出合同" in result["confidence_reason"]
    assert result["root_cause"]
    assert thinking_events == []


def test_rca_lite_mode_enables_text_fallback_after_native_structured_failure():
    node = RootCauseAnalyzerNode()
    node.workflow_config_override = {
        "rca_structured_output": {"schema": "full"},
    }
    node.ai_call = object()
    captured = {}

    def _fake_structured_agent(*args, **kwargs):
        captured.update(kwargs)
        parsed = RCAOutput.model_validate({
            "root_cause": "Pod 删除卡在 preStop hook",
                "root_cause_summary": "Pod 删除卡在 preStop hook",
                "causal_chain": {"root_cause": "preStop hook sleep 21600"},
                "confidence": 0.95,
                "confidence_reason": "Pod 生命周期配置明确包含长时间 preStop sleep",
            })
        return parsed, SimpleNamespace(result=parsed.model_dump_json()), []

    node._call_structured_agent = _fake_structured_agent

    result, _thinking_events = node._analyze_with_llm_lite(
        question="我的服务为什么异常",
        layer=Layer.L1,
        evidence_summary="kubectl_get_yaml: finalizers: <none>; lifecycle.preStop sleep 21600",
    )

    assert result["confidence"] == 0.95
    assert captured["schema"] is RCAOutput
    assert captured["use_tools"] is False
    assert captured["allow_text_fallback"] is True


def test_rca_lite_mode_exception_uses_generic_llm_fallback_without_rules():
    node = RootCauseAnalyzerNode()
    node.ai_call = object()

    def _raise(*args, **kwargs):
        raise RuntimeError("llm timeout")

    node._call_structured_agent = _raise

    result, thinking_events = node._analyze_with_llm_lite(
        question="我的服务为什么异常",
        layer=Layer.L2,
        evidence_summary="1. [✅ 已采集] pod 重启",
    )

    assert result["confidence"] <= 0.2
    assert "llm timeout" in result["confidence_reason"]
    assert thinking_events == []


def test_conclusion_strips_think_blocks_from_final_report():
    content = "<think>内部推理不能展示</think>\n\n## 诊断概览\nPod ImagePullBackOff"

    assert ConclusionFormatterNode._strip_think_blocks(content) == "## 诊断概览\nPod ImagePullBackOff"


def test_conclusion_llm_prompt_includes_structured_diagnosis_context():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall("## 诊断概览\n证据完整度: 1/2 (50%)")

    evidence_analysis = """{
  "collection_summary": "计划 2 项，实际采集 1 项，未采集 1 项，完整度 50%；其中真实环境证据 1/2 项，完整度 50%",
  "plan_total": 2,
  "plan_collected": 1,
  "plan_completeness": 0.5,
  "environment_evidence_total": 2,
  "environment_evidence_collected": 1,
  "environment_evidence_completeness": 0.5,
  "evidence_inventory": [
    {
      "id": "e1",
      "description": "获取 Pod 事件",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl get events -n aaa",
      "purpose": "确认失败原因",
      "collected": true,
      "source": "thinking_match"
    },
    {
      "id": "e2",
      "description": "获取 Pod YAML",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod p -n aaa -o yaml",
      "purpose": "确认镜像配置",
      "collected": false,
      "source": "planned"
    }
  ],
  "missing_reasons": ["e2(获取 Pod YAML): 已规划但工具执行失败或无匹配结果"]
}"""
    rca_analysis = """{
  "phenomenon": "Pod ImagePullBackOff",
  "root_cause": "节点出口网络超时导致镜像拉取失败",
  "root_cause_summary": "节点出口网络超时导致镜像拉取失败",
  "confidence": 0.84,
  "causal_chain": {
    "root_cause": "节点出口网络超时",
    "propagation": "镜像无法下载",
    "direct_cause": "容器无法创建",
    "manifestation": "Pod ImagePullBackOff"
  },
  "primary_runbooks": ["pod-imagepull-failed.md"],
  "limitations": "未验证节点出口网络"
}"""

    node._generate_with_llm(
        question="我的集群有什么问题",
        layer_analysis='{"layer":"L3"}',
        evidence_analysis=evidence_analysis,
        rca_analysis=rca_analysis,
        layer=Layer.L3,
    )

    prompt = node.ai_call.calls[0]["kwargs"]["question"]
    assert "# 用户问题" in prompt
    assert "# 阶段1：问题定位" in prompt
    assert "# 阶段2：证据采集摘要" in prompt
    assert "采集完成度" not in prompt
    assert "获取 Pod 事件" in prompt
    assert "获取 Pod YAML" in prompt
    assert "- 缺失原因: e2(获取 Pod YAML): 已规划但工具执行失败或无匹配结果" in prompt
    assert "# 阶段3：根因分析" in prompt
    assert "- 根因结论: 节点出口网络超时导致镜像拉取失败" in prompt
    assert "- 置信度:" not in prompt
    assert "- 局限性: 未验证节点出口网络" in prompt
    assert "# 工具采集的真实数据" in prompt
    assert "不输出修复建议或验证步骤" in prompt
    assert "kubectl rollout status deployment/<name>" not in prompt


def test_conclusion_prompt_does_not_inject_collection_statistics_block():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        """## 📊 诊断概览
## 🔍 现象描述
## 📊 可观测性数据（三维度 + 拓扑）
### 三大观测维度
| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |
|------|----------|----------|----------------------------------|----------|
## 🎯 根因分析
## 🛠️ 修复建议
"""
    )

    node._generate_with_llm(
        question="我的集群有什么问题",
        layer_analysis='{"layer":"L2"}',
        evidence_analysis=json.dumps({
            "collection_summary": "计划 1 项，实际采集 1 项",
            "plan_total": 1,
            "plan_collected": 1,
            "plan_completeness": 1.0,
            "evidence_inventory": [],
        }),
        rca_analysis="{}",
        layer=Layer.L2,
    )

    prompt = node.ai_call.calls[0]["kwargs"]["question"]
    assert "证据采集统计（系统数据" not in prompt
    assert "\nplan_stats:" not in prompt


def test_conclusion_token_budget_defaults_to_model_window(monkeypatch):
    monkeypatch.delenv("CONCLUSION_TOKEN_BUDGET", raising=False)
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    node = ConclusionFormatterNode()

    budget = node._resolve_context_token_budget(output_reserved=8192)

    assert 0 < budget < 32000
    assert budget <= 22000


def test_layer_prompt_is_diagnosis_and_healthy_only():
    expected_phrases = [
        "# 唯一职责：定位当前异常实体",
        "`HEALTHY / ABNORMAL`",
        "不分析根因",
        "交给 Evidence 节点",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
    assert "QUERY direct" not in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_event_validation_against_current_state():
    expected_phrases = [
        "以当前 Pod 状态为准",
        "事件只用于辅助定位",
        "不能把已消失或已恢复对象加入当前异常列表",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_defines_health_baseline_and_efficiency_rules():
    expected_phrases = [
        "不能仅凭 STATUS 判健康",
        "同时检查 Ready",
        "得到全部目标的当前状态",
        "立即停止",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_is_pod_abnormal_first():
    expected_phrases = [
        "哪些 Pod 当前异常",
        "abnormal_pods",
        "abnormal_groups",
        "pod_status_keyword",
        "pod_abnormal_type",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_global_abnormal_pod_scan_first():
    expected_phrases = [
        "未指定范围时先获取集群 Pod 列表",
        "`Running / Completed / Succeeded`",
        "其余当前非正常状态均保留",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_keeps_explicit_pod_request_in_scope():
    expected_phrases = [
        "指定 namespace/Pod 时只处理这些目标",
        "尊重用户范围",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_full_diagnosis_only_exposes_lightweight_locator_tools():
    class _Tool:
        def __init__(self, name):
            self.name = name

    node = LayerClassifierNode.__new__(LayerClassifierNode)
    node.tools = [
        _Tool("kubectl_get_by_kind_in_cluster"),
        _Tool("kubectl_get_by_name"),
        _Tool("fetch_runbook"),
        _Tool("kubectl_describe"),
        _Tool("kubectl_previous_logs"),
        _Tool("execute_prometheus_range_query"),
        _Tool("collect_aiops_case"),
    ]

    blocked = node._get_layer_blocked_tool_names()

    assert blocked == {
        "kubectl_describe",
        "kubectl_previous_logs",
        "execute_prometheus_range_query",
        "collect_aiops_case",
    }


def test_layer_explicit_pod_stop_checker_stops_after_target_pod_status():
    node = LayerClassifierNode()
    question = (
        "请诊断 namespace aiops-traced-oom 中 Pod "
        "trace-oom-api-598dcf5996-x6v6n 当前反复重启的问题"
    )
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "fetch_runbook",
            "tool_args": {"runbook_id": "pod-oomkilled.md"},
            "result": "OOMKilled runbook",
        },
        {
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {
                "kind": "pod",
                "name": "trace-oom-api-598dcf5996-x6v6n",
                "namespace": "aiops-traced-oom",
            },
            "result": (
                "NAME READY STATUS RESTARTS AGE\n"
                "trace-oom-api-598dcf5996-x6v6n 0/1 CrashLoopBackOff 15 70m"
            ),
        },
    ]

    assert node._should_stop_explicit_pod_early(question, events) is True


def test_layer_explicit_pod_stop_checker_ignores_global_or_failed_results():
    node = LayerClassifierNode()
    question = "我的集群现在有什么问题？"
    target_result = {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "kubectl_get_by_name",
        "tool_args": {
            "kind": "pod",
            "name": "trace-oom-api-598dcf5996-x6v6n",
            "namespace": "aiops-traced-oom",
        },
        "result": "trace-oom-api-598dcf5996-x6v6n CrashLoopBackOff",
    }
    failed_result = {
        **target_result,
        "semantic_success": False,
        "result": "No resources found in aiops-traced-oom namespace.",
    }

    assert node._should_stop_explicit_pod_early(question, [target_result]) is False
    assert node._should_stop_explicit_pod_early(
        "请诊断 aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n",
        [failed_result],
    ) is False


def test_layer_explicit_multi_pod_stop_waits_for_total_fan_in_in_any_order():
    node = LayerClassifierNode()
    targets = [
        ("team-a", "api-a"),
        ("team-b", "api-b"),
        ("team-c", "api-c"),
    ]
    question = "请诊断 " + " ".join(
        f"{namespace}/{name}" for namespace, name in targets
    )

    def result(namespace, name, *, semantic_success=True):
        return {
            "type": "tool_result",
            "status": "success",
            "semantic_success": semantic_success,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {
                "kind": "pod",
                "namespace": namespace,
                "name": name,
            },
            "result": f"NAME READY STATUS\n{name} 0/1 Pending",
        }

    events = [result(*targets[2]), result(*targets[0])]
    assert node._should_stop_explicit_pod_early(question, events) is False
    assert node._should_stop_explicit_pod_early(
        question,
        [*events, result(*targets[1])],
    ) is True
    assert node._should_stop_explicit_pod_early(
        question,
        [*events, result(*targets[1], semantic_success=False)],
    ) is False


def test_layer_extracts_ordered_explicit_pod_targets_from_supported_notation():
    targets = LayerClassifierNode._extract_explicit_pod_targets(
        "请诊断 team-a/api-a、namespace team-b 中 Pod api-b，Pod api-c 位于 namespace team-c",
        [
            {"type": "Pod", "namespace": "team-d", "name": "api-d"},
            {"type": "Pod", "namespace": "team-a", "name": "api-a"},
        ],
    )

    assert targets == [
        ("team-a", "api-a"),
        ("team-b", "api-b"),
        ("team-c", "api-c"),
    ]


def test_layer_extracts_five_natural_language_pairs_atomically():
    question = (
        "请分别诊断：namespace ns-01 中 Pod pod-a；"
        "namespace ns-02 中 Pod pod-b；"
        "namespace ns-04 中 Pod pod-c；"
        "namespace ns-06 中 Pod pod-d；"
        "namespace ns-09 中 Pod pod-e。"
    )

    targets = LayerClassifierNode._extract_explicit_pod_targets(
        question,
        [
            # Model extraction must not cross-pair or extend explicit text.
            {"type": "Pod", "namespace": "ns-02", "name": "pod-a"},
            {"type": "Pod", "namespace": "ns-extra", "name": "pod-extra"},
        ],
    )

    assert targets == [
        ("ns-01", "pod-a"),
        ("ns-02", "pod-b"),
        ("ns-04", "pod-c"),
        ("ns-06", "pod-d"),
        ("ns-09", "pod-e"),
    ]


def test_layer_runs_one_parallel_named_lookup_per_explicit_pod():
    captured = {}

    class _BatchAICall:
        def execute_tool_batch(self, **kwargs):
            captured.update(kwargs)
            return [{"type": "tool_result", "status": "success"}]

    node = LayerClassifierNode()
    node.ai_call = _BatchAICall()
    node.tools = [object()]
    node.current_run_id = "run-layer-fan-in"

    events = node._run_explicit_pod_location_baseline(
        "请诊断 team-a/api-a team-b/api-b team-c/api-c"
    )

    assert events == [{"type": "tool_result", "status": "success"}]
    assert captured["tool_requests"] == [
        {
            "tool_name": "kubectl_get_by_name",
            "tool_args": {"kind": "pod", "namespace": "team-a", "name": "api-a"},
        },
        {
            "tool_name": "kubectl_get_by_name",
            "tool_args": {"kind": "pod", "namespace": "team-b", "name": "api-b"},
        },
        {
            "tool_name": "kubectl_get_by_name",
            "tool_args": {"kind": "pod", "namespace": "team-c", "name": "api-c"},
        },
    ]
    assert captured["max_workers"] == 3
    assert captured["run_id"] == "run-layer-fan-in"


def test_layer_runs_exactly_five_baseline_calls_for_five_clauses():
    captured = {}

    class _BatchAICall:
        def execute_tool_batch(self, **kwargs):
            captured.update(kwargs)
            return []

    node = LayerClassifierNode()
    node.ai_call = _BatchAICall()
    node.tools = [object()]
    node.current_run_id = "run-five-targets"
    question = "；".join(
        f"namespace ns-{index:02d} 中 Pod pod-{index}"
        for index in range(1, 6)
    )

    node._run_explicit_pod_location_baseline(question)

    assert len(captured["tool_requests"]) == 5
    assert [
        (request["tool_args"]["namespace"], request["tool_args"]["name"])
        for request in captured["tool_requests"]
    ] == [
        (f"ns-{index:02d}", f"pod-{index}")
        for index in range(1, 6)
    ]


def test_layer_prompt_defines_pod_abnormal_type_taxonomy_and_derived_layer():
    expected_phrases = [
        "pod_status_keyword",
        "status_category",
        "轻量 `pod_abnormal_type` 归一化",
        "状态之外证据不足时保持通用类型",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_extract_prompt_preserves_pod_abnormal_type_taxonomy():
    extract_prompt = get_workflow_prompt("layer_extract")
    expected_phrases = [
        "只做当前状态提取",
        "`ABNORMAL`",
        "`HEALTHY`",
        "`pod_abnormal_type`",
        "无法细分时保留通用状态类型",
    ]

    for phrase in expected_phrases:
        assert phrase in extract_prompt


def test_layer_prompt_does_not_rely_on_general_health_runbooks():
    assert "private-k8s-health-reference.md" not in LAYER_CLASSIFIER_PROMPT
    assert "l4-dependency-503" not in LAYER_CLASSIFIER_PROMPT


def test_layer_extract_prompt_is_current_state_first():
    extract_prompt = get_workflow_prompt("layer_extract")
    expected_phrases = [
        "当前仍异常的全部 Pod",
        "状态关键字",
        "`pod_abnormal_type`",
        "历史事件",
        "`HEALTHY`",
    ]

    for phrase in expected_phrases:
        assert phrase in extract_prompt


def test_rca_prompt_delegates_shape_to_small_runtime_schema():
    rca_prompt = get_workflow_prompt("rca")
    expected_phrases = [
        "# 输出",
        "运行时 Pydantic schema",
        "关键证据字段",
        "少量真实原始观察",
        "不为了结构完整生成假设清单",
        "不输出 Markdown、代码块或额外说明",
    ]

    for phrase in expected_phrases:
        assert phrase in rca_prompt


def test_query_direct_prompt_boundaries_are_explicit():
    direct_prompt = get_workflow_prompt("layer_query_direct")
    expected_phrases = [
        "如果是 QUERY，你必须调用工具采集真实数据，并在本轮最终 JSON 中直接输出 `query_result`",
        "最终输出必须是纯 JSON",
        "`query_result` 必须可直接被 conclusion 节点本地渲染",
        "先把用户明确询问的查询项逐项列为采集清单",
        "每个查询项最终必须只有两种状态：已由真实 tool_result 支撑，或明确写入缺失项",
        "禁止把“已经发出的工具调用都返回了”当成“用户问题已完整回答”",
        "只采集用户明确询问的对象、维度和指标，不扩展无关指标",
        "优先调用 `fetch_runbook` 获取 `private-k8s-query-promql-reference.md` 作为查询参考",
        "涉及 Prometheus 指标查询时，必须先调用 `fetch_runbook`",
        "禁止跳过 runbook 直接调用 Prometheus 探索或自创 PromQL",
        "runbook 中已有直接适用模板时，必须优先逐字复用标准 PromQL",
        "execute_prometheus_instant_query",
        "execute_prometheus_range_query",
        "execute_pod_promql",
        "一旦已经获得回答用户问题所需的关键数据，立即停止采集并输出 JSON",
    ]

    for phrase in expected_phrases:
        assert phrase in direct_prompt


def test_query_prometheus_runbook_declares_query_and_pod_diagnosis_tool_boundary():
    configmap = yaml.safe_load(
        Path("deploy/configmap/runbooks.yaml").read_text(encoding="utf-8")
    )
    query_runbook = configmap["data"]["private-k8s-query-promql-reference.md"]

    assert "/query" in query_runbook
    assert "/ask" in query_runbook
    assert "execute_prometheus_instant_query" in query_runbook
    assert "execute_prometheus_range_query" in query_runbook
    assert "execute_pod_promql" in query_runbook


def test_deployed_workflow_disables_layer_early_stop_by_default():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    layer_early_stop = app_config["workflow"]["layer"]["early_stop"]
    assert layer_early_stop["enabled"] is False
    assert layer_early_stop["explicit_pod_enabled"] is True


def test_deployed_workflow_disables_rca_validation():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    assert app_config["workflow"]["rca_validation"]["enabled"] is False
    assert (
        app_config["workflow"]["rca_context"]["fact_ledger_enabled"]
        is False
    )
    assert (
        app_config["workflow"]["rca_context"]
        ["include_evidence_llm_analysis"]
        is True
    )
    assert app_config["workflow"]["rca_structured_output"]["schema"] == "compact"
    assert (
        app_config["workflow"]["evidence"]
        ["observability_first_round_gate"]["retry_failed_once"]
        is True
    )


def test_oom_and_liveness_runbooks_contain_scoped_query_shape_examples():
    configmap = yaml.safe_load(
        Path("deploy/configmap/runbooks.yaml").read_text(encoding="utf-8")
    )
    oom = configmap["data"]["pod-oomkilled.md"]
    crashloop = configmap["data"]["pod-crashloop-runtime.md"]

    for runbook in (oom, crashloop):
        assert '"tool":"execute_pod_promql"' in runbook
        assert '"query_type":"range"' in runbook
        assert '"tool":"query_pod_logs"' in runbook
        assert '"tool":"query_pod_tracing"' in runbook
        assert '"purpose":' in runbook
    assert "container_memory_working_set_bytes" in oom
    assert '"trace_id":"<trace_id>"' in oom
    assert '"request_resource":"<probe-path>"' in crashloop
    assert "不同 endpoint" in crashloop


def test_deployed_config_enables_autonomous_observability_and_disables_compatibility_servers():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    autonomous = app_config["mcp_servers"]["aiops-observability-query"]
    assert autonomous["enabled"] is True
    assert autonomous["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8100/sse"
    assert autonomous["config"]["mode"] == "sse"

    prometheus = app_config["mcp_servers"]["prometheus_tool"]
    assert prometheus["enabled"] is True
    assert (
        prometheus["config"]["url"]
        == "http://mcp-server-manager.mcp.svc.cluster.local:8095/sse"
    )
    assert prometheus["config"]["mode"] == "sse"
    assert "/query" in prometheus["description"]
    assert "/ask" in prometheus["description"]
    assert "execute_pod_promql" in prometheus["description"]

    coarse = app_config["mcp_servers"]["aiops-case-coarse"]
    assert coarse["enabled"] is False
    assert coarse["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8089/sse"
    assert coarse["config"]["mode"] == "sse"

    fine = app_config["mcp_servers"]["aiops-observability-fine"]
    assert fine["enabled"] is False
    assert fine["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8090/sse"
    assert fine["config"]["mode"] == "sse"
    assert app_config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert (
        app_config["workflow"]["evidence"]["observability_first_round_gate"]["enabled"]
        is True
    )


def test_query_evidence_normalization_prompt_is_disabled():
    assert get_query_evidence_normalization_prompt("zh") == ""


def test_layer_prompts_prioritize_runbook_as_high_priority_reference():
    expected_phrases = [
        "# Runbook",
        "只为已定位的异常类型选择直接相关 Runbook",
        "Runbook 只提供待验证问题",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_delegates_distinct_runbook_selection_to_qwen_without_duplicates():
    expected_phrases = [
        "只为已定位的异常类型选择",
        "同一 Runbook 最多获取一次",
        "无法可靠匹配时不强行选择",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_evidence_prompt_requires_pod_handoff_and_autonomous_observability_contract():
    expected_phrases = [
        "# 唯一职责：为当前作用域采集根因证据",
        "`layer_handoff` 指定的实体",
        "真实工具结果",
        "Kubernetes、Metrics、Logging、Tracing、Topology",
        "每次补证必须有新的明确 `purpose`",
        "NotFound、空结果、命令失败和身份冲突也要保留",
        "不为了维度齐全",
    ]

    for phrase in expected_phrases:
        assert phrase in EVIDENCE_COLLECTOR_PROMPT

    assert "collect_aiops_case" not in EVIDENCE_COLLECTOR_PROMPT
    assert "get_aiops_case_evidence" not in EVIDENCE_COLLECTOR_PROMPT
    assert "recommended_runbooks" not in EVIDENCE_COLLECTOR_PROMPT
    assert "evidence_plan 第一项应为 `fetch_runbook`" not in EVIDENCE_COLLECTOR_PROMPT


def test_workflow_prompts_default_to_chinese_and_support_english_switch():
    zh_prompt = get_workflow_prompt("layer")
    en_prompt = get_workflow_prompt("layer", prompt_language="en")

    assert "唯一职责：定位当前异常实体" in zh_prompt
    assert en_prompt == zh_prompt


def test_english_layer_prompt_is_diagnosis_and_healthy_only():
    en_prompt = get_workflow_prompt("layer", prompt_language="en")

    assert "唯一职责：定位当前异常实体" in en_prompt
    assert "If QUERY" not in en_prompt
    assert '"layer": "HEALTHY/L0/L1/L2/L3/L4/QUERY"' not in en_prompt


def test_workflow_prompts_do_not_contain_json_output_templates():
    prompt_names = [
        "layer",
        "layer_extract",
        "layer_query_direct",
        "layer_query_direct_extract",
        "evidence",
        "tool_observation_summarizer",
        "rca",
    ]
    forbidden = [
        "```json",
        "只输出 JSON",
        "输出 JSON",
        "纯 JSON",
        "最终 JSON",
        "evidence_plan JSON",
        "JSON 模板",
        "手写 JSON",
        "手写结构化示例",
    ]
    for name in prompt_names:
        prompt = get_workflow_prompt(name)
        if name in {"rca", "layer_query_direct"}:
            # RCA keeps a JSON text-fallback contract. `/query` direct also
            # intentionally uses JSON text output to avoid a second Pydantic
            # extraction call on the fast query path.
            continue
        for phrase in forbidden:
            assert phrase not in prompt


def test_remediation_plan_prompt_centralizes_workload_verify_rules():
    assert "REMEDIATION_PLAN_PROMPT" not in get_workflow_prompt("conclusion")
    assert "verify_command 禁止使用当前异常 Pod 的固定名称" in REMEDIATION_PLAN_PROMPT
    assert "kubectl rollout status deployment/<name>" in REMEDIATION_PLAN_PROMPT
    assert "仅因为探测命令返回某个常见名称 NotFound" in REMEDIATION_PLAN_PROMPT
    assert "查询 workload 模板" in REMEDIATION_PLAN_PROMPT
    assert "TerminatingStuck" in REMEDIATION_PLAN_PROMPT
    assert "kubectl patch pod <pod>" in REMEDIATION_PLAN_PROMPT
    assert "metadata.finalizers" in REMEDIATION_PLAN_PROMPT
    assert "remediation_available\": false" in REMEDIATION_PLAN_PROMPT


def test_conclusion_prompt_supports_independent_response_language():
    prompt = get_workflow_prompt(
        "conclusion",
        prompt_language="en",
        response_language="en",
    )

    assert "## 📊 异常概览与现象" in prompt
    assert "All user-facing final report text must be in English." in prompt


def test_conclusion_mode_instructions_are_centrally_managed():
    query_instruction = get_conclusion_mode_instruction("query", "查询 CPU", prompt_language="zh")
    healthy_instruction = get_conclusion_mode_instruction("healthy", "我的集群健康吗", prompt_language="zh")
    query_instruction_en = get_conclusion_mode_instruction("query", "show CPU", prompt_language="en")

    assert "只回答用户明确询问的对象、维度和指标" in query_instruction
    assert "绝对不要猜测" in query_instruction
    assert healthy_instruction == ""
    assert "绝对不要猜测" in query_instruction_en
    assert "show CPU" in query_instruction_en


def test_holmes_service_i18n_getters_preserve_default_behavior_and_allow_override():
    service = HolmesService()
    assert service.get_prompt_language() == "zh"
    assert service.get_response_language() == "zh"

    service.i18n_config = {"prompt_language": "en", "response_language": "en"}
    assert service.get_prompt_language() == "en"
    assert service.get_response_language() == "en"


def test_autonomous_observability_uses_model_selected_query_contract():
    """The agent selects scoped follow-ups without fault-specific routing."""
    from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode

    assert not hasattr(EvidenceCollectorNode, "_inject_aiops_case_plan_item")
    assert hasattr(EvidenceCollectorNode, "_ensure_mandatory_aiops_case_plan")
    assert "不按故障类型使用固定工具链" in EVIDENCE_COLLECTOR_PROMPT
    assert "每次补证必须有新的明确 `purpose`" in EVIDENCE_COLLECTOR_PROMPT
    assert "上下文使用率达到 80% 时停止新增采集" in EVIDENCE_COLLECTOR_PROMPT
    assert "Qwen" not in EVIDENCE_COLLECTOR_PROMPT
    assert "mandatory" not in EVIDENCE_COLLECTOR_PROMPT


def test_aiops_prompts_preserve_exact_observability_and_causality():
    assert "facts、samples、query、原始错误和 evidence_refs" in EVIDENCE_COLLECTOR_PROMPT
    assert "DeepFlow flow 与 Tempo span 分开解释" in EVIDENCE_COLLECTOR_PROMPT
    assert "`coverage=present` 只表示命中数据" in EVIDENCE_COLLECTOR_PROMPT
    assert "`empty/absent/weak/error` 表示数据边界" in EVIDENCE_COLLECTOR_PROMPT
    assert "原始数值、单位、状态、错误文本和标识符保持原意" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "完整 trace_id" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "查询成功、coverage、完整度和计划状态本身不是证据" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "只有状态、coverage 或普通成功请求时不能确诊" in ROOT_CAUSE_ANALYZER_PROMPT
    # 结论富模板：只依赖真实数据，不复述旧版事实合同措辞
    assert "只用真实" in CONCLUSION_FORMATTER_PROMPT
    assert "禁止编造" in CONCLUSION_FORMATTER_PROMPT


def test_conclusion_prompt_is_human_focused_and_grounded():
    prompt = CONCLUSION_FORMATTER_PROMPT

    for heading in (
        "## 📊 异常概览与现象",
        "## 🕵️ 证据内容 · <组号>",
        "## 🎯 根因分析",
    ):
        assert heading in prompt
    assert "## 🛠️ 修复建议" not in prompt
    assert "## 📋 验证步骤" not in prompt
    assert "只用真实" in prompt
    assert "禁止编造" in prompt
    assert "含 `numeric_fields` 时，必须展示 first/last 或 min/max" in prompt
    assert "每个维度至少展示一条代表证据" in prompt
    assert "不得仅因与 Kubernetes 部分重复而整维省略" in prompt
    assert "不得写成“单个请求内部”" in prompt


def test_active_workflow_prompts_stay_within_attention_budgets():
    budgets = {
        "layer": 2600,
        "layer_extract": 1400,
        "layer_query_direct": 1900,
        "evidence": 4000,
        "rca": 4300,
    }

    for name, ceiling in budgets.items():
        assert len(get_workflow_prompt(name)) <= ceiling


def test_runtime_prompts_encode_tasks_not_prompt_methodology():
    active = "\n".join(
        get_workflow_prompt(name)
        for name in (
            "layer",
            "layer_extract",
            "layer_query_direct",
            "evidence",
            "rca",
            "conclusion",
        )
    )

    for phrase in ("第一性原理", "隐性提纯", "负向配平", "高维潜空间"):
        assert phrase not in active


def test_rca_and_conclusion_prompts_require_verbatim_per_pod_observability():
    rca_phrases = [
        "锁定当前 namespace/Pod/UID",
        "只使用该实体的真实工具结果",
        "来源工具 + 真实值/原文 + 诊断作用",
        "原始数值、单位、状态、错误文本和标识符保持原意",
    ]

    for phrase in rca_phrases:
        assert phrase in ROOT_CAUSE_ANALYZER_PROMPT


def test_active_rca_and_conclusion_prompts_are_fixture_free():
    active_prompts = ROOT_CAUSE_ANALYZER_PROMPT + CONCLUSION_FORMATTER_PROMPT
    for forbidden in (
        "PAYMENT_GATEWAY_TOKEN",
        "/allocate",
        "trace-oom",
        "trace-config",
        "aiops-traced",
        "required config PAYMENT_GATEWAY_TOKEN is missing",
    ):
        assert forbidden not in active_prompts

    for phrase in (
        "原始数值、单位、状态、错误文本和标识符保持原意",
        "只有完整 trace_id 相同时",
        "输入中存在 fact_id 时一并保留",
    ):
        assert phrase in ROOT_CAUSE_ANALYZER_PROMPT


def test_active_rca_and_conclusion_prompts_have_no_fault_specific_anchor():
    active = ROOT_CAUSE_ANALYZER_PROMPT + CONCLUSION_FORMATTER_PROMPT
    for fault_specific in (
        "OOMKilled",
        "ImagePullBackOff",
        "CrashLoopBackOff",
        "Exit Code 137",
        "96Mi",
        "finalizer",
    ):
        assert fault_specific not in active
    assert "明确原因、失败事件和原始错误优先" in active
    assert "Runbook、候选场景" in active


def test_prompts_refine_runbooks_after_live_evidence_and_preserve_topology_semantics():
    assert "计划、Runbook 和归档不是证据" in EVIDENCE_COLLECTOR_PROMPT
    assert "不为了维度齐全" in EVIDENCE_COLLECTOR_PROMPT
    assert "补充更具体的 runbook" not in EVIDENCE_COLLECTOR_PROMPT
    assert "拿到 `collect_aiops_case` 的真实结果后" not in EVIDENCE_COLLECTOR_PROMPT
    assert "通用 CrashLoop runbook" not in EVIDENCE_COLLECTOR_PROMPT


def test_diagnostic_prompts_are_focused_and_bounded():
    assert len(LAYER_CLASSIFIER_PROMPT) < 1200
    assert len(EVIDENCE_COLLECTOR_PROMPT) < 1200
    assert len(ROOT_CAUSE_ANALYZER_PROMPT) < 2000
    assert "最终根因报告或修复方案" in EVIDENCE_COLLECTOR_PROMPT
    assert "根本原因 → 失败机制 → 直接失败 → 当前现象" in ROOT_CAUSE_ANALYZER_PROMPT


def test_deployment_enables_autonomous_evidence_context_stop():
    manifest_path = Path(__file__).resolve().parents[3] / "deploy" / "configmap" / "config.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(manifest["data"]["config.yaml"])

    assert config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert config["workflow"]["evidence"]["early_stop"]["enabled"] is True


def test_conclusion_tool_data_uses_final_observability_projection():
    node = ConclusionFormatterNode()
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_pod_promql",
            "semantic_success": False,
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "purpose": "确认内存趋势",
            },
            "result_preview": "invalid_time_range",
            "structured": {
                "status": "query_rejected",
                "dimension": "metrics",
                "coverage": "error",
                "entity": {"namespace": "demo", "pod": "api"},
                "purpose": "确认内存趋势",
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_pod_promql",
            "semantic_success": True,
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "purpose": "确认内存趋势",
            },
            "result_preview": "memory-working-set=70168576",
            "structured": {
                "status": "query_succeeded",
                "dimension": "metrics",
                "coverage": "present",
                "entity": {"namespace": "demo", "pod": "api"},
                "purpose": "确认内存趋势",
                "facts": [{
                    "name": "container_memory_working_set_bytes",
                    "value": "70168576", "unit": "bytes", "dimension": "metrics",
                }],
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_pod_promql",
            "semantic_success": True,
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "purpose": "确认重启增量",
            },
            "result_preview": "restart-increase=4",
            "structured": {
                "status": "query_succeeded",
                "dimension": "metrics",
                "coverage": "present",
                "entity": {"namespace": "demo", "pod": "api"},
                "purpose": "确认重启增量",
                "facts": [{
                    "name": "kube_pod_container_status_restarts_total",
                    "value": "4", "unit": "count", "dimension": "metrics",
                }],
            },
        },
    ]

    section = node._build_tool_data_section(events)

    assert "70168576" in section
    assert "= 4 count" in section
    assert "invalid_time_range" not in section


def test_conclusion_projection_excludes_transport_only_query_success():
    node = ConclusionFormatterNode()
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "semantic_success": False,
            "tool_name": "execute_pod_promql",
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "purpose": "确认内存趋势",
            },
            "result_preview": "invalid_time_range",
            "structured": {
                "status": "query_rejected",
                "dimension": "metrics",
                "coverage": "error",
                "entity": {"namespace": "demo", "pod": "api"},
                "purpose": "确认内存趋势",
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_pod_promql",
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "purpose": "确认内存趋势",
            },
            "result_preview": "transport-only-memory=70168576",
            "structured": {
                "status": "query_succeeded",
                "dimension": "metrics",
                "coverage": "present",
                "entity": {"namespace": "demo", "pod": "api"},
                "purpose": "确认内存趋势",
                "facts": [],
            },
        },
    ]

    section = node._build_tool_data_section(events)

    # transport-only（HTTP 成功但无真实事实）不伪装成有数据；
    # 结构化路径下渲染为诚实"未返回真实数据"，不吐出 result_preview 里的假值
    assert "transport-only-memory=70168576" not in section
    assert "未返回真实数据" in section


def test_offline_replay_fixture_import_enforces_measured_boundary():
    repo_root = Path(__file__).resolve().parents[3]
    replay_path = (
        repo_root
        / "tests/fixtures/observability/offline_replay_import.py"
    )
    probe = r'''
import json
import os
import runpy
import socket
import subprocess
import sys

attempts = []


def blocked(category, target):
    attempts.append({"category": category, "target": str(target)})
    raise RuntimeError(f"external access blocked: {category}: {target}")


def block_socket_connect(_socket, address, *args, **kwargs):
    return blocked("network", address)


def block_create_connection(address, *args, **kwargs):
    return blocked("network", address)


def block_process(*args, **kwargs):
    target = args[0] if args else kwargs
    return blocked("subprocess", target)


socket.socket.connect = block_socket_connect
socket.socket.connect_ex = block_socket_connect
socket.create_connection = block_create_connection
subprocess.Popen = block_process
subprocess.run = block_process
subprocess.call = block_process
subprocess.check_call = block_process
subprocess.check_output = block_process
os.system = block_process

error = None
driver_audit = None
try:
    namespace = runpy.run_path(sys.argv[1], run_name="a026_replay_import")
    guard = namespace.get("OFFLINE_GUARD")
    if guard is None:
        error = "replay driver did not expose OFFLINE_GUARD"
    else:
        driver_audit = guard.audit()
except BaseException as exc:
    error = f"{type(exc).__name__}: {exc}"

payload = {
    "attempts": attempts,
    "driver_audit": driver_audit,
    "error": error,
}
print(json.dumps(payload, sort_keys=True))
if (
    error
    or attempts
    or not driver_audit
    or driver_audit.get("attempt_count") != 0
    or driver_audit.get("attempts") != []
    or driver_audit.get("enforced") is not True
    or set(driver_audit.get("guarded_categories") or [])
    != {"network", "subprocess", "llm", "mcp", "kubernetes"}
):
    raise SystemExit(1)
'''
    completed = subprocess.run(
        [sys.executable, "-c", probe, str(replay_path)],
        cwd=repo_root,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
