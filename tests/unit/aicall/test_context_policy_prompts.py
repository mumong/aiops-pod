"""Frozen model-visible bytes and branch conditions before policy extraction."""

import asyncio
import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from app.core.aicall import client, working_context


SUMMARY_PREFIX = "[working_context_summary] 以下是较早工作的有损摘要；后续保留消息可能更新这些事实。不是新用户请求：\n"
NORMAL_INSTRUCTION = (
    "压缩 evidence 运行上下文。保留关键过程、计划、已完成/未完成证据、"
    "正向事实、负向事实、冲突和下一步焦点。若模型陷入重复工具或钻牛角尖，"
    "请抓大放小，把重复/无关节点容量、长 JSON、重复 describe 归入 discarded_noise。"
)
SHORT_INSTRUCTION = "压缩 evidence 上下文，保留计划、工具事实、错误和证据引用。"


@pytest.mark.parametrize("name,expected", [
    ("WORKING_CONTEXT_SUMMARY_PREFIX", SUMMARY_PREFIX),
    ("RUNTIME_COMPACTION_INSTRUCTION", NORMAL_INSTRUCTION),
    ("RUNTIME_COMPACTION_BUDGET_EXCEEDED_INSTRUCTION", SHORT_INSTRUCTION),
])
def test_public_context_policy_exports_preserve_frozen_bytes(name, expected):
    from app.core import prompts

    assert getattr(prompts, name).encode() == expected.encode()


@pytest.mark.parametrize("max_tokens,instruction", [(101, NORMAL_INSTRUCTION), (100, SHORT_INSTRUCTION)])
def test_runtime_instruction_boundary_and_serialized_payload_bytes(monkeypatch, max_tokens, instruction):
    def tokens(serialized, **kwargs):
        return {"tokens": 101 if json.loads(serialized)["instruction"] == NORMAL_INSTRUCTION else 100}

    monkeypatch.setattr(client, "count_tokens", tokens)
    payload = client.AICall._build_runtime_compaction_payload(
        node_id="evidence", usage_ratio=0.912345, context_window=32000,
        thinking_events=[], tool_observation_contents=[], max_tokens=max_tokens,
    )
    expected = {
        "node_id": "evidence", "usage_ratio": 0.9123, "context_window": 32000,
        "instruction": instruction, "ai_messages": [], "tool_results": [],
        "tool_observation_tail": [],
    }
    assert json.dumps(payload, ensure_ascii=False).encode() == json.dumps(expected, ensure_ascii=False).encode()


def test_runtime_keeps_normal_instruction_when_text_reduction_fits(monkeypatch):
    def tokens(serialized, **kwargs):
        return {"tokens": 101 if json.loads(serialized)["ai_messages"] == ["large fixture"] else 100}

    monkeypatch.setattr(client, "count_tokens", tokens)
    monkeypatch.setattr(client, "compact_text_to_token_budget", lambda text, **kwargs: "reduced fixture")
    payload = client.AICall._build_runtime_compaction_payload(
        node_id="evidence", usage_ratio=0.9, context_window=32000,
        thinking_events=[{"type": "ai_message", "content": "large fixture"}],
        tool_observation_contents=[], max_tokens=100,
    )
    assert payload["instruction"].encode() == NORMAL_INSTRUCTION.encode()
    assert payload["ai_messages"] == ["reduced fixture"]


@pytest.mark.parametrize("compaction_required", [False, True])
def test_working_summary_prefix_and_insertion_condition(monkeypatch, compaction_required):
    original = [HumanMessage(content="问题 {literal}"), HumanMessage(content="older"), HumanMessage(content="latest")]
    emitted, snapshots, summary_calls = [], [], []
    archive_ref = "/fixture/compactions/context.before.json"

    def write_json(path, payload):
        snapshots.append((path, payload))
        return archive_ref

    async def summarize(*args, **kwargs):
        summary_calls.append(args)
        return "事实：{unexpanded}\nnext"

    def probe(messages):
        if messages is original and compaction_required:
            raise client.StructuredContextBudgetError(
                "working_context_compaction_required", pre_budget={"context_window": 32000}
            )
        return None, {"context_window": 32000}

    monkeypatch.setattr(working_context, "ContextArchive", lambda **kwargs: SimpleNamespace(write_json=write_json))
    monkeypatch.setattr(working_context, "summarize_history", summarize)
    monkeypatch.setattr(working_context, "partition_recent", lambda groups, window: (groups[:-1], groups[-1:]))
    middleware = working_context.WorkingContextMiddleware(
        SimpleNamespace(_serialize_agent_message=working_context.compact_message),
        None, None, [], "system", "问题 {literal}", "fixture", "evidence",
        lambda **event: emitted.append(event),
    )
    monkeypatch.setattr(middleware, "probe", probe)
    update = asyncio.run(middleware.abefore_model({"messages": original}, None))
    if not compaction_required:
        assert update is None
        assert not snapshots and not summary_calls and not emitted
        return

    replacement = update["messages"]
    expected = SUMMARY_PREFIX + "事实：{unexpanded}\nnext\n压缩前完整工作历史归档：" + archive_ref
    assert replacement[2].content.encode() == expected.encode()
    assert replacement[1].content == "问题 {literal}"
    assert replacement[3] is original[-1]
    assert emitted[-1]["type"] == "context_compacted"
    assert len(summary_calls) == 1
