import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.aicall.client import AICall
from app.core.context.observation import ObservationProcessor
from langchain_core.messages import AIMessage, ToolMessage


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


def test_aicall_returns_compact_yaml_summary_under_context_threshold(tmp_path, monkeypatch):
    ai = AICall(
        model="openai/test",
        api_key="sk-test",
        observation_summary_mode="rule",
        observation_summary_max_chars=500,
    )
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "20000")

    raw_yaml = "kind: Pod\nmetadata:\n  name: ham-wcc79\nspec:\n  imagePullSecrets:\n  - name: xnet-bmcs\n" + ("noise: value\n" * 50)
    msg = ToolMessage(content=raw_yaml, tool_call_id="tc-yaml", name="kubectl_get_yaml")

    def fake_summary(tool_name, raw, current_summary):
        raise AssertionError("yaml should not be summarized below threshold")

    ai._summarize_tool_observation = fake_summary

    processed = ai._process_tool_observation(
        processor=ai._build_observation_processor(),
        run_id="run-full-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        tool_content=msg.content,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "system"},
            {"name": "user_message", "category": "static_input", "content": "user"},
        ],
        prior_tool_observations=[],
    )

    assert processed["summary"] != raw_yaml
    assert "imagePullSecrets: xnet-bmcs" in processed["summary"]
    assert processed["processor"] == "k8s_yaml"
    assert processed["structured"]["kind"] == "Pod"
    assert processed["structured"]["imagePullSecrets"] == ["xnet-bmcs"]


def test_aicall_summarizes_yaml_tool_when_context_threshold_exceeded(tmp_path, monkeypatch):
    ai = AICall(
        model="openai/test",
        api_key="sk-test",
        observation_summary_mode="rule",
        observation_summary_max_chars=500,
    )
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "300")

    raw = "kind: Pod\nmetadata:\n  name: ham-wcc79\n" + ("noise: value\n" * 300)

    def fake_summary(tool_name, raw_content, current_summary):
        return json.dumps({
            "summary": "Pod ham-wcc79 yaml compressed because context budget is high",
            "key_facts": ["imagePullSecrets should be checked"],
            "conflicts": [],
            "missing": [],
        }, ensure_ascii=False)

    ai._summarize_tool_observation = fake_summary

    processed = ai._process_tool_observation(
        processor=ai._build_observation_processor(),
        run_id="run-compress-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        tool_content=raw,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "system" * 100},
            {"name": "user_message", "category": "static_input", "content": "user" * 100},
        ],
        prior_tool_observations=[],
    )

    assert "compressed because context budget is high" in processed["summary"]
    assert processed["processor"] == "k8s_yaml+llm"
    assert processed["structured"]["kind"] == "Pod"


def test_aicall_deduplicates_replayed_agent_updates(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    first_ai = AIMessage(
        content="<think>planning</think>",
        tool_calls=[{
            "name": "kubectl_run_image",
            "args": {"image": "busybox:1.36", "command": "nslookup xnet.registry.io"},
            "id": "call-1",
            "type": "tool_call",
        }],
    )
    tool_msg = ToolMessage(
        content=json.dumps({
            "success": False,
            "stdout": "pod \"curl-test\" deleted\n",
            "stderr": "error: timed out waiting for the condition\n",
            "returncode": 1,
        }, ensure_ascii=False),
        tool_call_id="call-1",
        name="kubectl_run_image",
    )
    final_ai = AIMessage(content="最终结论")

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
            yield ("updates", {"agent": {"messages": [first_ai]}})
            yield ("updates", {"tools": {"messages": [tool_msg]}})
            yield ("updates", {"agent": {"messages": [first_ai]}})
            yield ("updates", {"tools": {"messages": [tool_msg]}})
            yield ("updates", {"agent": {"messages": [final_ai]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_run_image", "description": "run image", "args_schema": None})()
    result, events = ai.call(
        "system prompt",
        "user prompt",
        tools=[tool],
        node_id="evidence",
        run_id="run-dedupe",
        max_steps=2,
    )

    tool_start_events = [e for e in events if e["type"] == "tool_start"]
    tool_result_events = [e for e in events if e["type"] == "tool_result"]

    assert result.tool_call_count == 1
    assert len(result.tool_calls) == 1
    assert len(tool_start_events) == 1
    assert len(tool_result_events) == 1
    assert tool_start_events[0]["tool_name"] == "kubectl_run_image"
    assert tool_start_events[0]["tool_args"] == {"image": "busybox:1.36", "command": "nslookup xnet.registry.io"}


def test_observation_processor_extracts_kubectl_run_image_failure(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=500)

    processed = processor.process(
        run_id="run-kri",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_run_image",
        raw_content=json.dumps({
            "success": False,
            "stdout": "pod \"curl-test\" deleted\n",
            "stderr": "error: timed out waiting for the condition\n",
            "returncode": 1,
        }, ensure_ascii=False),
    )

    assert processed["processor"] == "k8s_run_image+passthrough_full"
    assert processed["structured"]["status"] == "run_image_result"
    assert processed["structured"]["success"] is False
    assert processed["structured"]["signals"] == ["timeout"]
    assert "timed out waiting for the condition" in processed["summary"]
    assert processed["semantic_success"] is False


def test_observation_processor_keeps_secret_table_image_pull_facts(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)
    raw = """NAME        TYPE                             DATA   AGE
xnet-bmcs   Opaque                           1      215d
pull-good   kubernetes.io/dockerconfigjson   1      1d
other       Opaque                           1      1d
"""

    processed = processor.process(
        run_id="run-secret-table",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_namespace",
        raw_content=raw,
    )

    assert processed["processor"] == "k8s_secret_table"
    assert processed["structured"]["resource_kind"] == "Secret"
    assert processed["structured"]["docker_secret_count"] == 1
    assert "pull-good" in processed["summary"]
    assert "xnet-bmcs" in processed["summary"]


def test_observation_processor_marks_failed_yaml_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-yaml-failed",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content='Command failed (exit 1):\nkubectl get -o yaml configmap registry-config -n kube-system\nError from server (NotFound): configmaps "registry-config" not found',
    )

    assert processed["structured"]["status"] == "command_failed"
    assert processed["semantic_success"] is False
    assert "NotFound" in processed["summary"]


def test_observation_processor_marks_failed_describe_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-describe-failed",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content='Command failed (exit 1):\nkubectl describe pod memhog -n aiops-e2e\nError from server (NotFound): pods "memhog" not found',
    )

    assert processed["structured"]["status"] == "command_failed"
    assert processed["semantic_success"] is False
    assert "NotFound" in processed["summary"]
