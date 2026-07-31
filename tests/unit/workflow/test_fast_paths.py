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
    FACT_LEDGER_REMEDIATION_PLAN_PROMPT,
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
    attach_internal_report_authority,
    evaluate_report_authority,
)
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.schemas import (
    ConclusionOutput,
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

    def call(self, **kwargs):
        self.calls.append({"args": (), "kwargs": kwargs})
        structured = ConclusionOutput.model_validate({
            "title": "诊断报告",
            "diagnosis_overview": {},
            "evidence_chain": [],
            "root_cause": "",
            "recommendations": [],
            "limitations": [],
            "markdown_report": self.content,
        })
        return SimpleNamespace(
            result=structured.model_dump_json(),
            structured_response=structured,
            tool_call_count=0,
            duration_ms=1,
            iterations=1,
        ), [{"type": "structured_response", "node": "conclusion"}]

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

    assert result["layer"] == Layer.L2
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

    assert result["layer"] == Layer.L2
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
    assert result["layer"] == Layer.L2


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
    assert result["layer"] == Layer.L1


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


def test_conclusion_appends_machine_verifiable_exact_topology_edges():
    content = "\n".join([
        "## 拓扑关系",
        "- Pod trace-oom-api-pod --owned_by--> ReplicaSet trace-oom-api-rs",
    ])
    structured_context = "\n".join([
        "TOPOLOGY_ENTITY_COUNT value=11",
        "TOPOLOGY_EXACT_EDGES count=2",
        "REPORT_MUST_QUOTE_TOPOLOGY_VERBATIM=true",
        "FORBID_RELATIONSHIP_REVERSAL=true",
        (
            '- TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" '
            "source=trace-oom-api-pod target=trace-oom-api-rs "
            "directness=direct confidence=high"
        ),
        (
            '- TOPOLOGY relationship="ReplicaSet --owned_by--> Deployment" '
            "source=trace-oom-api-rs target=trace-oom-api "
            "directness=direct confidence=high"
        ),
    ])

    result = ConclusionFormatterNode._append_exact_topology_appendix(
        content,
        structured_context,
    )

    assert "## 附录：机器可核验拓扑原始边" in result
    assert "TOPOLOGY_ENTITY_COUNT value=11" in result
    assert "TOPOLOGY_EXACT_EDGES count=2" in result
    assert (
        'TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" '
        "source=trace-oom-api-pod target=trace-oom-api-rs "
        "directness=direct confidence=high"
    ) in result
    assert (
        'TOPOLOGY relationship="ReplicaSet --owned_by--> Deployment" '
        "source=trace-oom-api-rs target=trace-oom-api "
        "directness=direct confidence=high"
    ) in result


def test_conclusion_sanitizes_model_generated_evidence_ref_aliases():
    content = "\n".join([
        "## 📊 可观测性数据（三维度 + 拓扑）",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号 | 证据 ref |",
        "|------|----------|----------|--------------|----------|",
        "| Metrics | Prometheus | present | peak=76.9Mi | metric-oom-mem-high |",
        (
            "| Logging | Elasticsearch | present | CONFIG_MISSING | "
            "log-aiops-traced-config-api-current |"
        ),
        "## 🕵️ 证据链",
    ])
    structured_context = "\n".join([
        (
            "METRIC metric=container_memory_working_set_bytes "
            "evidence_ref=metric-aiops-traced-oom-api-prometheus"
        ),
        (
            "LOG event=config_missing "
            "evidence_ref=log-aiops-traced-config-api-current"
        ),
    ])

    result = ConclusionFormatterNode._sanitize_observability_evidence_refs(
        content,
        structured_context,
    )

    assert "metric-oom-mem-high" not in result
    assert "见机器可核验附录" in result
    assert "log-aiops-traced-config-api-current" in result


def test_conclusion_sanitizes_nonstandard_evidence_ref_aliases_and_plan_ids():
    content = "\n".join([
        "## 📊 可观测性数据（三维度 + 拓扑）",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号 | 证据 ref |",
        "|------|----------|----------|--------------|----------|",
        (
            "| Metrics | Prometheus | present | peak=77.0Mi | "
            "evidence_prometheus_metrics_oom |"
        ),
        (
            "| Logging | Elasticsearch | present | CONFIG_MISSING | "
            "ep-1-collect-case-config (Logging) |"
        ),
        (
            "| K8s | K8s-API | present | OOMKilled exit=137 | "
            "k8s-aiops-traced-oom-pod-last-terminated |"
        ),
        "## 🕵️ 证据链",
    ])
    structured_context = "\n".join([
        (
            "- METRIC metric=container_memory_working_set_bytes "
            "evidence_ref=metric-aiops-traced-oom-prometheus"
        ),
        (
            "- LOG event=config_missing "
            "evidence_ref=log-aiops-traced-config-previous"
        ),
        (
            '- K8S_SIGNAL observed="OOMKilled exit=137" '
            'evidence_refs=["k8s-aiops-traced-oom-pod-last-terminated"]'
        ),
    ])

    result = ConclusionFormatterNode._sanitize_observability_evidence_refs(
        content,
        structured_context,
    )

    assert "evidence_prometheus_metrics_oom" not in result
    assert "ep-1-collect-case-config" not in result
    assert result.count("见机器可核验附录") == 2
    assert "k8s-aiops-traced-oom-pod-last-terminated" in result


def test_conclusion_appends_machine_verifiable_k8s_signals():
    content = "\n".join([
        "## 根因结论",
        "Pod 发生了内存异常。",
    ])
    structured_context = "\n".join([
        "REPORT_MUST_QUOTE_K8S_SIGNAL_VERBATIM=true",
        (
            '- K8S_SIGNAL signal_id=sig-k8s-present strength=strong '
            'observed="Last terminated state: business-api=OOMKilled exit=137" '
            'evidence_refs=["k8s.trace-oom-api.last-terminated"]'
        ),
    ])

    result = ConclusionFormatterNode._append_exact_k8s_signal_appendix(
        content,
        structured_context,
    )

    assert "## 附录：机器可核验 Kubernetes 强证据" in result
    assert "REPORT_MUST_QUOTE_K8S_SIGNAL_VERBATIM=true" in result
    assert "Last terminated state: business-api=OOMKilled exit=137" in result
    assert "k8s.trace-oom-api.last-terminated" in result


def test_conclusion_appends_machine_verifiable_observability_facts():
    content = "\n".join([
        "## 根因结论",
        "应用内存随请求持续累积。",
    ])
    structured_context = "\n".join([
        "REPORT_MUST_QUOTE_OBSERVABILITY_FACTS_VERBATIM=true",
        "IGNORE_UNSUPPORTED_LAYER_NUMERIC_FACTS=true",
        (
            '- TRACE_CORRELATION log_tempo_trace_ids=["ba7cabb5d9d1d26b89951c07b70a60fa"] '
            'deepflow_trace_ids=["8ee108b5780011aa6a60a4b86c562fa8"] do_not_merge=true'
        ),
        (
            "- METRIC metric=container_memory_working_set_bytes start=3.7Mi "
            "max=74.9Mi limit=80.0Mi max_limit_ratio=0.9368"
        ),
        (
            "- LOG event=allocate trace_id=ba7cabb5d9d1d26b89951c07b70a60fa "
            "path=/allocate?mib=2&step=2018 allocated_mib=62"
        ),
        (
            '- DEEPFLOW src=172.16.104.8 dst=172.16.104.13 '
            'request="GET /allocate?mib=2&step=2019" duration_us=0 '
            "trace_id=8ee108b5780011aa6a60a4b86c562fa8"
        ),
        (
            '- TEMPO trace_id=ba7cabb5d9d1d26b89951c07b70a60fa '
            'span="GET /allocate" aiops.allocated_mib.before=60 '
            "aiops.allocated_mib.after=62"
        ),
    ])

    result = ConclusionFormatterNode._append_exact_observability_facts_appendix(
        content,
        structured_context,
    )

    assert "## 附录：机器可核验可观测性核心事实" in result
    assert "REPORT_MUST_QUOTE_OBSERVABILITY_FACTS_VERBATIM=true" in result
    assert "ba7cabb5d9d1d26b89951c07b70a60fa" in result
    assert "8ee108b5780011aa6a60a4b86c562fa8" in result
    assert "start=3.7Mi max=74.9Mi limit=80.0Mi" in result
    assert "allocated_mib=62" in result
    assert "do_not_merge=true" in result


def test_conclusion_corrects_tracing_absent_when_structured_trace_is_present():
    content = "\n".join([
        "## 📊 可观测性数据（三维度 + 拓扑）",
        "### 三大观测维度",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |",
        "|------|----------|----------|----------------------------------|----------|",
        "| **Metrics** | Prometheus | present | peak=66.9Mi | metric-real |",
        "| **Logging** | ES/Filebeat | present | CONFIG_MISSING | log-real |",
        "| **Tracing** | DeepFlow/Tempo | absent | 本轮未采集到 Trace 数据 | - |",
        "| **K8s** | Kubernetes API | present | OOMKilled exit=137 | k8s-real |",
        "### 拓扑关系（实体与边）",
    ])
    structured_context = "\n".join([
        (
            "COVERAGE k8s=present metrics=present logs=present "
            "tracing=present trace=present topology=present"
        ),
        (
            '- TRACE_CORRELATION log_tempo_trace_ids=["13fa16403170f1e56a27a32b18b50030"] '
            'deepflow_trace_ids=["13fa16403170f1e56a27a32b18b50030"] '
            'shared_trace_ids=["13fa16403170f1e56a27a32b18b50030"] '
            "do_not_merge=false"
        ),
        (
            '- DEEPFLOW src=172.16.104.8 dst=172.16.104.13 '
            'request="GET /allocate?mib=2&step=26246" response_code=200 '
            "duration_us=5918 trace_id=13fa16403170f1e56a27a32b18b50030 "
            "evidence_ref=deepflow-real"
        ),
        (
            '- TEMPO trace_id=13fa16403170f1e56a27a32b18b50030 '
            'service=aiops-traced-oom-api span="GET /allocate" '
            "aiops.allocated_mib.before=60 aiops.allocated_mib.after=62 "
            "evidence_ref=tempo-real"
        ),
    ])

    result = ConclusionFormatterNode._enforce_observability_dimension_table(
        content,
        structured_context,
    )

    tracing_row = next(
        line for line in result.splitlines()
        if line.startswith("| **Tracing**")
    )
    assert "| present |" in tracing_row
    assert "absent" not in tracing_row
    assert "13fa16403170f1e56a27a32b18b50030" in tracing_row
    assert "GET /allocate?mib=2&step=26246" in tracing_row
    assert "response_code=200" in tracing_row
    assert "duration_us=5918" in tracing_row
    assert "aiops.allocated_mib.before=60" in tracing_row
    assert "deepflow-real" in tracing_row
    assert "tempo-real" in tracing_row


def test_conclusion_marks_unexecuted_dimensions_as_unverified_not_absent():
    content = "\n".join([
        "## 📊 可观测性数据",
        "### 三大观测维度",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |",
        "|------|----------|----------|----------------------------------|----------|",
        "| **Metrics** | Prometheus | present | value=245760 KB | metric-real |",
        "| **Logging** | ES/Filebeat | absent | 本轮未采集到日志 | - |",
        "| **Tracing** | DeepFlow/Tempo | absent | 本轮未采集到 Trace | - |",
        "| **K8s** | Kubernetes API | present | OOMKilled exit=137 | k8s-real |",
    ])
    structured_context = "\n".join([
        (
            "OBSERVABILITY_EXECUTION "
            "metrics=present logging=not_executed tracing=not_executed"
        ),
        (
            "- QUERY_FACT ref=metric-real "
            "name=container_memory_working_set_bytes value=245760 "
            "unit=bytes sample_count=1 trend_evaluable=false "
            "series_role=pod_aggregate directness=related_context"
        ),
    ])

    result = ConclusionFormatterNode._enforce_observability_dimension_table(
        content,
        structured_context,
    )

    logging_row = next(
        line for line in result.splitlines()
        if line.startswith("| **Logging**")
    )
    tracing_row = next(
        line for line in result.splitlines()
        if line.startswith("| **Tracing**")
    )
    assert "| not_executed |" in logging_row
    assert "| not_executed |" in tracing_row
    assert "未验证" in logging_row
    assert "未验证" in tracing_row
    assert "absent" not in logging_row
    assert "absent" not in tracing_row


def test_conclusion_expands_metrics_logging_and_k8s_rows_from_exact_facts():
    content = "\n".join([
        "## 📊 可观测性数据（三维度 + 拓扑）",
        "### 三大观测维度",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |",
        "|------|----------|----------|----------------------------------|----------|",
        "| **Metrics** | Prometheus | present | series=34 | metric-old |",
        "| **Logging** | ES/Filebeat | present | 27 records | log-old |",
        "| **Tracing** | DeepFlow/Tempo | present | trace present | trace-old |",
        "| **K8s** | Kubernetes API | present | CrashLoopBackOff | k8s-old |",
        "### 拓扑关系（实体与边）",
    ])
    structured_context = "\n".join([
        (
            "COVERAGE k8s=present metrics=present logs=present "
            "tracing=present trace=present topology=present"
        ),
        (
            "- METRIC metric=container_memory_working_set_bytes "
            "pod=api-pod start=3.5Mi max=66.9Mi last=66.9Mi "
            "limit=80.0Mi max_limit_ratio=0.8365 "
            'samples=["02:53:25=3.5Mi","02:54:25=66.9Mi"] '
            "evidence_ref=metric-real"
        ),
        (
            '- LOG role=target event=config_missing level=error '
            'message="required config PAYMENT_GATEWAY_TOKEN is missing" '
            "trace_id=trace-config error_code=CONFIG_MISSING pod=api-pod "
            "evidence_ref=log-real"
        ),
        (
            '- K8S_SIGNAL signal_id=sig-k8s-present strength=strong '
            'observed="Last terminated state: business-api=Error exit=78" '
            'evidence_refs=["k8s-last","k8s-events"]'
        ),
        (
            '- DEEPFLOW request="GET /checkout" response_code=500 '
            "duration_us=4029 trace_id=trace-config evidence_ref=deepflow-real"
        ),
        (
            '- TEMPO trace_id=trace-config service=config-api '
            'span="GET /checkout" error.type=CONFIG_MISSING '
            "evidence_ref=tempo-real"
        ),
    ])

    result = ConclusionFormatterNode._enforce_observability_dimension_table(
        content,
        structured_context,
    )

    assert "series=34" not in result
    assert "metric=container_memory_working_set_bytes" in result
    assert "start=3.5Mi" in result
    assert "max=66.9Mi" in result
    assert "limit=80.0Mi" in result
    assert 'samples=["02:53:25=3.5Mi","02:54:25=66.9Mi"]' in result
    assert "27 records" not in result
    assert "required config PAYMENT_GATEWAY_TOKEN is missing" in result
    assert "error_code=CONFIG_MISSING" in result
    assert "Last terminated state: business-api=Error exit=78" in result
    assert "metric-real" in result
    assert "log-real" in result
    assert "k8s-last" in result


def test_conclusion_evidence_scope_preserves_observability_rows_with_html_breaks():
    content = "\n".join([
        "## 📊 可观测性数据（三维度 + 拓扑）",
        "### 三大观测维度",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |",
        "|------|----------|----------|----------------------------------|----------|",
        (
            "| **Metrics** | Prometheus | present | "
            "pod=config-api max=3.6Mi limit=96.0Mi<br>"
            "pod=oom-api max=75.0Mi limit=80.0Mi | metric-config<br>metric-oom |"
        ),
        (
            "| **Logging** | ES/Filebeat | present | "
            "required config PAYMENT_GATEWAY_TOKEN is missing<br>"
            "event=allocate allocated_mib=62 | log-config<br>log-oom |"
        ),
        (
            "| **Tracing** | DeepFlow/Tempo | present | "
            "GET /checkout response_code=500<br>"
            "GET /allocate response_code=200 | deepflow-config<br>tempo-oom |"
        ),
        (
            "| **K8s** | Kubernetes API | present | "
            "Error exit=78<br>OOMKilled exit=137 | k8s-config<br>k8s-oom |"
        ),
        "### 拓扑关系（实体与边）",
    ])
    structured_context = "\n".join([
        "AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff",
        "ENTITY kind=Pod namespace=ns name=config-api",
        (
            '- LOG event=config_missing message="required config '
            'PAYMENT_GATEWAY_TOKEN is missing" missing_config=PAYMENT_GATEWAY_TOKEN'
        ),
        "AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled",
        "ENTITY kind=Pod namespace=ns name=oom-api",
        (
            "- K8S_SIGNAL strength=strong "
            'observed="Last terminated state: app=OOMKilled exit=137"'
        ),
        (
            "- METRIC metric=container_memory_working_set_bytes pod=oom-api "
            "start=3.7Mi max=75.0Mi last=75.0Mi limit=80.0Mi "
            "max_limit_ratio=0.937"
        ),
    ])

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert sum(
        1
        for line in result.splitlines()
        if line.startswith("| **")
        and any(name in line for name in ("Metrics", "Logging", "Tracing", "K8s"))
    ) == 4
    assert "<br>" in result


def test_conclusion_metric_boundary_does_not_modify_fenced_remediation_json():
    content = """## 🎯 根因分析
- oom-api 内存从 3.7Mi 增至 75.0Mi，并突破 80Mi Limit。

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "issue_groups": [
    {
      "group_id": "g1",
      "problem_type": "OOMKilled",
      "auto_fixable": false,
      "strategy": "应用内存逼近 limit，触发 OOMKilled；先采集基线"
    }
  ],
  "actions": []
}
```
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=oom-api start=3.7Mi max=75.0Mi last=75.0Mi limit=80.0Mi max_limit_ratio=0.937
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    remediation_body = result.split("```json", 1)[1].split("```", 1)[0]
    parsed = json.loads(remediation_body)
    assert parsed["issue_groups"][0]["strategy"] == (
        "应用内存逼近 limit，触发 OOMKilled；先采集基线"
    )
    assert "Prometheus 观测峰值 `75.0Mi`" in result.split("```json", 1)[0]


def test_conclusion_validation_rejects_invalid_remediation_json():
    content = """## 📊 诊断概览
## 🔍 证据链
## 🎯 根因分析
## 🛠️ 修复建议
## 🧩 结构化修复计划
```json
{
  "remediation_available": true,
  "actions": [
    {"id": "a1",}
  ]
}
```
"""

    errors = ConclusionFormatterNode._diagnosis_report_validation_errors(content)

    assert "invalid_remediation_json" in errors


def test_conclusion_repairs_invalid_remediation_json_to_safe_manual_plan():
    content = """## 📊 诊断概览
## 🔍 证据链
## 🎯 根因分析
## 🛠️ 修复建议
## 🧩 结构化修复计划
```json
{
  "remediation_available": true,
  "actions": [
    {"id": "a1",}
  ]
}
```
"""

    result = ConclusionFormatterNode._repair_invalid_remediation_json(content)
    plan = extract_remediation_plan(result)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.actions == []
    assert "invalid_remediation_json" not in (
        ConclusionFormatterNode._diagnosis_report_validation_errors(result)
    )


def test_conclusion_execute_runs_final_validation_after_postprocessors(monkeypatch):
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        """## 📊 诊断概览
## 🔍 证据链
## 🎯 根因分析
## 🛠️ 修复建议
## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "actions": []
}
```
"""
    )

    monkeypatch.setattr(
        node,
        "_enforce_evidence_scope_claims",
        lambda content, _context: content.replace(
            '"actions": []',
            '"actions": [{"id": "broken",}]',
        ),
    )

    result = node.execute({
        "question": "我的集群有什么问题？",
        "layer": Layer.L2,
        "layer_analysis": "{}",
        "evidence_analysis": "{}",
        "rca_analysis": "{}",
        "thinking_events": [],
    })

    plan = extract_remediation_plan(result["conclusion"])
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []
    assert "invalid_remediation_json" not in (
        node._diagnosis_report_validation_errors(result["conclusion"])
    )


def test_below_limit_oom_fact_selects_metric_from_oom_entity():
    structured_context = """
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
ENTITY kind=Pod namespace=ns name=config-api
- METRIC metric=container_memory_working_set_bytes pod=config-api start=3.6Mi max=3.6Mi last=3.6Mi limit=96.0Mi max_limit_ratio=0.0377
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
ENTITY kind=Pod namespace=ns name=oom-api
- K8S_SIGNAL strength=strong observed="Last terminated state: app=OOMKilled exit=137"
- METRIC metric=container_memory_working_set_bytes pod=oom-api start=3.7Mi max=75.0Mi last=75.0Mi limit=80.0Mi max_limit_ratio=0.937
"""

    fact = ConclusionFormatterNode._below_limit_oom_fact(structured_context)

    assert fact == {
        "maximum": "75.0Mi",
        "limit": "80.0Mi",
        "pod": "oom-api",
    }


def test_conclusion_evidence_stats_floor_fractional_collected_count():
    stats = ConclusionFormatterNode._extract_evidence_stats({
        "diagnostic_evidence_total": 10,
        "diagnostic_evidence_collected": 10,
        "diagnostic_evidence_completeness": 1.0,
        "dimension_coverage": 1.0,
        "diagnostic_sufficiency": 0.95,
        "diagnostic_sufficiency_label": "充分",
    })

    assert stats["primary_total"] == 10
    assert stats["primary_collected"] == 9
    assert stats["primary_completeness_pct"] == "95%"


def test_conclusion_corrects_sampled_value_claimed_to_trigger_higher_limit():
    content = "\n".join([
        "## 根因分析",
        "Pod `trace-oom-api-abc` 工作内存增长至 66.9Mi，触发 cgroup 80Mi 硬限制。",
    ])
    structured_context = "\n".join([
        (
            "- METRIC metric=container_memory_working_set_bytes "
            "pod=trace-oom-api-abc start=48.8Mi max=66.9Mi "
            "last=66.9Mi limit=80.0Mi max_limit_ratio=0.8364"
        ),
    ])

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "66.9Mi，触发 cgroup 80Mi 硬限制" not in result
    assert "Prometheus 观测峰值 `66.9Mi`" in result
    assert "低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


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
    assert "# 结构化诊断上下文" in prompt
    assert "evidence_plan_stats: 1/2 (50%)" in prompt
    assert "已采集证据:" in prompt
    assert "e1: 获取 Pod 事件" in prompt
    assert "未采集证据:" in prompt
    assert "e2: 获取 Pod YAML" in prompt
    assert "rca_root_cause: 节点出口网络超时导致镜像拉取失败" in prompt
    assert "rca_confidence: 84%" in prompt
    assert "rca_limitations: 未验证节点出口网络" in prompt
    assert "## 🧩 结构化修复计划" in prompt
    assert "verify_command 禁止使用当前异常 Pod 的固定名称" in prompt
    assert "kubectl rollout status deployment/<name>" in prompt


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


def test_conclusion_inserts_missing_observability_rows_from_exact_facts():
    content = "\n".join([
        "## 📊 可观测性数据（三维度 + 拓扑）",
        "### 三大观测维度",
        "| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |",
        "|------|----------|----------|----------------------------------|----------|",
        "### 拓扑关系（实体与边）",
    ])
    structured_context = "\n".join([
        "COVERAGE k8s=present metrics=present logs=present tracing=present trace=present topology=present",
        "- METRIC metric=container_memory_working_set_bytes pod=api-pod max=66.9Mi limit=80.0Mi evidence_ref=metric-real",
        '- LOG event=config_missing message="required config PAYMENT_GATEWAY_TOKEN is missing" evidence_ref=log-real',
        "- DEEPFLOW request=\"GET /checkout\" response_code=500 trace_id=trace-real evidence_ref=deepflow-real",
        "- TEMPO trace_id=trace-real span=\"GET /checkout\" error.type=CONFIG_MISSING evidence_ref=tempo-real",
        '- K8S_SIGNAL observed="Last terminated state: business-api=Error exit=78" evidence_refs=["k8s-real"]',
    ])

    result = ConclusionFormatterNode._enforce_observability_dimension_table(
        content,
        structured_context,
    )

    assert result.count("| **Metrics** |") == 1
    assert result.count("| **Logging** |") == 1
    assert result.count("| **Tracing** |") == 1
    assert result.count("| **K8s** |") == 1
    assert "PAYMENT_GATEWAY_TOKEN" in result
    assert "response_code=500" in result


def test_conclusion_rejects_prompt_echo_and_falls_back_to_deterministic_report():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        """# 用户问题
我的集群现在有什么问题？

# 阶段1：问题定位分析
{"abnormal_pods": [{"name": "pod-a"}]}

# ⚠️ 证据采集统计（系统数据，必须原样引用，禁止自行计算）
plan_stats: 1/1 (100%)

```json
{"broken": true}
"""
    )
    state = {
        "question": "我的集群现在有什么问题？",
        "layer": Layer.L2,
        "layer_analysis": json.dumps({
            "layer": "L2",
            "confidence": 0.9,
            "pod_status_keyword": "CrashLoopBackOff",
            "pod_abnormal_type": "CrashLoopBackOffRuntime",
            "abnormal_pods": [
                {"namespace": "ns", "name": "pod-a", "status": "CrashLoopBackOff"}
            ],
        }),
        "evidence_analysis": json.dumps({
            "plan_total": 1,
            "plan_collected": 1,
            "plan_completeness": 1.0,
            "environment_evidence_total": 1,
            "environment_evidence_collected": 1,
            "environment_evidence_completeness": 1.0,
            "diagnostic_evidence_total": 5,
            "diagnostic_evidence_collected": 3,
            "diagnostic_evidence_completeness": 0.6,
            "evidence_inventory": [],
        }),
        "rca_analysis": json.dumps({
            "phenomenon": "pod-a CrashLoopBackOff",
            "root_cause": "应用启动失败",
            "root_cause_summary": "应用启动失败",
            "confidence": 0.7,
        }),
        "thinking_events": [],
    }

    result = node.execute(state)["conclusion"]

    assert "# 用户问题\n" not in result
    assert "证据采集统计（系统数据" not in result
    assert result.count("```") % 2 == 0
    assert "## 📊 诊断概览" in result
    assert "## 📊 可观测性数据（三维度 + 拓扑）" in result
    assert "## 🎯 阶段三：根因分析与因果链" in result
    assert "## 🛠️ 修复建议" in result


def test_conclusion_uses_diagnostic_plan_as_primary_completeness():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "collection_summary": (
            "Pod 可观测性覆盖 2/2，完整度 100%；"
            "去重后证据计划 1/3，完整度 33%"
        ),
        "plan_total": 3,
        "plan_collected": 1,
        "plan_completeness": 1 / 3,
        "environment_evidence_total": 3,
        "environment_evidence_collected": 1,
        "environment_evidence_completeness": 1 / 3,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "evidence_inventory": [],
    })

    stats = node._extract_evidence_stats(json.loads(evidence_analysis))
    report = node._enforce_evidence_stats(
        "| 项目 | 内容 |\n|---|---|\n| **证据完整度** | 1/3 (33%) |",
        evidence_analysis,
    )

    assert stats["observability_target_collected"] == 2
    assert stats["observability_target_total"] == 2
    assert stats["primary_completeness_pct"] == "33%"
    assert "| **证据完整度** | 1/3 (33%) |" in report


def test_conclusion_removes_redundant_collection_statistics_table():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "collection_summary": "Pod 可观测性覆盖 2/2，完整度 100%",
        "plan_total": 2,
        "plan_collected": 2,
        "plan_completeness": 1.0,
        "environment_evidence_total": 2,
        "environment_evidence_collected": 2,
        "environment_evidence_completeness": 1.0,
        "executed_tool_count": 3,
        "matched_tool_count": 2,
        "unplanned_tool_count": 1,
        "case_tool_count": 2,
        "supplemental_tool_count": 1,
        "skipped_plan_count": 1,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "early_stop": {
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
        "evidence_inventory": [],
    })
    content = """# 诊断报告

