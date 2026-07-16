import asyncio
import hashlib
import os
import sys
import json
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.aicall.client import AICall
from app.core.context.observation import ObservationProcessor
from langchain_core.messages import AIMessage, ToolMessage


def _canonical_fact_record(**overrides):
    record = {
        "entity_id": "k8s.pod:demo/api:uid-a",
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "logging",
        "fact_type": "log",
        "attribute": "log.message",
        "value": {"message": "request returned status 503"},
        "source_system": "elasticsearch",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["logs:target"],
    }
    record.update(overrides)
    identity = {
        key: value
        for key, value in record.items()
        if key != "fact_id"
        and value not in (None, {}, [])
    }
    identity["evidence_refs"] = sorted(set(identity["evidence_refs"]))
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    record["fact_id"] = (
        "fact-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    )
    return record


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


def test_observation_processor_preserves_sanitized_canonical_fact_ledger(tmp_path):
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=1200,
    )
    entity_id = "k8s.pod:demo/api:uid-a"
    valid_record = _canonical_fact_record(entity_id=entity_id)
    evaluator_record = _canonical_fact_record(
        entity_id=entity_id,
        value={"message": "must be rejected"},
        evidence_refs=["logs:evaluator"],
        metadata={
            "nested": {
                "expected/remediation": "must not reach the agent",
                "LaBeL": "evaluator-only",
            }
        },
    )
    raw = json.dumps({
        "ok": True,
        "case_id": "case-facts",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-a",
        },
        "coverage": {"logs": "present"},
        "fact_ledger": {
            "contract_version": "aiops.fact-ledger.v1",
            "case_id": "case-facts",
            "scope_entity_ids": [entity_id],
            "records": [valid_record, evaluator_record],
            "record_count": 2,
            "truncated": False,
            "source": "mcp_canonical",
            "legacy_contract": False,
        },
    })

    processed = processor.process(
        run_id="run-fact-ledger",
        node_id="evidence",
        sequence=1,
        tool_name="collect_aiops_case",
        raw_content=raw,
    )

    ledger = processed["structured"]["fact_ledger"]
    assert ledger["contract_version"] == "aiops.fact-ledger.v1"
    assert ledger["scope_entity_ids"] == [entity_id]
    assert [record["fact_id"] for record in ledger["records"]] == [
        valid_record["fact_id"]
    ]
    assert ledger["record_count"] == 1
    assert "must not reach the agent" not in json.dumps(ledger)
    assert "evaluator-only" not in json.dumps(ledger)


def test_observation_processor_strips_nested_causal_keys_but_keeps_source_text(
    tmp_path,
):
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=2000,
    )
    raw = json.dumps({
        "ok": True,
        "case_id": "case-legacy-sanitized",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-a",
        },
        "dimension_details": {
            "metrics": {
                "highlights": [
                    {
                        "metric": "request_latency_seconds",
                        "samples": [
                            {
                                "value": 1.25,
                                "rootCauseState": "must not reach the agent",
                                "causalRole": "must not reach the agent",
                                "causalRoleState": "must not reach the agent",
                                "prefix.CAUSAL-role/Suffix": "must not reach the agent",
                                "diagnosticRole": "must not reach the agent",
                                "diagnosticRoleState": "must not reach the agent",
                                "prefix.DIAGNOSTIC-role/Suffix": "must not reach the agent",
                            }
                        ],
                    }
                ]
            },
            "logs": {
                "samples": [
                    {
                        "message": (
                            "request driver logged root cause label, causal role, "
                            "and diagnostic role as source text"
                        )
                    }
                ]
            },
            "tracing": {
                "spans": [
                    {
                        "trace_id": "trace-a",
                        "attributes": {
                            "safe.attribute": "kept",
                            "diagnosisReason": "must not reach the agent",
                            "preFailureBehavior": "must not reach the agent",
                            "requestDriver": "must not reach the agent",
                            "causalRoleState": "must not reach the agent",
                            "diagnosticRoleState": "must not reach the agent",
                        },
                    }
                ]
            },
        },
    })

    processed = processor.process(
        run_id="run-legacy-sanitized",
        node_id="evidence",
        sequence=1,
        tool_name="collect_aiops_case",
        raw_content=raw,
    )

    rendered = json.dumps(
        processed["structured"]["dimension_details"],
        ensure_ascii=False,
    )
    assert "must not reach the agent" not in rendered
    assert "safe.attribute" in rendered
    assert (
        "request driver logged root cause label, causal role, and diagnostic "
        "role as source text"
    ) in rendered


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


def test_aicall_tool_result_event_includes_context_usage_ratio(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n",
        tool_call_id="tc-context",
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

    original_process = ai._process_tool_observation

    def _process_with_context_ratio(**kwargs):
        result = original_process(**kwargs)
        result["context_usage_ratio"] = 0.81
        return result

    monkeypatch.setattr(ai, "_process_tool_observation", _process_with_context_ratio)
    monkeypatch.setattr("langchain.agents.create_agent", lambda **kwargs: _Agent())
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "d", "args_schema": None})()
    _, events = ai.call(
        "sys",
        "q",
        tools=[tool],
        node_id="evidence",
        run_id="run-context-ratio",
        max_steps=2,
    )

    tool_result = next(event for event in events if event["type"] == "tool_result")
    assert tool_result["context_usage_ratio"] == 0.81


def test_aicall_tool_archive_sequence_can_continue_across_rounds(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    msg = ToolMessage(
        content="Name: pod-b\nNamespace: default\nReason: Error\n",
        tool_call_id="tc-sequence",
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

    monkeypatch.setattr("langchain.agents.create_agent", lambda **kwargs: _Agent())
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "d", "args_schema": None})()
    result, _ = ai.call(
        "sys",
        "q",
        tools=[tool],
        node_id="evidence",
        run_id="run-sequence",
        max_steps=2,
        tool_result_sequence_start=5,
    )

    assert "/006-evidence-kubectl_describe.raw.txt" in result.tool_calls[0]["raw_ref"]


