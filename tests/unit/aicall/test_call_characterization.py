"""Characterization tests for ``AICall.call`` agent-stream consumption.

A scripted fake ``agent.astream`` feeds a fixed sequence of ``messages`` and
``updates`` chunks (tokens, tool calls, replayed updates, structured output,
runtime compaction, early exits).  The full ``thinking_events`` list, the
stream-queue payloads and the ``AICallResult`` fields are compared against a
golden snapshot so refactors of ``call`` cannot silently change ordering or
payloads.

Regenerate the snapshot only for intentional behavior changes::

    UPDATE_AICALL_GOLDEN=1 python -m pytest tests/unit/aicall/test_call_characterization.py
"""

import json
import logging
import os
import queue
import threading
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from pydantic import BaseModel

from app.core.aicall.client import AICall

GOLDEN_PATH = Path(__file__).parent / "golden" / "call_characterization.json"
_VOLATILE_KEYS = {"timestamp", "duration_ms", "model_duration_ms", "elapsed_ms"}


class _Verdict(BaseModel):
    status: str
    reason: str


class _Tool:
    def __init__(self, name: str):
        self.name = name
        self.description = f"{name} tool"
        self.args_schema = None


def _ai(content="", tool_calls=None, usage=None, msg_id=None):
    kwargs: Dict[str, Any] = {"content": content, "tool_calls": tool_calls or []}
    if usage:
        kwargs["usage_metadata"] = usage
    if msg_id:
        kwargs["id"] = msg_id
    return AIMessage(**kwargs)


def _tool_msg(content, name, call_id, status="success"):
    return ToolMessage(content=content, name=name, tool_call_id=call_id, status=status)


def _rich_script():
    usage = {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}
    first_ai = _ai(
        "Checking pods.",
        tool_calls=[{"id": "c1", "name": "kubectl_get", "args": {"ns": "demo"}}],
        usage=usage,
        msg_id="ai-1",
    )
    tool_1 = _tool_msg("NAME STATUS\napi Running\n" * 3, "kubectl_get", "c1")
    second_ai = _ai(
        "",
        tool_calls=[
            {"id": "c2", "name": "kubectl_logs", "args": {"pod": "api"}},
            {"id": "s1", "name": "_Verdict", "args": {"status": "ok", "reason": "fine"}},
        ],
        msg_id="ai-2",
    )
    tool_2 = _tool_msg("error: connection refused", "kubectl_logs", "c2", status="error")
    structured_tool = _tool_msg("结构化结果已生成。", "_Verdict", "s1")
    return [
        42,  # unknown chunk type is ignored
        ("messages", (AIMessageChunk(content="Check"), {"langgraph_node": "model"})),
        {"type": "messages", "data": (AIMessageChunk(content="ing"), {"langgraph_node": "model"})},
        ("messages", (AIMessageChunk(content="tool-noise"), {"langgraph_node": "tools"})),
        ("messages", (AIMessageChunk(content="hidden"), {"aiops_internal_compaction": True})),
        ("messages", "malformed"),
        ("updates", {"before_model": None, "model": {"messages": [first_ai]}}),
        # replayed update: same tool call signature and no new content -> ignored
        ("updates", {"model": {"messages": [_ai("", tool_calls=list(first_ai.tool_calls))]}}),
        ("updates", {"tools": {"messages": [tool_1]}}),
        # replayed tool result -> ignored
        ("updates", {"tools": {"messages": [_tool_msg(tool_1.content, "kubectl_get", "c1")]}}),
        ("updates", {"model": {"messages": [second_ai]}}),
        ("updates", {"tools": {"messages": [tool_2, structured_tool]}}),
        (
            "updates",
            {
                "model": {
                    "messages": [_ai("Final answer: api is healthy.")],
                    "structured_response": _Verdict(status="ok", reason="fine"),
                }
            },
        ),
        ("custom", {"ignored": True}),
    ]