## 📊 诊断概览

| 项目 | 结果 |
|---|---|
| **证据完整度** | 1/3 (33%) |

## 🔍 现象描述

保持原文。
"""

    result = node._enforce_evidence_stats(content, evidence_analysis)
    repeated = node._enforce_evidence_stats(result, evidence_analysis)

    assert "| **证据完整度** | 2/2 (100%) |" in result
    assert "### 采集统计" not in result
    assert repeated == result


def test_conclusion_keeps_incomplete_diagnostic_evidence_without_statistics_section():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "plan_total": 3,
        "plan_collected": 2,
        "plan_completeness": 2 / 3,
        "environment_evidence_total": 3,
        "environment_evidence_collected": 2,
        "environment_evidence_completeness": 2 / 3,
        "executed_tool_count": 3,
        "matched_tool_count": 2,
        "unplanned_tool_count": 0,
        "case_tool_count": 1,
        "supplemental_tool_count": 2,
        "skipped_plan_count": 0,
        "observability_target_total": 2,
        "observability_target_collected": 1,
        "observability_target_completeness": 0.5,
        "early_stop": {
            "triggered": True,
            "reason": "context_budget_threshold",
        },
        "missing_reasons": ["p3: 上下文达到阈值，未执行"],
        "evidence_inventory": [],
    })
    content = """# 诊断报告

## 诊断概览

| 项目 | 结果 |
|---|---|
| **证据完整度** | 1/2 (50%) |

## 根因分析

保持原文。
"""

    result = node._enforce_evidence_stats(content, evidence_analysis)

    assert "| **证据完整度** | 2/3 (67%) |" in result
    assert "### 采集统计" not in result


def test_conclusion_statistics_recover_tool_composition_from_legacy_archives():
    node = ConclusionFormatterNode()
    stats = node._extract_evidence_stats({
        "plan_total": 3,
        "plan_collected": 3,
        "plan_completeness": 1.0,
        "environment_evidence_total": 3,
        "environment_evidence_collected": 3,
        "environment_evidence_completeness": 1.0,
        "executed_tool_count": 3,
        "matched_tool_count": 3,
        "unplanned_tool_count": 0,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "tool_data": [
            {"tool": "collect_aiops_case", "semantic_success": True},
            {"tool": "collect_aiops_case", "semantic_success": True},
            {"tool": "kubectl_describe", "semantic_success": True},
        ],
        "evidence_inventory": [],
    })

    assert stats["case_tool_count"] == 2
    assert stats["supplemental_tool_count"] == 1
    assert stats["executed_tool_count"] == 3


def test_conclusion_statistics_do_not_hide_missing_items_with_skip_count():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "plan_total": 4,
        "plan_collected": 2,
        "plan_completeness": 0.5,
        "environment_evidence_total": 2,
        "environment_evidence_collected": 2,
        "environment_evidence_completeness": 1.0,
        "executed_tool_count": 2,
        "matched_tool_count": 2,
        "unplanned_tool_count": 0,
        "case_tool_count": 2,
        "supplemental_tool_count": 0,
        "skipped_plan_count": 2,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "early_stop": {
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
        "missing_reasons": [
            "p3-fallback-oom-detect: 已规划但工具执行失败或无匹配结果",
            "p4-fallback-config-detect: 已规划但工具执行失败或无匹配结果",
        ],
        "evidence_inventory": [],
    })
    content = """# 诊断报告

## 诊断概览

| 项目 | 结果 |
|---|---|
| **证据完整度** | 2/2 (100%) |

## 根因分析
"""

    result = node._enforce_evidence_stats(content, evidence_analysis)

    assert "| **证据完整度** | 2/4 (50%) |" in result
    assert "### 采集统计" not in result


def test_conclusion_statistics_keep_large_skip_count_separate_from_plan_total():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "plan_total": 2,
        "plan_collected": 2,
        "plan_completeness": 1.0,
        "environment_evidence_total": 2,
        "environment_evidence_collected": 2,
        "environment_evidence_completeness": 1.0,
        "executed_tool_count": 2,
        "matched_tool_count": 2,
        "unplanned_tool_count": 0,
        "case_tool_count": 2,
        "supplemental_tool_count": 0,
        "skipped_plan_count": 4,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "early_stop": {
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
        "missing_reasons": [],
        "evidence_inventory": [],
    })
    content = """# 诊断报告