def test_aicall_assigns_stable_sequence_to_parallel_tool_results(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "tc-a",
                "name": "kubectl_get_by_name",
                "args": {"kind": "Pod", "namespace": "default", "name": "pod-a"},
            },
            {
                "id": "tc-b",
                "name": "kubectl_get_by_name",
                "args": {"kind": "Pod", "namespace": "default", "name": "pod-b"},
            },
        ],
    )
    tool_messages = [
        ToolMessage(
            content="NAME pod-a STATUS Running",
            tool_call_id="tc-a",
            name="kubectl_get_by_name",
        ),
        ToolMessage(
            content="NAME pod-b STATUS CrashLoopBackOff",
            tool_call_id="tc-b",
            name="kubectl_get_by_name",
        ),
    ]

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
            yield ("updates", {"model": {"messages": [ai_message]}})
            yield ("updates", {"tools": {"messages": tool_messages}})

    monkeypatch.setattr("langchain.agents.create_agent", lambda **kwargs: _Agent())
    monkeypatch.setattr(
        "concurrent.futures.ThreadPoolExecutor",
        lambda max_workers=1: _Executor(),
    )

    tool = type(
        "T",
        (),
        {"name": "kubectl_get_by_name", "description": "d", "args_schema": None},
    )()
    _, events = ai.call(
        "sys",
        "q",
        tools=[tool],
        node_id="layer",
        run_id="run-parallel-sequence",
        max_steps=4,
    )

    starts = [event for event in events if event["type"] == "tool_start"]
    results = [event for event in events if event["type"] == "tool_result"]
    assert [event["tool_sequence"] for event in starts] == [1, 2]
    assert [event["tool_sequence"] for event in results] == [1, 2]


def test_tool_dedup_middleware_reuses_success_for_same_name_and_args():
    middleware = AICall._build_tool_dedup_middleware()
    executions = []

    async def handler(request):
        executions.append(request.tool_call["id"])
        return ToolMessage(
            content='{"status":"success","pod":"pod-a"}',
            tool_call_id=request.tool_call["id"],
            name=request.tool_call["name"],
        )

    first_request = SimpleNamespace(
        tool_call={
            "id": "tc-first",
            "name": "kubectl_get_by_name",
            "args": {"kind": "Pod", "namespace": "default", "name": "pod-a"},
        }
    )
    second_request = SimpleNamespace(
        tool_call={
            "id": "tc-second",
            "name": "kubectl_get_by_name",
            "args": {"name": "pod-a", "namespace": "default", "kind": "Pod"},
        }
    )

    first = asyncio.run(middleware.awrap_tool_call(first_request, handler))
    second = asyncio.run(middleware.awrap_tool_call(second_request, handler))

    assert first.content == second.content
    assert executions == ["tc-first"]
    assert second.tool_call_id == "tc-second"
    assert second.additional_kwargs["aiops_deduplicated"] is True
    assert second.additional_kwargs["aiops_original_tool_call_id"] == "tc-first"


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


def test_aicall_compacts_evidence_runtime_context_when_small_window_is_hot(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/Qwen3-32B-AWQ", api_key="sk-test")
    ai._compact_context_with_lite_llm = lambda payload, **kwargs: {
        "process_summary": [
            "先输出 evidence_plan",
            "随后连续调用多个 run_bash_command 检查 registry 网络",
            "最后发现存在重复节点信息查询，应抓大放小",
        ],
        "evidence_plan": [{"id": "e1", "description": "检查 docker.io 连通性"}],
        "completed_items": [{"id": "e1", "outcome": "negative", "fact": "curl registry 超时"}],
        "open_items": [{"id": "e2", "reason": "镜像存在性未能独立验证"}],
        "key_facts": ["Pod test1-redis-master-0 为 ImagePullBackOff"],
        "negative_facts": ["curl registry-1.docker.io timed out"],
        "conflicts": [],
        "discarded_noise": ["重复 node capacity 查询"],
        "next_focus": ["不要继续查询 Node capacity，优先总结网络不可达证据"],
    }
    static_components = [
        {"name": "node_system_prompt", "category": "static_input", "content": "s" * 4000},
        {"name": "user_message", "category": "static_input", "content": "u" * 4000},
        {"name": "tool_schema", "category": "static_input", "content": "t" * 4000},
    ]
    plan_text = json.dumps({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "检查 docker.io 连通性",
                "level": "important",
                "tool": "run_bash_command",
                "command": "curl https://registry-1.docker.io/v2/",
                "purpose": "验证镜像仓库连通性",
            }
        ],
        "collection_strategy": "先确认镜像拉取失败。",
    }, ensure_ascii=False)
    thinking_events = [
        {
            "type": "ai_message",
            "node": "evidence",
            "full_content": plan_text,
            "content": plan_text[:500],
        },
        {
            "type": "ai_message",
            "node": "evidence",
            "full_content": "第一轮分析" + ("循环思考" * 3000),
            "content": "第一轮分析",
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "tool_name": "run_bash_command",
            "result": '{"success": false, "stderr": "curl: (28) timed out"}',
            "result_preview": "curl timed out",
            "semantic_success": False,
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "tool_name": "run_bash_command",
            "result": '{"success": true, "stdout": "node capacity noise"}' * 1000,
            "result_preview": "node capacity noise",
            "semantic_success": True,
            "raw_ref": "/archive/tools/node.raw.txt",
            "structured_ref": "/archive/tools/node.structured.json",
            "summary_ref": "/archive/tools/node.summary.txt",
        },
    ]

    compacted = ai._maybe_compact_runtime_context(
        node_id="evidence",
        run_id="run-compact",
        static_context_components=static_components,
        thinking_events=thinking_events,
        tool_observation_contents=[
            '{"success": false, "stderr": "curl: (28) timed out"}',
            '{"success": true, "stdout": "node capacity noise"}' * 1000,
        ],
    )

    assert compacted is True
    assert thinking_events[0]["type"] == "context_summary"
    assert len([ev for ev in thinking_events if ev.get("type") == "ai_message"]) == 2
    assert len([ev for ev in thinking_events if ev.get("type") == "tool_result"]) == 2
    assert any("evidence_plan" in (ev.get("full_content") or "") for ev in thinking_events)
    assert any("timed out" in (ev.get("result") or "") for ev in thinking_events if ev.get("type") == "tool_result")
    assert any(
        "[compacted: see raw_ref/structured_ref/summary_ref]" in (ev.get("result") or "")
        for ev in thinking_events
        if ev.get("type") == "tool_result"
    )
    summary = thinking_events[0]["full_content"]
    assert "process_summary" in summary
    assert "curl registry 超时" in summary
    assert "重复 node capacity 查询" in summary
    assert all("循环思考循环思考循环思考" not in json.dumps(ev, ensure_ascii=False) for ev in thinking_events)


