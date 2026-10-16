"""A round made only of repeated calls ends the loop (IdleRoundReached)."""

import asyncio

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from app.core.aicall.client import AICall
from app.core.aicall.errors import IdleRoundReached
from app.core.aicall.guards import AgentGuards


class _Request:
    def __init__(self, call_id, args, turn_ids):
        self.tool_call = {"id": call_id, "name": "query_pod_lifecycle", "args": args}
        self.messages = []
        self.state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {"id": i, "name": "query_pod_lifecycle", "args": {}} for i in turn_ids
                    ],
                )
            ]
        }


async def _handler(request):
    return ToolMessage("rows", tool_call_id=request.tool_call["id"], name="query_pod_lifecycle")


def _drive(turns, guards):
    fn = AICall._build_tool_dedup_middleware(0, guards=guards).awrap_tool_call

    async def go():
        out = []
        for turn in turns:
            ids = [c for c, _ in turn]
            for call_id, args in turn:
                out.append(await fn(_Request(call_id, args, ids), _handler))
        return out

    return asyncio.run(go())


def test_round_of_only_repeats_ends_the_loop():
    a, b = {"pod": "a"}, {"pod": "b"}
    with pytest.raises(IdleRoundReached) as info:
        _drive([[("c1", a), ("c2", b)], [("c3", a), ("c4", b)]], AgentGuards(16, 3, 3000))
    assert info.value.calls == 2 and "没有新的查询" in str(info.value)


def test_round_with_one_new_call_keeps_going():
    a, b = {"pod": "a"}, {"pod": "b"}
    out = _drive([[("c1", a)], [("c2", a), ("c3", b)]], AgentGuards(16, 3, 3000))
    assert "重复调用" in out[1].content and out[2].content == "rows"


def test_flag_off_falls_back_to_notices():
    a = {"pod": "a"}
    guards = AgentGuards(16, 3, 3000, finalize_on_idle_round=False)
    out = _drive([[("c1", a)], [("c2", a)], [("c3", a)]], guards)
    assert all("重复调用" in m.content for m in out[1:])


def test_guard_flag_parses_from_config_and_env():
    assert (
        AgentGuards.from_config(
            {"finalize_on_idle_round": False}, environ={}
        ).finalize_on_idle_round
        is False
    )
    assert (
        AgentGuards.from_config(
            {}, environ={"AICALL_FINALIZE_ON_IDLE_ROUND": "off"}
        ).finalize_on_idle_round
        is False
    )
    assert (
        AgentGuards.from_config(
            {"finalize_on_idle_round": "weird"}, environ={}
        ).finalize_on_idle_round
        is True
    )