## 诊断概览

| 项目 | 结果 |
|---|---|
| **证据完整度** | 2/2 (100%) |

## 根因分析
"""

    result = node._enforce_evidence_stats(content, evidence_analysis)

    assert "| **证据完整度** | 2/2 (100%) |" in result
    assert "### 采集统计" not in result


def test_conclusion_does_not_inject_statistics_under_level_one_diagnosis_overview():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "plan_total": 2,
        "plan_collected": 2,
        "plan_completeness": 1.0,
        "environment_evidence_total": 2,
        "environment_evidence_collected": 2,
        "environment_evidence_completeness": 1.0,
        "executed_tool_count": 2,
        "matched_tool_count": 2,
        "unplanned_tool_count": 0,
        "case_tool_count": 2,
        "supplemental_tool_count": 0,
        "skipped_plan_count": 0,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "early_stop": {
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
        "evidence_inventory": [],
    })
    content = """## 节点四：汇总总结

# 诊断概览

| 项目 | 结果 |
|---|---|
| **证据完整度** | 2/2 (100%) |

# 可观测性数据

保持原文。
"""

    result = node._enforce_evidence_stats(content, evidence_analysis)

    assert "### 采集统计" not in result
    assert result.index("# 诊断概览") < result.index("# 可观测性数据")


def test_conclusion_does_not_append_diagnosis_statistics_to_query_report():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "plan_total": 1,
        "plan_collected": 1,
        "plan_completeness": 1.0,
        "environment_evidence_total": 1,
        "environment_evidence_collected": 1,
        "environment_evidence_completeness": 1.0,
        "executed_tool_count": 1,
        "matched_tool_count": 1,
        "unplanned_tool_count": 0,
        "skipped_plan_count": 0,
        "evidence_inventory": [],
    })
    content = "## 📊 查询结果\n\n- 当前异常 Pod: 2\n"

    result = node._enforce_evidence_stats(content, evidence_analysis)

    assert "### 采集统计" not in result


def test_conclusion_replaces_model_topology_section_with_exact_edges():
    content = """# 诊断报告

### 拓扑关系（实体与边）
- `Deployment --owned_by--> ReplicaSet --owned_by--> Pod`
- `driver --calls--> api` (related_context/weak)
- 无 `owned_by` 控制器边显示，视为独立测试 Pod。

---

## 根因分析
保持原文。
"""
    structured_context = """
TOPOLOGY_EXACT_EDGES count=3
- TOPOLOGY relationship="Pod --calls--> Pod" source=driver-pod target=api-pod source_system=deepflow+kubernetes directness=direct confidence=high
- TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" source=api-pod target=api-rs source_system=kubernetes directness=direct confidence=high
- TOPOLOGY relationship="ReplicaSet --owned_by--> Deployment" source=api-rs target=api source_system=kubernetes directness=direct confidence=high
"""

    result = ConclusionFormatterNode._enforce_exact_topology_section(
        content,
        structured_context,
    )

    assert "Deployment --owned_by--> ReplicaSet --owned_by--> Pod" not in result
    assert "related_context/weak" not in result
    assert "独立测试 Pod" not in result
    assert "`Pod --calls--> Pod`: `driver-pod` -> `api-pod`" in result
    assert "`Pod --owned_by--> ReplicaSet`: `api-pod` -> `api-rs`" in result
    assert "`ReplicaSet --owned_by--> Deployment`: `api-rs` -> `api`" in result
    assert "direct/high" in result
    assert "调用方 `driver-pod` 的流量进入目标 Pod `api-pod`" in result
    assert "目标 Pod `api-pod` 由 Deployment `api` 管理" in result
    assert "责任边界落在 Deployment `api` 管理的工作负载" in result
    assert "## 根因分析\n保持原文。" in result


def test_autonomous_report_removes_inferred_topology_when_not_executed():
    report = """## 📊 可观测性数据

### 拓扑关系（实体与边）
- `Pod --owned_by--> Deployment (推测)`：根据标签推测。
- `Pod --scheduled_on--> Node`：node2。

---

## 🎯 根因分析
root cause
"""
    structured_context = """
observability_collection_mode: autonomous_query
OBSERVABILITY_EXECUTION metrics=present logging=present tracing=present topology=not_executed
OBSERVABILITY_SOURCE dimension=logging tool=query_pod_logs source_system=elasticsearch coverage=present
OBSERVABILITY_SOURCE dimension=tracing tool=query_pod_tracing source_system=deepflow+tempo coverage=present
"""

    result = ConclusionFormatterNode._enforce_exact_topology_section(
        report,
        structured_context,
    )

    assert "Pod --owned_by--> Deployment (推测)" not in result
    assert "Pod --scheduled_on--> Node" not in result
    assert "本轮未执行 `query_pod_topology`" in result
    assert "不对 Deployment、Service 或调用关系作推断" in result


def test_conclusion_corrects_below_limit_metric_overclaims():
    content = """## 根因分析
- trace-oom-api 内存从 3.3Mi 增至 76.9Mi，并突破 80Mi Limit。
- 96.18% 的采样值直接触发 OOMKilled。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc container=business-api start=3.3Mi max=76.9Mi last=76.9Mi limit=80.0Mi max_limit_ratio=0.9618
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "突破 80Mi" not in result
    assert "直接触发 OOMKilled" not in result
    assert "Prometheus 观测峰值 `76.9Mi`，低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


def test_conclusion_corrects_real_growth_then_breaks_limit_sentence():
    content = """### 三大观测维度
| **Metrics** | Prometheus | Present | **Pod `trace-oom-api` 内存峰值 `72.9Mi`，Limit `80.0Mi` (利用率 91.17%)**。请求 `GET /allocate?mib=2&step=28070` 触发分配，从 60Mi 增至 62Mi 后突破 Limit。 | 见机器可核验附录 |
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=72.9Mi last=72.9Mi limit=80.0Mi max_limit_ratio=0.9117
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "从 60Mi 增至 62Mi 后突破 Limit" not in result
    assert "Prometheus 观测峰值 `72.9Mi`，低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


def test_conclusion_normalizes_real_malformed_repeated_metric_correction():
    content = """### 因果链
  -> 容器内存使用未由本次采样证明已突破硬限制；Prometheus 观测峰值 `72.9Mi`，低于 limit `80.0Mi`；实际触及硬限制的瞬间未被采样直接捕获> 80Mi 阈值；Prometheus 观测峰值 `72.9Mi`，低于 limit `80.0Mi`；实际触及硬限制的瞬间未被采样直接捕获；K8s OOM) 结论应以 Kubernetes termination reason 为准
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=72.9Mi last=72.9Mi limit=80.0Mi max_limit_ratio=0.9117
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "捕获> 80Mi" not in result
    assert result.count("Prometheus 观测峰值 `72.9Mi`") == 1
    assert "K8s OOM)" not in result
    assert "容器终止事实应以 Kubernetes termination reason 为准" in result


def test_conclusion_normalizes_triggered_kubernetes_boundary_claim():
    content = """### 根因结论
1. **trace-oom-api**: Prometheus 观测峰值 79.0Mi，低于 limit 80.0Mi，触发了 Kubernetes 的内存保护机制（OOMKilled）。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.4Mi max=79.0Mi last=79.0Mi limit=80.0Mi max_limit_ratio=0.9872
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "；了 Kubernetes" not in result
    assert "Prometheus 观测峰值 `79.0Mi`，低于 limit `80.0Mi`" in result
    assert result.count("Prometheus 观测峰值") == 1
    assert "OOMKilled 结论应以 Kubernetes termination reason 为准" in result


def test_conclusion_normalizes_deployed_triggered_kubernetes_fragment():
    content = """### 根因结论
1. **trace-oom-api**: Prometheus 观测峰值 `79.0Mi`，低于 limit `80.0Mi`；实际触及硬限制的瞬间未被采样直接捕获；了 Kubernetes 的内存保护机制（OOMKilled） 结论应以 Kubernetes termination reason 为准。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.4Mi max=79.0Mi last=79.0Mi limit=80.0Mi max_limit_ratio=0.9872
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "；了 Kubernetes" not in result
    assert result.count("Prometheus 观测峰值 `79.0Mi`") == 1
    assert "OOMKilled 结论应以 Kubernetes termination reason 为准" in result


def test_conclusion_corrects_metric_table_claim_that_growth_touched_hard_limit():
    content = """### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 2 | Memory Metric | Prometheus | `container_memory_working_set_bytes` 峰值 **79.0Mi** (Limit 80.0Mi) | 内存持续增长且触及硬限制 |
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=26.8Mi max=79.0Mi last=79.0Mi limit=80.0Mi max_limit_ratio=0.9872
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "内存持续增长且触及硬限制" not in result
    assert "Prometheus 观测峰值 `79.0Mi`，低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


def test_conclusion_corrects_accumulation_claimed_to_touch_numeric_limit():
    content = """## 诊断摘要
2. `trace-oom-api-598dcf5996-x6v6n` Pod 因内存累积触及 80Mi 限制，被系统 OOMKilled。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=26.8Mi max=79.0Mi last=79.0Mi limit=80.0Mi max_limit_ratio=0.9872
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )
    second = ConclusionFormatterNode._enforce_metric_boundary_claims(
        result,
        structured_context,
    )

    assert "内存累积触及 80Mi 限制" not in result
    assert "Prometheus 观测峰值 `79.0Mi`，低于 limit `80.0Mi`" in result
    assert "因Prometheus" not in result
    assert "容器终止事实应以 Kubernetes termination reason 为准，被系统 OOMKilled" not in result
    assert result == second


def test_conclusion_corrects_standalone_memory_limit_touch_in_causal_chain():
    content = """### 因果链
[trace-oom-api-598dcf5996-x6v6n] 内存使用量持续增长 (26.8Mi -> 79.0Mi)
  -> 触及容器 Memory Limit (80.0Mi)
  -> Linux OOM Killer 强制终止容器
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=26.8Mi max=79.0Mi last=79.0Mi limit=80.0Mi max_limit_ratio=0.9872
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )
    second = ConclusionFormatterNode._enforce_metric_boundary_claims(
        result,
        structured_context,
    )

    assert "触及容器 Memory Limit (80.0Mi)" not in result
    assert "Prometheus 观测峰值 `79.0Mi`，低于 limit `80.0Mi`" in result
    assert result == second


@pytest.mark.parametrize(
    "unsupported_claim",
    [
        "当内存达到 80.0Mi Limit 时，容器被 OOMKilled。",
        "trace-oom-api 触及 Limit -> OOMKilled。",
        "trace-oom-api 触及 80Mi 限制被杀。",
        "trace-oom-api 超过了设定的 80Mi Limit。",
        "trace-oom-api 达到 80Mi 限制。",
        "trace-oom-api 76.9Mi，触及 Limit 80.0Mi。",
        "trace-oom-api 逼近并触及 K8s 限制。",
        "trace-oom-api 触碰 Kubernetes memory limit。",
        "trace-oom-api 触及 Kubernetes 内存 Limit。",
        "trace-oom-api 内存使用触及 Limit。",
        "trace-oom-api 业务代码分配内存超过 Limit。",
    ],
)
def test_conclusion_corrects_fixed_archive_limit_overclaim_variants(
    unsupported_claim,
):
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=76.9Mi last=76.9Mi limit=80.0Mi max_limit_ratio=0.9612
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        unsupported_claim,
        structured_context,
    )
    repeated = ConclusionFormatterNode._enforce_metric_boundary_claims(
        result,
        structured_context,
    )

    assert unsupported_claim not in result
    assert "Prometheus 观测峰值 `76.9Mi`，低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result
    assert repeated == result


def test_conclusion_keeps_canonical_metric_sampling_boundary_idempotent():
    content = (
        "trace-oom-api: Prometheus 观测峰值 `76.9Mi`，低于 limit `80.0Mi`；"
        "实际触及硬限制的瞬间未被采样直接捕获；"
        "容器终止事实应以 Kubernetes termination reason 为准。"
    )
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=76.9Mi last=76.9Mi limit=80.0Mi max_limit_ratio=0.9612
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert result == content


def test_conclusion_uses_nearby_metric_values_to_disambiguate_generic_limit_claim():
    content = """| 2 | K8s Status | `trace-config-api`: exit=78 |
| 3 | Metrics | `trace-oom-api`: 峰值 77.0Mi / limit 80.0Mi |
| 4 | Logging | `trace-config-api`: required config is missing |
| 5 | Tracing | `trace-oom-api`: GET /allocate |

### 证据关联分析
1. **OOM 场景关联**：请求驱动 -> 内存无界累积 -> 触碰 Limit -> 系统 OOM Kill。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-config-api-84bc7cb976-vgtl8 container=business-api start=3.7Mi max=4.1Mi last=4.1Mi limit=96.0Mi max_limit_ratio=0.0427
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=77.0Mi last=77.0Mi limit=80.0Mi max_limit_ratio=0.9625
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "触碰 Limit" not in result
    assert "Prometheus 观测峰值 `77.0Mi`，低于 limit `80.0Mi`" in result
    assert "limit `96.0Mi`" not in result


def test_conclusion_scopes_metric_boundary_corrections_to_matching_pod():
    content = """## 根因分析
### trace-config-api
- trace-config-api 内存保持 3.7Mi，低于 96Mi limit。

### trace-oom-api
- trace-oom-api 内存从 3.4Mi 增至 75.0Mi，并突破 80Mi Limit。
- 93.81% 的采样值直接触发 OOMKilled。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-config-api-84bc7cb976-vgtl8 container=business-api start=3.7Mi max=3.7Mi last=3.7Mi limit=96.0Mi max_limit_ratio=0.0384
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.4Mi max=75.0Mi last=75.0Mi limit=80.0Mi max_limit_ratio=0.9381
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "突破 80Mi" not in result
    assert "93.81% 的采样值直接触发 OOMKilled" not in result
    assert "Prometheus 观测峰值 `75.0Mi`，低于 limit `80.0Mi`" in result
    assert "Prometheus 观测峰值 `3.7Mi`，低于 limit `96.0Mi`" not in result
    assert "trace-config-api 内存保持 3.7Mi，低于 96Mi limit。" in result


def test_conclusion_metric_boundary_correction_keeps_sentence_spacing():
    content = """## 根因分析
- trace-oom-api 的内存使用量突破 80Mi Limit。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc container=business-api start=3.3Mi max=76.9Mi last=76.9Mi limit=80.0Mi max_limit_ratio=0.9618
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "量Prometheus" not in result
    assert "内存使用量未由本次采样证明已突破硬限制" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


def test_conclusion_metric_boundary_correction_consumes_trailing_limit_word():
    content = """## 根因分析
- trace-oom-api 内存已超过 80Mi limit 限制。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc container=business-api start=3.3Mi max=76.9Mi last=76.9Mi limit=80.0Mi max_limit_ratio=0.9618
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "捕获限制" not in result
    assert "limit 限制" not in result
    assert "Prometheus 观测峰值 `76.9Mi`，低于 limit `80.0Mi`" in result


def test_conclusion_corrects_causal_overclaims_from_below_limit_samples():
    content = """## 根因分析
- trace-oom-api 指标证实内存逼近限制阈值，且 `allocate` 操作导致越界。
- 由于当前 Limit 为 80Mi，且使用率达 86% 即崩溃，建议直接提高限制。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc container=business-api start=3.3Mi max=68.9Mi last=68.9Mi limit=80.0Mi max_limit_ratio=0.8617
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "操作导致越界" not in result
    assert "使用率达 86% 即崩溃" not in result
    assert "Prometheus 观测峰值 `68.9Mi`，低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


