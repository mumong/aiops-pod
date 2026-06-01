import os
import sys
import json
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.prompts import get_workflow_prompt
from app.core.skills.models import Layer
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.graph import _make_layer_router
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.schemas import ConclusionOutput, LayerOutput


def test_layer_router_query_direct_goes_to_conclusion():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        query_mode="direct",
    )

    assert router({"layer": Layer.QUERY}) == "conclusion"


def test_layer_router_query_full_goes_to_evidence():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        query_mode="full",
    )

    assert router({"layer": Layer.QUERY}) == "evidence"


def test_layer_router_non_query_path_is_unchanged_in_direct_mode():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        query_mode="direct",
    )

    assert router({"layer": Layer.L2}) == "evidence"


def test_query_conclusion_direct_mode_renders_query_result_without_llm():
    node = ConclusionFormatterNode(
        holmes_service=SimpleNamespace()
    )
    node.workflow_config_override = {"query_mode": "direct"}

    class _NoConclusionLLM:
        def call_structured(self, **kwargs):
            raise AssertionError("query direct conclusion should render locally")

        def call_simple(self, *args, **kwargs):
            raise AssertionError("query direct conclusion should render locally")

    node.ai_call = _NoConclusionLLM()

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

    assert "## 📊 查询结果" in result["conclusion"]
    assert "master" in result["conclusion"]
    assert "cpu_query" in result["conclusion"]


def test_query_conclusion_uses_query_specific_local_rendering():
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {
        "query_mode": "direct",
        "conclusion": {"max_tokens": {"query": 1024, "diagnosis": 8192}},
    }

    class _NoConclusionLLM:
        def call_structured(self, **kwargs):
            raise AssertionError("query direct conclusion should not call structured LLM")

        def call_simple(self, *args, **kwargs):
            raise AssertionError("query direct conclusion should not call simple LLM")

    node.ai_call = _NoConclusionLLM()

    result = node.execute({
        "question": "查询 CPU",
        "layer": Layer.QUERY,
        "query_result": {
            "query_target": "查询 CPU",
            "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
            "columns": [{"key": "node", "label": "节点"}, {"key": "cpu", "label": "CPU"}],
            "rows": [{"node": "node1", "cpu": "1%"}],
            "notes": [],
            "missing": [],
            "sources": [{"tool": "execute_prometheus_instant_query", "query": "cpu_query"}],
        },
    })

    assert "node1" in result["conclusion"]
    assert "| node1 | 1% |" in result["conclusion"]


def test_diagnosis_conclusion_uses_plain_markdown_by_default():
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {
        "conclusion": {"max_tokens": {"query": 1024, "diagnosis": 4096}},
    }

    class _PlainAICall:
        def __init__(self):
            self.simple_calls = []
            self.structured_calls = []

        def call_simple(self, system_prompt, question, **kwargs):
            self.simple_calls.append({
                "system_prompt": system_prompt,
                "question": question,
                **kwargs,
            })
            return "## 📊 诊断概览\n\nImagePullBackOff"

        def call_structured(self, **kwargs):
            self.structured_calls.append(kwargs)
            raise AssertionError("diagnosis conclusion should not use structured output by default")

    node.ai_call = _PlainAICall()

    result = node.execute({
        "question": "我的集群有什么问题？",
        "layer": Layer.L3,
        "layer_analysis": '{"layer":"L3"}',
        "evidence_analysis": "{}",
        "rca_analysis": "{}",
    })

    assert node.ai_call.simple_calls[0]["max_tokens"] == 4096
    assert "CONCLUSION_FORMATTER_PROMPT" not in node.ai_call.simple_calls[0]["system_prompt"]
    assert node.ai_call.structured_calls == []
    assert "## 📊 诊断概览" in result["conclusion"]


def test_query_conclusion_normalizes_legacy_string_fields():
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}

    class _NoConclusionLLM:
        def call_structured(self, **kwargs):
            raise AssertionError("query direct conclusion should render locally")

        def call_simple(self, *args, **kwargs):
            raise AssertionError("query direct conclusion should render locally")

    node.ai_call = _NoConclusionLLM()

    state = {
        "question": "查询 CPU",
        "layer": Layer.QUERY,
        "query_result": {
            "query_target": "查询 CPU",
            "collection_summary": "计划 1 项，实际采集 0 项",
            "columns": ["node", "cpu"],
            "rows": [{"node": "node1", "cpu": "未获取到"}],
            "missing": ["Prometheus 返回空"],
            "sources": ["up_query"],
        },
        "thinking_events": [],
    }

    result = node.execute(state)

    assert "**未获取到** `result`: Prometheus 返回空" in result["conclusion"]
    assert "| - | up_query |" in result["conclusion"]


