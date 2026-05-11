import sys
import types
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
import queue

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from app.core.aicall.client import AICall
from app.core.workflow.schemas import EvidencePlanOutput


def _install_fake_langfuse(monkeypatch):
    calls = {"sessions": [], "spans": []}

    @contextmanager
    def _propagate_attributes(**kwargs):
        calls["sessions"].append(kwargs.get("session_id"))
        yield

    class _FakeClient:
        @contextmanager
        def start_as_current_observation(self, **kwargs):
            calls["spans"].append(kwargs)
            yield

    def _get_client():
        return _FakeClient()

    fake_langfuse = types.ModuleType("langfuse")
    fake_langfuse.propagate_attributes = _propagate_attributes
    fake_langfuse.get_client = _get_client
    fake_langfuse_langchain = types.ModuleType("langfuse.langchain")

    class _CallbackHandler:
        pass

    fake_langfuse_langchain.CallbackHandler = _CallbackHandler

    monkeypatch.setitem(sys.modules, "langfuse", fake_langfuse)
    monkeypatch.setitem(sys.modules, "langfuse.langchain", fake_langfuse_langchain)
    return calls


def test_call_simple_creates_fresh_chat_model_per_invocation():
    model_instances = []

    def _new_model(**kwargs):
        model = MagicMock()
        model.invoke.return_value = MagicMock(content=f"resp-{len(model_instances)}")
        model_instances.append(model)
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")

        first = ai.call_simple("sys", "q1")
        second = ai.call_simple("sys", "q2")

    assert first == "resp-0"
    assert second == "resp-1"
    assert len(model_instances) == 2
    assert model_instances
    assert model_instances[0] is not model_instances[1]
    model_instances[0].invoke.assert_called_once()
    model_instances[1].invoke.assert_called_once()


