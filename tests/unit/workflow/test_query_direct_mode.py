import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.prompts import get_workflow_prompt
from app.core.skills.models import Layer
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.graph import _make_layer_router
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode


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

    class _FailingAICall:
        def call_simple(self, *args, **kwargs):
            raise AssertionError("QUERY direct mode should not call conclusion LLM")

    node.ai_call = _FailingAICall()

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