def test_layer_execute_persists_query_result_only_in_query_direct_mode():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace()
    )
    node.workflow_config_override = {"query_mode": "direct"}
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._analyze_with_llm = lambda question: (
        {
            "layer": "QUERY",
            "layers": ["QUERY"],
            "layer_name": "查询请求",
            "confidence": 0.95,
            "reasoning": "QUERY direct",
            "key_entities": [],
            "possible_scenarios": [],
            "query_result": {
                "query_target": question,
                "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
                "columns": [{"key": "value", "label": "值"}],
                "rows": [{"value": "ok"}],
                "notes": [],
                "missing": [],
                "sources": [],
            },
        },
        [],
    )

    result = node.execute({"question": "查询 CPU"})

    assert result["layer"] == Layer.QUERY
    assert result["query_result"]["rows"] == [{"value": "ok"}]


def test_layer_execute_normalizes_legacy_query_result_columns_without_fallback():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace()
    )
    node.workflow_config_override = {"query_mode": "direct"}
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._analyze_with_llm = lambda question: (
        {
            "layer": "query",
            "layers": ["query"],
            "layer_name": "查询请求",
            "confidence": 0.99,
            "reasoning": "QUERY direct",
            "key_entities": [],
            "possible_scenarios": [],
            "query_result": {
                "query_target": question,
                "collection_summary": {"collected": "100%", "missing": "0%"},
                "columns": [
                    {"name": "节点", "type": "string"},
                    {"name": "CPU使用率(%)", "type": "float"},
                    {"name": "Memory使用率(%)", "type": "float"},
                ],
                "rows": [{"节点": "node1", "CPU使用率(%)": "12.1", "Memory使用率(%)": "55.2"}],
                "notes": "Prometheus 查询结果",
                "missing": [],
                "sources": {"tool": "execute_prometheus_instant_query", "query": "cpu/memory"},
            },
        },
        [],
    )

    result = node.execute({"question": "查询我集群cpu和memory的使用率"})

    assert result["layer"] == Layer.QUERY
    assert result["query_result"]["columns"][0]["key"] == "节点"
    assert result["query_result"]["columns"][1]["key"] == "CPU使用率(%)"
    assert result["query_result"]["rows"][0]["节点"] == "node1"
    assert not result.get("errors")


def test_layer_execute_query_result_validation_failure_stays_query_not_diagnosis():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace()
    )
    node.workflow_config_override = {"query_mode": "direct"}
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._analyze_with_llm = lambda question: (
        {
            "layer": "QUERY",
            "layers": ["QUERY"],
            "layer_name": "查询请求",
            "confidence": 0.95,
            "reasoning": "QUERY direct",
            "key_entities": [],
            "possible_scenarios": [],
            "query_result": {
                "query_target": question,
                "columns": [{"type": "float"}],
                "rows": [],
                "missing": [],
                "sources": [],
            },
        },
        [],
    )

    result = node.execute({"question": "查询 CPU"})

    assert result["layer"] == Layer.QUERY
    assert result["query_result"]["rows"] == []
    assert result["query_result"]["missing"][0]["field"] == "query_result"
    assert "结构化校验失败" in result["query_result"]["missing"][0]["reason"]
    assert not result.get("pod_abnormal_type")


def test_layer_execute_does_not_persist_query_result_for_non_query_mode():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace()
    )
    node.workflow_config_override = {"query_mode": "direct"}
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._analyze_with_llm = lambda question: (
        {
            "layer": "L2",
            "layers": ["L2"],
            "layer_name": "工作负载层",
            "confidence": 0.88,
            "reasoning": "diagnosis",
            "key_entities": [],
            "possible_scenarios": [],
            "query_result": {
                "query_target": question,
                "collection_summary": "should not leak",
            },
        },
        [],
    )

    result = node.execute({"question": "我的集群有什么问题"})

    assert result["layer"] == Layer.L2
    assert "query_result" not in result


def test_layer_direct_query_mode_uses_dedicated_prompt():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    assert node._get_layer_prompt() == get_workflow_prompt("layer_query_direct")


def test_layer_defaults_to_diagnosis_prompt_without_request_override():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            workflow_config={"query_mode": "direct"},
            get_prompt_language=lambda: "zh",
        )
    )

    assert node._get_layer_prompt() == get_workflow_prompt("layer")