def test_aicall_compaction_rewrites_non_plan_ai_messages_in_agent_context(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    ai = AICall(model="openai/Qwen3-32B-AWQ", api_key="sk-test")
    ai.context_compaction_config = {
        "enabled": True,
        "nodes": ["evidence"],
        "max_context_window": 35000,
        "trigger_ratio": 0.01,
        "summary_max_tokens": 500,
    }
    ai._compact_context_with_lite_llm = lambda payload, **kwargs: {
        "process_summary": ["先输出计划，随后执行 describe。"],
        "evidence_plan": [{"id": "e1", "description": "describe pod"}],
        "completed_items": [{"id": "e1", "outcome": "positive"}],
        "open_items": [],
        "key_facts": ["Pod 异常"],
        "negative_facts": [],
        "conflicts": [],
        "discarded_noise": ["长思考已压缩"],
        "next_focus": ["停止重复 describe"],
    }

    plan_message = AIMessage(content=json.dumps({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "describe pod",
                "level": "critical",
                "tool": "kubectl_describe",
                "command": "kubectl describe pod p -n n",
                "purpose": "确认状态",
            }
        ],
        "collection_strategy": "先 describe。",
    }, ensure_ascii=False))
    noisy_message = AIMessage(content="后续长思考" + ("循环分析" * 2000))
    tool_message = ToolMessage(
        content=json.dumps({"success": True, "stdout": "registry probe\n" + ("network noise\n" * 500)}, ensure_ascii=False),
        tool_call_id="tc-1",
        name="run_bash_command",
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
            yield ("updates", {"agent": {"messages": [plan_message]}})
            yield ("updates", {"agent": {"messages": [noisy_message]}})
            yield ("updates", {"tools": {"messages": [tool_message]}})

    monkeypatch.setattr("langchain.agents.create_agent", lambda **kwargs: _Agent())
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "run_bash_command", "description": "run readonly shell", "args_schema": None})()
    _, events = ai.call(
        "s" * 2000,
        "u" * 2000,
        tools=[tool],
        node_id="evidence",
        run_id="run-compact-agent-context",
        max_steps=3,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "s" * 2000},
            {"name": "user_message", "category": "static_input", "content": "u" * 2000},
            {"name": "tool_schema", "category": "static_input", "content": "t" * 2000},
        ],
    )

    assert "evidence_plan" in plan_message.content
    assert noisy_message.content.startswith("[compacted ai_message:")
    assert tool_message.content.startswith("[compacted tool_result:")
    assert events[0]["type"] == "context_summary"
    assert any(ev.get("type") == "tool_result" for ev in events)


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


def test_observation_processor_includes_pod_lifecycle_structured_facts_in_yaml_summary(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw_yaml = """
apiVersion: v1
kind: Pod
metadata:
  name: terminating-stuck
  namespace: aiops-e2e
  creationTimestamp: "2026-04-29T06:54:19Z"
  deletionTimestamp: "2026-04-29T06:56:00Z"
  deletionGracePeriodSeconds: 0
  finalizers:
  - aiops.e2e/hold
  labels:
    pod_abnormal_type: TerminatingStuck
  annotations:
    aiops.e2e/runbook: pod-terminating-stuck.md
    kubectl.kubernetes.io/last-applied-configuration: "very noisy"
spec:
  nodeName: node1
  terminationGracePeriodSeconds: 30
  restartPolicy: Always
  containers:
  - name: app
    image: busybox:1.36
status:
  phase: Running
  conditions:
  - type: Ready
    status: "False"
    reason: ContainersNotReady
  containerStatuses:
  - name: app
    ready: false
    restartCount: 0
    state:
      terminated:
        exitCode: 137
        reason: Error
        startedAt: "2026-04-29T06:54:19Z"
        finishedAt: "2026-04-29T06:56:30Z"
"""

    processed = processor.process(
        run_id="run-pod-lifecycle",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content=raw_yaml,
    )

    structured = processed["structured"]
    summary = processed["summary"]

    assert structured["deletionTimestamp"] == "2026-04-29T06:56:00Z"
    assert structured["deletionGracePeriodSeconds"] == 0
    assert structured["finalizers"] == ["aiops.e2e/hold"]
    assert structured["labels"]["pod_abnormal_type"] == "TerminatingStuck"
    assert structured["diagnostic_annotations"] == {"aiops.e2e/runbook": "pod-terminating-stuck.md"}
    assert structured["terminationGracePeriodSeconds"] == 30
    assert structured["restartPolicy"] == "Always"
    assert structured["conditions"][0]["type"] == "Ready"
    assert "deletionTimestamp: 2026-04-29T06:56:00Z" in summary
    assert "finalizers: aiops.e2e/hold" in summary
    assert "deletionGracePeriodSeconds: 0" in summary
    assert "aiops.e2e/runbook=pod-terminating-stuck.md" in summary
    assert "conditions:" in summary


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


def test_observation_processor_preserves_describe_event_not_found_as_diagnostic_evidence(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = """Name:             volume-mount-failed
Namespace:        aiops-e2e
Status:           Pending
Containers:
  app:
    State:          Waiting
      Reason:       ContainerCreating
Events:
  Type     Reason       Age                  From               Message
  ----     ------       ----                 ----               -------
  Warning  FailedMount  68s (x45 over 76m)   kubelet            MountVolume.SetUp failed for volume "missing-config" : configmap "definitely-missing-configmap" not found
"""

    processed = processor.process(
        run_id="run-describe-diagnostic-notfound",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content=raw,
    )

    assert processed["processor"] == "k8s_describe"
    assert processed["structured"]["status"] != "command_failed"
    assert "关键诊断行" in processed["summary"]
    assert 'configmap "definitely-missing-configmap" not found' in processed["summary"]
    assert any("MountVolume.SetUp failed" in line for line in processed["structured"]["key_events"])


def test_observation_processor_preserves_kubectl_events_not_found_as_diagnostic_evidence(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = """LAST SEEN             TYPE      REASON        OBJECT                    MESSAGE
15m (x20 over 74m)    Warning   FailedMount   Pod/volume-mount-failed   Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-4nj8h]: timed out waiting for the condition
68s (x45 over 76m)    Warning   FailedMount   Pod/volume-mount-failed   MountVolume.SetUp failed for volume "missing-config" : configmap "definitely-missing-configmap" not found
"""

    processed = processor.process(
        run_id="run-events-diagnostic-notfound",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_events",
        raw_content=raw,
    )

    assert processed["processor"] == "k8s_events"
    assert processed["structured"]["status"] == "events_found"
    assert "关键诊断行" in processed["summary"]
    assert 'configmap "definitely-missing-configmap" not found' in processed["summary"]
    assert any("MountVolume.SetUp failed" in line for line in processed["structured"]["key_events"])


def test_observation_processor_logs_not_found_line_is_not_tool_failure(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-log-app-notfound",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_previous_logs",
        raw_content="ERROR failed to load config: /etc/app/config.yaml not found\n",
    )

    assert processed["processor"] == "k8s_logs"
    assert processed["structured"]["status"] == "logs_summarized"
    assert processed["semantic_success"] is True
    assert "config.yaml not found" in processed["summary"]


def test_observation_processor_marks_invalid_tool_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-invalid-tool",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_logs",
        raw_content="Error: kubectl_logs is not a valid tool, try one of [kubectl_describe, kubectl_get_yaml].",
    )

    assert processed["processor"] == "invalid_tool"
    assert processed["structured"]["status"] == "invalid_tool"
    assert processed["semantic_success"] is False
    assert "not a valid tool" in processed["summary"]


def test_observation_processor_marks_medium_empty_output_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-empty-medium",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_name",
        raw_content="No resources found in aiops-e2e namespace.",
    )

    assert processed["processor"] == "generic_empty"
    assert processed["structured"]["status"] == "empty"
    assert processed["semantic_success"] is False


def test_observation_processor_marks_medium_command_failure_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-failed-medium",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_name",
        raw_content='Command failed (exit 1):\nkubectl get customresource -n aiops-e2e\nerror: the server doesn\'t have a resource type "customresource"',
    )

    assert processed["processor"] == "generic_failure"
    assert processed["structured"]["status"] == "command_failed"
    assert processed["semantic_success"] is False


