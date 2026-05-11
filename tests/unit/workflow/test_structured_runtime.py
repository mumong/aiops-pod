from types import SimpleNamespace
from unittest.mock import MagicMock

from pydantic import BaseModel

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.structured_runtime import StructuredAgentRuntime


class DemoOutput(BaseModel):
    value: str


def test_extract_structured_response_accepts_pydantic_instance():
    response = SimpleNamespace(structured_response=DemoOutput(value="ok"))

    parsed = StructuredAgentRuntime.extract_structured_response(response, DemoOutput)

    assert parsed == DemoOutput(value="ok")


def test_extract_structured_response_accepts_dict():
    response = SimpleNamespace(structured_response={"value": "ok"})

    parsed = StructuredAgentRuntime.extract_structured_response(response, DemoOutput)

    assert parsed == DemoOutput(value="ok")


def test_extract_structured_response_returns_none_when_missing():
    response = SimpleNamespace(result="text only")

    parsed = StructuredAgentRuntime.extract_structured_response(response, DemoOutput)

    assert parsed is None


def test_layer_output_normalizes_query_result_alias_to_query():
    normalized = LayerClassifierNode._normalize_layer_output_dict({
        "layer": "query_result",
        "derived_layer": "query_result",
        "layers": ["query_result"],
        "confidence": 0.9,
        "reasoning": "查询结果已生成",
    })

    assert normalized["layer"] == "QUERY"
    assert normalized["derived_layer"] == "QUERY"
    assert normalized["layers"] == ["QUERY"]


def test_workflow_node_structured_agent_helper_with_tools_uses_agent_response_schema():
    class _Node(WorkflowNode):
        node_id = "demo"
        node_name = "demo"

        def execute(self, state):
            return {}

    node = _Node()
    events = [{"type": "structured_response"}]
    captured = {}

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(structured_response=DemoOutput(value="ok")), events

    node._call_llm = _fake_call_llm

    parsed, response, returned_events = node._call_structured_agent(
        question="q",
        system_prompt="sys",
        schema=DemoOutput,
        use_tools=True,
    )

    assert parsed == DemoOutput(value="ok")
    assert response.structured_response == DemoOutput(value="ok")
    assert returned_events == events
    assert captured["response_schema"] is DemoOutput
    assert captured["force_no_tools"] is False


def test_workflow_node_structured_agent_helper_uses_call_structured_without_tools():
    class _Node(WorkflowNode):
        node_id = "demo"
        node_name = "demo"

        def execute(self, state):
            return {}

    node = _Node()
    captured = {}

    class _AICall:
        def call_structured(self, **kwargs):
            captured.update(kwargs)
            return DemoOutput(value="ok"), '{"value":"ok"}'

    node.ai_call = _AICall()
    node.current_run_id = "run-1"

    parsed, response, returned_events = node._call_structured_agent(
        question="q",
        system_prompt="sys",
        schema=DemoOutput,
        use_tools=False,
        max_tokens=123,
    )

    assert parsed == DemoOutput(value="ok")
    assert response.result == '{"value":"ok"}'
    assert response.structured_response == DemoOutput(value="ok")
    assert returned_events == [{"type": "structured_response", "node": "demo", "schema": "DemoOutput"}]
    assert captured["schema"] is DemoOutput
    assert captured["node_id"] == "demo"
    assert captured["run_id"] == "run-1"
    assert captured["max_tokens"] == 123


def test_call_llm_force_no_tools_passes_empty_tool_list_to_aicall():
    class _Node(WorkflowNode):
        node_id = "demo"
        node_name = "demo"

        def execute(self, state):
            return {}

    node = _Node()
    node.tools = [MagicMock(name="real_tool")]
    node.current_run_id = "run-1"
    captured = {}

    class _AICall:
        model_str = "test-model"
        model = "test-model"
        api_base = ""
        api_key = ""

        def call(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                result="ok",
                tool_call_count=0,
                duration_ms=1,
                iterations=1,
            ), []

    node.ai_call = _AICall()

    node._call_llm("q", "sys", force_no_tools=True)

    assert captured["tools"] == []


def test_call_llm_retries_without_response_schema_on_gateway_structured_failure():
    class _Node(WorkflowNode):
        node_id = "demo"
        node_name = "demo"

        def execute(self, state):
            return {}

    node = _Node()
    node.current_run_id = "run-1"
    node.workflow_config_override = {
        "structured_runtime": {"enabled": True, "fallback_enabled": True},
        "max_steps": {"demo": 15},
    }
    calls = []

    class _AICall:
        model_str = "openai/Qwen3-32B-AWQ"
        model = "openai/Qwen3-32B-AWQ"
        api_base = "http://llm/v1"
        api_key = "sk-test"

        def call(self, **kwargs):
            calls.append(kwargs)
            if kwargs.get("response_schema") is DemoOutput:
                return SimpleNamespace(
                    result="Agent 执行异常: Error code: 500 - Expecting ':' delimiter",
                    tool_call_count=0,
                    duration_ms=1,
                    iterations=1,
                ), []
            return SimpleNamespace(
                result="已完成真实工具采集",
                tool_call_count=1,
                duration_ms=1,
                iterations=1,
            ), [
                {
                    "type": "tool_result",
                    "tool_name": "kubectl_get_by_kind_in_cluster",
                    "status": "success",
                    "result": "pod list",
                }
            ]

    node.ai_call = _AICall()

    response, events = node._call_llm("q", "sys", response_schema=DemoOutput)

    assert response.result == "已完成真实工具采集"
    assert events[0]["type"] == "tool_result"
    assert calls[0]["response_schema"] is DemoOutput
    assert "response_schema" not in calls[1]