def test_conclusion_metric_boundary_correction_keeps_causal_sentence_grammatical():
    content = """## 证据链
- 决定性证据：容器因内存超过 80Mi 被 Linux OOM Killer 终止。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc container=business-api start=3.3Mi max=68.9Mi last=68.9Mi limit=80.0Mi max_limit_ratio=0.8617
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "因内存未由本次采样" not in result
    assert "因内存使用量未由本次采样证明已突破硬限制" in result


def test_conclusion_metric_boundary_correction_removes_malformed_kill_suffix():
    content = """## 证据关联分析
- Trace 证明请求触发内存增长，导致应用工作内存增长至 77.2Mi，触发 cgroup 80Mi 硬限制的 Limit 被内核 Kill 掉。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc container=business-api start=3.3Mi max=77.2Mi last=77.2Mi limit=80.0Mi max_limit_ratio=0.9649
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "硬限制的 Limit" not in result
    assert "未被采样直接捕获的 Limit" not in result
    assert "Prometheus 观测峰值 `77.2Mi`，低于 limit `80.0Mi`" in result
    assert "容器终止事实应以 Kubernetes termination reason 为准" in result


def test_conclusion_corrects_peak_below_limit_claimed_to_trigger_failure():
    content = """### 三大观测维度
| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |
|------|----------|----------|----------------------------------|----------|
| **Metrics** | Prometheus | Present | **Pod A**: `container_memory_working_set_bytes` 峰值 **75.0Mi** (Limit 80.0Mi, 93.7%)，触发 OOM | metric-real |
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=20.9Mi max=75.0Mi last=75.0Mi limit=80.0Mi max_limit_ratio=0.937
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "93.7%)，触发 OOM" not in result
    assert "Prometheus 观测峰值 `75.0Mi`，低于 limit `80.0Mi`" in result
    assert "容器终止事实应以 Kubernetes termination reason 为准" in result


def test_conclusion_corrects_below_limit_proximity_claimed_to_trigger_failure():
    content = """## 证据链
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 2 | Metrics | Prometheus | **Pod A**: `container_memory_working_set_bytes` 峰值 75.0Mi (Limit 80.0Mi) | 确认内存使用逼近 Limit，触发 OOM |
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=20.9Mi max=75.0Mi last=75.0Mi limit=80.0Mi max_limit_ratio=0.937
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "逼近 Limit，触发 OOM" not in result
    assert "Prometheus 观测峰值 `75.0Mi`，低于 limit `80.0Mi`" in result
    assert "实际触及硬限制的瞬间未被采样直接捕获" in result


def test_conclusion_metric_boundary_correction_consumes_application_prefix():
    content = """## 证据链
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 2 | Metrics | Prometheus | Max Usage: 75.0Mi (Limit: 80.0Mi) | 确认应用内存使用逼近 Limit，触发 OOM |
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=75.0Mi last=75.0Mi limit=80.0Mi max_limit_ratio=0.937
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "确认应用Prometheus" not in result
    assert "确认应用内存使用逼近 Limit" not in result
    assert "Prometheus 观测峰值 `75.0Mi`，低于 limit `80.0Mi`" in result


def test_conclusion_metric_boundary_correction_keeps_separator_before_correction():
    content = """## 证据链
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| E2 | Metrics | Prometheus | Memory 从 3.6Mi 持续积累至 **77.0Mi** (Limit 80.0Mi)，触发 OOMKilled | 内存持续增长。 |
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.6Mi max=77.0Mi last=77.0Mi limit=80.0Mi max_limit_ratio=0.962
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "MiPrometheus" not in result
    assert ")Prometheus" not in result
    assert "；Prometheus 观测峰值 `77.0Mi`" in result
    assert "OOMKilled 结论应以 Kubernetes termination reason 为准" in result


def test_conclusion_corrects_sampled_value_claimed_to_touch_higher_limit():
    content = """## 根因分析
- trace-oom-api 使用量达到 77.0Mi 触及 80.0Mi Limit。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.6Mi max=77.0Mi last=77.0Mi limit=80.0Mi max_limit_ratio=0.962
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "77.0Mi 触及 80.0Mi" not in result
    assert "Prometheus 观测峰值 `77.0Mi`，低于 limit `80.0Mi`" in result
    assert "容器终止事实应以 Kubernetes termination reason 为准" in result


def test_conclusion_rebuilds_root_cause_when_unique_evidence_is_bound_to_wrong_pod():
    content = """## 🎯 根因分析
### 根因结论
#### trace-oom-api-598dcf5996-x6v6n
- **直接证据**：日志显示 `required config PAYMENT_GATEWAY_TOKEN is missing`。

#### trace-config-api-84bc7cb976-vgtl8
- **直接证据**：Kubernetes 显示 `OOMKilled exit=137`。

## 🛠️ 修复建议
保持后续内容。
"""
    structured_context = """
aiops_observability_facts:
- [collect_aiops_case]
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
ENTITY entity=Pod aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n node=node2 pod_ip=172.16.104.13
K8S_SIGNAL strength=strong observed="Last terminated state: business-api=OOMKilled exit=137" evidence_refs=["k8s-oom"]
METRIC metric=container_memory_working_set_bytes start=3.6Mi max=74.9Mi last=74.9Mi limit=80.0Mi ratio=0.9369
LOG event=allocate trace_id=oom-trace path=/allocate?mib=2 alloc_mib=2 allocated_mib=62
DEEPFLOW src=172.16.104.8 dst=172.16.104.13 request=GET /allocate?mib=2 response_code=200 duration_us=7699 trace_id=oom-trace
TEMPO trace_id=oom-trace service=aiops-traced-oom-api span=GET /allocate allocated_before=60 allocated_after=62
TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" source=trace-oom-api-598dcf5996-x6v6n target=trace-oom-api-598dcf5996 directness=direct confidence=high
- [collect_aiops_case]
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
ENTITY entity=Pod aiops-traced-config/trace-config-api-84bc7cb976-vgtl8 node=node2 pod_ip=172.16.104.2
K8S_SIGNAL strength=strong observed="Last terminated state: business-api=Error exit=78" evidence_refs=["k8s-config"]
METRIC metric=container_memory_working_set_bytes start=3.7Mi max=3.7Mi last=3.7Mi limit=96.0Mi ratio=0.0381
LOG event=config_missing trace_id=config-trace path=/checkout error_code=CONFIG_MISSING missing_config=PAYMENT_GATEWAY_TOKEN http_status=500
DEEPFLOW src=172.16.104.56 dst=172.16.104.2 request=GET /checkout response_code=500 duration_us=5010 trace_id=config-trace
TEMPO trace_id=config-trace service=aiops-traced-config-api span=GET /checkout http.response.status_code=500 error.type=CONFIG_MISSING config.key=PAYMENT_GATEWAY_TOKEN config.present=false
TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" source=trace-config-api-84bc7cb976-vgtl8 target=trace-config-api-84bc7cb976 directness=direct confidence=high
"""

    result = ConclusionFormatterNode._enforce_entity_evidence_consistency(
        content,
        structured_context,
    )

    oom_section = result.split(
        "### `aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n`",
        1,
    )[1].split(
        "### `aiops-traced-config/trace-config-api-84bc7cb976-vgtl8`",
        1,
    )[0]
    config_section = result.split(
        "### `aiops-traced-config/trace-config-api-84bc7cb976-vgtl8`",
        1,
    )[1].split("## 🛠️ 修复建议", 1)[0]

    assert "PAYMENT_GATEWAY_TOKEN" not in oom_section
    assert "OOMKilled exit=137" in oom_section
    assert "request=GET /allocate?mib=2" in oom_section
    assert "required config PAYMENT_GATEWAY_TOKEN is missing" not in result
    assert "missing_config=PAYMENT_GATEWAY_TOKEN" in config_section
    assert "Error exit=78" in config_section
    assert "保持后续内容。" in result


def test_conclusion_entity_blocks_support_deployed_agent_facts_entity_format():
    structured_context = """
- [collect_aiops_case]
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
ENTITY kind=Pod namespace=aiops-traced-config name=trace-config-api-84bc7cb976-vgtl8 node=node2 pod_ip=172.16.104.2
K8S_SIGNAL strength=strong observed="Last terminated state: business-api=Error exit=78" evidence_refs=["k8s-config"]
LOG event=config_missing missing_config=PAYMENT_GATEWAY_TOKEN
"""

    blocks = ConclusionFormatterNode._extract_entity_evidence_blocks(
        structured_context,
    )

    assert len(blocks) == 1
    assert blocks[0]["namespace"] == "aiops-traced-config"
    assert blocks[0]["pod"] == "trace-config-api-84bc7cb976-vgtl8"
    assert "PAYMENT_GATEWAY_TOKEN".casefold() in blocks[0]["markers"]


def test_conclusion_downgrades_unproven_memory_leak_claim_without_leak_evidence():
    content = """## 🎯 根因分析
- `trace-oom-api-598dcf5996-x6v6n` 存在内存泄漏，最终进入 CrashLoopBackOff。
"""
    structured_context = """
- [collect_aiops_case]
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
ENTITY entity=Pod aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n node=node2 pod_ip=172.16.104.13
K8S_SIGNAL strength=strong observed="Last terminated state: business-api=OOMKilled exit=137" evidence_refs=["k8s-oom"]
LOG event=allocate trace_id=oom-trace path=/allocate?mib=2 alloc_mib=2 allocated_mib=62
TEMPO trace_id=oom-trace service=aiops-traced-oom-api span=GET /allocate allocated_before=60 allocated_after=62
"""

    result = ConclusionFormatterNode._enforce_entity_evidence_consistency(
        content,
        structured_context,
    )

    assert "内存泄漏" not in result
    assert "请求驱动的持续内存累积（未证明泄漏机制）" in result


def test_conclusion_downgrades_unproven_low_memory_limit_claim_without_baseline():
    content = """## 🎯 根因分析
- `trace-oom-api-598dcf5996-x6v6n` 的根因是 memory limit 80Mi 过低。
"""
    structured_context = """
- [collect_aiops_case]
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
ENTITY entity=Pod aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n node=node2 pod_ip=172.16.104.13
- K8S_SIGNAL strength=strong observed="Last terminated state: business-api=OOMKilled exit=137" evidence_refs=["k8s-oom"]
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n max=72.9Mi limit=80.0Mi ratio=0.9118
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "limit 80Mi 过低" not in result
    assert "是否偏低仍需结合正常业务基线验证" in result
    assert "OOMKilled" not in result


def test_conclusion_corrects_real_report_low_limit_and_false_comparison_variants():
    content = """## 🎯 根因分析
- **根因**: 内存限制不足。当前 Limit 80Mi 无法支撑 `/allocate` 请求的峰值内存需求（观测到 70.9Mi）。

## 🧩 结构化修复计划
- OOM Pod Last State OOMKilled exit=137, Metrics Max 70.9Mi > 80Mi Limit (需增加)
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=3.3Mi max=70.9Mi last=70.9Mi limit=80.0Mi max_limit_ratio=0.8866
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "内存限制不足" not in result
    assert "当前 Limit 80Mi 无法支撑" not in result
    assert "70.9Mi > 80Mi" not in result
    assert "是否偏低仍需结合正常业务基线验证" in result
    assert "Prometheus 观测峰值 `70.9Mi`，低于 limit `80.0Mi`" in result


def test_conclusion_enforces_topology_trace_and_source_evidence_boundaries():
    content = """## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **置信度** | 高 (95%) |
| **证据完整度** | 10/10 (100%) |

## 🕵️ 证据链
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | K8s 状态 | `kubectl describe pod/trace-oom-api...` | OOMKilled exit=137 | 确认 OOMKilled |
| 2 | Logging | `logs --previous` | config missing | 确认配置缺失 |
| 3 | Metrics | `container_memory_working_set_bytes` | Max 70.9Mi / Limit 80Mi | 证据 1 确认 Pod 1 触顶 |
| 4 | Tracing | `deepflow` traces | trace-oom | 关联了外部请求与内部崩溃的具体行为 |

## 🎯 根因分析
- 当前问题由内存限制不足导致 OOMKilled。
- 根本原因: trace-oom-api 容器内存限制（Limit: 80Mi）过低。
- Service/RS/Deployment 链路正常，因此排除网络和调度问题。
- Trace 显示 `/allocate` 操作触发。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 本轮所有维度均已获取决定性证据 |

## 🧩 结构化修复计划
- Metrics Max 70.9Mi < 80Mi Limit (需增加)

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 验证接口 | `kubectl port-forward svc/trace-config-api -n aiops-traced-config 8080:80` | HTTP 200 |

## 🛠️ 修复建议
```bash
kubectl set env deployment/trace-config-api -n aiops-traced-config PAYMENT_GATEWAY_TOKEN=<REAL_TOKEN_VALUE>
```

如果是独立 Pod：
```bash
kubectl delete pod trace-config-api-abc -n aiops-traced-config
```

```bash
```
"""
    structured_context = """
TOPOLOGY_SCOPE relationships_only=true health_not_proven=true complete_call_chain_not_proven=true
- detail: tool=get_aiops_case_evidence
- K8S_SIGNAL strength=strong observed="Last terminated state: business-api=OOMKilled exit=137" evidence_refs=["k8s-oom"]
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc max=70.9Mi limit=80.0Mi max_limit_ratio=0.8866
- LOG event=config_missing message="required config PAYMENT_GATEWAY_TOKEN is missing" missing_config=PAYMENT_GATEWAY_TOKEN
- DEEPFLOW request="GET /allocate?mib=2" response_code=200 trace_id=trace-oom
- TEMPO trace_id=trace-oom span="GET /allocate" aiops.allocated_mib.before=60 aiops.allocated_mib.after=62
- TOPOLOGY relationship="Service --selects--> Pod" source=trace-oom-api target=trace-oom-api-abc source_system=kubernetes directness=direct confidence=high
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "`kubectl describe pod/trace-oom-api...`" not in result
    assert "`logs --previous`" not in result
    assert "`deepflow` traces" not in result
    assert result.count("`collect_aiops_case`") >= 3
    assert "`get_aiops_case_evidence`" in result
    assert "来源命令" not in result
    assert "采集来源" in result
    assert "链路正常" not in result
    assert "排除网络和调度问题" not in result
    assert "仅确认实体关系" in result
    assert "操作触发 OOM" not in result
    assert "单次内存分配" in result
    assert "未证明该请求直接触发 OOM" in result
    assert "内存限制不足" not in result
    assert "Limit: 80Mi）过低" not in result
    assert "(需增加)" not in result
    assert "是否偏低尚待正常业务基线验证" in result
    assert "**可观测性维度覆盖**" in result
    assert "不代表根因结论充分" in result
    assert "**分项置信度**" in result
    assert "OOM 资源规格归因中等" in result
    assert "8080:80" not in result
    assert "先查询 Service 端口映射" in result
    assert "| 无 | - | 无 |" not in result
    assert "| 无 | - | 本轮所有维度均已获取决定性证据 |" not in result
    assert "正常业务基线" in result
    assert "Node MemoryPressure" in result
    assert "确认 Pod 1 触顶" not in result
    assert "未捕获触及硬限制的瞬间" in result
    assert "关联了外部请求与内部崩溃" not in result
    assert "未证明请求直接导致崩溃" in result
    assert "<REAL_TOKEN_VALUE>" not in result
    assert "kubectl set env deployment/trace-config-api" not in result
    assert "kubectl delete pod trace-config-api-abc" not in result
    assert "```bash\n```" not in result


def test_conclusion_coarse_case_logging_source_remains_collect_aiops_case():
    content = """## 🕵️ 证据链
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Logging | `logs --previous` | config missing | 确认配置缺失 |
"""
    structured_context = """
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
- LOG event=config_missing message="required config TOKEN is missing"
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "`collect_aiops_case`" in result
    assert "`get_aiops_case_evidence`" not in result


def test_conclusion_removes_chinese_secret_placeholder_advice():
    content = """## 🛠️ 修复建议
- 建议执行 `kubectl set env deployment/api -n demo TOKEN=<填入真实token>`
"""
    structured_context = """
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
- LOG event=config_missing message="required config TOKEN is missing" missing_config=TOKEN
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "<填入真实token>" not in result
    assert "kubectl set env" not in result
    assert "Secret 引用尚未获取" in result