def test_observation_processor_does_not_mark_runbook_diagnostic_text_as_failure(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)
    raw = """<runbook>
# Pod ImagePullFailed / ImagePullBackOff

重点关注 Events 部分:
- `Failed to pull image "xxx"`: 具体镜像地址
- `manifest unknown/not found`: 镜像或 tag 不存在
- `i/o timeout`: 节点到镜像仓库访问失败
</runbook>
Note: the above runbook is for DIAGNOSTIC REFERENCE ONLY.
"""

    processed = processor.process(
        run_id="run-runbook-diagnostic-text",
        node_id="evidence",
        sequence=1,
        tool_name="fetch_runbook",
        raw_content=raw,
    )

    assert processed["processor"] == "runbook+passthrough_full"
    assert processed["structured"]["status"] == "runbook_loaded"
    assert processed["semantic_success"] is True
    assert "Failed to pull image" in processed["summary"]


def test_observation_processor_summarizes_aiops_case_without_label_leakage(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=3000)
    raw = json.dumps({
        "ok": True,
        "case_id": "oom-aiops-temp-aiops-oom-business",
        "abnormal_type": "oomkilled",
        "scenario": "oomkilled",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "aiops-temp",
            "name": "aiops-oom-business",
        },
        "coverage": {
            "kubernetes": "observed",
            "metrics": "observed",
            "logging": "observed",
            "tracing": "weak_context",
            "topology": "observed",
        },
        "signals_summary": [
            {
                "signal_id": "sig_status_oom",
                "dimension": "kubernetes",
                "strength": "critical",
                "observed": "Last terminated state: business-api=OOMKilled exit=137",
                "evidence_refs": [
                    "k8s.trace-oom-api.pod-yaml",
                    "k8s.trace-oom-api.last-terminated",
                ],
            },
            {
                "signal_id": "sig_logs_memory_growth",
                "dimension": "logging",
                "strength": "important",
                "observed": True,
                "evidence_refs": ["log.memory_growth"],
            },
        ],
        "timeline_summary": [
            {
                "timestamp": "2026-07-06T10:00:00Z",
                "dimension": "kubernetes",
                "summary": "container lastState terminated reason=OOMKilled exitCode=137",
                "evidence_refs": ["k8s.describe"],
            }
        ],
        "topology_summary": {
            "entity_count": 4,
            "edge_count": 3,
            "entity_kinds": {"Pod": 1, "Container": 1, "Node": 1, "Service": 1},
            "relations": {"runs_on": 1, "contains": 1, "selects": 1},
            "directness": {"direct": 2, "related_context": 1},
            "confidence": {"high": 2, "weak": 1},
        },
        "dimension_details": {
            "metrics": {
                "coverage": "present",
                "highlights": [
                    {
                        "metric": "container_memory_working_set_bytes",
                        "container": "business-api",
                        "start": "18.4Mi",
                        "max": "63.2Mi",
                        "last": "0.3Mi",
                        "limit": "64.0Mi",
                        "max_limit_ratio": 0.9875,
                        "samples": ["01:00:00=18.4Mi", "01:01:00=63.2Mi"],
                        "evidence_ref": "metric.memory_limit",
                    }
                ],
            },
            "logs": {
                "coverage": "present",
                "samples": [
                    {
                        "timestamp": "2026-07-06T10:00:00Z",
                        "message": "trace_id=abc123 allocated_mib=50",
                        "container": "business-api",
                        "evidence_ref": "log.memory_growth",
                    }
                ],
            },
            "tracing": {
                "coverage": "present",
                "flows": [
                    {
                        "timestamp": "2026-07-06T10:00:00Z",
                        "src": "10.244.0.20",
                        "dst": "10.244.0.10",
                        "protocol": "HTTP",
                        "request": "GET /allocate?mib=2",
                        "response_code": 200,
                        "duration_us": 1820,
                        "trace_id": "abc123",
                        "span_id": "span01",
                        "evidence_ref": "deepflow.flow",
                    }
                ],
                "spans": [
                    {
                        "trace_id": "abc123",
                        "service": "aiops-oom-business",
                        "name": "GET /allocate",
                        "start": "2026-07-06T10:00:00Z",
                        "end": "2026-07-06T10:00:00.001820Z",
                        "attributes": {"aiops.allocated_mib.after": 50},
                        "evidence_ref": "tempo.span",
                    }
                ],
                "call_chains": [],
            },
            "topology": {
                "coverage": "present",
                "entities": [
                    {"entity_id": "service:aiops-temp/oom", "kind": "Service", "name": "oom"}
                ],
                "edges": [
                    {
                        "relationship": "Service --selects--> Pod",
                        "source": "oom",
                        "target": "aiops-oom-business",
                        "directness": "direct",
                        "confidence": "high",
                        "evidence_refs": ["k8s.describe"],
                    }
                ],
            },
        },
        "evidence_inventory": [
            {"ref": "evidence/k8s_describe.txt", "exists": True, "records": 80},
            {"ref": "evidence/logs.jsonl", "exists": True, "records": 20},
        ],
        "evidence_refs": ["k8s.describe", "log.memory_growth", "metric.memory_limit"],
        "recommended_refs_by_dimension": {
            "k8s": ["k8s.describe"],
            "metrics": ["metric.memory_limit"],
            "tracing": ["deepflow.node_context"],
        },
        "package_ref": "/cases/oom-aiops-temp-aiops-oom-business",
        "root_cause": "OOMKilled label only for evaluator",
        "expected_remediation": "increase memory limit",
        "labels": {"root_cause": "oom"},
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-case",
        node_id="evidence",
        sequence=1,
        tool_name="collect_aiops_case",
        raw_content=raw,
    )

    assert processed["processor"] == "aiops_case"
    assert processed["semantic_success"] is True
    assert processed["structured"]["status"] == "case_collected"
    assert processed["structured"]["case_id"] == "oom-aiops-temp-aiops-oom-business"
    assert processed["structured"]["coverage"]["metrics"] == "observed"
    assert processed["structured"]["evidence_refs"] == [
        "k8s.describe",
        "log.memory_growth",
        "metric.memory_limit",
    ]
    assert processed["structured"]["recommended_refs_by_dimension"]["metrics"] == ["metric.memory_limit"]
    assert processed["structured"]["topology_summary"]["directness"]["related_context"] == 1
    assert processed["structured"]["topology_summary"]["confidence"]["weak"] == 1
    details = processed["structured"]["dimension_details"]
    assert details["metrics"]["highlights"][0]["max"] == "63.2Mi"
    assert details["logs"]["samples"][0]["message"] == "trace_id=abc123 allocated_mib=50"
    assert details["tracing"]["flows"][0]["request"] == "GET /allocate?mib=2"
    assert details["tracing"]["spans"][0]["attributes"]["aiops.allocated_mib.after"] == 50
    assert details["topology"]["edges"][0]["relationship"] == "Service --selects--> Pod"
    assert "collect_aiops_case 摘要" in processed["summary"]
    assert "aiops-temp/aiops-oom-business" in processed["summary"]
    assert "tracing=weak_context" in processed["summary"]
    assert (
        'K8S_SIGNAL strength=critical observed="Last terminated state: '
        'business-api=OOMKilled exit=137"'
    ) in processed["summary"]
    assert "k8s.trace-oom-api.last-terminated" in processed["summary"]
    assert "recommended_refs_by_dimension" in processed["summary"]
    assert "directness={'direct': 2, 'related_context': 1}" in processed["summary"]
    assert "k8s.describe" in processed["summary"]
    assert "63.2Mi" in processed["summary"]
    assert "allocated_mib=50" in processed["summary"]
    assert "GET /allocate?mib=2" in processed["summary"]
    assert "Service --selects--> Pod" in processed["summary"]
    assert len(processed["summary"]) <= processor.max_observation_chars
    assert "root_cause" not in processed["summary"]
    assert "expected_remediation" not in processed["summary"]