class _ScriptedAgent:
    def __init__(self, script, hook=None):
        self.script = script
        self.hook = hook
        self.calls: List[Dict[str, Any]] = []

    async def astream(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        for index, chunk in enumerate(self.script):
            if self.hook:
                self.hook(index)
            yield chunk


def _normalize(value, tmp_root: str):
    if isinstance(value, dict):
        return {
            k: ("<volatile>" if k in _VOLATILE_KEYS else _normalize(v, tmp_root))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(v, tmp_root) for v in value]
    if isinstance(value, str):
        return value.replace(tmp_root, "<tmp>")
    if isinstance(value, BaseModel):
        return value.model_dump()
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return str(value)


def _drain(q: queue.Queue):
    items = []
    while not q.empty():
        items.append(q.get_nowait())
    return items


@pytest.fixture
def harness(monkeypatch, tmp_path):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path / "archives"))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "128000")
    monkeypatch.setattr("app.core.aicall.client.ChatOpenAI", lambda **kw: MagicMock())

    state: Dict[str, Any] = {"agent": None, "create_kwargs": None}

    def _create_agent(**kwargs):
        state["create_kwargs"] = kwargs
        return state["agent"]

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)

    def run(name, script, *, hook=None, compaction=None, **call_kwargs):
        ai = AICall(model="openai/test-model", api_key="sk-test")
        trace: List[Any] = []
        if compaction is not None:

            def _fake_compact(**kwargs):
                trace.append(
                    ("maybe_compact", kwargs["node_id"], len(kwargs["tool_observation_contents"]))
                )
                return compaction(kwargs)

            ai._maybe_compact_runtime_context = _fake_compact
            ai._compact_langgraph_ai_messages_in_place = lambda msgs: trace.append(
                ("compact_ai", len(msgs))
            )
            ai._compact_langgraph_tool_messages_in_place = lambda msgs: trace.append(
                ("compact_tool", len(msgs))
            )
        final_budget: Dict[str, Any] = {}
        ai._write_final_context_budget = lambda **kw: final_budget.update(kw)
        state["agent"] = _ScriptedAgent(script, hook)
        log_records: List[logging.LogRecord] = []
        handler = logging.Handler(level=logging.DEBUG)
        handler.emit = log_records.append
        client_logger = logging.getLogger("app.core.aicall.client")
        previous_level = client_logger.level
        client_logger.addHandler(handler)
        client_logger.setLevel(logging.DEBUG)
        q: queue.Queue = queue.Queue()
        # A fixed run_id keeps archive paths deterministic (no adhoc-<time>).
        call_kwargs.setdefault("run_id", f"run-{name}")
        result, events = ai.call(
            "system prompt",
            "is api healthy?",
            tools=[_Tool("kubectl_get"), _Tool("kubectl_logs")],
            stream_queue=q,
            node_id="evidence",
            **call_kwargs,
        )
        client_logger.removeHandler(handler)
        client_logger.setLevel(previous_level)
        assert result.intermediate_events is events
        agent_kwargs = state["agent"].calls[0]["kwargs"] if state["agent"].calls else {}
        snapshot = {
            "events": events,
            "queue": _drain(q),
            "result": {
                "result": result.result,
                "tool_calls": result.tool_calls,
                "iterations": result.iterations,
                "tool_call_count": result.tool_call_count,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "structured_response": result.structured_response,
            },
            "astream_kwargs": {
                "config_recursion_limit": agent_kwargs.get("config", {}).get("recursion_limit"),
                "stream_mode": agent_kwargs.get("stream_mode"),
                "version": agent_kwargs.get("version"),
            },
            "create_agent_keys": sorted((state["create_kwargs"] or {}).keys()),
            "final_budget": {
                k: final_budget.get(k) for k in ("run_id", "node_id", "final_content")
            }
            if final_budget
            else None,
            "trace": trace,
            # Message templates (not args: those include wall-clock timings).
            "logs": [(r.levelname, r.msg) for r in log_records],
        }
        return _normalize(snapshot, str(tmp_path))

    return run


