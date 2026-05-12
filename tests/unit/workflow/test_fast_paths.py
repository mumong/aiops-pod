import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.service import HolmesService
from app.core.prompts import (
    EVIDENCE_COLLECTOR_PROMPT,
    LAYER_CLASSIFIER_PROMPT,
    get_query_evidence_normalization_prompt,
    get_conclusion_mode_instruction,
    get_workflow_prompt,
)
from app.core.skills.models import Layer
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.schemas import ConclusionOutput, LayerOutput, QueryResult


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


def test_query_conclusion_uses_llm_even_when_query_result_present():
    node = ConclusionFormatterNode()

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

    assert len(node.ai_call.calls) == 1
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
  "primary_runbooks": ["l3-imagepull-failed.md"],
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
    assert "计划 1 项，实际采集 1 项" in prompt


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


def test_query_direct_prompt_boundaries_are_explicit():
    direct_prompt = get_workflow_prompt("layer_query_direct")
    expected_phrases = [
        "如果是 QUERY，你必须调用工具采集真实数据；本轮 agent 最终只写自然语言采集摘要",
        "禁止人工编写 `query_result`、结构化对象、Markdown 表格或最终报告",
        "`LayerOutput.query_result` 只能由后续 Pydantic schema 提取生成",
        "先把用户明确询问的查询项逐项列为采集清单",
        "每个查询项最终必须只有两种状态：已由真实 tool_result 支撑，或明确写入缺失项",
        "禁止把“已经发出的工具调用都返回了”当成“用户问题已完整回答”",
        "只采集用户明确询问的对象、维度和指标，不扩展无关指标",
        "优先调用 `fetch_runbook` 获取 `private-k8s-query-promql-reference.md` 作为查询参考",
        "涉及 Prometheus 指标查询时，必须先调用 `fetch_runbook`",
        "禁止跳过 runbook 直接调用 Prometheus 探索或自创 PromQL",
        "runbook 中已有直接适用模板时，必须优先逐字复用标准 PromQL",
        "只有当用户明确查询项全部已采集或已明确缺失，才允许写采集摘要",
    ]

    for phrase in expected_phrases:
        assert phrase in direct_prompt


def test_deployed_workflow_disables_layer_early_stop_by_default():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    assert app_config["workflow"]["layer"]["early_stop"]["enabled"] is False


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


def test_evidence_prompt_requires_pod_abnormal_handoff_fields():
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
    ]

    for phrase in expected_phrases:
        assert phrase in EVIDENCE_COLLECTOR_PROMPT

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
        for phrase in forbidden:
            assert phrase not in prompt


def test_conclusion_prompt_supports_independent_response_language():
    prompt = get_workflow_prompt(
        "conclusion",
        prompt_language="en",
        response_language="en",
    )

    assert "你是资深 K8s 诊断报告专家" in prompt
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
