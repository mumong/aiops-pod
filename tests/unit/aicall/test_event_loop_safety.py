import sys
import types
import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import queue

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from openai import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
    UnprocessableEntityError,
)
from pydantic import BaseModel

from app.core.aicall.client import AICall
from app.core.context.budget import count_tokens, serialize_tool_schema
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


def _patch_length_token_counter(monkeypatch, *, accuracy):
    def _count(value, model=""):
        if value is None:
            value = ""
        elif not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return {
            "tokens": len(value),
            "source": f"test:length-{accuracy}",
            "accuracy": accuracy,
        }

    monkeypatch.setattr("app.core.context.budget.count_tokens", _count)
    monkeypatch.setattr("app.core.aicall.client.count_tokens", _count)
    return _count


class _BoundaryAgentRequest(SimpleNamespace):
    def override(self, **kwargs):
        values = vars(self).copy()
        values.update(kwargs)
        return type(self)(**values)


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


def test_call_simple_replays_stream_eof_once_without_streaming(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/gpt-5.6-sol", api_key="sk-test")
    created = []
    invocations = []

    class _Model:
        def __init__(self, result=None, error=None):
            self.result = result
            self.error = error
            self.bind_kwargs = {}

        def bind(self, **kwargs):
            self.bind_kwargs = kwargs
            return self

        def invoke(self, messages, config=None):
            invocations.append({
                "messages": messages,
                "config": config,
                "bind_kwargs": dict(self.bind_kwargs),
            })
            if self.error is not None:
                raise self.error
            return self.result

    models = [
        _Model(
            error=APIError(
                "unexpected EOF",
                request=httpx.Request("POST", "http://llm.example/v1/chat/completions"),
                body=None,
            )
        ),
        _Model(result=AIMessage(content="recovered report")),
    ]

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return models[len(created) - 1]

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    result = ai.call_simple(
        "system",
        "question",
        node_id="conclusion",
        max_tokens=8192,
    )

    assert result == "recovered report"
    assert len(created) == 2
    assert created[0].get("disable_streaming", False) is False
    assert created[1]["disable_streaming"] is True
    assert len(invocations) == 2
    assert [message.content for message in invocations[0]["messages"]] == [
        message.content for message in invocations[1]["messages"]
    ]
    assert invocations[0]["bind_kwargs"] == invocations[1]["bind_kwargs"] == {
        "max_tokens": 8192,
    }
    assert invocations[0]["config"] == invocations[1]["config"]


@pytest.mark.parametrize(
    "message",
    [
        "unexpected EOF",
        "empty_stream",
        "closed before first payload",
    ],
)
def test_call_simple_replays_measured_stream_interruptions_once_for_api_subclasses(
    monkeypatch,
    message,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/gpt-5.6-sol", api_key="sk-test")
    created = []
    request = httpx.Request(
        "POST",
        "http://llm.example/v1/chat/completions",
    )
    interruption = InternalServerError(
        message,
        response=httpx.Response(500, request=request),
        body=None,
    )

    class _Model:
        def __init__(self, *, error=None, content=""):
            self.error = error
            self.content = content

        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            if self.error is not None:
                raise self.error
            return AIMessage(content=self.content)

    models = [
        _Model(error=interruption),
        _Model(content="recovered"),
    ]

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return models[len(created) - 1]

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    assert ai.call_simple("system", "question") == "recovered"
    assert len(created) == 2
    assert created[0].get("disable_streaming", False) is False
    assert created[1]["disable_streaming"] is True


class _UnexpectedEOFTimeout(APITimeoutError):
    def __str__(self):
        return "unexpected EOF"


def test_call_simple_retries_api_connection_eof_once_without_streaming(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created = []
    interruption = APIConnectionError(
        message="unexpected EOF",
        request=httpx.Request(
            "POST",
            "http://llm.example/v1/chat/completions",
        ),
    )

    class _Model:
        def __init__(self, *, error=None, content=""):
            self.error = error
            self.content = content

        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            if self.error is not None:
                raise self.error
            return AIMessage(content=self.content)

    models = [
        _Model(error=interruption),
        _Model(content="recovered"),
    ]

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return models[len(created) - 1]

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    assert ai.call_simple("system", "question") == "recovered"
    assert len(created) == 2
    assert created[1]["disable_streaming"] is True


def test_call_simple_retries_api_connection_eof_from_cause_chain(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created = []
    interruption = APIConnectionError(
        request=httpx.Request(
            "POST",
            "http://llm.example/v1/chat/completions",
        ),
    )
    interruption.__cause__ = RuntimeError("unexpected EOF")
    assert str(interruption) == "Connection error."

    class _Model:
        def __init__(self, *, error=None, content=""):
            self.error = error
            self.content = content

        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            if self.error is not None:
                raise self.error
            return AIMessage(content=self.content)

    models = [
        _Model(error=interruption),
        _Model(content="recovered from wrapped EOF"),
    ]

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return models[len(created) - 1]

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    assert ai.call_simple("system", "question") == "recovered from wrapped EOF"
    assert len(created) == 2
    assert created[1]["disable_streaming"] is True


@pytest.mark.parametrize(
    "outer_error",
    [
        APITimeoutError(
            request=httpx.Request(
                "POST",
                "http://llm.example/v1/chat/completions",
            ),
        ),
        AuthenticationError(
            "authentication failed",
            response=httpx.Response(
                401,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        RuntimeError("provider wrapper failed"),
    ],
    ids=["timeout", "authentication", "generic"],
)
def test_stream_eof_cause_chain_preserves_outer_exception_exclusions(
    outer_error,
):
    outer_error.__cause__ = RuntimeError("empty_stream")

    assert AICall._is_retryable_stream_eof(outer_error) is False


@pytest.mark.parametrize(
    "error",
    [
        _UnexpectedEOFTimeout(
            request=httpx.Request(
                "POST",
                "http://llm.example/v1/chat/completions",
            ),
        ),
        AuthenticationError(
            "unexpected EOF",
            response=httpx.Response(
                401,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        RateLimitError(
            "empty_stream",
            response=httpx.Response(
                429,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        BadRequestError(
            "closed before first payload",
            response=httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        UnprocessableEntityError(
            "unexpected EOF",
            response=httpx.Response(
                422,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        APIResponseValidationError(
            response=httpx.Response(
                200,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
            message="unexpected EOF",
        ),
    ],
    ids=[
        "timeout",
        "authentication",
        "rate-limit",
        "bad-request",
        "unprocessable-request",
        "response-validation",
    ],
)
def test_call_simple_does_not_retry_excluded_api_errors_with_eof_signatures(
    monkeypatch,
    error,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created = []

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            raise error

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return _Model()

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    with pytest.raises(type(error)) as exc_info:
        ai.call_simple("system", "question")

    assert exc_info.value is error
    assert len(created) == 1


def test_call_simple_does_not_retry_generic_exception_with_eof_signature(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created = []
    error = RuntimeError("unexpected EOF")

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            raise error

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return _Model()

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    with pytest.raises(RuntimeError) as exc_info:
        ai.call_simple("system", "question")

    assert exc_info.value is error
    assert len(created) == 1


def test_call_simple_retries_matching_api_error_only_once(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created = []
    first_error = APIError(
        "unexpected EOF",
        request=httpx.Request(
            "POST",
            "http://llm.example/v1/chat/completions",
        ),
        body=None,
    )
    second_error = APIError(
        "empty_stream",
        request=httpx.Request(
            "POST",
            "http://llm.example/v1/chat/completions",
        ),
        body=None,
    )

    class _Model:
        def __init__(self, error):
            self.error = error

        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            raise self.error

    models = [_Model(first_error), _Model(second_error)]

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return models[len(created) - 1]

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    with pytest.raises(APIError) as exc_info:
        ai.call_simple("system", "question")

    assert exc_info.value is second_error
    assert len(created) == 2
    assert created[1]["disable_streaming"] is True


@pytest.mark.parametrize(
    "error",
    [
        BadRequestError(
            "maximum context length exceeded",
            response=httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        APITimeoutError(
            request=httpx.Request(
                "POST",
                "http://llm.example/v1/chat/completions",
            )
        ),
        BadRequestError(
            "invalid request payload",
            response=httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
        InternalServerError(
            "upstream overloaded",
            response=httpx.Response(
                500,
                request=httpx.Request(
                    "POST",
                    "http://llm.example/v1/chat/completions",
                ),
            ),
            body=None,
        ),
    ],
    ids=[
        "context-error",
        "timeout",
        "ordinary-4xx",
        "ordinary-5xx",
    ],
)
def test_call_simple_does_not_retry_non_whitelisted_api_errors(
    monkeypatch,
    error,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/gpt-5.6-sol", api_key="sk-test")
    created = []

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            raise error

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return _Model()

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    with pytest.raises(type(error)) as exc_info:
        ai.call_simple("system", "question")

    assert exc_info.value is error
    assert len(created) == 1


def test_call_simple_does_not_retry_other_api_errors(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/gpt-5.6-sol", api_key="sk-test")
    created = []
    error = APIError(
        "upstream returned malformed payload",
        request=httpx.Request("POST", "http://llm.example/v1/chat/completions"),
        body=None,
    )

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            raise error

    def _create_chat_model(**kwargs):
        created.append(kwargs)
        return _Model()

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)

    with pytest.raises(APIError) as exc_info:
        ai.call_simple(
            "system",
            "question",
            node_id="conclusion",
            max_tokens=8192,
        )

    assert exc_info.value is error
    assert len(created) == 1


def test_call_simple_hard_guard_bounds_provider_input_and_archives_budget(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    ai = AICall(
        model="openai/Qwen3.6-35B-A3B",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_preserve_tail_tokens": 1200,
        },
    )
    captured = {}

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            captured["system"] = messages[0].content
            captured["question"] = messages[-1].content
            return AIMessage(content="bounded")

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    question = (
        "HEAD preserve diagnosis scope\n"
        + ("oversized plain workflow context " * 6000)
        + "\nTAIL preserve final report constraints"
    )

    result = ai.call_simple(
        "plain workflow system contract " * 300,
        question,
        node_id="conclusion",
        run_id="run-simple-hard-guard",
        max_tokens=6000,
    )

    final_input_tokens = count_tokens(
        {
            "system": captured["system"],
            "question": captured["question"],
        },
        model=ai.model_str,
    )["tokens"]
    assert result == "bounded"
    assert final_input_tokens <= 23040
    assert captured["question"].startswith("HEAD preserve diagnosis scope")
    assert captured["question"].endswith(
        "TAIL preserve final report constraints"
    )
    assert "deterministic context compaction" in captured["question"]

    pre_guard = json.loads(
        (
            tmp_path
            / "run-simple-hard-guard"
            / "budget"
            / "conclusion_pre_guard.json"
        ).read_text()
    )
    final_budget = json.loads(
        (
            tmp_path
            / "run-simple-hard-guard"
            / "budget"
            / "conclusion.json"
        ).read_text()
    )
    assert pre_guard["hard_guard"]["triggered"] is True
    assert final_budget["hard_guard"]["final_input_tokens"] <= 23040
    assert final_budget["reserved_tokens"] == 8000


def test_call_simple_hard_guard_uses_fixed_estimator_drift_metadata(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    monkeypatch.delenv("AIOPS_TIKTOKEN_ENCODING", raising=False)
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_estimator_drift_reserve": 0,
        },
    )

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            return AIMessage(content="bounded")

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())

    assert ai.call_simple(
        "system",
        "question",
        node_id="conclusion",
        run_id="run-simple-drift",
        max_tokens=6000,
    ) == "bounded"

    final_budget = json.loads(
        (
            tmp_path
            / "run-simple-drift"
            / "budget"
            / "conclusion.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == 256
    assert hard_guard["effective_input_target"] == 22784


@pytest.mark.parametrize(
    (
        "configured_reserve",
        "expected_reserve",
        "expected_target",
    ),
    [
        (0, 256, 22784),
        (512, 512, 22528),
    ],
    ids=["minimum", "upward-override"],
)
def test_hard_guard_estimator_drift_reserve_has_minimum_and_upward_config(
    monkeypatch,
    configured_reserve,
    expected_reserve,
    expected_target,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_estimator_drift_reserve": configured_reserve,
        },
    )

    (
        _system_prompt,
        guarded_question,
        hard_guard,
        _pre_budget,
        _final_budget,
    ) = ai._prepare_structured_call_context(
        system_prompt="system",
        question="question",
        schema=None,
        node_id="simple",
        output_reserved=6000,
    )

    assert guarded_question == "question"
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == expected_reserve
    assert hard_guard["effective_input_target"] == expected_target


def test_call_simple_hard_guard_reserves_provider_framing_with_exact_content_counts(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    def _exact_count(value, model=""):
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return {
            "tokens": max(1, (len(value) + 3) // 4) if value else 0,
            "source": "test:exact-tokenizer",
            "accuracy": "exact",
        }

    monkeypatch.setattr(
        "app.core.context.budget.count_tokens",
        _exact_count,
    )
    monkeypatch.setattr(
        "app.core.aicall.client.count_tokens",
        _exact_count,
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            return AIMessage(content="exact")

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())

    assert ai.call_simple(
        "system",
        "question",
        node_id="conclusion",
        run_id="run-simple-exact",
        max_tokens=6000,
    ) == "exact"

    final_budget = json.loads(
        (
            tmp_path
            / "run-simple-exact"
            / "budget"
            / "conclusion.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    provider_overhead = next(
        component
        for component in final_budget["components"]
        if component["name"] == "provider_request_overhead"
    )
    assert provider_overhead["token_accuracy"] == "estimated"
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == 256
    assert hard_guard["effective_input_target"] == 22784


def test_call_simple_estimated_boundary_compacts_above_effective_target(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    token_count = _patch_length_token_counter(
        monkeypatch,
        accuracy="estimated",
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )
    captured = {}

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            captured["question"] = messages[-1].content
            return AIMessage(content="bounded")

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    system_prompt = "s" * 100
    desired_total = 22900
    question = "q" * (
        desired_total
        - token_count(system_prompt)["tokens"]
        - 64
    )

    assert ai.call_simple(
        system_prompt,
        question,
        node_id="conclusion",
        run_id="run-simple-estimated-boundary",
        max_tokens=6000,
    ) == "bounded"

    final_budget = json.loads(
        (
            tmp_path
            / "run-simple-estimated-boundary"
            / "budget"
            / "conclusion.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    assert hard_guard["original_input_tokens"] == desired_total
    assert hard_guard["original_input_tokens"] > 22784
    assert hard_guard["triggered"] is True
    assert hard_guard["final_input_tokens"] <= 22784
    assert captured["question"] != question
    assert len(captured["question"]) < len(question)


def test_call_simple_exact_boundary_compacts_above_effective_target(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    token_count = _patch_length_token_counter(
        monkeypatch,
        accuracy="exact",
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )
    captured = {}

    class _Model:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages, config=None):
            captured["question"] = messages[-1].content
            return AIMessage(content="exact")

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    system_prompt = "s" * 100
    desired_total = 22900
    question = "q" * (
        desired_total
        - token_count(system_prompt)["tokens"]
        - 64
    )

    assert ai.call_simple(
        system_prompt,
        question,
        node_id="conclusion",
        run_id="run-simple-exact-boundary",
        max_tokens=6000,
    ) == "exact"

    final_budget = json.loads(
        (
            tmp_path
            / "run-simple-exact-boundary"
            / "budget"
            / "conclusion.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    assert 22785 <= hard_guard["original_input_tokens"] <= 23040
    assert hard_guard["original_input_tokens"] == desired_total
    assert hard_guard["final_input_tokens"] <= 22784
    assert hard_guard["triggered"] is True
    assert captured["question"] != question
    assert len(captured["question"]) < len(question)


def test_call_simple_hard_guard_fails_closed_before_provider_when_window_unknown(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("MODEL_CONTEXT_WINDOW", raising=False)
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "app.core.aicall.client.ModelContextResolver.resolve",
        lambda self, *args, **kwargs: {
            "context_window": None,
            "source": "unavailable",
            "accuracy": "unknown",
        },
    )
    ai = AICall(
        model="openai/unknown-local-model",
        api_key="sk-test",
        context_compaction_config={"hard_guard_enabled": True},
    )
    provider_calls = []
    monkeypatch.setattr(
        ai,
        "_create_chat_model",
        lambda **kwargs: provider_calls.append(kwargs),
    )

    with pytest.raises(RuntimeError, match="context window is unavailable"):
        ai.call_simple(
            "system",
            "question",
            node_id="conclusion",
            run_id="run-simple-unknown-window",
        )

    assert provider_calls == []
    archived = json.loads(
        (
            tmp_path
            / "run-simple-unknown-window"
            / "budget"
            / "conclusion_pre_guard.json"
        ).read_text()
    )
    assert archived["hard_guard"]["error"] == "context_window_unavailable"


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

    def _capture_agent(model=None, tools=None, system_prompt=None, **kwargs):
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


def test_call_with_tools_retries_stream_interruption_before_agent_progress(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created_models = []
    created_agents = []
    interruption = InternalServerError(
        "empty_stream",
        response=httpx.Response(
            500,
            request=httpx.Request(
                "POST",
                "http://llm.example/v1/chat/completions",
            ),
        ),
        body=None,
    )

    class _Model:
        def bind(self, **kwargs):
            return self

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

    class _FailingAgent:
        async def astream(self, *args, **kwargs):
            raise interruption
            if False:
                yield None

    class _SuccessfulAgent:
        async def astream(self, *args, **kwargs):
            yield (
                "updates",
                {
                    "model": {
                        "messages": [
                            AIMessage(content="recovered agent response")
                        ]
                    }
                },
            )

    agents = [_FailingAgent(), _SuccessfulAgent()]

    def _create_chat_model(**kwargs):
        created_models.append(kwargs)
        return _Model()

    def _create_agent(**kwargs):
        created_agents.append(kwargs)
        return agents[len(created_agents) - 1]

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)
    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("langchain.agents.create_agent", side_effect=_create_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        result, events = ai.call("sys", "q", tools=[tool], max_steps=3)

    assert result.result == "recovered agent response"
    assert result.tool_call_count == 0
    assert len(created_models) == 2
    assert created_models[0].get("disable_streaming", False) is False
    assert created_models[1]["disable_streaming"] is True
    assert len(created_agents) == 2
    assert not [event for event in events if event.get("type") == "tool_start"]


def test_call_with_tools_does_not_retry_stream_interruption_after_tool_call(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/generic-model", api_key="sk-test")
    created_models = []
    created_agents = []
    interruption = InternalServerError(
        "empty_stream",
        response=httpx.Response(
            500,
            request=httpx.Request(
                "POST",
                "http://llm.example/v1/chat/completions",
            ),
        ),
        body=None,
    )

    class _Model:
        def bind(self, **kwargs):
            return self

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

    class _PartiallyProgressedAgent:
        async def astream(self, *args, **kwargs):
            yield (
                "updates",
                {
                    "model": {
                        "messages": [
                            AIMessage(
                                content="",
                                tool_calls=[
                                    {
                                        "name": "tool_a",
                                        "args": {"value": "once"},
                                        "id": "tool-call-1",
                                    }
                                ],
                            )
                        ]
                    }
                },
            )
            raise interruption

    def _create_chat_model(**kwargs):
        created_models.append(kwargs)
        return _Model()

    def _create_agent(**kwargs):
        created_agents.append(kwargs)
        return _PartiallyProgressedAgent()

    monkeypatch.setattr(ai, "_create_chat_model", _create_chat_model)
    tool = MagicMock()
    tool.name = "tool_a"
    tool.description = "tool"
    tool.args_schema = None

    with patch("langchain.agents.create_agent", side_effect=_create_agent), \
         patch("concurrent.futures.ThreadPoolExecutor", return_value=_Executor()):
        result, events = ai.call("sys", "q", tools=[tool], max_steps=3)

    assert result.result == f"Agent 执行异常: {interruption}"
    assert result.tool_call_count == 1
    assert len(created_models) == 1
    assert len(created_agents) == 1
    assert len([
        event for event in events if event.get("type") == "tool_start"
    ]) == 1


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


def test_call_structured_hard_guard_bounds_provider_input_and_archives_budget(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    ai = AICall(
        model="openai/Qwen3.6-35B-A3B",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_preserve_tail_tokens": 1200,
        },
    )
    captured = {}

    class _StructuredModel:
        def invoke(self, messages, config=None):
            captured["system"] = messages[0].content
            captured["question"] = messages[-1].content
            return EvidencePlanOutput(
                layer="L3",
                evidence_plan=[],
                collection_strategy="bounded",
            )

    class _Model:
        def bind(self, **kwargs):
            return self

        def with_structured_output(self, schema, **kwargs):
            return _StructuredModel()

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    system_prompt = "RCA system contract " * 300
    question = (
        "HEAD scoped entities and direct facts\n"
        + ("oversized evidence payload " * 6000)
        + "\nTAIL RCAOutput requirements"
    )

    parsed, _raw = ai.call_structured(
        system_prompt,
        question,
        EvidencePlanOutput,
        node_id="rca",
        run_id="run-hard-guard",
        max_tokens=6000,
    )

    schema_tokens = count_tokens(
        EvidencePlanOutput.model_json_schema(),
        model=ai.model_str,
    )["tokens"]
    final_input_tokens = (
        count_tokens(captured["system"], model=ai.model_str)["tokens"]
        + count_tokens(captured["question"], model=ai.model_str)["tokens"]
        + schema_tokens
    )
    assert isinstance(parsed, EvidencePlanOutput)
    assert final_input_tokens <= 23040
    assert captured["question"].startswith("HEAD scoped entities")
    assert captured["question"].endswith("TAIL RCAOutput requirements")
    assert "deterministic context compaction" in captured["question"]

    pre_guard = json.loads(
        (tmp_path / "run-hard-guard" / "budget" / "rca_pre_guard.json").read_text()
    )
    final_budget = json.loads(
        (tmp_path / "run-hard-guard" / "budget" / "rca.json").read_text()
    )
    assert pre_guard["hard_guard"]["triggered"] is True
    assert final_budget["hard_guard"]["final_input_tokens"] <= 23040
    assert final_budget["reserved_tokens"] == 8000
    assert any(
        component["name"] == "safety_margin"
        and component["tokens"] == 2000
        for component in final_budget["components"]
    )
    assert final_budget["hard_guard"]["original_question_chars"] > final_budget["hard_guard"]["final_question_chars"]


def test_call_structured_hard_guard_reserves_estimator_drift_below_public_limit(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    monkeypatch.delenv("AIOPS_TIKTOKEN_ENCODING", raising=False)
    ai = AICall(
        model="openai/Qwen3.6-35B-A3B",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_preserve_tail_tokens": 1200,
            "hard_guard_estimator_drift_reserve": 0,
        },
    )

    class _StructuredModel:
        def invoke(self, messages, config=None):
            return EvidencePlanOutput(
                layer="L3",
                evidence_plan=[],
                collection_strategy="estimated-count-reserve",
            )

    class _Model:
        def bind(self, **kwargs):
            return self

        def with_structured_output(self, schema, **kwargs):
            return _StructuredModel()

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    ai.call_structured(
        "RCA system contract " * 300,
        "HEAD\n" + ("estimated evidence payload " * 6000) + "\nTAIL",
        EvidencePlanOutput,
        node_id="rca",
        run_id="run-estimator-drift",
        max_tokens=6000,
    )

    final_budget = json.loads(
        (
            tmp_path
            / "run-estimator-drift"
            / "budget"
            / "rca.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    assert final_budget["token_count_accuracy"] != "exact"
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == 256
    assert hard_guard["effective_input_target"] == 22784
    assert hard_guard["final_input_tokens"] <= 22784


def test_call_structured_hard_guard_reserves_provider_framing_with_exact_content_counts(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    def _exact_count(value, model=""):
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return {
            "tokens": max(1, (len(value) + 3) // 4) if value else 0,
            "source": "test:exact-tokenizer",
            "accuracy": "exact",
        }

    monkeypatch.setattr(
        "app.core.context.budget.count_tokens",
        _exact_count,
    )
    monkeypatch.setattr(
        "app.core.aicall.client.count_tokens",
        _exact_count,
    )
    ai = AICall(
        model="openai/Qwen3.6-35B-A3B",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_preserve_tail_tokens": 1200,
        },
    )

    class _StructuredModel:
        def invoke(self, messages, config=None):
            return EvidencePlanOutput(
                layer="L3",
                evidence_plan=[],
                collection_strategy="exact-count-no-reserve",
            )

    class _Model:
        def bind(self, **kwargs):
            return self

        def with_structured_output(self, schema, **kwargs):
            return _StructuredModel()

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    ai.call_structured(
        "RCA system contract " * 300,
        "HEAD\n" + ("exact tokenizer evidence payload " * 6000) + "\nTAIL",
        EvidencePlanOutput,
        node_id="rca",
        run_id="run-exact-tokenizer",
        max_tokens=6000,
    )

    final_budget = json.loads(
        (
            tmp_path
            / "run-exact-tokenizer"
            / "budget"
            / "rca.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    provider_overhead = next(
        component
        for component in final_budget["components"]
        if component["name"] == "provider_request_overhead"
    )
    assert provider_overhead["token_accuracy"] == "estimated"
    assert final_budget["token_count_accuracy"] != "exact"
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == 256
    assert hard_guard["effective_input_target"] == 22784
    assert hard_guard["final_input_tokens"] <= 22784


def test_call_structured_exact_boundary_compacts_above_effective_target(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    token_count = _patch_length_token_counter(
        monkeypatch,
        accuracy="exact",
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )
    captured = {}

    class _StructuredModel:
        def invoke(self, messages, config=None):
            captured["question"] = messages[-1].content
            return EvidencePlanOutput(
                layer="L3",
                evidence_plan=[],
                collection_strategy="exact-boundary-no-compaction",
            )

    class _Model:
        def bind(self, **kwargs):
            return self

        def with_structured_output(self, schema, **kwargs):
            return _StructuredModel()

    monkeypatch.setattr(ai, "_create_chat_model", lambda **kwargs: _Model())
    system_prompt = "s" * 100
    schema_payload = EvidencePlanOutput.model_json_schema()
    desired_total = 22900
    question = "q" * (
        desired_total
        - token_count(system_prompt)["tokens"]
        - token_count(schema_payload)["tokens"]
        - 64
    )

    parsed, _raw = ai.call_structured(
        system_prompt,
        question,
        EvidencePlanOutput,
        node_id="rca",
        run_id="run-structured-exact-boundary",
        max_tokens=6000,
    )

    final_budget = json.loads(
        (
            tmp_path
            / "run-structured-exact-boundary"
            / "budget"
            / "rca.json"
        ).read_text()
    )
    hard_guard = final_budget["hard_guard"]
    assert isinstance(parsed, EvidencePlanOutput)
    assert 22785 <= hard_guard["original_input_tokens"] <= 23040
    assert hard_guard["original_input_tokens"] == desired_total
    assert hard_guard["final_input_tokens"] <= 22784
    assert hard_guard["triggered"] is True
    assert captured["question"] != question
    assert len(captured["question"]) < len(question)


def test_agent_hard_guard_records_fixed_estimator_drift_metadata(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    monkeypatch.delenv("AIOPS_TIKTOKEN_ENCODING", raising=False)
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
            "hard_guard_estimator_drift_reserve": 0,
        },
    )
    request = SimpleNamespace(
        model_settings={"max_tokens": 6000},
        system_message=SystemMessage(content="system"),
        messages=[HumanMessage(content="question")],
        tools=[],
        response_format=None,
    )

    guarded_request, budget = ai._guard_agent_model_request(
        request,
        node_id="evidence",
    )

    hard_guard = budget["hard_guard"]
    assert guarded_request is request
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == 256
    assert hard_guard["effective_input_target"] == 22784


def test_agent_hard_guard_reserves_provider_framing_with_exact_content_counts(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")

    def _exact_count(value, model=""):
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return {
            "tokens": max(1, (len(value) + 3) // 4) if value else 0,
            "source": "test:exact-tokenizer",
            "accuracy": "exact",
        }

    monkeypatch.setattr(
        "app.core.context.budget.count_tokens",
        _exact_count,
    )
    monkeypatch.setattr(
        "app.core.aicall.client.count_tokens",
        _exact_count,
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )
    request = SimpleNamespace(
        model_settings={"max_tokens": 6000},
        system_message=SystemMessage(content="system"),
        messages=[HumanMessage(content="question")],
        tools=[],
        response_format=None,
    )

    guarded_request, budget = ai._guard_agent_model_request(
        request,
        node_id="evidence",
    )

    hard_guard = budget["hard_guard"]
    provider_overhead = next(
        component
        for component in budget["components"]
        if component["name"] == "provider_request_overhead"
    )
    assert guarded_request is request
    assert provider_overhead["token_accuracy"] == "estimated"
    assert hard_guard["token_count_accuracy"] != "exact"
    assert hard_guard["max_input_tokens"] == 23040
    assert hard_guard["estimator_drift_reserve"] == 256
    assert hard_guard["effective_input_target"] == 22784


def test_agent_estimated_boundary_compacts_above_effective_target(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    token_count = _patch_length_token_counter(
        monkeypatch,
        accuracy="estimated",
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )
    system_prompt = "system"
    empty_history = [
        ai._serialize_agent_message(HumanMessage(content=""))
    ]
    fixed_tokens = (
        token_count(system_prompt)["tokens"]
        + token_count(empty_history)["tokens"]
        + token_count(serialize_tool_schema([]))["tokens"]
        + token_count(ai._serialize_agent_response_format(None))["tokens"]
        + 64
    )
    desired_total = 22900
    question = "q" * (desired_total - fixed_tokens)
    request = _BoundaryAgentRequest(
        model_settings={"max_tokens": 6000},
        system_message=SystemMessage(content=system_prompt),
        messages=[HumanMessage(content=question)],
        tools=[],
        response_format=None,
    )

    guarded_request, budget = ai._guard_agent_model_request(
        request,
        node_id="evidence",
    )

    hard_guard = budget["hard_guard"]
    assert hard_guard["original_input_tokens"] == desired_total
    assert hard_guard["original_input_tokens"] > 22784
    assert hard_guard["triggered"] is True
    assert hard_guard["final_input_tokens"] <= 22784
    assert guarded_request is not request
    assert request.messages[0].content == question
    assert len(guarded_request.messages) == 1
    assert guarded_request.messages[0].content != question
    assert "context_compacted" in guarded_request.messages[0].content


def test_agent_exact_boundary_compacts_above_effective_target(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    token_count = _patch_length_token_counter(
        monkeypatch,
        accuracy="exact",
    )
    ai = AICall(
        model="openai/generic-model",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 2000,
        },
    )
    system_prompt = "system"
    empty_history = [
        ai._serialize_agent_message(HumanMessage(content=""))
    ]
    fixed_tokens = (
        token_count(system_prompt)["tokens"]
        + token_count(empty_history)["tokens"]
        + token_count(serialize_tool_schema([]))["tokens"]
        + token_count(ai._serialize_agent_response_format(None))["tokens"]
        + 64
    )
    desired_total = 22900
    question = "q" * (desired_total - fixed_tokens)
    request = _BoundaryAgentRequest(
        model_settings={"max_tokens": 6000},
        system_message=SystemMessage(content=system_prompt),
        messages=[HumanMessage(content=question)],
        tools=[],
        response_format=None,
    )

    guarded_request, budget = ai._guard_agent_model_request(
        request,
        node_id="evidence",
    )

    hard_guard = budget["hard_guard"]
    assert 22785 <= hard_guard["original_input_tokens"] <= 23040
    assert hard_guard["original_input_tokens"] == desired_total
    assert hard_guard["final_input_tokens"] <= 22784
    assert hard_guard["triggered"] is True
    assert guarded_request is not request
    assert request.messages[0].content == question
    assert guarded_request.messages[0].content != question
    assert "context_compacted" in guarded_request.messages[0].content


def test_call_structured_hard_guard_rejects_oversized_static_contract_before_provider(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "1000")
    ai = AICall(
        model="openai/Qwen3.6-35B-A3B",
        api_key="sk-test",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": 0.72,
            "hard_guard_safety_tokens": 200,
        },
    )
    provider_calls = []
    monkeypatch.setattr(
        ai,
        "_create_chat_model",
        lambda **kwargs: provider_calls.append(kwargs),
    )

    with pytest.raises(
        RuntimeError,
        match="system prompt and structured schema exceed hard input budget",
    ):
        ai.call_structured(
            "static RCA contract " * 600,
            "short user message",
            EvidencePlanOutput,
            node_id="rca",
            max_tokens=500,
        )

    assert provider_calls == []


def test_call_structured_hard_guard_fails_closed_and_archives_unknown_window(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("MODEL_CONTEXT_WINDOW", raising=False)
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "app.core.aicall.client.ModelContextResolver.resolve",
        lambda self, *args, **kwargs: {
            "context_window": None,
            "source": "unavailable",
            "accuracy": "unknown",
        },
    )
    ai = AICall(
        model="openai/unknown-local-model",
        api_key="sk-test",
        context_compaction_config={"hard_guard_enabled": True},
    )
    provider_calls = []
    monkeypatch.setattr(
        ai,
        "_create_chat_model",
        lambda **kwargs: provider_calls.append(kwargs),
    )

    with pytest.raises(RuntimeError, match="context window is unavailable"):
        ai.call_structured(
            "system",
            "oversized" * 20000,
            EvidencePlanOutput,
            node_id="rca",
            run_id="run-unknown-window",
        )

    assert provider_calls == []
    pre_guard_path = (
        tmp_path
        / "run-unknown-window"
        / "budget"
        / "rca_pre_guard.json"
    )
    assert pre_guard_path.exists()
    archived = json.loads(pre_guard_path.read_text())
    assert archived["hard_guard"]["enabled"] is True
    assert archived["hard_guard"]["error"] == "context_window_unavailable"


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


def test_call_wraps_provider_reasoning_content_for_stream_filters():
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
                    AIMessage(content="", additional_kwargs={"reasoning_content": "内部推理"}),
                    {"langgraph_node": "model"},
                ),
            )
            yield (
                "updates",
                {
                    "model": {
                        "messages": [
                            AIMessage(content="最终答案", additional_kwargs={"reasoning_content": "内部推理"})
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

    queued_events = []
    while not event_queue.empty():
        _, evt = event_queue.get_nowait()
        queued_events.append(evt)

    token_event = next(evt for evt in queued_events if evt.get("type") == "ai_token")
    message_event = next(evt for evt in queued_events if evt.get("type") == "ai_message")
    assert token_event["content"] == "<think>内部推理</think>"
    assert message_event["full_content"].startswith("<think>内部推理</think>最终答案")


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