def test_conclusion_singular_log_source_uses_actual_fine_evidence_tool():
    content = """## 🕵️ 证据链
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 3 | Log | `kubectl logs -p` | config missing | 确认配置缺失 |
"""
    structured_context = """
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
- detail: tool=get_aiops_case_evidence
- LOG event=config_missing message="required config TOKEN is missing"
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "`kubectl logs -p`" not in result
    assert "`get_aiops_case_evidence`" in result


def test_conclusion_removes_ascii_secret_placeholder_command():
    content = """## 🛠️ 修复建议
```bash
# 示例：请替换下方 YOUR_TOKEN_VALUE
kubectl set env deployment/api -n demo TOKEN=YOUR_TOKEN_VALUE
```
"""
    structured_context = """
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
- LOG event=config_missing message="required config TOKEN is missing" missing_config=TOKEN
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "YOUR_TOKEN_VALUE" not in result
    assert "kubectl set env" not in result
    assert "Secret 引用尚未获取" in result


def test_conclusion_downgrades_real_oom_low_limit_claims_without_baseline():
    content = """## 🕵️ 证据链
| # | 证据类型 | 采集来源 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 2 | Metrics | `collect_aiops_case` | max=77.0Mi, limit=80.0Mi | **佐证**：内存使用率 96.2%，证明 Limit 确实过小。 |

## 🎯 根因分析
Root Cause: Deployment 定义的 memory limits (80Mi) 低于应用实际运行需求。
- **trace-oom-api**: 根因为 **内存配置过小**。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n container=business-api start=22.7Mi max=77.0Mi last=77.0Mi limit=80.0Mi max_limit_ratio=0.962 samples=["01:45:50=22.7Mi","01:46:05=32.8Mi","01:46:20=44.8Mi","01:46:35=62.9Mi","01:46:50=77.0Mi"]
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )

    assert "证明 Limit 确实过小" not in result
    assert "低于应用实际运行需求" not in result
    assert "根因为 **内存配置过小**" not in result
    assert "是否偏低仍需结合正常业务基线验证" in result


def test_conclusion_downgrades_sparse_metric_exclusion_and_preserves_known_logs():
    content = """## 🕵️ 证据关联分析
- **Case 2 (Config)**: Metrics 证明内存无压力，排除资源问题，确认为配置缺失。

## 🎯 根因分析
Result: Pod 启动失败，无业务日志，服务不可用。
"""
    structured_context = """
- METRIC metric=container_memory_working_set_bytes pod=trace-config-api-84bc7cb976-vgtl8 container=business-api start=3.5Mi max=3.5Mi last=3.5Mi limit=96.0Mi max_limit_ratio=0.0368 samples=["01:53:57=3.5Mi"]
- LOG event=config_missing message="required config PAYMENT_GATEWAY_TOKEN is missing" pod=trace-config-api-84bc7cb976-vgtl8
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "Metrics 证明内存无压力" not in result
    assert "排除资源问题" not in result
    assert "单点指标" in result
    assert "无业务日志" not in result
    assert "已有配置缺失业务日志" in result


def test_conclusion_does_not_attribute_missing_runtime_config_to_secret_source():
    content = """## 🎯 根因分析
- 根因是 ConfigMap/Secret 中缺失 `PAYMENT_GATEWAY_TOKEN` 环境变量。
"""
    structured_context = """
- LOG event=config_missing message="required config PAYMENT_GATEWAY_TOKEN is missing" missing_config=PAYMENT_GATEWAY_TOKEN
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "ConfigMap/Secret 中缺失" not in result
    assert "运行时缺少" in result
    assert "env/envFrom" in result


def test_conclusion_corrects_english_false_metric_comparison_in_remediation_basis():
    content = """## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "basis": [
    "Metric Evidence: Memory usage 77.0Mi exceeds limit 80.0Mi"
  ],
  "actions": []
}
```
"""
    structured_context = """
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-598dcf5996-x6v6n max=77.0Mi limit=80.0Mi max_limit_ratio=0.962
"""

    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        content,
        structured_context,
    )

    assert "77.0Mi exceeds limit 80.0Mi" not in result
    assert "77.0Mi < 80.0Mi" in result


def test_conclusion_downgrades_live_report_source_and_capacity_overclaims():
    content = """## 🕵️ 证据关联分析
- trace-oom-api 的证据链闭环，根因明确为**内存不足**。

## 🎯 根因分析
**Case A: OOMKilled**
2. **trace-oom-api (OOMKilled)**：根因是 **Memory Limit 设置过低**。容器分配的内存限制为 **80.0Mi**，无法承载业务峰值（达到 77.0Mi）。

**Case B: Config Error**
Deployment 未定义/注入必需的环境变量 PAYMENT_GATEWAY_TOKEN。
1. **trace-config-api (ConfigError)**：根因是 **Deployment 配置缺失**。环境变量 `PAYMENT_GATEWAY_TOKEN` 未在 `aiops-traced-config` 的 Deployment 模板中正确定义。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 资源验证 | `kubectl get deployment api -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'` | 输出为 `128Mi` |

## ⚠️ 注意事项
- **内存峰值基线**：128Mi 是基于当前证据的推荐值。
"""
    structured_context = """
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
K8S_SIGNAL strength=strong observed="Last terminated state: api=OOMKilled exit=137"
- METRIC metric=container_memory_working_set_bytes pod=trace-oom-api-abc max=77.0Mi limit=80.0Mi max_limit_ratio=0.962 samples=["01:00:00=77.0Mi"]
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
- LOG event=config_missing message="required config PAYMENT_GATEWAY_TOKEN is missing" missing_config=PAYMENT_GATEWAY_TOKEN
"""

    result = ConclusionFormatterNode._enforce_metric_boundary_claims(
        content,
        structured_context,
    )
    result = ConclusionFormatterNode._enforce_evidence_scope_claims(
        result,
        structured_context,
    )

    assert "根因明确为**内存不足**" not in result
    assert "Memory Limit 设置过低" not in result
    assert "80Mi 无法承载业务峰值" not in result
    assert "输出为 `128Mi`" not in result
    assert "128Mi 是基于当前证据的推荐值" not in result
    assert "Deployment 未定义/注入" not in result
    assert "Deployment 配置缺失" not in result
    assert "运行时缺少 `PAYMENT_GATEWAY_TOKEN`" in result
    assert "正常业务基线" in result


def test_conclusion_corrects_pod_ips_and_restart_counts_from_authoritative_entities():
    content = """## 🔍 现象描述
| 类型 | 值 |
|------|-----|
| 节点 | node2 (IP: 172.16.104.2 / 172.16.104.13) |

## 🎯 根因分析
1. OOM 故障 (`trace-oom-api-598dcf5996-x6v6n`):
   -> 用户可见现象: CrashLoopBackOff, 554+ 次重启
2. Config 故障 (`trace-config-api-84bc7cb976-vgtl8`):
   -> 用户可见现象: CrashLoopBackOff, 488 次重启
"""
    layer_analysis = json.dumps({
        "current_abnormal_summary": {
            "selected_rows": [
                (
                    "aiops-traced-config trace-config-api-84bc7cb976-vgtl8 "
                    "0/1 CrashLoopBackOff 554 (3m36s ago) 2d "
                    "172.16.104.2 node2"
                ),
                (
                    "aiops-traced-oom trace-oom-api-598dcf5996-x6v6n "
                    "0/1 CrashLoopBackOff 488 (46s ago) 2d2h "
                    "172.16.104.13 node2"
                ),
            ],
        },
    })
    structured_context = """
- [collect_aiops_case]
AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled
ENTITY entity=Pod aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n node=node2 pod_ip=172.16.104.13
- [collect_aiops_case]
AIOPS_CASE case_id=config status=case_collected abnormal_type=crashloopbackoff
ENTITY entity=Pod aiops-traced-config/trace-config-api-84bc7cb976-vgtl8 node=node2 pod_ip=172.16.104.2
"""

    result = ConclusionFormatterNode._enforce_entity_identity_facts(
        content,
        layer_analysis,
        structured_context,
    )

    assert "| **节点** | `node2` |" in result
    assert (
        "| **Pod IP** | "
        "`trace-oom-api-598dcf5996-x6v6n=172.16.104.13`, "
        "`trace-config-api-84bc7cb976-vgtl8=172.16.104.2` |"
    ) in result
    assert "node2 (IP:" not in result
    assert "CrashLoopBackOff, 488 次重启" in result
    assert "CrashLoopBackOff, 554 次重启" in result


def test_conclusion_keeps_memory_leak_claim_when_tool_fact_explicitly_confirms_it():
    content = """## 🎯 根因分析
- `api-pod` 的日志明确确认内存泄漏。
"""
    structured_context = """