def test_layer_query_direct_returns_failure_when_first_json_has_no_real_tool_results():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    calls = {"count": 0}

    first_result = {
        "layer": "QUERY",
        "layers": ["QUERY"],
        "layer_name": "查询请求",
        "confidence": 0.95,
        "reasoning": "用户明确查询 CPU 和内存使用率。",
        "key_entities": [],
        "possible_scenarios": [],
        "query_result": {
            "query_target": "每个节点的 CPU 和内存使用率",
            "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
            "columns": [
                {"key": "node", "label": "节点"},
                {"key": "cpu_usage_percent", "label": "CPU 使用率 (%)"},
                {"key": "memory_usage_percent", "label": "内存使用率 (%)"},
            ],
            "rows": [],
            "notes": [],
            "missing": [],
            "sources": [
                {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
                {"tool": "execute_prometheus_instant_query", "query": "mem_query"},
            ],
        },
    }

    def _fake_call_llm(question, prompt, **kwargs):
        calls["count"] += 1
        return SimpleNamespace(result=json.dumps(first_result, ensure_ascii=False)), []

    node._call_llm = _fake_call_llm

    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询每个节点的 CPU 和内存使用率")

    assert calls["count"] == 1
    assert result["layer"] == "QUERY"
    assert result["query_result"]["rows"] == []
    assert "未获得可渲染 JSON" in result["query_result"]["missing"][0]["reason"]
    assert thinking_events == []


def test_layer_query_direct_accepts_first_round_json_without_pydantic_extract():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "cpu_query"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 1},
            "result": '{"status":"success","data":{"result":[{"metric":{"node":"master"},"value":[1,"12.1"]}]}}',
        }
    ]
    first_result = {
        "layer": "QUERY",
        "layers": ["QUERY"],
        "layer_name": "查询请求",
        "confidence": 0.95,
        "reasoning": "已用 Prometheus 查询 CPU。",
        "key_entities": [],
        "possible_scenarios": [],
        "query_result": {
            "query_target": "查询 CPU",
            "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
            "columns": [{"key": "node", "label": "节点"}, {"key": "cpu", "label": "CPU"}],
            "rows": [{"node": "master", "cpu": "12.1"}],
            "missing": [],
            "sources": [{"tool": "execute_prometheus_instant_query", "query": "cpu_query"}],
        },
    }

    node._call_llm = lambda question, prompt, **kwargs: (
        SimpleNamespace(result=json.dumps(first_result, ensure_ascii=False)),
        events,
    )

    def _fail_extract(**kwargs):
        raise AssertionError("query direct should parse first-round JSON text without Pydantic layer_extract")

    node._extract_with_lite_llm = _fail_extract
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询 CPU")

    assert result["layer"] == "QUERY"
    assert result["query_result"]["rows"] == [{"node": "master", "cpu": "12.1"}]
    assert thinking_events == events


def test_layer_query_direct_returns_query_failure_when_prometheus_errors_are_not_usable():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    events = [
        {
            "type": "early_stop",
            "reason": "stop_checker",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "semantic_success": False,
            "result": '{"error": "400 Client Error: Bad Request for url: http://prometheus/api/v1/query?query=bad"}',
            "structured": {"status": "prometheus_error"},
        }
    ]
    extracted = {
        "layer": "L1",
        "layers": ["L1", "QUERY"],
        "layer_name": "Pod 生命周期层",
        "confidence": 0.5,
        "reasoning": "Prometheus 查询 400，被错误当成诊断问题。",
        "key_entities": [],
        "possible_scenarios": [],
    }

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result="Prometheus 400"), events)
    node._extract_with_lite_llm = lambda **kwargs: extracted
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询集群 CPU 使用率")

    assert result["layer"] == "QUERY"
    assert result["query_result"]["rows"] == []
    assert result["query_result"]["missing"][0]["field"] == "query_result"
    assert "未获得任何可用" in result["query_result"]["missing"][0]["reason"]
    assert thinking_events == events