def test_aiops_case_uses_deterministic_summary_with_trace_and_topology_constraints(tmp_path):
    summarizer_calls = []

    def _lossy_summarizer(tool, raw, summary):
        summarizer_calls.append((tool, raw, summary))
        return "generic lossy summary"

    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=1800,
        summarizer=_lossy_summarizer,
        summary_mode="rule",
    )
    raw = json.dumps({
        "ok": True,
        "case_id": "auto-aiops-traced-oom-trace-oom-api-abc",
        "abnormal_type": "oomkilled",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "aiops-traced-oom",
            "name": "trace-oom-api-abc",
            "node": "node2",
            "pod_ip": "172.16.104.13",
        },
        "coverage": {
            "k8s": "present",
            "metrics": "present",
            "logs": "present",
            "tracing": "present",
            "trace": "present",
            "topology": "present",
        },
        "signals_summary": [
            {
                "signal_id": f"signal-{index}",
                "dimension": "logging",
                "strength": "important",
                "observed": True,
                "evidence_refs": [f"log-{index}"],
            }
            for index in range(12)
        ],
        "timeline_summary": [
            {
                "timestamp": f"2026-07-13T05:15:{index:02d}Z",
                "dimension": "logging",
                "summary": "memory allocation request observed " + ("x" * 100),
                "evidence_refs": [f"log-{index}"],
            }
            for index in range(12)
        ],
        "dimension_details": {
            "metrics": {
                "coverage": "present",
                "highlights": [{
                    "metric": "container_memory_working_set_bytes",
                    "container": "business-api",
                    "start": "3.6Mi",
                    "max": "77.0Mi",
                    "last": "77.0Mi",
                    "limit": "80.0Mi",
                    "max_limit_ratio": 0.9619,
                    "evidence_ref": "metric-memory",
                }],
            },
            "logs": {
                "coverage": "present",
                "samples": [{
                    "message": json.dumps({
                        "event": "allocate",
                        "trace_id": "a6725e70f3ba82f6097397a3dad5e444",
                        "path": "/allocate?mib=2&step=1267",
                        "allocated_mib": 62,
                    }),
                    "role": "target",
                    "evidence_ref": "log-target",
                }],
            },
            "tracing": {
                "coverage": "present",
                "deepflow_coverage": "present",
                "tempo_coverage": "present",
                "flows": [{
                    "src": "172.16.104.8",
                    "dst": "172.16.104.13",
                    "request": "GET /allocate?mib=2&step=1268",
                    "duration_us": "0",
                    "trace_id": "f715a43e716af7177105c5e793cbe5f6",
                    "evidence_ref": "deepflow-flow",
                }],
                "spans": [{
                    "trace_id": "a6725e70f3ba82f6097397a3dad5e444",
                    "service": "aiops-traced-oom-api",
                    "name": "GET /allocate",
                    "attributes": {
                        "aiops.allocated_mib.before": 60,
                        "aiops.allocated_mib.after": 62,
                    },
                    "evidence_ref": "tempo-span",
                }],
            },
            "topology": {
                "coverage": "present",
                "edges": [
                    {
                        "relationship": "Pod --calls--> Pod",
                        "source": "trace-oom-driver-xyz",
                        "target": "trace-oom-api-abc",
                        "directness": "direct",
                        "confidence": "high",
                    },
                    {
                        "relationship": "Service --selects--> Pod",
                        "source": "trace-oom-api",
                        "target": "trace-oom-api-abc",
                        "directness": "direct",
                        "confidence": "high",
                    },
                    {
                        "relationship": "Pod --owned_by--> ReplicaSet",
                        "source": "trace-oom-api-abc",
                        "target": "trace-oom-api-rs",
                        "directness": "direct",
                        "confidence": "high",
                    },
                    {
                        "relationship": "ReplicaSet --owned_by--> Deployment",
                        "source": "trace-oom-api-rs",
                        "target": "trace-oom-api",
                        "directness": "direct",
                        "confidence": "high",
                    },
                ],
            },
        },
        "recommended_refs_by_dimension": {
            "metrics": ["metric-memory"],
            "logs": ["log-target"],
            "tracing": ["deepflow-flow"],
            "trace": ["tempo-span"],
        },
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-deterministic-summary",
        node_id="evidence",
        sequence=1,
        tool_name="collect_aiops_case",
        raw_content=raw,
    )

    assert summarizer_calls == []
    assert processed["processor"] == "aiops_case"
    assert len(processed["summary"]) <= 1800
    assert processed["summary"].startswith(
        "AIOPS_CASE case_id=auto-aiops-traced-oom-trace-oom-api-abc"
    )
    assert "TRACE_CORRELATION" in processed["summary"]
    assert "log_tempo_trace_id=a6725e70f3ba82f6097397a3dad5e444" in processed["summary"]
    assert "deepflow_trace_id=f715a43e716af7177105c5e793cbe5f6" in processed["summary"]
    assert "do_not_merge=true" in processed["summary"]
    assert "duration_us=0 is_not_failure_evidence=true" in processed["summary"]
    assert "MEMORY_PATTERN" not in processed["summary"]
    assert 'relationship="Pod --calls--> Pod"' in processed["summary"]
    assert 'relationship="Service --selects--> Pod"' in processed["summary"]
    assert 'relationship="Pod --owned_by--> ReplicaSet"' in processed["summary"]
    assert 'relationship="ReplicaSet --owned_by--> Deployment"' in processed["summary"]
    assert (
        "DIMENSION_DETAILS complete=true "
        "action=post_case_reconciliation"
    ) in processed["summary"]
    assert "do_not_guess_evidence_refs=true" in processed["summary"]