- [collect_aiops_case]
AIOPS_CASE case_id=leak status=case_collected abnormal_type=oomkilled
ENTITY entity=Pod app/api-pod node=node2 pod_ip=172.16.104.20
K8S_SIGNAL strength=strong observed="Last terminated state: api=OOMKilled exit=137" evidence_refs=["k8s-leak"]
LOG event=memory_leak_detected message=memory_leak_confirmed trace_id=leak-trace
"""

    result = ConclusionFormatterNode._enforce_entity_evidence_consistency(
        content,
        structured_context,
    )

    assert "内存泄漏" in result
    assert "未证明泄漏机制" not in result


def test_conclusion_prompt_uses_compact_structured_context_without_full_raw_duplication():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall("## 诊断概览\n证据完整度: 1/1 (100%)")
    raw_blob = "raw kubectl event line\n" * 300
    evidence_analysis = json.dumps({
        "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
        "evidence_inventory": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events",
                "collected": True,
                "raw_data": raw_blob,
            }
        ],
        "tool_data": [
            {"tool": "kubectl_events", "data": raw_blob},
        ],
    }, ensure_ascii=False)
    rca_analysis = json.dumps({
        "root_cause": "节点出口网络超时导致镜像拉取失败",
        "root_cause_summary": "节点出口网络超时导致镜像拉取失败",
        "confidence": 0.9,
        "evidence_analysis": [{"raw_data": raw_blob, "interpretation": "镜像拉取失败"}],
    }, ensure_ascii=False)

    node._generate_with_llm(
        question="我的集群有什么问题",
        layer_analysis='{"layer":"L3"}',
        evidence_analysis=evidence_analysis,
        rca_analysis=rca_analysis,
        layer=Layer.L3,
    )

    prompt = node.ai_call.calls[0]["kwargs"]["question"]
    assert "# 结构化诊断上下文" in prompt
    assert "# 阶段2：证据采集分析\n{" not in prompt
    assert "# 阶段3：根因分析\n{" not in prompt
    assert raw_blob not in prompt
    assert "节点出口网络超时导致镜像拉取失败" in prompt
    assert "evidence_plan_stats: 1/1 (100%)" in prompt
    assert "证据采集统计（系统数据" not in prompt


def test_conclusion_prompt_marks_authoritative_tool_facts_above_candidate_scenarios():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall("## 诊断概览\nTerminating")

    evidence_analysis = json.dumps({
        "collection_summary": "计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%",
        "plan_total": 3,
        "plan_collected": 3,
        "plan_completeness": 1.0,
        "evidence_inventory": [
            {
                "id": "e1",
                "description": "获取 Pod YAML 确认 deletionTimestamp/finalizers/preStop",
                "level": "critical",
                "tool": "kubectl_get_yaml",
                "command": "kubectl get pod rc-terminating-prestop -n aiops-e2e -o yaml",
                "collected": True,
            }
        ],
        "tool_data": [
            {
                "tool": "kubectl_get_yaml",
                "data": "\n".join([
                    "kind: Pod",
                    "name: rc-terminating-prestop",
                    "deletionTimestamp: 2026-05-19T12:09:54Z",
                    "deletionGracePeriodSeconds: 21600",
                    "finalizers: <none>",
                    "terminationGracePeriodSeconds: 21600",
                    "lifecycle: {\"preStop\": {\"exec\": {\"command\": [\"sh\", \"-c\", \"echo stuck; sleep 21600\"]}}}",
                ]),
            },
            {
                "tool": "kubectl_describe",
                "data": "\n".join([
                    "status: Terminating",
                    "Termination Grace Period: 21600s",
                    "Normal  Killing  42m  kubelet  Stopping container app",
                ]),
            },
            {
                "tool": "kubectl_get_by_name",
                "data": "NAME    STATUS\nnode1   Ready",
            },
        ],
    }, ensure_ascii=False)
    rca_analysis = json.dumps({
        "root_cause": "[L1层] 当前无法基于 LLM 输出确定根本原因",
        "confidence": 0.1,
        "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同",
        "causal_chain": {"trigger": "LLM 未生成可靠因果链"},
    }, ensure_ascii=False)
    layer_analysis = json.dumps({
        "layer": "L1",
        "possible_scenarios": [
            {"scenario": "Finalizer 清理卡住", "probability": "high"},
            {"scenario": "preStop hook 或应用退出慢", "probability": "medium"},
        ],
    }, ensure_ascii=False)

    node._generate_with_llm(
        question="我的集群有什么问题",
        layer_analysis=layer_analysis,
        evidence_analysis=evidence_analysis,
        rca_analysis=rca_analysis,
        layer=Layer.L1,
    )

    prompt = node.ai_call.calls[0]["kwargs"]["question"]
    assert "# 权威工具事实（最高优先级）" in prompt
    assert "finalizers: <none>" in prompt
    assert "排除 finalizer 未清理根因" in prompt
    assert "preStop hook" in prompt
    assert "sleep 21600" in prompt
    assert "候选场景不能覆盖权威工具事实" in prompt


def test_conclusion_token_budget_defaults_to_model_window(monkeypatch):
    monkeypatch.delenv("CONCLUSION_TOKEN_BUDGET", raising=False)
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    node = ConclusionFormatterNode()

    budget = node._resolve_context_token_budget(output_reserved=8192)

    assert 0 < budget < 32000
    assert budget <= 22000


def test_layer_prompt_is_diagnosis_and_healthy_only():
    expected_phrases = [
        "这个节点只服务于诊断类和健康检查类请求",
        "这个节点只服务于诊断类和健康检查类请求，负责输出 `HEALTHY / L0 / L1 / L2 / L3 / L4`",
        "你只负责“定位分析”和“定层”，不负责完整证据采集",
        "详细证据采集、深度验证、更多工具调用统一交给下游 evidence 节点",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
    assert "QUERY direct" not in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_event_validation_against_current_state():
    expected_phrases = [
        "events 只能作为辅助证据",
        "当前环境中的活跃异常对象",
        "如果 Warning 事件指向某个 Pod/Node/Workload",
        "该事件视为历史噪音",
        "不要把“曾经发生过异常”当成“当前仍有故障”",
        "Events 禁止向 `abnormal_pods` 添加当前 Pod 扫描中不存在的 Pod",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_defines_health_baseline_and_efficiency_rules():
    expected_phrases = [
        "健康检查不能只看 Pod Running",
        "Pod Running/Ready 只是信号之一，不等于整体健康",
        "Node / Workload / Service-EndPoints / Storage / Events",
        "不要为了健康检查默认做全量扫描",
        "只有在当前问题或当前信号指向某一资源面时，才扩展到该资源面",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_is_pod_abnormal_first():
    expected_phrases = [
        "第一目标是识别当前异常 Pod 的状态关键字",
        "abnormal_pods",
        "abnormal_groups",
        "pod_status_keyword",
        "pod_abnormal_type",
        "Pending / CrashLoopBackOff / ImagePullBackOff / OOMKilled / Evicted",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_requires_global_abnormal_pod_scan_first():
    expected_phrases = [
        "首轮必须先做全局 Pod 状态扫描",
        "kubectl_get_by_kind_in_cluster(kind=\"Pod\")",
        "kubectl get pods -A",
        "排除 `STATUS=Running`、`STATUS=Completed`、`STATUS=Succeeded`",
        "第一个真实工具调用必须优先获取全局 Pod 列表",
        "必须先过滤掉 Running / Completed / Succeeded",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_keeps_explicit_pod_request_in_scope():
    expected_phrases = [
        "用户明确指定 namespace + Pod",
        "其他异常 Pod 只作为背景",
        "不得加入本次 issue_groups",
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


def test_layer_prompt_defines_pod_abnormal_type_taxonomy_and_derived_layer():
    expected_phrases = [
        "L0-L4 只是 Pod 异常状态的归因分类兼容字段",
        "derived_layer",
        "status_category",
        "Evicted",
        "VolumeMountFailed",
        "PendingUnschedulable",
        "NodeLostOrUnknown",
        "TerminatingStuck",
        "OOMKilled",
        "CrashLoopBackOffRuntime",
        "ImagePullFailed",
        "SandboxCreateFailed",
        "ConfigError",
        "NotReadyProbeFailed",
        "CrashLoopBackOff 只是状态关键字，不是最终异常类型",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_extract_prompt_preserves_pod_abnormal_type_taxonomy():
    extract_prompt = get_workflow_prompt("layer_extract")
    expected_phrases = [
        "Pod 异常状态优先",
        "derived_layer",
        "status_category",
        "VolumeMountFailed",
        "PendingUnschedulable",
        "SandboxCreateFailed",
        "NotReadyProbeFailed",
    ]

    for phrase in expected_phrases:
        assert phrase in extract_prompt


def test_layer_prompt_does_not_rely_on_general_health_runbooks():
    assert "private-k8s-health-reference.md" not in LAYER_CLASSIFIER_PROMPT
    assert "l4-dependency-503" not in LAYER_CLASSIFIER_PROMPT


def test_layer_extract_prompt_is_current_state_first():
    extract_prompt = get_workflow_prompt("layer_extract")
    expected_phrases = [
        "当前仍异常的 Pod",
        "pod_status_keyword",
        "pod_abnormal_type",
        "历史 event",
        "HEALTHY",
    ]

    for phrase in expected_phrases:
        assert phrase in extract_prompt


def test_rca_prompt_includes_json_contract_for_text_fallback():
    rca_prompt = get_workflow_prompt("rca")
    expected_phrases = [
        "如果 native structured output 不可用",
        "只输出一个 JSON 对象",
        '"root_cause_summary"',
        '"confidence"',
        '"primary_runbooks"',
        '"alternative_causes"',
        "不要输出 Markdown",
        "不要输出代码块围栏",
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
        "一旦已经获得回答用户问题所需的关键数据，立即停止采集并输出 JSON",
    ]

    for phrase in expected_phrases:
        assert phrase in direct_prompt


def test_deployed_workflow_disables_layer_early_stop_by_default():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    layer_early_stop = app_config["workflow"]["layer"]["early_stop"]
    assert layer_early_stop["enabled"] is False
    assert layer_early_stop["explicit_pod_enabled"] is True


def test_deployed_config_enables_autonomous_observability_and_disables_compatibility_servers():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    autonomous = app_config["mcp_servers"]["aiops-observability-query"]
    assert autonomous["enabled"] is True
    assert autonomous["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8100/sse"
    assert autonomous["config"]["mode"] == "sse"

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
        "### Runbook 使用原则",
        "优先调用 fetch_runbook 获取参考",
        "只允许使用与 Pod 异常状态直接相关的 runbook",
        "runbook 选择必须按 Pod 异常类型匹配",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_layer_prompt_delegates_distinct_runbook_selection_to_qwen_without_duplicates():
    expected_phrases = [
        "由你根据每个异常 Pod 的当前状态和异常类型自主选择",
        "多个独立异常类型需要调用多个对应 runbook",
        "同一个 runbook 在本节点内最多调用一次",
        "不能因为多个 Pod 都显示 CrashLoopBackOff 就只选择一个 runbook",
        "每个已识别的独立异常类型已经获得匹配 runbook",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT


def test_evidence_prompt_requires_pod_handoff_and_autonomous_observability_contract():
    expected_phrases = [
        "abnormal_pods",
        "abnormal_groups",
        "pod_status_keyword",
        "pod_abnormal_type",
        "核心任务",
        "找证据",
        "layer_handoff.matched_runbooks",
        "不要在 evidence 阶段重新选择 runbook",
        "异常 Pod 返回 NotFound",
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
        "每个通用查询都必须填写明确 `purpose`",
        "首轮门控",
        "不保证每个维度都有数据",
        "三维首轮结果返回后",
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

    assert "诊断类和健康检查类请求" in zh_prompt
    assert en_prompt == zh_prompt


def test_english_layer_prompt_is_diagnosis_and_healthy_only():
    en_prompt = get_workflow_prompt("layer", prompt_language="en")

    assert "诊断类和健康检查类请求" in en_prompt
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


def test_remediation_plan_prompt_uses_fact_ledger_diagnostic_only_architecture():
    prompt = FACT_LEDGER_REMEDIATION_PLAN_PROMPT
    assert "Fact Ledger 主路径仅用于诊断" in prompt
    assert '"fix_type": "manual_only"' in prompt
    assert '"actions": []' in prompt
    assert "Remediation Policy Contract" in prompt
    assert "get、describe、logs、top、rollout status" in prompt
    assert "supporting_fact_ids" not in prompt
    assert "target_entity_id" not in prompt
    assert '"remediation_available": true' not in prompt


def test_active_fact_ledger_prompt_excludes_legacy_executable_schema():
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {}
    node.ai_call = _RecordingAICall(
        "## 诊断概览\n\n## 根因分析\n\n## 修复建议\n"
    )

    node._generate_with_llm(
        question="为什么 api Pod 异常？",
        layer_analysis="{}",
        evidence_analysis="{}",
        rca_analysis="{}",
        layer=Layer.L2,
        fact_ledger_authoritative=True,
    )

    call = node.ai_call.calls[-1]["kwargs"]
    active_prompt = call["system_prompt"] + "\n" + call["question"]
    assert "supporting_fact_ids" not in active_prompt
    assert "target_entity_id" not in active_prompt
    assert '"remediation_available": true' not in active_prompt
    assert "修复命令可直接复制执行" not in active_prompt


def test_conclusion_prompt_supports_independent_response_language():
    prompt = get_workflow_prompt(
        "conclusion",
        prompt_language="en",
        response_language="en",
    )

    assert "把已验证诊断事实写成给人看的 Markdown 报告" in prompt
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
    """Qwen selects scoped queries while the legacy coarse helper remains available."""
    from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode

    assert not hasattr(EvidenceCollectorNode, "_inject_aiops_case_plan_item")
    assert hasattr(EvidenceCollectorNode, "_ensure_mandatory_aiops_case_plan")
    assert "MCP 只校验 Pod scope 并执行，不按异常类型选择固定指标" in EVIDENCE_COLLECTOR_PROMPT
    assert "补证由上一轮真实结果驱动" in EVIDENCE_COLLECTOR_PROMPT
    assert "不使用固定工具顺序，也不按故障类型写死工具链" in EVIDENCE_COLLECTOR_PROMPT
    assert "evidence 上下文使用率达到 80% 后必须停止新增工具调用" in EVIDENCE_COLLECTOR_PROMPT
    assert "mandatory" not in EVIDENCE_COLLECTOR_PROMPT


def test_aiops_prompts_preserve_exact_observability_and_causality():
    assert "facts/samples/query/evidence_refs" in EVIDENCE_COLLECTOR_PROMPT
    assert "DeepFlow flow 与 Tempo span 是不同证据" in EVIDENCE_COLLECTOR_PROMPT
    assert "coverage=present 只表示命中真实数据，不自动等于根因成立" in EVIDENCE_COLLECTOR_PROMPT
    assert "empty/absent/weak/error 是明确的数据边界" in EVIDENCE_COLLECTOR_PROMPT
    assert "决定性 Fact 的原始 value 必须逐字保留" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "完整 trace_id" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "Tempo span attributes" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "不得把 direct/high 降级为 weak" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "不同 trace_id 不得合并" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "duration_us=0" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "不能推断请求无响应或失败" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "精确值、状态、实体、来源和因果只能来自" in CONCLUSION_FORMATTER_PROMPT
    assert "不同实体、时间窗口或 trace_id 不拼接" in CONCLUSION_FORMATTER_PROMPT
    assert "拓扑事实只描述关系，不自动证明健康或因果" in CONCLUSION_FORMATTER_PROMPT
    assert "背景证据不得升级为根因" in CONCLUSION_FORMATTER_PROMPT


def test_conclusion_prompt_is_human_focused_and_grounded():
    prompt = CONCLUSION_FORMATTER_PROMPT

    for heading in (
        "诊断概览",
        "现象描述",
        "关键证据",
        "证据关联与因果链",
        "根因结论",
        "修复建议",
        "验证步骤",
        "注意事项",
    ):
        assert heading in prompt
    assert "<!-- facts:fact-id[,fact-id...] -->" in prompt
    assert "Markdown 粗体" in prompt
    assert "正文不展示 Fact ID、entity ID 或 JSON" in prompt
    assert "背景证据不得升级为根因" in prompt


def test_conclusion_prompt_does_not_teach_one_fault_scenario():
    prompt = CONCLUSION_FORMATTER_PROMPT

    for scenario in (
        "OOMKilled",
        "ImagePullBackOff",
        "ConfigError",
        "TerminatingStuck",
    ):
        assert scenario not in prompt
    assert len(prompt) < 6000
    for seeded_example in (
        "metric-...-prometheus",
        "log-...-current",
        "deepflow-...",
        "k8s-...-pod-yaml",
        "allocated business cache chunk=25 approx_mib=50",
        "memory limit: 256Mi",
        "共 N 个",
    ):
        assert seeded_example not in CONCLUSION_FORMATTER_PROMPT


def test_rca_and_conclusion_prompts_require_verbatim_per_pod_observability():
    rca_phrases = [
        "每个异常 Pod 都必须独立形成证据分析和根因结论",
        "至少引用一条最有判别力的日志 message 原文",
        "决定性 Fact 的原始 value 必须逐字保留",
        "不能只写抽象故障标签",
    ]
    conclusion_phrases = [
        "多实体分别总结",
        "可观测性表只做维度摘要",
        "核心实体、状态、错误、指标和值使用 Markdown 粗体",
        "每个事实段落末尾添加",
        "根因只使用 validated supporting facts",
    ]

    for phrase in rca_phrases:
        assert phrase in ROOT_CAUSE_ANALYZER_PROMPT
    for phrase in conclusion_phrases:
        assert phrase in CONCLUSION_FORMATTER_PROMPT


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
        "决定性 Fact 的原始 value 必须逐字保留",
        "只有完整 trace_id 完全相同的记录才能合并",
        "topology relationship、source、target、directness、confidence",
    ):
        assert phrase in ROOT_CAUSE_ANALYZER_PROMPT
    assert "不同实体、时间窗口或 trace_id 不拼接" in CONCLUSION_FORMATTER_PROMPT
    assert "拓扑事实只描述关系，不自动证明健康或因果" in CONCLUSION_FORMATTER_PROMPT


def test_prompts_refine_runbooks_after_live_evidence_and_preserve_topology_semantics():
    evidence_phrases = [
        "拿到 Kubernetes 与通用可观测性查询的真实结果后",
        "补充更具体的 runbook",
        "同一 runbook 在整个诊断流程中只允许调用一次",
        "多个独立异常类型可以分别补充不同 runbook",
    ]
    conclusion_phrases = [
        "拓扑事实只描述关系，不自动证明健康或因果",
        "原始关系由机器附录保留",
        "只引用输入中存在的完整 Fact ID",
    ]

    for phrase in evidence_phrases:
        assert phrase in EVIDENCE_COLLECTOR_PROMPT
    assert "拿到 `collect_aiops_case` 的真实结果后" not in EVIDENCE_COLLECTOR_PROMPT
    assert "通用 CrashLoop runbook" not in EVIDENCE_COLLECTOR_PROMPT
    for phrase in conclusion_phrases:
        assert phrase in CONCLUSION_FORMATTER_PROMPT


def test_deployment_enables_autonomous_evidence_context_stop():
    manifest_path = Path(__file__).resolve().parents[3] / "deploy" / "configmap" / "config.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(manifest["data"]["config.yaml"])

    assert config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert config["workflow"]["evidence"]["early_stop"]["enabled"] is True


def test_traced_oom_manifest_does_not_leak_fault_answer_in_span_attributes():
    manifest = (
        Path(__file__).resolve().parents[3] / "testcases" / "aiops-traced-oom.yaml"
    ).read_text(encoding="utf-8")

    assert "aiops.fault.type" not in manifest
    assert "resource.memory.oomkilled" not in manifest


def test_conclusion_keeps_deepflow_only_trace_ids_out_of_tempo():
    report = """| 维度 | 数据源 | 状态 | 核心事实 | 证据 ref |
|---|---|---|---|---|
| **Tracing** | DeepFlow/Tempo | present | old | old-ref |
"""
    structured_context = """