def test_layer_query_direct_accepts_lowercase_query_layer_with_usable_result():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "result": '{"status":"success","data":{"result":[{"metric":{"instance":"10.2.0.48:9100"},"value":[1,"14.895"]}]}}',
        }
    ]
    extracted = {
        "layer": "query",
        "layers": ["query"],
        "layer_name": "查询请求",
        "confidence": 0.99,
        "reasoning": "已通过 Prometheus 获取节点 CPU 和内存使用率。",
        "key_entities": [],
        "possible_scenarios": [],
        "query_result": {
            "query_target": "集群节点级 CPU/内存使用率",
            "collection_summary": {"total_nodes": 1, "collected_nodes": 1, "missing_nodes": 0},
            "columns": [
                {"name": "节点", "type": "string"},
                {"name": "CPU 使用率 (%)", "type": "float"},
            ],
            "rows": [{"节点": "10.2.0.48", "CPU 使用率 (%)": 14.895}],
            "notes": ["数据来自 Prometheus node-exporter 指标"],
            "missing": [],
            "sources": [{"type": "prometheus_instant_query", "query": "cpu_query"}],
        },
    }

    node._call_llm = lambda question, prompt, **kwargs: (
        SimpleNamespace(result=json.dumps(extracted, ensure_ascii=False)),
        events,
    )
    node._extract_with_lite_llm = lambda **kwargs: extracted
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询集群 CPU 和内存使用率")

    assert result["layer"] == "QUERY"
    assert result["layers"] == ["QUERY"]
    assert result["query_result"]["rows"][0]["节点"] == "10.2.0.48"
    assert result["query_result"]["columns"][0]["key"] == "节点"
    assert result["query_result"]["sources"][0]["tool"] == "prometheus_instant_query"
    assert thinking_events == events


def test_layer_query_direct_does_not_retry_when_rows_exist_but_sources_are_missing():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    calls = {"count": 0}
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "cpu_query"},
            "result": '{"status":"success","data":{"result":[{"metric":{"instance":"10.2.0.48:9100"},"value":[1,"14.895"]}]}}',
        }
    ]
    extracted = {
        "layer": "QUERY",
        "layers": ["QUERY"],
        "layer_name": "查询请求",
        "confidence": 0.98,
        "reasoning": "已通过 Prometheus 获取节点级 CPU 使用率。",
        "key_entities": [],
        "possible_scenarios": [],
        "query_result": {
            "query_target": "集群节点级 CPU 使用率",
            "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
            "columns": [
                {"key": "node", "label": "节点"},
                {"key": "cpu_usage_percent", "label": "CPU 使用率 (%)"},
            ],
            "rows": [{"node": "10.2.0.48:9100", "cpu_usage_percent": 14.895}],
            "notes": [],
            "missing": [],
            "sources": [],
        },
    }

    def _fake_call_llm(question, prompt, **kwargs):
        calls["count"] += 1
        return SimpleNamespace(result="已查询到真实 Prometheus 数据"), events

    node._call_llm = _fake_call_llm
    node._extract_with_lite_llm = lambda **kwargs: extracted
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询集群 CPU 使用率")

    assert calls["count"] == 1
    assert result["query_result"]["rows"][0]["node"] == "10.2.0.48:9100"
    assert result["query_result"]["sources"][0] == {
        "tool": "execute_prometheus_instant_query",
        "query": "cpu_query",
    }
    assert thinking_events == events


def test_layer_query_direct_replaces_blank_sources_from_successful_tool_events():
    node = LayerClassifierNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}
    result = {
        "layer": "QUERY",
        "layers": ["QUERY"],
        "query_result": {
            "query_target": "集群节点级 CPU/内存使用率",
            "columns": [{"key": "node", "label": "节点"}],
            "rows": [{"node": "10.2.0.48:9100"}],
            "sources": [{"tool": "-", "query": "-"}],
        },
    }
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "cpu_query"},
            "structured": {"status": "prometheus_result", "result_count": 3},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "memory_query"},
            "structured": {"status": "prometheus_result", "result_count": 3},
        },
    ]

    enriched = node._normalize_query_result_sources(result, thinking_events)

    assert enriched["query_result"]["sources"] == [
        {"tool": "execute_prometheus_instant_query", "query": "cpu_query"},
        {"tool": "execute_prometheus_instant_query", "query": "memory_query"},
    ]


def test_layer_query_direct_passes_stop_checker_to_agent():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}
    captured = {}

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured["stop_checker"] = kwargs.get("stop_checker")
        return SimpleNamespace(result=""), []

    node._call_llm = _fake_call_llm
    node._extract_with_lite_llm = lambda **kwargs: {
        "layer": "QUERY",
        "layers": ["QUERY"],
        "layer_name": "查询请求",
        "confidence": 0.3,
        "reasoning": "未采集",
        "key_entities": [],
        "possible_scenarios": [],
        "query_result": {
            "query_target": "查询 CPU",
            "collection_summary": "计划 0 项，实际采集 0 项，未采集 1 项，完整度 0%",
            "columns": [],
            "rows": [],
            "missing": [{"field": "result", "reason": "未采集"}],
            "sources": [],
        },
    }
    node.ai_call = object()

    node._analyze_with_llm("查询 CPU")

    assert captured["stop_checker"] == node._should_stop_query_direct_early


