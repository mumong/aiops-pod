import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.aicall.client import AICall
from app.core.context.observation import ObservationProcessor
from langchain_core.messages import ToolMessage


def test_aicall_process_tool_observation_returns_bounded_summary(tmp_path):
    ai = AICall(model="openai/test", api_key="sk-test")
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=500)

    processed = ai._process_tool_observation(
        processor=processor,
        run_id="run-a",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        tool_content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n" + ("noise\n" * 1000),
    )

    assert processed["processed"] is True
    assert len(processed["summary"]) <= 500
    assert "OOMKilled" in processed["summary"]
    assert processed["raw_ref"].endswith(".raw.txt")


def test_aicall_mutates_tool_message_to_bounded_observation(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n" + ("noise\n" * 1000),
        tool_call_id="tc-1",
        name="kubectl_describe",
    )

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
            yield ("updates", {"tools": {"messages": [msg]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "d", "args_schema": None})()
    result, events = ai.call(
        "sys",
        "q",
        tools=[tool],
        node_id="evidence",
        run_id="run-b",
        max_steps=2,
    )

    assert len(msg.content) < 3000
    assert "OOMKilled" in msg.content
    assert "raw_ref" in result.tool_calls[0]
    assert events[0]["observation_processed"] is True


def test_aicall_writes_final_budget_with_dynamic_context(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "8192")

    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n",
        tool_call_id="tc-1",
        name="kubectl_describe",
    )

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
            yield ("updates", {"tools": {"messages": [msg]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "describe pods", "args_schema": None})()
    ai.call(
        "system prompt",
        "user prompt",
        tools=[tool],
        node_id="evidence",
        run_id="run-dynamic",
        max_steps=2,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "system prompt"},
            {"name": "user_message", "category": "static_input", "content": "user prompt"},
        ],
    )

    budget = json.loads((tmp_path / "run-dynamic" / "budget" / "evidence.json").read_text())
    names = {c["name"] for c in budget["components"]}
    assert "tool_observations" in names
    assert "final_output" in names
    assert budget["dynamic_context_tokens"] > 0


def test_aicall_passes_ai_summary_mode_to_observation_processor(tmp_path, monkeypatch):
    ai = AICall(
        model="openai/test",
        api_key="sk-test",
        observation_summary_mode="ai",
        observation_summary_max_chars=500,
    )
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n",
        tool_call_id="tc-1",
        name="kubectl_describe",
    )

    def fake_summary(tool_name, raw, current_summary):
        return "AI forced summary"

    ai._summarize_tool_observation = fake_summary

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
            yield ("updates", {"tools": {"messages": [msg]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "describe pods", "args_schema": None})()
    result, events = ai.call(
        "system prompt",
        "user prompt",
        tools=[tool],
        node_id="evidence",
        run_id="run-ai-mode",
        max_steps=2,
    )

    assert msg.content == "AI forced summary"
    assert result.tool_calls[0]["summary_chars"] == len("AI forced summary")
    assert events[0]["observation_processor"] == "k8s_describe+llm"