def test_aiops_case_summary_reserves_budget_for_recommended_refs_after_core_topology(tmp_path):
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=3000,
        summary_mode="rule",
    )
    trace_id = "4dc7a082a2043f2dcedfbb5a0de47718"
    pod = "trace-config-api-84bc7cb976-vgtl8"
    structured = {
        "status": "case_collected",
        "tool": "collect_aiops_case",
        "case_id": f"auto-aiops-traced-config-{pod}",
        "abnormal_type": "crashloopbackoff",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "aiops-traced-config",
            "name": pod,
            "node": "node2",
            "pod_ip": "172.16.104.2",
        },
        "coverage": {
            "k8s": "present",
            "metrics": "present",
            "logs": "present",
            "tracing": "present",
            "trace": "present",
            "caller_logs": "present",
            "topology": "present",
        },
        "signals_summary": [{
            "dimension": "k8s",
            "strength": "strong",
            "observed": "Last terminated state: business-api=Error exit=78",
            "evidence_refs": [
                f"k8s-aiops-traced-config-{pod}-{suffix}"
                for suffix in (
                    "pod-yaml",
                    "last-terminated",
                    "events",
                    "current",
                    "previous",
                )
            ],
        }],
        "dimension_details": {
            "metrics": {
                "highlights": [{
                    "metric": "container_memory_working_set_bytes",
                    "start": "3.7Mi",
                    "max": "3.7Mi",
                    "last": "3.7Mi",
                    "limit": "96.0Mi",
                    "max_limit_ratio": 0.0381,
                }],
            },
            "logs": {
                "samples": [{
                    "message": json.dumps({
                        "event": "config_missing",
                        "trace_id": trace_id,
                        "path": "/checkout?order_id=order-58973",
                        "error_code": "CONFIG_MISSING",
                        "missing_config": "PAYMENT_GATEWAY_TOKEN",
                        "http_status": 500,
                    }),
                }],
            },
            "tracing": {
                "flows": [{
                    "src": "172.16.104.56",
                    "dst": "172.16.104.2",
                    "request": "GET /checkout?order_id=order-58973",
                    "response_code": 500,
                    "duration_us": 5010,
                    "trace_id": trace_id,
                }],
                "spans": [{
                    "trace_id": trace_id,
                    "service": "aiops-traced-config-api",
                    "name": "GET /checkout",
                    "attributes": {
                        "http.response.status_code": 500,
                        "error.type": "CONFIG_MISSING",
                        "config.key": "PAYMENT_GATEWAY_TOKEN",
                        "config.present": False,
                    },
                }],
            },
            "topology": {
                "edges": [
                    {
                        "relationship": relationship,
                        "source": source,
                        "target": target,
                        "directness": "direct",
                        "confidence": "high",
                    }
                    for relationship, source, target in (
                        (
                            "Pod --calls--> Pod",
                            "trace-config-driver-59fd97ff89-jh8t6",
                            pod,
                        ),
                        ("Service --selects--> Pod", "trace-config-api", pod),
                        (
                            "Pod --owned_by--> ReplicaSet",
                            pod,
                            "trace-config-api-84bc7cb976",
                        ),
                        (
                            "ReplicaSet --owned_by--> Deployment",
                            "trace-config-api-84bc7cb976",
                            "trace-config-api",
                        ),
                        ("Evidence --observes--> Pod", "prometheus-metrics", pod),
                    )
                ],
            },
        },
        "topology_summary": {
            "directness": {"direct": 10, "related_context": 2},
            "confidence": {"high": 8, "medium": 2, "weak": 2},
        },
        "recommended_refs_by_dimension": {
            "k8s": [f"k8s-aiops-traced-config-{pod}-pod-yaml"],
            "metrics": [f"metric-aiops-traced-config-{pod}-prometheus"],
            "logs": [f"log-aiops-traced-config-{pod}-elasticsearch"],
            "tracing": [f"deepflow-aiops-traced-config-{pod}-pod-ip-flow"],
            "trace": [f"tempo-aiops-traced-config-{pod}-spans"],
            "caller_logs": [f"caller-log-aiops-traced-config-{pod}-driver"],
        },
    }

    summary = processor._build_aiops_case_prompt_summary(structured)

    assert len(summary) <= 3000
    assert 'relationship="ReplicaSet --owned_by--> Deployment"' in summary
    assert "recommended_refs_by_dimension=" in summary
    assert f"metric-aiops-traced-config-{pod}-prometheus" in summary