def test_call_simple_propagates_langfuse_session_id(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    langfuse_calls = _install_fake_langfuse(monkeypatch)
    invoke_configs = []
    model_instances = []
    created_kwargs = []

    def _new_model(**kwargs):
        created_kwargs.append(kwargs)
        model = MagicMock()

        def _invoke(messages, config=None):
            invoke_configs.append(config)
            return MagicMock(content="ok")

        model.bind.return_value = model
        model.invoke.side_effect = _invoke
        model_instances.append(model)
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result = ai.call_simple("sys", "q", run_id="run-session-1", node_id="evidence")

    assert result == "ok"
    assert langfuse_calls["sessions"] == ["run-session-1"]
    assert langfuse_calls["spans"][0]["name"] == "workflow-evidence"
    assert langfuse_calls["spans"][0]["metadata"]["session_id"] == "run-session-1"
    assert langfuse_calls["spans"][0]["metadata"]["node_id"] == "evidence"
    assert langfuse_calls["spans"][0]["metadata"]["trace_id"] == "run-session-1:evidence"
    assert invoke_configs[0]["metadata"]["session_id"] == "run-session-1"
    assert invoke_configs[0]["metadata"]["node_id"] == "evidence"
    assert invoke_configs[0]["metadata"]["trace_id"] == "run-session-1:evidence"
    assert len(invoke_configs[0]["callbacks"]) == 1
    assert "session:run-session-1" in invoke_configs[0]["tags"]
    assert created_kwargs[0]["extra_body"]["metadata"]["session_id"] == "run-session-1"
    assert created_kwargs[0]["extra_body"]["metadata"]["node_id"] == "evidence"
    assert created_kwargs[0]["extra_body"]["metadata"]["trace_id"] == "run-session-1:evidence"
    assert created_kwargs[0]["extra_body"]["trace_id"] == "run-session-1:evidence"
    assert created_kwargs[0]["extra_body"]["generation_name"] == "workflow-evidence"
    assert created_kwargs[0]["extra_body"]["user"] == "run-session-1"
    bound_kwargs = model_instances[0].bind.call_args.kwargs
    assert bound_kwargs["extra_body"]["metadata"]["session_id"] == "run-session-1"
    assert bound_kwargs["extra_body"]["metadata"]["langfuse_session_id"] == "run-session-1"
    assert bound_kwargs["extra_body"]["trace_id"] == "run-session-1:evidence"
    assert bound_kwargs["extra_body"]["generation_name"] == "workflow-evidence"
    assert model_instances[0].bind.call_args.kwargs["extra_body"]["user"] == "run-session-1"
    assert bound_kwargs["extra_body"]["metadata"]["node_id"] == "evidence"


def test_chat_model_extra_body_merges_with_session_metadata(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    _install_fake_langfuse(monkeypatch)
    created_kwargs = []

    def _new_model(**kwargs):
        created_kwargs.append(kwargs)
        model = MagicMock()
        model.bind.return_value = model
        model.invoke.return_value = MagicMock(content="ok")
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(
            model="openai/Qwen3-32B-AWQ",
            api_key="sk-test",
            chat_model_extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
                "metadata": {"model_profile": "qwen-no-think"},
            },
        )
        result = ai.call_simple("sys", "q", run_id="run-session-1", node_id="layer")

    assert result == "ok"
    extra_body = created_kwargs[0]["extra_body"]
    assert extra_body["chat_template_kwargs"] == {"enable_thinking": False}
    assert extra_body["metadata"]["model_profile"] == "qwen-no-think"
    assert extra_body["metadata"]["session_id"] == "run-session-1"
    assert extra_body["metadata"]["node_id"] == "layer"
    assert extra_body["trace_id"] == "run-session-1:layer"


def test_call_with_tools_creates_fresh_chat_model_per_invocation():
    model_instances = []
    create_agent_calls = []

    def _new_model(**kwargs):
        model = MagicMock()
        model_instances.append(model)
        return model

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            if False:
                yield None

    def _capture_agent(model=None, tools=None, system_prompt=None):
        create_agent_calls.append(model)
        return _Agent()

    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model), \
         patch("langchain.agents.create_agent", side_effect=_capture_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call("sys", "q1", tools=[tool])
        ai.call("sys", "q2", tools=[tool])

    assert len(model_instances) == 2
    assert len(create_agent_calls) == 2
    assert create_agent_calls[0] is model_instances[0]
    assert create_agent_calls[1] is model_instances[1]
    assert create_agent_calls[0] is not create_agent_calls[1]


def test_call_with_tools_can_return_structured_response_without_extra_extract_llm():
    create_agent_kwargs = []

    class _LayerLikeOutput(BaseModel):
        layer: str
        confidence: float
        reasoning: str

    parsed = _LayerLikeOutput(layer="L3", confidence=0.91, reasoning="工具结果已定位")

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield (
                "updates",
                {
                    "model": {
                        "structured_response": parsed,
                        "messages": [
                            AIMessage(
                                content="",
                                tool_calls=[
                                    {
                                        "name": "_LayerLikeOutput",
                                        "args": parsed.model_dump(),
                                        "id": "structured-1",
                                    }
                                ],
                            )
                        ],
                    }
                },
            )

    def _create_agent(**kwargs):
        create_agent_kwargs.append(kwargs)
        return _Agent()

    tool = MagicMock()
    tool.name = "kubectl_get_by_kind_in_cluster"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", return_value=MagicMock()), \
         patch("langchain.agents.create_agent", side_effect=_create_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, events = ai.call("sys", "q", tools=[tool], response_schema=_LayerLikeOutput)

    response_format = create_agent_kwargs[0]["response_format"]
    assert response_format.schema is _LayerLikeOutput
    assert result.structured_response == parsed
    assert result.result == parsed.model_dump_json()
    assert result.tool_call_count == 0
    assert not [ev for ev in events if ev.get("type") == "tool_start"]


def test_call_without_real_tools_can_use_agent_structured_response():
    create_agent_kwargs = []

    class _SummaryOutput(BaseModel):
        summary: str

    parsed = _SummaryOutput(summary="ok")

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"model": {"structured_response": parsed, "messages": []}})

    def _create_agent(**kwargs):
        create_agent_kwargs.append(kwargs)
        return _Agent()

    with patch("app.core.aicall.client.ChatOpenAI", return_value=MagicMock()), \
         patch("langchain.agents.create_agent", side_effect=_create_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, events = ai.call("sys", "q", tools=[], response_schema=_SummaryOutput)

    assert create_agent_kwargs[0]["tools"] == []
    assert create_agent_kwargs[0]["response_format"].schema is _SummaryOutput
    assert result.structured_response == parsed
    assert result.result == parsed.model_dump_json()
    assert events[0]["type"] == "structured_response"


def test_call_with_tools_propagates_langfuse_session_id(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    langfuse_calls = _install_fake_langfuse(monkeypatch)
    astream_configs = []
    created_kwargs = []

    def _new_model(**kwargs):
        created_kwargs.append(kwargs)
        return MagicMock()

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, input_messages, config=None, **kwargs):
            astream_configs.append(config)
            if False:
                yield None

    def _create_agent(**kwargs):
        return _Agent()

    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model), \
         patch("langchain.agents.create_agent", side_effect=_create_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call("sys", "q", tools=[tool], run_id="run-session-2", node_id="layer", max_steps=3)

    assert langfuse_calls["sessions"] == ["run-session-2"]
    assert langfuse_calls["spans"][0]["name"] == "workflow-layer"
    assert langfuse_calls["spans"][0]["metadata"]["session_id"] == "run-session-2"
    assert langfuse_calls["spans"][0]["metadata"]["node_id"] == "layer"
    assert langfuse_calls["spans"][0]["metadata"]["trace_id"] == "run-session-2:layer"
    assert astream_configs[0]["recursion_limit"] == 3
    assert astream_configs[0]["metadata"]["session_id"] == "run-session-2"
    assert astream_configs[0]["metadata"]["node_id"] == "layer"
    assert astream_configs[0]["metadata"]["trace_id"] == "run-session-2:layer"
    assert len(astream_configs[0]["callbacks"]) == 1
    assert "session:run-session-2" in astream_configs[0]["tags"]
    assert "node:layer" in astream_configs[0]["tags"]
    assert created_kwargs[0]["extra_body"]["metadata"]["session_id"] == "run-session-2"
    assert created_kwargs[0]["extra_body"]["metadata"]["node_id"] == "layer"
    assert created_kwargs[0]["extra_body"]["metadata"]["trace_id"] == "run-session-2:layer"
    assert created_kwargs[0]["extra_body"]["trace_id"] == "run-session-2:layer"
    assert created_kwargs[0]["extra_body"]["generation_name"] == "workflow-layer"
    assert created_kwargs[0]["extra_body"]["user"] == "run-session-2"


def test_langfuse_session_scope_preserves_original_exception(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    _install_fake_langfuse(monkeypatch)
    ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")

    with pytest.raises(ValueError, match="original failure"):
        with ai._langfuse_session_scope("run-session-error", "layer"):
            raise ValueError("original failure")


def test_langfuse_sdk_is_disabled_without_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    langfuse_calls = _install_fake_langfuse(monkeypatch)
    invoke_configs = []

    def _new_model(**kwargs):
        model = MagicMock()

        def _invoke(messages, config=None):
            invoke_configs.append(config)
            return MagicMock(content="ok")

        model.bind.return_value = model
        model.invoke.side_effect = _invoke
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call_simple("sys", "q", run_id="run-session-no-sdk", node_id="layer")

    assert langfuse_calls["sessions"] == []
    assert langfuse_calls["spans"] == []
    assert "callbacks" not in invoke_configs[0]
    assert invoke_configs[0]["metadata"]["session_id"] == "run-session-no-sdk"
    assert invoke_configs[0]["metadata"]["trace_id"] == "run-session-no-sdk:layer"


def test_langfuse_trace_id_is_unique_per_workflow_node():
    assert AICall._session_metadata("run-a", "layer")["session_id"] == "run-a"
    assert AICall._session_metadata("run-a", "evidence")["session_id"] == "run-a"
    assert AICall._session_metadata("run-a", "layer")["trace_id"] == "run-a:layer"
    assert AICall._session_metadata("run-a", "evidence")["trace_id"] == "run-a:evidence"


def test_create_chat_model_can_disable_streaming_for_structured_calls():
    captured = {}

    def _new_model(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="openai/Qwen3-32B-AWQ", api_key="sk-test")
        ai._create_chat_model(node_id="layer_extract", disable_streaming=True)

    assert captured["streaming"] is False
    assert captured["disable_streaming"] is True


def test_call_simple_json_parses_fenced_json_output():
    def _new_model(**kwargs):
        model = MagicMock()
        model.invoke.return_value = MagicMock(
            content='```json\n{"layer":"QUERY","confidence":0.9,"reasoning":"ok"}\n```'
        )
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        parsed, raw = ai.call_simple_json("sys", "q")

    assert parsed == {"layer": "QUERY", "confidence": 0.9, "reasoning": "ok"}
    assert "```json" in raw


def test_call_structured_disables_text_fallback_by_default(monkeypatch):
    ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")

    def _fake_simple(system_prompt, question, **kwargs):
        return """```json
{
  "layer": "L3",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 事件",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl get events -n aaa",
      "purpose": "确认镜像拉取失败原因"
    }
  ],
  "collection_strategy": "先确认当前异常 Pod。"
}
```"""

    monkeypatch.setattr(ai, "call_simple", _fake_simple)

    parsed, raw = ai.call_structured("sys", "q", EvidencePlanOutput)

    assert parsed is None
    assert raw == ""


def test_call_structured_legacy_text_fallback_requires_explicit_opt_in(monkeypatch):
    ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")

    def _fake_simple(system_prompt, question, **kwargs):
        return """```json
{
  "layer": "L3",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 事件",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl get events -n aaa",
      "purpose": "确认镜像拉取失败原因"
    }
  ],
  "collection_strategy": "先确认当前异常 Pod。"
}
```"""

    monkeypatch.setattr(ai, "call_simple", _fake_simple)

    parsed, raw = ai.call_structured(
        "sys",
        "q",
        EvidencePlanOutput,
        allow_text_fallback=True,
    )

    assert isinstance(parsed, EvidencePlanOutput)
    assert parsed.evidence_plan[0].id == "e1"
    assert "```json" in raw


def test_call_structured_prefers_native_pydantic_output(monkeypatch):
    ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
    created_models = []

    class _StructuredModel:
        def invoke(self, messages, config=None):
            return EvidencePlanOutput(
                layer="L3",
                evidence_plan=[
                    {
                        "id": "e1",
                        "description": "获取 Pod 事件",
                        "level": "critical",
                        "tool": "kubectl_events",
                        "command": "kubectl get events -n aaa",
                        "purpose": "确认镜像拉取失败原因",
                    }
                ],
                collection_strategy="先确认当前异常 Pod。",
            )

    class _Model:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            created_models.append(self)

        def bind(self, **kwargs):
            return self

        def with_structured_output(self, schema, **kwargs):
            assert schema is EvidencePlanOutput
            assert kwargs.get("method") == "function_calling"
            return _StructuredModel()

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model(**kwargs))

    def fail_simple(*args, **kwargs):
        raise AssertionError("native structured output should avoid JSON prompt fallback")

    monkeypatch.setattr(ai, "call_simple", fail_simple)

    parsed, raw = ai.call_structured("sys", "q", EvidencePlanOutput)

    assert isinstance(parsed, EvidencePlanOutput)
    assert parsed.evidence_plan[0].tool == "kubectl_events"
    assert "kubectl_events" in raw
    assert created_models
    assert created_models[0].kwargs["disable_streaming"] is True


def test_call_with_expect_json_interrupts_on_valid_json_message():
    model_instances = []

    def _new_model(**kwargs):
        model = MagicMock()
        model_instances.append(model)
        return model

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield (
                "updates",
                {
                    "model": {
                        "messages": [
                            AIMessage(content='{"layer":"QUERY","confidence":0.9,"reasoning":"ok"}')
                        ]
                    }
                },
            )

    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model), \
         patch("langchain.agents.create_agent", return_value=_Agent()), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        result, _ = ai.call(
            "sys",
            "q1",
            tools=[tool],
            expect_json=True,
            json_validator=lambda data: data.get("layer") == "QUERY",
        )

    assert result.result == '{"layer": "QUERY", "confidence": 0.9, "reasoning": "ok"}'