def test_layer_query_direct_stop_checker_stops_on_prometheus_semantic_failure():
    node = LayerClassifierNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}

    assert node._should_stop_query_direct_early([
        {
            "type": "tool_start",
            "tool_name": "execute_prometheus_instant_query",
            "tool_call_id": "cpu-call",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_call_id": "cpu-call",
            "semantic_success": False,
            "structured": {"status": "prometheus_error"},
            "result": "execute_prometheus_instant_query 查询失败: 400 Client Error",
        }
    ]) is True


def test_layer_query_direct_stop_checker_does_not_stop_without_tool_start_ids():
    node = LayerClassifierNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}

    assert node._should_stop_query_direct_early([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 3},
            "result": '{"status":"success","data":{"result":[]}}',
        }
    ]) is False


def test_layer_query_direct_stop_checker_waits_for_parallel_prometheus_results():
    node = LayerClassifierNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}

    events = [
        {
            "type": "tool_start",
            "tool_name": "execute_prometheus_instant_query",
            "tool_call_id": "cpu-call",
        },
        {
            "type": "tool_start",
            "tool_name": "execute_prometheus_instant_query",
            "tool_call_id": "memory-call",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_call_id": "cpu-call",
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 3},
            "result": '{"status":"success","data":{"result":[]}}',
        },
    ]

    assert node._should_stop_query_direct_early(events) is False

    events.append({
        "type": "tool_result",
        "status": "success",
        "tool_name": "execute_prometheus_instant_query",
        "tool_call_id": "memory-call",
        "semantic_success": True,
        "structured": {"status": "prometheus_result", "result_count": 3},
        "result": '{"status":"success","data":{"result":[]}}',
    })

    assert node._should_stop_query_direct_early(events) is True


def test_layer_query_direct_builds_query_result_from_successful_prometheus_tool_events():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "fetch_runbook",
            "result": "# PromQL reference",
            "structured": {"status": "runbook_loaded"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 3},
            "result": json.dumps({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"instance": "10.2.0.49:9100"}, "value": [1778320592.531, "1.8052083333330082"]},
                        {"metric": {"instance": "10.2.0.50:9100"}, "value": [1778320592.531, "8.194444444440396"]},
                        {"metric": {"instance": "10.2.0.48:9100"}, "value": [1778320592.531, "15.534945116021026"]},
                    ],
                },
            }),
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 3},
            "result": json.dumps({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"instance": "10.2.0.49:9100"}, "value": [1778320592.631, "8.370335231905957"]},
                        {"metric": {"instance": "10.2.0.50:9100"}, "value": [1778320592.631, "14.514200644664953"]},
                        {"metric": {"instance": "10.2.0.48:9100"}, "value": [1778320592.631, "40.29723968764428"]},
                    ],
                },
            }),
        },
    ]
    extracted = {
        "layer": "QUERY",
        "layers": ["QUERY"],
        "layer_name": "查询请求",
        "confidence": 0.5,
        "reasoning": "已通过工具查询到节点 CPU 和内存，但结构化提取器没有填充 query_result。",
        "key_entities": [],
        "possible_scenarios": [],
    }

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result="已查询到 3 个节点 CPU 和内存"), events)
    node._extract_with_lite_llm = lambda **kwargs: extracted
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("集群 CPU和内存memory 使用率是多少，具体到每个node级别")

    assert result["layer"] == "QUERY"
    assert result["query_result"]["collection_summary"] == "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%"
    assert result["query_result"]["columns"] == [
        {"key": "node", "label": "节点"},
        {"key": "cpu_usage_percent", "label": "CPU 使用率 (%)"},
        {"key": "memory_usage_percent", "label": "内存使用率 (%)"},
    ]
    assert result["query_result"]["rows"] == [
        {"node": "10.2.0.49:9100", "cpu_usage_percent": 1.81, "memory_usage_percent": 8.37},
        {"node": "10.2.0.50:9100", "cpu_usage_percent": 8.19, "memory_usage_percent": 14.51},
        {"node": "10.2.0.48:9100", "cpu_usage_percent": 15.53, "memory_usage_percent": 40.3},
    ]
    assert len(result["query_result"]["sources"]) == 2