def test_aiops_case_summary_preserves_generic_log_and_trace_error_fields(tmp_path):
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=3000,
        summary_mode="rule",
    )
    raw = json.dumps({
        "ok": True,
        "case_id": "auto-config-crashloop",
        "abnormal_type": "crashloopbackoff",
        "coverage": {
            "k8s": "present",
            "metrics": "present",
            "logs": "present",
            "tracing": "present",
            "trace": "present",
            "topology": "present",
        },
        "dimension_details": {
            "metrics": {"coverage": "present", "highlights": []},
            "logs": {
                "coverage": "present",
                "samples": [{
                    "message": json.dumps({
                        "event": "config_missing",
                        "error_code": "CONFIG_MISSING",
                        "missing_config": "PAYMENT_GATEWAY_TOKEN",
                        "http_status": 500,
                        "exit_code": 78,
                        "trace_id": "trace-config-1",
                        "path": "/checkout",
                    }),
                    "role": "target",
                    "evidence_ref": "log-config",
                }],
            },
            "tracing": {
                "coverage": "present",
                "flows": [],
                "spans": [{
                    "trace_id": "trace-config-1",
                    "service": "config-api",
                    "name": "GET /checkout",
                    "attributes": {
                        "http.response.status_code": 500,
                        "error.type": "CONFIG_MISSING",
                        "config.key": "PAYMENT_GATEWAY_TOKEN",
                        "config.present": False,
                    },
                    "evidence_ref": "tempo-config",
                }],
            },
            "topology": {"coverage": "present", "edges": []},
        },
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-config-crashloop",
        node_id="evidence",
        sequence=1,
        tool_name="collect_aiops_case",
        raw_content=raw,
    )

    summary = processed["summary"]
    assert "event=config_missing" in summary
    assert "error_code=CONFIG_MISSING" in summary
    assert "missing_config=PAYMENT_GATEWAY_TOKEN" in summary
    assert "http_status=500" in summary
    assert "exit_code=78" in summary
    assert "http.response.status_code=500" in summary
    assert "error.type=CONFIG_MISSING" in summary
    assert "config.key=PAYMENT_GATEWAY_TOKEN" in summary
    assert "config.present=false" in summary
    assert "MEMORY_PATTERN" not in summary


def test_aiops_case_summary_marks_fully_mismatched_trace_sources_non_mergeable(tmp_path):
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=3000,
        summary_mode="rule",
    )

    summary = processor._build_aiops_case_prompt_summary({
        "status": "case_collected",
        "tool": "collect_aiops_case",
        "case_id": "trace-mismatch",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "ns",
            "name": "pod-a",
        },
        "coverage": {
            "k8s": "present",
            "metrics": "present",
            "logs": "present",
            "tracing": "present",
            "topology": "present",
        },
        "dimension_details": {
            "logs": {
                "samples": [
                    {
                        "message": json.dumps({
                            "trace_id": "log-trace",
                            "path": "/allocate?step=2",
                        })
                    }
                ]
            },
            "tracing": {
                "flows": [
                    {
                        "trace_id": "network-trace",
                        "request": "GET /allocate?step=1",
                    }
                ],
                "spans": [
                    {
                        "trace_id": "network-trace",
                        "name": "GET /allocate",
                    }
                ],
            },
        },
    })

    assert "log_tempo_trace_id=-" in summary
    assert "deepflow_trace_id=network-trace" in summary
    assert "do_not_merge=true" in summary