def test_chat_model_requests_stream_usage_for_exact_context_usage():
    created_kwargs = []

    def _new_model(**kwargs):
        created_kwargs.append(kwargs)
        model = MagicMock()
        model.invoke.return_value = MagicMock(content="ok")
        return model

    with patch("app.core.aicall.client.ChatOpenAI", side_effect=_new_model):
        ai = AICall(model="openai/Qwen3-32B-AWQ", api_key="sk-test", api_base="http://llm/v1")
        ai.call_simple("sys", "q")

    assert created_kwargs[0]["streaming"] is True
    assert created_kwargs[0]["stream_usage"] is True


def test_call_surfaces_reasoning_content_in_stream_events():
    event_queue = queue.Queue()

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield (
                "messages",
                (
                    AIMessage(content="", additional_kwargs={"reasoning_content": "<think>内部推理</think>"}),
                    {"langgraph_node": "model"},
                ),
            )
            yield (
                "updates",
                {
                    "model": {
                        "messages": [
                            AIMessage(content="最终答案", additional_kwargs={"reasoning_content": "<think>内部推理</think>"})
                        ]
                    }
                },
            )

    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("app.core.aicall.client.ChatOpenAI", return_value=MagicMock()), \
         patch("langchain.agents.create_agent", return_value=_Agent()), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        ai = AICall(model="deepseek/deepseek-chat", api_key="sk-test")
        ai.call("sys", "q", tools=[tool], stream_queue=event_queue, node_id="layer", max_steps=3)

    seen_ai_token = False
    seen_ai_message = False
    while not event_queue.empty():
        _, evt = event_queue.get_nowait()
        if evt.get("type") == "ai_token" and "内部推理" in (evt.get("content") or ""):
            seen_ai_token = True
        if evt.get("type") == "ai_message" and "内部推理" in (evt.get("full_content") or ""):
            seen_ai_message = True

    assert seen_ai_token is True
    assert seen_ai_message is True


def test_extract_usage_metadata_supports_usage_metadata_and_token_usage():
    msg = MagicMock()
    msg.usage_metadata = {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}
    assert AICall._extract_usage_metadata(msg) == {
        "input_tokens": 10,
        "output_tokens": 2,
        "total_tokens": 12,
    }

    msg2 = MagicMock()
    msg2.usage_metadata = None
    msg2.response_metadata = {
        "token_usage": {
            "prompt_tokens": 11,
            "completion_tokens": 3,
            "total_tokens": 14,
        }
    }
    assert AICall._extract_usage_metadata(msg2) == {
        "input_tokens": 11,
        "output_tokens": 3,
        "total_tokens": 14,
    }