OBSERVABILITY_EXECUTION metrics=present logging=present tracing=present topology=present
- QUERY_FACT ref=deepflow-only source_system=deepflow name=l7_flow trace_id=deepflow-trace directness=direct
- QUERY_FACT ref=tempo-shared source_system=tempo name=application_span trace_id=shared-trace directness=direct
"""

    result = ConclusionFormatterNode._enforce_observability_dimension_table(
        report,
        structured_context,
    )
    tracing_row = next(
        line for line in result.splitlines() if line.startswith("| **Tracing**")
    )

    assert "DeepFlow trace_id=deepflow-trace" in tracing_row
    assert "Tempo trace_id=shared-trace" in tracing_row
    assert "Tempo trace_id=deepflow-trace" not in tracing_row


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
            },
        },
    ]

    section = node._build_tool_data_section(events)

    assert "memory-working-set=70168576" in section
    assert "restart-increase=4" in section
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
            },
        },
    ]

    section = node._build_tool_data_section(events)

    assert "invalid_time_range" in section
    assert "transport-only-memory=70168576" not in section


def test_actual_topology_query_facts_reach_conclusion_as_edges():
    structured = {
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-api",
        },
        "purpose": "确认控制器关系",
        "coverage": "present",
        "directness": "direct",
        "facts": [
            {
                "ref": "topology-owned-by",
                "source_system": "kubernetes",
                "name": "kubernetes.relationship",
                "relation": "owned_by",
                "value": {
                    "relation": "owned_by",
                    "relationship": "Pod --owned_by--> ReplicaSet",
                    "source": {
                        "kind": "Pod",
                        "namespace": "demo",
                        "name": "api",
                        "uid": "uid-api",
                    },
                    "target": {
                        "kind": "ReplicaSet",
                        "namespace": "demo",
                        "name": "api-rs",
                        "uid": "uid-rs",
                    },
                    "source_field": "metadata.ownerReferences",
                },
                "directness": "direct",
                "confidence": "high",
            }
        ],
        "samples": [],
        "evidence_refs": ["topology-owned-by"],
    }
    agent_facts = EvidenceCollectorNode._build_aiops_agent_facts(
        "query_pod_topology",
        structured,
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "query_pod_topology",
                "agent_facts": agent_facts,
                "agent_context": json.dumps(structured),
            }
        ]
    })

    context = ConclusionFormatterNode._build_structured_diagnosis_context(
        evidence_analysis,
        "{}",
    )

    assert (
        'TOPOLOGY relationship="Pod --owned_by--> ReplicaSet"'
        in context
    )
    assert "source_field=metadata.ownerReferences" in context
    assert "topology-owned-by" in context


def test_deployed_partial_topology_reaches_ledger_rca_and_conclusion_context():
    node = EvidenceCollectorNode()
    structured = {
        "ok": False,
        "status": "query_partial",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api-abc",
            "pod_uid": "uid-api",
            "node": "node1",
        },
        "purpose": "确认目标 Pod 的控制器、Service 和节点关系",
        "coverage": "partial",
        "directness": "direct",
        "query": {"namespace": "demo", "pod": "api-abc"},
        "facts": [
            {
                "ref": "k8s-topology-owned-by",
                "source_system": "kubernetes",
                "dimension": "topology",
                "name": "topology.relationship",
                "value": {
                    "relation": "owned_by",
                    "relationship": "Pod --owned_by--> ReplicaSet",
                    "source": {
                        "kind": "Pod",
                        "namespace": "demo",
                        "name": "api-abc",
                        "uid": "uid-api",
                    },
                    "target": {
                        "kind": "ReplicaSet",
                        "namespace": "demo",
                        "name": "api-rs",
                        "uid": "uid-rs",
                    },
                },
                "directness": "direct",
            }
        ],
        "samples": [],
        "entities": [
            {
                "kind": "Pod",
                "namespace": "demo",
                "name": "api-abc",
                "uid": "uid-api",
                "source_system": "kubernetes",
            },
            {
                "kind": "ReplicaSet",
                "namespace": "demo",
                "name": "api-rs",
                "uid": "uid-rs",
                "source_system": "kubernetes",
            },
        ],
        "edges": [
            {
                "relation": "owned_by",
                "relationship": "Pod --owned_by--> ReplicaSet",
                "source": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api-abc",
                    "uid": "uid-api",
                },
                "target": {
                    "kind": "ReplicaSet",
                    "namespace": "demo",
                    "name": "api-rs",
                    "uid": "uid-rs",
                },
                "source_field": "metadata.ownerReferences",
                "source_system": "kubernetes",
                "directness": "direct",
                "confidence": "high",
                "evidence_refs": ["k8s-topology-owned-by"],
            }
        ],
        "topology_summary": {
            "entity_count": 2,
            "edge_count": 1,
            "relations": ["owned_by"],
        },
        "limitations": [
            "Service and Endpoint discovery exceeded the topology response limit"
        ],
        "evidence_refs": ["k8s-topology-owned-by"],
        "truncated": True,
        "limits": {"max_entities": 20, "max_edges": 20},
    }
    event = {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "query_pod_topology",
        "tool_args": {
            "namespace": "demo",
            "pod": "api-abc",
            "purpose": structured["purpose"],
        },
        "result": "partial topology",
        "result_preview": "partial topology",
        "raw_ref": "/archive/partial-topology.raw",
        "structured_ref": "/archive/partial-topology.structured.json",
        "structured": structured,
    }

    independent_uid_event = {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "kubectl_describe",
        "tool_args": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api-abc",
        },
        "structured": {
            "primary_entity": {
                "kind": "Pod",
                "namespace": "demo",
                "name": "api-abc",
                "uid": "uid-api",
            }
        },
    }
    tool_data = node._extract_tool_data_from_thinking(
        [event, independent_uid_event]
    )
    query_tool_data = [
        item
        for item in tool_data
        if item.get("tool") == "query_pod_topology"
    ]

    assert len(query_tool_data) == 1
    ledger = query_tool_data[0]["fact_ledger"]
    records = ledger["records"]
    records_by_attribute = {
        record["attribute"]: record
        for record in records
        if record["attribute"] != "topology.relationship"
    }
    relationships = [
        record
        for record in records
        if record["attribute"] == "topology.relationship"
    ]
    assert records_by_attribute["topology.entities"]["value"] == (
        structured["entities"]
    )
    assert records_by_attribute["topology.summary"]["value"] == (
        structured["topology_summary"]
    )
    assert len(relationships) == 1
    assert relationships[0]["value"] == {
        "relation": "owned_by",
        "relationship": "Pod --owned_by--> ReplicaSet",
        "source": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api-abc",
            "uid": "uid-api",
            "source_system": "kubernetes",
            "entity_id": "k8s.pod:demo/api-abc:uid-api",
        },
        "target": {
            "kind": "ReplicaSet",
            "namespace": "demo",
            "name": "api-rs",
            "uid": "uid-rs",
            "source_system": "kubernetes",
            "entity_id": "k8s.replicaset:demo/api-rs:uid-rs",
        },
        "source_field": "metadata.ownerReferences",
    }
    assert relationships[0]["source_system"] == "kubernetes"
    assert relationships[0]["directness"] == "direct"
    assert relationships[0]["confidence"] == "high"
    assert relationships[0]["evidence_refs"] == [
        "k8s-topology-owned-by"
    ]
    assert records_by_attribute["topology.coverage"]["value"] == {
        "coverage": "partial",
        "limitations": structured["limitations"],
    }

    evidence_analysis = json.dumps(
        {"tool_data": query_tool_data},
        ensure_ascii=False,
    )
    rca_context = RootCauseAnalyzerNode()._extract_tool_data_for_rca(
        evidence_analysis,
        max_chars=20000,
    )
    fact_report_context = ConclusionFormatterNode._build_fact_report_context(
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
    )
    assert fact_report_context is not None
    conclusion_context = json.dumps(
        [
            selected.model_dump(mode="json", exclude_none=True)
            for selected in fact_report_context[0]
        ],
        ensure_ascii=False,
    )

    for context in (rca_context, conclusion_context):
        assert "topology.entities" in context
        assert "api-abc" in context
        assert "api-rs" in context
        assert "topology.summary" in context
        assert "entity_count" in context
        assert "Pod --owned_by--> ReplicaSet" in context
        assert "metadata.ownerReferences" in context
        assert "k8s-topology-owned-by" in context
        assert "confidence" in context
        assert "high" in context
        assert structured["limitations"][0] in context


def test_deterministic_report_reconciles_present_facts_and_isolates_entity_chains():
    def fact(
        *,
        entity_id,
        entity_name,
        dimension,
        fact_type,
        attribute,
        value,
        source_system,
        ref,
        unit=None,
    ):
        record = {
            "entity_id": entity_id,
            "entity_kind": "Pod",
            "namespace": "demo",
            "entity_name": entity_name,
            "dimension": dimension,
            "fact_type": fact_type,
            "attribute": attribute,
            "value": value,
            "source_system": source_system,
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
            "evidence_refs": [ref],
        }
        if unit:
            record["unit"] = unit
        record["fact_id"] = _canonical_fact_id(record)
        return record

    def coverage(*, entity_id, entity_name, dimension):
        record = {
            "entity_id": entity_id,
            "entity_kind": "Pod",
            "namespace": "demo",
            "entity_name": entity_name,
            "dimension": dimension,
            "fact_type": "coverage",
            "attribute": f"{dimension}.coverage",
            "value": {"coverage": "present"},
            "source_system": "structured-query",
            "directness": "direct",
            "confidence": "high",
            "strength": "supporting",
            "evidence_refs": [],
        }
        record["fact_id"] = _canonical_fact_id(record)
        return record

    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    invented_summary_fragments = [
        "CPU=99.9%",
        "trace_id=trace-invented",
        "ref=ref-invented",
        "Service --owns--> Pod",
    ]
    records_by_entity = {}
    for entity_id, entity_name, suffix in (
        (entity_a, "api-a", "a"),
        (entity_b, "api-b", "b"),
    ):
        records = [
            fact(
                entity_id=entity_id,
                entity_name=entity_name,
                dimension="kubernetes",
                fact_type="state",
                attribute="pod.current_state",
                value={"ready": False, "restart_count": 3},
                source_system="kubernetes",
                ref=f"k8s-{suffix}",
            ),
            fact(
                entity_id=entity_id,
                entity_name=entity_name,
                dimension="metrics",
                fact_type="measurement",
                attribute="container.request_rate",
                value={"value": 17 + len(suffix)},
                source_system="prometheus",
                ref=f"metric-{suffix}",
                unit="requests/s",
            ),
            fact(
                entity_id=entity_id,
                entity_name=entity_name,
                dimension="logging",
                fact_type="log",
                attribute="application.error",
                value={
                    "message": (
                        f"entity-{suffix} startup failed"
                        + (
                            " ... 截断，原始 545 字符"
                            if suffix == "a"
                            else ""
                        )
                    )
                },
                source_system="elasticsearch",
                ref=f"log-{suffix}",
            ),
            fact(
                entity_id=entity_id,
                entity_name=entity_name,
                dimension="tracing",
                fact_type="span",
                attribute="application.span",
                value={
                    "trace_id": f"trace-{suffix}",
                    "span": f"GET /entity-{suffix}",
                },
                source_system="tempo",
                ref=f"trace-{suffix}",
            ),
            fact(
                entity_id=entity_id,
                entity_name=entity_name,
                dimension="topology",
                fact_type="relationship",
                attribute="topology.relationship",
                value={
                    "relation": "owned_by",
                    "relationship": "Pod --owned_by--> ReplicaSet",
                    "source_entity_id": entity_id,
                    "target_entity_id": (
                        f"k8s.replicaset:demo/{entity_name}-rs"
                    ),
                },
                source_system="kubernetes",
                ref=f"topology-{suffix}",
            ),
        ]
        records.extend(
            coverage(
                entity_id=entity_id,
                entity_name=entity_name,
                dimension=dimension,
            )
            for dimension in (
                "kubernetes",
                "metrics",
                "logging",
                "tracing",
                "topology",
            )
        )
        records_by_entity[entity_id] = records

    ledgers = []
    for index, (entity_id, records) in enumerate(
        records_by_entity.items(),
        start=1,
    ):
        ledgers.append({
            "contract_version": "aiops.fact-ledger.v1",
            "case_id": f"case-{index}",
            "scope_entity_ids": [entity_id],
            "records": records,
            "record_count": len(records),
            "truncated": False,
            "source": "mcp_canonical",
            "legacy_contract": False,
        })

    supporting_by_entity = {
        entity_id: [
            record["fact_id"]
            for record in records
            if record["fact_type"] != "coverage"
        ]
        for entity_id, records in records_by_entity.items()
    }
    authority_tool_data = []
    for ledger in ledgers:
        scoped_entity_id = ledger["scope_entity_ids"][0]
        pod_name = ledger["records"][0]["entity_name"]
        pod_uid = scoped_entity_id.rsplit(":", 1)[-1]
        item = {
            "tool": "query_pod_logs",
            "semantic_success": True,
            "authority_context": {
                "semantic_success": True,
                "status": "query_succeeded",
                "coverage": "present",
                "source_system": "kubernetes",
                "entity": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "pod": pod_name,
                    "pod_uid": pod_uid,
                },
                "trusted_pod_uid": pod_uid,
            },
            "fact_ledger": ledger,
        }
        decision = evaluate_report_authority(
            ledger_input=ledger,
            tool_item=item,
        )
        attach_internal_report_authority(
            item,
            ledger_input=ledger,
            decision=decision,
        )
        authority_tool_data.append(item)
    evidence_analysis = json.dumps(
        {"tool_data": authority_tool_data},
        ensure_ascii=False,
    )
    rca_analysis = json.dumps({
        "diagnostic_status": "diagnosed",
        "root_cause_summary": "Two independent entity-scoped failures",
        "supporting_fact_ids": [
            fact_id
            for fact_ids in supporting_by_entity.values()
            for fact_id in fact_ids
        ],
        "contradicting_fact_ids": [],
        "hypotheses": [
            {
                "hypothesis_id": "entity-a-hypothesis",
                "entity_id": entity_a,
                "summary": " ".join([
                    *invented_summary_fragments,
                    entity_b,
                    "entity-b startup failed",
                ]),
                "supporting_fact_ids": supporting_by_entity[entity_a],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.91,
            },
            {
                "hypothesis_id": "entity-b-hypothesis",
                "entity_id": entity_b,
                "summary": "api-b has an independent entity-scoped startup failure",
                "supporting_fact_ids": supporting_by_entity[entity_b],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.89,
            },
        ],
        "confidence": 0.9,
        "confidence_reason": "Each hypothesis references only same-entity direct facts",
        "limitations": (
            "Metrics、Logging、Tracing、Kubernetes 和 Topology 未提供该维度；"
            "... 截断，原始 545 字符"
        ),
    }, ensure_ascii=False)
    layer_analysis = json.dumps({
        "layer": "L3",
        "issue_groups": [
            {
                "group_id": "group-a",
                "entities": [
                    {"kind": "Pod", "namespace": "demo", "name": "api-a"}
                ],
            },
            {
                "group_id": "group-b",
                "entities": [
                    {"kind": "Pod", "namespace": "demo", "name": "api-b"}
                ],
            },
        ],
    }, ensure_ascii=False)

    result = ConclusionFormatterNode().execute({
        "question": "What is failing?",
        "layer": Layer.L3,
        "layer_analysis": layer_analysis,
        "evidence_analysis": evidence_analysis,
        "rca_analysis": rca_analysis,
        "root_cause": "combined stale root cause",
        "causal_chain": {
            "trigger": "combined trigger",
            "mechanism": "cross-entity mechanism",
            "manifestation": "combined manifestation",
        },
        "thinking_events": [],
    })["conclusion"]

    for dimension in ("Metrics", "Logging", "Tracing", "K8s"):
        row = next(
            line
            for line in result.splitlines()
            if line.startswith(f"| **{dimension}**")
        )
        assert "| present |" in row
        assert "未返回可用" not in row
        assert "未获取到" not in row
    assert "Pod --owned_by--> ReplicaSet" in result
    assert "本轮未返回可核验的拓扑原始边" not in result
    assert "未提供该维度" not in result
    assert "... 截断，原始 545 字符" not in result
    assert "combined trigger" not in result
    assert "Two independent entity-scoped failures" not in result
    for fragment in invented_summary_fragments:
        assert fragment not in result
    assert result.count("#### 实体隔离因果链") == 2

    entity_a_section = result.split(f"### `{entity_a}`", 1)[1].split(
        f"### `{entity_b}`",
        1,
    )[0]
    entity_b_section = result.split(f"### `{entity_b}`", 1)[1].split(
        "### 支持事实",
        1,
    )[0]
    assert entity_a in entity_a_section
    assert entity_b not in entity_a_section
    assert "entity-b startup failed" not in entity_a_section
    assert entity_b in entity_b_section
    assert entity_a not in entity_b_section


def test_a021_autonomous_query_fact_json_populates_log_k8s_and_tool_sources():
    report = """## 📊 可观测性数据

### 三大观测维度
| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |
|------|----------|----------|----------------------------------|----------|
| **Metrics** | Prometheus | present | old | old |
| **Logging** | ES/Filebeat | present | 未返回可用日志原文 | old |
| **Tracing** | DeepFlow/Tempo | present | old | old |
| **K8s** | Kubernetes API | present | 未返回可用 Kubernetes 强信号 | old |
"""
    structured_context = r'''
observability_collection_mode: autonomous_query
OBSERVABILITY_EXECUTION metrics=present logging=present tracing=present topology=present
OBSERVABILITY_SOURCE dimension=metrics tool=execute_pod_promql source_system=prometheus coverage=present
OBSERVABILITY_SOURCE dimension=logging tool=query_pod_logs source_system=elasticsearch coverage=present
OBSERVABILITY_SOURCE dimension=tracing tool=query_pod_tracing source_system=deepflow+tempo coverage=present
OBSERVABILITY_SOURCE dimension=topology tool=query_pod_topology source_system=kubernetes coverage=present
- QUERY_FACT ref=log-config source_system=elasticsearch name=log.message value="{\"event\": \"fatal configuration error\", \"message\": \"required config PAYMENT_GATEWAY_TOKEN is missing\", \"details\": {\"quoted\": \"value with spaces\"}, \"exit_code\": 78}" raw_ref={"source_system":"elasticsearch","document_id":"doc-1"} directness=direct
- QUERY_FACT ref=tempo-config source_system=tempo name=application_span value={"trace_id":"4033f62179da91859589a57617a467df","attributes":{"error.type":"CONFIG_MISSING","config.key":"PAYMENT_GATEWAY_TOKEN"}} trace_id=4033f62179da91859589a57617a467df directness=direct
- CANONICAL_FACT fact_id=fact-oom-reason dimension=kubernetes fact_type=state attribute=container.last_terminated_reason value={"container":"business-api","reason":"OOMKilled"} source_system=kubernetes evidence_refs=["kubectl-describe-oom"] tool=kubectl_describe
- CANONICAL_FACT fact_id=fact-oom-exit dimension=kubernetes fact_type=state attribute=container.last_exit_code value={"container":"business-api","exit_code":137} source_system=kubernetes evidence_refs=["kubectl-describe-oom"] tool=kubectl_describe
'''

    result = ConclusionFormatterNode._enforce_observability_dimension_table(
        report,
        structured_context,
    )

    logging_row = next(
        line for line in result.splitlines()
        if line.startswith("| **Logging**")
    )
    tracing_row = next(
        line for line in result.splitlines()
        if line.startswith("| **Tracing**")
    )
    k8s_row = next(
        line for line in result.splitlines()
        if line.startswith("| **K8s**")
    )
    assert "query_pod_logs" in logging_row
    assert "required config PAYMENT_GATEWAY_TOKEN is missing" in logging_row
    assert "fatal configuration error" in logging_row
    assert "value with spaces" in logging_row
    assert "未返回可用日志原文" not in logging_row
    assert "query_pod_tracing" in tracing_row
    assert "4033f62179da91859589a57617a467df" in tracing_row
    assert "kubectl_describe" in k8s_row
    assert "OOMKilled" in k8s_row
    assert "exit_code" in k8s_row
    assert "137" in k8s_row
    assert "未返回可用 Kubernetes 强信号" not in k8s_row


def test_a021_topology_uses_query_tool_entities_and_removes_stale_limitations():
    report = """## 📊 可观测性数据