def test_observation_processor_preserves_aiops_evidence_strength_fields(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = json.dumps({
        "ok": True,
        "case_id": "oom-aiops-temp-aiops-oom-business",
        "ref": "deepflow.node_context",
        "truncated": False,
        "record": {
            "evidence_id": "deepflow.node_context",
            "timestamp": "2026-07-08T05:00:00Z",
            "source_system": "deepflow",
            "dimension": "tracing",
            "summary": "node-level related flow only",
            "severity": "info",
            "confidence": "weak",
            "directness": "related_context",
            "trace_correlation": {"pod_ip": "10.244.0.10", "trace_ids": []},
            "payload": {
                "samples": [
                    {
                        "timestamp": "2026-07-08T05:00:00Z",
                        "src": "10.244.0.20",
                        "dst": "10.244.0.10",
                        "protocol": "HTTP",
                        "request": "GET /allocate?mib=2",
                        "response_code": 200,
                        "duration_us": 1820,
                        "trace_id": "abc123",
                        "span_id": "span01",
                    }
                ],
                "large": "not selected",
                "root_cause": "must not leak",
            },
        },
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-case-evidence",
        node_id="evidence",
        sequence=1,
        tool_name="get_aiops_case_evidence",
        raw_content=raw,
    )

    record = processed["structured"]["record"]
    assert record["confidence"] == "weak"
    assert record["directness"] == "related_context"
    assert record["trace_correlation"]["pod_ip"] == "10.244.0.10"
    assert record["payload"]["samples"][0]["request"] == "GET /allocate?mib=2"
    assert record["payload"]["samples"][0]["trace_id"] == "abc123"
    assert "large" not in record["payload"]
    assert "root_cause" not in record["payload"]
    assert "GET /allocate?mib=2" in processed["summary"]
    assert "labels" not in processed["structured"]


def test_observation_processor_does_not_inline_aiops_case_evaluator_file_content(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = json.dumps({
        "ok": True,
        "case_id": "oom-aiops-temp-aiops-oom-business",
        "ref": "labels.yaml",
        "truncated": False,
        "content": (
            "root_cause: OOMKilled\n"
            "expected_remediation: increase memory limit\n"
            "labels:\n"
            "  pod_abnormal_type: OOMKilled\n"
        ),
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-case-label-file",
        node_id="evidence",
        sequence=1,
        tool_name="get_aiops_case_evidence",
        raw_content=raw,
    )

    assert processed["processor"] == "aiops_case"
    assert processed["semantic_success"] is True
    assert processed["structured"]["status"] == "case_evidence_loaded"
    assert processed["structured"]["ref"] == "labels.yaml"
    assert processed["structured"]["content_chars"] > 0
    assert "labels.yaml" in processed["summary"]
    assert "content_chars=" in processed["summary"]
    assert "root_cause" not in processed["summary"]
    assert "expected_remediation" not in processed["summary"]
    assert "pod_abnormal_type" not in processed["summary"]
    assert "content" not in processed["structured"]


def test_observation_processor_summarizes_kubectl_logs(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-logs",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_previous_logs",
        raw_content="\n".join([
            "2026-04-30T01:00:00Z INFO startup ok",
            "2026-04-30T01:00:01Z ERROR failed to load config key DB_URL",
            "2026-04-30T01:00:02Z Traceback most recent call last",
        ]),
    )

    assert processed["processor"] == "k8s_logs"
    assert processed["structured"]["status"] == "logs_summarized"
    assert processed["structured"]["signal_count"] == 2
    assert "failed to load config" in processed["summary"]
    assert processed["semantic_success"] is True


def test_observation_processor_table_marks_terminating_and_image_pull_as_abnormal(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE     NAME                    READY   STATUS             RESTARTS   AGE
aaa           test1-redis-master-0    0/1     ImagePullBackOff   0          24h
aaa           test1-redis-slave-0     0/1     ErrImagePull       0          24h
aiops-e2e     terminating-stuck       0/1     Terminating        0          7d18h
aiops         aiops-copilot-abc       1/1     Running            0          15h
"""

    processed = processor.process(
        run_id="run-table-terminating",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["status"] == "table_summarized"
    assert processed["structured"]["abnormal_count"] == 3
    assert processed["structured"]["status_counts"]["ImagePullBackOff"] == 1
    assert processed["structured"]["status_counts"]["ErrImagePull"] == 1
    assert processed["structured"]["status_counts"]["Terminating"] == 1
    assert any("terminating-stuck" in row for row in processed["structured"]["selected_rows"])


def test_observation_processor_table_filters_running_and_completed_from_status_column(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE     NAME                                      READY   STATUS             RESTARTS       AGE
xnet          observability-kepler-8fhp6                1/1     Running            10 (24h ago)   9d
xnet          observability-kibana-65d7c45f6d-7zc9l     0/1     Completed          0              12d
aaa           test1-redis-master-0                      0/1     ImagePullBackOff   0              24h
aiops-e2e     terminating-stuck                         0/1     Terminating        0              7d18h
"""

    processed = processor.process(
        run_id="run-table-status-filter",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 2
    selected_rows = processed["structured"]["selected_rows"]
    assert any("test1-redis-master-0" in row for row in selected_rows)
    assert any("terminating-stuck" in row for row in selected_rows)
    assert all("observability-kepler-8fhp6" not in row for row in selected_rows)
    assert all("observability-kibana-65d7c45f6d-7zc9l" not in row for row in selected_rows)


def test_observation_processor_table_selects_running_pod_with_recent_restart(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE          NAME                         READY   STATUS    RESTARTS          AGE
aiops-traced-oom   trace-oom-api-598dcf-x6v6n   1/1     Running   234 (5m23s ago)   5d
xnet               stable-api-5d7c8             1/1     Running   0                 12d
"""

    processed = processor.process(
        run_id="run-table-recent-restart",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    structured = processed["structured"]
    assert structured["abnormal_count"] == 1
    assert structured["recent_restart_count"] == 1
    assert structured["recent_restart_rows"] == [
        "aiops-traced-oom   trace-oom-api-598dcf-x6v6n   1/1     Running   234 (5m23s ago)   5d"
    ]
    assert structured["selected_rows"] == structured["recent_restart_rows"]


def test_observation_processor_table_keeps_old_running_restart_as_normal(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE   NAME                    READY   STATUS    RESTARTS       AGE
xnet        observability-kepler    1/1     Running   1 (69d ago)    90d
"""

    processed = processor.process(
        run_id="run-table-old-restart",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 0
    assert processed["structured"]["recent_restart_count"] == 0
    assert processed["structured"]["recent_restart_rows"] == []


def test_observation_processor_table_keeps_zero_restart_running_pod_normal(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE   NAME          READY   STATUS    RESTARTS   AGE
xnet        stable-api    1/1     Running   0          12d
"""

    processed = processor.process(
        run_id="run-table-zero-restart",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 0
    assert processed["structured"]["recent_restart_count"] == 0
    assert processed["structured"]["recent_restart_rows"] == []


def test_observation_processor_table_treats_ready_bound_and_active_as_normal(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAME        STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP
master      Ready    control-plane   223d   v1.26.8   10.2.0.48     <none>
node1       Ready    <none>          223d   v1.26.8   10.2.0.49     <none>
"""

    processed = processor.process(
        run_id="run-table-ready-normal",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 0
    assert "# 样例行" in processed["summary"]
    assert "# 异常行" not in processed["summary"]

    pvc_raw = """NAME        STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-0      Bound    pvc-1    8Gi        RWO            nfs-storage    20d
data-1      Bound    pvc-2    8Gi        RWO            nfs-storage    20d
"""
    pvc_processed = processor.process(
        run_id="run-table-bound-normal",
        node_id="evidence",
        sequence=2,
        tool_name="kubectl_get_by_kind_in_namespace",
        raw_content=pvc_raw,
    )

    assert pvc_processed["structured"]["abnormal_count"] == 0
    assert "# 样例行" in pvc_processed["summary"]

    namespace_raw = """NAME      STATUS   AGE
default   Active   223d
kube      Active   223d
"""
    namespace_processed = processor.process(
        run_id="run-table-active-normal",
        node_id="evidence",
        sequence=3,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=namespace_raw,
    )

    assert namespace_processed["structured"]["abnormal_count"] == 0
    assert "# 样例行" in namespace_processed["summary"]