def _scenarios(run):
    out = {}
    out["rich_stream"] = run(
        "rich_stream",
        _rich_script(),
        run_id="run-char",
        max_steps=8,
        response_schema=_Verdict,
        tool_result_sequence_start=3,
        compaction=lambda kw: True,
    )

    json_script = [
        ("updates", {"model": {"messages": [_ai('{"status": "draft"}')]}}),
        ("updates", {"model": {"messages": [_ai("not json at all")]}}),
        ("updates", {"model": {"messages": [_ai('```json\n{"status": "final"}\n```')]}}),
        ("updates", {"model": {"messages": [_ai("never reached")]}}),
    ]
    out["expect_json_guard"] = run(
        "expect_json_guard",
        json_script,
        run_id="run-json",
        max_steps=4,
        expect_json=True,
        json_validator=lambda parsed: "status" in parsed,
        json_acceptance_guard=lambda parsed, events: parsed.get("status") == "final",
    )

    stop_script = [
        (
            "updates",
            {
                "model": {
                    "messages": [
                        _ai("", tool_calls=[{"id": "c1", "name": "kubectl_get", "args": {}}])
                    ]
                }
            },
        ),
        ("updates", {"tools": {"messages": [_tool_msg("pods ok", "kubectl_get", "c1")]}}),
        ("updates", {"model": {"messages": [_ai("never reached")]}}),
    ]
    out["stop_checker"] = run(
        "stop_checker",
        stop_script,
        max_steps=4,
        stop_checker=lambda events: any(e.get("type") == "tool_result" for e in events),
    )

    def _boom(events):
        raise RuntimeError("checker broke")

    out["stop_checker_error"] = run(
        "stop_checker_error",
        stop_script[:1] + [("updates", {"model": {"messages": [_ai("final words")]}})],
        max_steps=4,
        stop_checker=_boom,
    )

    cancel = threading.Event()

    def _cancel_hook(index):
        if index == 2:
            cancel.set()

    out["cancel_mid_stream"] = run(
        "cancel_mid_stream",
        [
            ("messages", (AIMessageChunk(content="tok"), {"langgraph_node": "model"})),
            ("updates", {"model": {"messages": [_ai("partial")]}}),
            ("updates", {"model": {"messages": [_ai("after cancel")]}}),
            ("updates", {"model": {"messages": [_ai("never")]}}),
        ],
        hook=_cancel_hook,
        cancel_event=cancel,
        max_steps=4,
    )

    class _ExplodingScript(list):
        def __iter__(self):
            yield ("updates", {"model": {"messages": [_ai("before failure")]}})
            raise ValueError("stream exploded")

    out["stream_exception"] = run(
        "stream_exception",
        _ExplodingScript(),
        max_steps=4,
    )
    return out


def test_call_stream_characterization(harness):
    actual = json.loads(json.dumps(_scenarios(harness), ensure_ascii=False, default=str))
    if os.getenv("UPDATE_AICALL_GOLDEN"):
        GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_PATH.write_text(
            json.dumps(actual, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    expected = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert sorted(actual) == sorted(expected)
    for name in expected:
        assert actual[name] == expected[name], name


def test_call_timeout_reports_agent_timeout(monkeypatch, tmp_path):
    import asyncio

    import app.core.aicall.client as client_module
    from app.core import async_bridge

    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path / "archives"))
    monkeypatch.setattr(client_module, "ChatOpenAI", lambda **kw: MagicMock())
    seen: Dict[str, Any] = {}

    def _bounded_run(factory, *, timeout=None, worker_context=None, thread_name=""):
        seen.update(
            timeout=timeout,
            thread_name=thread_name,
            has_worker_context=callable(worker_context),
        )
        return async_bridge.run_coroutine_sync(
            factory,
            timeout=0.2,
            worker_context=worker_context,
            thread_name=thread_name,
        )

    monkeypatch.setattr(client_module, "run_coroutine_sync", _bounded_run)

    class _SlowAgent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"model": {"messages": [_ai("still working")]}})
            await asyncio.sleep(30)

    monkeypatch.setattr("langchain.agents.create_agent", lambda **kw: _SlowAgent())
    ai = AICall(model="openai/test-model", api_key="sk-test")
    q: queue.Queue = queue.Queue()
    result, events = ai.call(
        "sys",
        "q",
        tools=[_Tool("kubectl_get")],
        max_steps=3,
        stream_queue=q,
        node_id="evidence",
    )
    assert seen == {"timeout": 90, "thread_name": "aicall-agent", "has_worker_context": True}
    assert [(e["type"], e.get("reason")) for e in events] == [
        ("ai_message", None),
        ("execution_incomplete", "agent_timeout"),
    ]
    assert result.result == "still working"
    assert result.iterations == 1
    assert [item[1]["type"] for item in _drain(q)] == ["ai_message", "execution_incomplete"]