### 拓扑关系（实体与边）
> 以下关系由 `collect_aiops_case` 的结构化原始边确定性生成。
- stale edge

---

### 缺失证据（如有）
- 未提供 OOM 应用日志原文。
- 两个工作负载的真实 Deployment 名称不可用。
- OOM ReplicaSet 到 Deployment 关系 unavailable。
- 完整 trace ID 未获取到。
- 尚未提供 resources.limits.memory。

| 证据 | 级别 | 影响 |
|------|------|------|
| 完整 `trace_id` 与逐 span 原始属性 | 中 | 不能把不同请求合并成一条完整调用链；当前仅能依据每条查询返回的请求/响应事实判断影响。 |

当前尚未获得完整 `env`、`envFrom` 引用及 Deployment 名称。

需要人工确认：
- 上层 Deployment 的真实名称；
- 真实上层 Deployment 名称以及 `resources.limits.memory`。

```json
{
  "stop_conditions": [
    "未获得两个工作负载的真实 Deployment 名称",
    "未获得 resources.limits.memory"
  ]
}
```
"""
    structured_context = r'''
observability_collection_mode: autonomous_query
OBSERVABILITY_SOURCE dimension=logging tool=query_pod_logs source_system=elasticsearch coverage=present
OBSERVABILITY_SOURCE dimension=tracing tool=query_pod_tracing source_system=deepflow+tempo coverage=present
OBSERVABILITY_SOURCE dimension=topology tool=query_pod_topology source_system=kubernetes coverage=present
- QUERY_FACT ref=log-oom source_system=elasticsearch name=log.message value="{\"event\":\"allocate\",\"message\":\"allocated memory\",\"allocated_mib\":62}" raw_ref={"document_id":"oom-log"} directness=direct
- QUERY_FACT ref=tempo-oom source_system=tempo name=application_span value={"trace_id":"2d670350586cf4c6ec20f89865c1ede4"} trace_id=2d670350586cf4c6ec20f89865c1ede4 directness=direct
TOPOLOGY_ENTITY entity_id=e:pod kind=Pod namespace=demo name=api-pod source_system=kubernetes tool=query_pod_topology
TOPOLOGY_ENTITY entity_id=e:rs kind=ReplicaSet namespace=demo name=api-rs source_system=kubernetes tool=query_pod_topology
TOPOLOGY_ENTITY entity_id=e:deploy kind=Deployment namespace=demo name=api source_system=kubernetes tool=query_pod_topology
TOPOLOGY_ENTITY entity_id=e:deploy-worker kind=Deployment namespace=demo name=worker source_system=kubernetes tool=query_pod_topology
TOPOLOGY_EXACT_EDGES count=2
- TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" source=e:pod target=e:rs source_system=kubernetes directness=direct confidence=high
- TOPOLOGY relationship="ReplicaSet --owned_by--> Deployment" source=e:rs target=e:deploy source_system=kubernetes directness=direct confidence=high
'''

    result = ConclusionFormatterNode._enforce_exact_topology_section(
        report,
        structured_context,
    )
    result = ConclusionFormatterNode._append_exact_topology_appendix(
        result,
        structured_context,
    )
    result = ConclusionFormatterNode._reconcile_legacy_report_limitations(
        result,
        structured_context,
    )

    assert "`query_pod_topology`" in result
    assert "`collect_aiops_case`" not in result
    assert "Deployment `demo/api`" in result
    assert "未提供 OOM 应用日志原文" not in result
    assert "真实 Deployment 名称不可用" not in result
    assert "ReplicaSet 到 Deployment 关系 unavailable" not in result
    assert "完整 trace ID 未获取到" not in result
    assert "完整 `trace_id` 与逐 span 原始属性" not in result
    assert "已有精确 trace_id 与代表性 Tempo application span" in result
    assert "当前采样不能证明完整端到端调用链" in result
    assert "引用及 Deployment 名称" not in result
    assert "上层 Deployment 的真实名称" not in result
    assert "真实上层 Deployment 名称以及" not in result
    assert "未获得两个工作负载的真实 Deployment 名称" not in result
    assert "完整 `env`、`envFrom` 引用" in result
    assert "resources.limits.memory" in result
    assert "尚未提供 resources.limits.memory" in result


def test_a024_short_trace_id_table_row_becomes_sampling_boundary():
    report = """### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 完整 trace_id | 中 | 不能将不同流记录拼接成单一完整调用链。 |
"""
    structured_context = """
OBSERVABILITY_SOURCE dimension=tracing tool=query_pod_tracing source_system=deepflow+tempo coverage=present
- QUERY_FACT ref=deepflow-a source_system=deepflow name=flow value={"trace_id":"0123456789abcdef0123456789abcdef"} trace_id=0123456789abcdef0123456789abcdef directness=direct
- QUERY_FACT ref=tempo-a source_system=tempo name=application_span value={"trace_id":"0123456789abcdef0123456789abcdef","span":"GET /orders"} trace_id=0123456789abcdef0123456789abcdef directness=direct
"""

    result = ConclusionFormatterNode._reconcile_legacy_report_limitations(
        report,
        structured_context,
    )

    assert "| 完整 trace_id |" not in result
    assert "已有精确 trace_id 与代表性 Tempo application span" in result
    assert "当前采样不能证明完整端到端调用链" in result


def test_a024_known_deployment_keeps_only_podtemplate_resource_gap():
    report = """### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| `orders-api` 上层 Deployment 的准确名称及 PodTemplate | 高 | 无法安全生成针对该工作负载的资源写操作。 |
"""
    structured_context = """
OBSERVABILITY_SOURCE dimension=topology tool=query_pod_topology source_system=kubernetes coverage=present
TOPOLOGY_ENTITY entity_id=e:deployment kind=Deployment namespace=demo name=orders-api source_system=kubernetes tool=query_pod_topology
"""

    result = ConclusionFormatterNode._reconcile_legacy_report_limitations(
        report,
        structured_context,
    )

    assert "Deployment `demo/orders-api`" in result
    assert "准确名称" not in result
    assert "PodTemplate/resources" in result
    assert "资源写操作" in result


def test_a006_replay_shows_previous_logs_and_deepflow_in_human_body():
    fixture_path = (
        Path(__file__).resolve().parents[2]
        / "fixtures/observability/a006_human_report_replay.json"
    )
    replay = json.loads(fixture_path.read_text(encoding="utf-8"))
    ledgers = [
        FactLedger.model_validate(item)
        for item in replay["fact_ledgers"]
    ]

    report = ConclusionFormatterNode._apply_fact_ledger_report_contract(
        "",
        ledgers=ledgers,
        validated_claim=replay["validated_claim"],
        observations=replay["observations"],
    )
    body, appendix = report.split("## 机器可核验附录", 1)
    logging = next(
        line for line in body.splitlines()
        if line.startswith("| **Logging**")
    )
    tracing = next(
        line for line in body.splitlines()
        if line.startswith("| **Tracing**")
    )

    assert "kubectl_previous_logs" in logging
    assert "2 MiB" in logging
    assert "62 MiB" in logging
    assert "未获取到" not in logging
    assert "deepflow" in tracing
    assert "GET" in tracing and "/allocate" in tracing and "200" in tracing
    assert "26577 us" in tracing
    assert "未获取到" not in tracing
    for ledger in ledgers:
        for record in ledger.records:
            assert record.fact_id not in body
    assert "fact-a00600000004" in appendix
    plan = extract_remediation_plan(report)
    assert plan is not None
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


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


def test_a026_unknown_deployment_subject_is_not_replaced_from_context():
    report = """### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| `worker-api` 上层 Deployment 的准确名称及 PodTemplate | 高 | 无法安全生成针对该工作负载的资源写操作。 |
"""
    structured_context = """
OBSERVABILITY_SOURCE dimension=topology tool=query_pod_topology source_system=kubernetes coverage=present
TOPOLOGY_ENTITY entity_id=e:deployment kind=Deployment namespace=demo name=orders-api source_system=kubernetes tool=query_pod_topology
"""

    result = ConclusionFormatterNode._reconcile_legacy_report_limitations(
        report,
        structured_context,
    )

    assert "`worker-api` 上层 Deployment 的准确名称及 PodTemplate" in result
    assert "Deployment `demo/orders-api`" not in result


def test_a027_owned_deployment_subject_is_not_replaced_from_context():
    report = """### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| `worker-api` 对应的上层 Deployment 的准确名称及 PodTemplate | 高 | 无法安全生成针对该工作负载的资源写操作。 |
"""
    structured_context = """
OBSERVABILITY_SOURCE dimension=topology tool=query_pod_topology source_system=kubernetes coverage=present
TOPOLOGY_ENTITY entity_id=e:deployment kind=Deployment namespace=demo name=orders-api source_system=kubernetes tool=query_pod_topology
"""

    result = ConclusionFormatterNode._reconcile_legacy_report_limitations(
        report,
        structured_context,
    )

    assert (
        "`worker-api` 对应的上层 Deployment 的准确名称及 PodTemplate"
        in result
    )
    assert "Deployment `demo/orders-api`" not in result


def test_a021_evidence_stats_separate_dimension_coverage_from_sufficiency():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "observability_target_total": 8,
        "observability_target_collected": 8,
        "observability_target_completeness": 1.0,
        "diagnostic_evidence_total": 8,
        "diagnostic_evidence_collected": 8,
        "diagnostic_evidence_completeness": 1.0,
        "dimension_coverage": 1.0,
        "diagnostic_sufficiency": 0.85,
        "diagnostic_sufficiency_label": "充分",
        "evidence_inventory": [],
    })
    report = """## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **诊断证据充分度** | 6/8 (85%) |
"""

    result = node._enforce_evidence_stats(report, evidence_analysis)

    assert "| **可观测性维度覆盖** | 8/8 (100%) |" in result
    assert "| **诊断证据充分度** | 85% |" in result
    assert "6/8 (85%)" not in result


def test_a029_fact_ledger_report_keeps_weak_tracing_and_known_owners_truthful():
    def fact(
        *,
        entity_id,
        namespace,
        entity_name,
        dimension,
        fact_type,
        attribute,
        value,
        source_system,
        marker,
        directness="direct",
        confidence="high",
        strength="strong",
    ):
        record = {
            "entity_id": entity_id,
            "entity_kind": "Pod",
            "namespace": namespace,
            "entity_name": entity_name,
            "dimension": dimension,
            "fact_type": fact_type,
            "attribute": attribute,
            "value": value,
            "source_system": source_system,
            "directness": directness,
            "confidence": confidence,
            "strength": strength,
            "evidence_refs": [f"ref:{marker}"],
        }
        record["fact_id"] = _canonical_fact_id(record)
        return record

    ledgers = []
    for workload, trace_coverage in (
        ("config-api", "present"),
        ("oom-api", "weak"),
    ):
        namespace = f"demo-{workload}"
        entity_id = f"k8s.pod:{namespace}/{workload}:uid-{workload}"
        trace_id = (
            "0123456789abcdef0123456789abcdef"
            if workload == "config-api"
            else "fedcba9876543210fedcba9876543210"
        )
        records = [
            fact(
                entity_id=entity_id,
                namespace=namespace,
                entity_name=workload,
                dimension="tracing",
                fact_type="flow",
                attribute="l7_flow",
                value={"trace_id": trace_id},
                source_system="deepflow",
                marker=f"{workload}-flow",
            ),
            fact(
                entity_id=entity_id,
                namespace=namespace,
                entity_name=workload,
                dimension="topology",
                fact_type="relationship",
                attribute="kubernetes.relationship",
                value={
                    "relation": "owned_by",
                    "relationship": (
                        "ReplicaSet --owned_by--> Deployment"
                    ),
                    "source": {
                        "kind": "ReplicaSet",
                        "namespace": namespace,
                        "name": f"{workload}-rs",
                    },
                    "target": {
                        "kind": "Deployment",
                        "namespace": namespace,
                        "name": workload,
                    },
                },
                source_system="kubernetes",
                marker=f"{workload}-owner",
            ),
        ]
        if trace_coverage == "present":
            records.append(
                fact(
                    entity_id=entity_id,
                    namespace=namespace,
                    entity_name=workload,
                    dimension="tracing",
                    fact_type="span",
                    attribute="application_span",
                    value={"trace_id": trace_id, "name": "GET /work"},
                    source_system="tempo",
                    marker=f"{workload}-span",
                )
            )
        else:
            records.append(
                fact(
                    entity_id=entity_id,
                    namespace=namespace,
                    entity_name=workload,
                    dimension="tracing",
                    fact_type="coverage",
                    attribute="tracing.coverage",
                    value={
                        "coverage": "weak",
                        "telemetry": {
                            "deepflow": {"coverage": "present"},
                            "tempo": {"coverage": "error"},
                        },
                    },
                    source_system="deepflow+tempo",
                    marker=f"{workload}-coverage",
                    directness="related_context",
                    confidence="medium",
                    strength="supporting",
                )
            )
        ledgers.append(FactLedger.model_validate({
            "contract_version": "aiops.fact-ledger.v1",
            "case_id": f"case-{workload}",
            "scope_entity_ids": [entity_id],
            "records": records,
            "record_count": len(records),
            "truncated": False,
            "source": "mcp_canonical",
            "legacy_contract": False,
        }))

    report = """## 📊 可观测性数据

### 三大观测维度
| 维度 | 数据来源 | 覆盖状态 | 关键原始信号 | 证据 ref |
|---|---|---|---|---|
| **Tracing** | DeepFlow/Tempo | present | stale | stale |

### 拓扑关系（实体与边）
- stale

### 缺失证据（如有）
- 两个工作负载的真实 Deployment 名称不可用。
- oom-api ReplicaSet 到 Deployment 关系 unavailable。
"""
    result = ConclusionFormatterNode._apply_fact_ledger_report_contract(
        report,
        ledgers=ledgers,
        validated_claim={
            "diagnostic_status": "inconclusive",
            "supporting_fact_ids": [],
            "contradicting_fact_ids": [],
            "hypotheses": [],
            "claim_validation": {
                "valid": True,
                "valid_supporting_fact_ids": [],
                "valid_contradicting_fact_ids": [],
                "invalid_fact_ids": [],
                "reasons": [],
            },
        },
    )
    tracing_row = next(
        line
        for line in result.splitlines()
        if line.startswith("| **Tracing**")
    )

    assert "| partial |" in tracing_row
    assert "| present |" not in tracing_row
    assert "真实 Deployment 名称不可用" not in result
    assert "ReplicaSet 到 Deployment 关系 unavailable" not in result
    assert "demo-config-api/config-api" in result
    assert "demo-oom-api/oom-api" in result