def test_layer_query_direct_ignores_prometheus_metadata_as_metric_column():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 1},
            "result": json.dumps({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"instance": "10.2.0.49:9100"}, "value": [1778320592.531, "4.35"]},
                    ],
                },
            }),
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "node_uname_info"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 1},
            "result": json.dumps({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"instance": "10.2.0.49:9100", "nodename": "node1"}, "value": [1778320592.531, "1"]},
                    ],
                },
            }),
        },
    ]

    result = node._query_result_from_prometheus_tool_events("查询 CPU", events)

    assert result["columns"] == [
        {"key": "node", "label": "节点"},
        {"key": "cpu_usage_percent", "label": "CPU 使用率 (%)"},
    ]
    assert result["rows"] == [{"node": "10.2.0.49:9100", "cpu_usage_percent": 4.35}]
    assert result["collection_summary"] == "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%"


def test_layer_query_direct_does_not_treat_empty_prometheus_vectors_as_collected_rows():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}

    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": 'sum(node_filesystem_used_bytes{fstype="ext4"}) by (device)'},
            "semantic_success": False,
            "structured": {"status": "prometheus_empty", "result_count": 0},
            "result": '{"status":"success","data":{"resultType":"vector","result":[]}}',
        },
    ]

    result = node._query_result_from_prometheus_tool_events(
        "集群 磁盘存储使用率是多少",
        events,
    )

    assert result is None


def test_layer_query_direct_skips_extract_when_prometheus_tool_result_is_usable():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}
    events = [
        {
            "type": "early_stop",
            "reason": "stop_checker",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "up by instance"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 1},
            "result": json.dumps({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"instance": "10.2.0.49:9100"}, "value": [1778320592.531, "1"]},
                    ],
                },
            }),
        },
    ]

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result=""), events)

    def _fail_extract(**kwargs):
        raise AssertionError("layer_extract should not run when Prometheus tool_result is usable")

    node._extract_with_lite_llm = _fail_extract
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询 up")

    assert result["layer"] == "QUERY"
    assert result["query_result"]["rows"] == [{"node": "10.2.0.49:9100", "metric_1": 1.0}]
    assert thinking_events == events


def test_layer_query_direct_skips_extract_from_prometheus_events_without_early_stop():
    node = LayerClassifierNode(
        holmes_service=SimpleNamespace(
            get_prompt_language=lambda: "zh",
        )
    )
    node.workflow_config_override = {"query_mode": "direct"}
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_prometheus_instant_query",
            "tool_args": {"query": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100"},
            "semantic_success": True,
            "structured": {"status": "prometheus_result", "result_count": 1},
            "result": json.dumps({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"instance": "10.2.0.49:9100"}, "value": [1778320592.531, "4.35"]},
                    ],
                },
            }),
        },
    ]

    node._call_llm = lambda question, prompt, **kwargs: (SimpleNamespace(result=""), events)

    def _fail_extract(**kwargs):
        raise AssertionError("layer_extract should not run when query_result can be built from Prometheus events")

    node._extract_with_lite_llm = _fail_extract
    node.ai_call = object()

    result, thinking_events = node._analyze_with_llm("查询 CPU")

    assert result["layer"] == "QUERY"
    assert result["query_result"]["rows"] == [{"node": "10.2.0.49:9100", "cpu_usage_percent": 4.35}]
    assert thinking_events == events


def test_executor_does_not_propagate_ambient_query_mode_to_nodes(monkeypatch):
    captured = {}

    class _DummyWorkflow:
        def stream(self, initial_state):
            return iter([])

    def _fake_build_workflow(holmes_service, metrics, runbook_catalog, node_config=None, query_mode="full"):
        captured["query_mode"] = query_mode
        node = SimpleNamespace(
            node_id="layer",
            set_event_queue=lambda q: None,
        )
        captured["node"] = node
        return _DummyWorkflow(), [node]

    monkeypatch.setattr("app.core.workflow.executor.build_diagnosis_workflow", _fake_build_workflow)

    executor = WorkflowExecutor(
        holmes_service=SimpleNamespace(
            workflow_config={"query_mode": "direct", "nodes": {"layer": True, "conclusion": True}},
            merged_catalog=None,
        )
    )

    list(executor.execute_stream("我的集群有什么问题？"))

    assert captured["query_mode"] == "full"
    assert getattr(captured["node"], "workflow_config_override", {}).get("query_mode") is None
