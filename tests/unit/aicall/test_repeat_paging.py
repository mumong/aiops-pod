"""Repeating a call whose result was bounded pages through the archived raw output."""

import asyncio

from langchain_core.messages import ToolMessage

from app.core.aicall.client import AICall
from app.core.aicall.errors import RepeatLimitReached
from app.core.aicall.guards import AgentGuards


class _Request:
    def __init__(self, call_id):
        self.tool_call = {"id": call_id, "name": "get_metric_names", "args": {}}
        self.messages = []


RAW = "".join(f"metric_{i:04d}\n" for i in range(900))  # 11,700 chars -> 4 pages of 3000


async def _handler(request):
    return ToolMessage(RAW, tool_call_id=request.tool_call["id"], name="get_metric_names")


def _collect(limit, page_chars, calls):
    fn = AICall._build_tool_dedup_middleware(
        0, guards=AgentGuards(16, limit, page_chars)
    ).awrap_tool_call

    async def go():
        out = []
        for i in range(calls):
            out.append(await fn(_Request(f"c{i}"), _handler))
        return out

    return asyncio.run(go())


def test_repeats_serve_successive_raw_slices_then_notice_then_stop():
    out = _collect(limit=2, page_chars=3000, calls=6)
    assert out[0].content == RAW
    assert (
        out[1].content.startswith("【重复调用：返回同一结果的原始内容第 2/4 段")
        and "metric_0" in out[1].content
    )
    assert out[2].content.startswith("【重复调用：返回同一结果的原始内容第 3/4 段")
    assert (
        out[3].content.startswith("【重复调用：返回同一结果的原始内容第 4/4 段")
        and "metric_0899" in out[3].content
    )
    assert out[1].additional_kwargs["aiops_repeat_page"] == 2
    assert "【重复调用" in out[4].content and "aiops_repeat_page" not in out[4].additional_kwargs
    assert "【同一调用已重复" in out[5].content  # repeat 5 >= limit 2 -> limit notice
    try:
        _collect(limit=2, page_chars=3000, calls=7)
    except RepeatLimitReached:
        return
    raise AssertionError("seventh identical call must stop the stage")


def test_small_results_do_not_page():
    fn = AICall._build_tool_dedup_middleware(0, guards=AgentGuards(16, 3, 3000)).awrap_tool_call

    async def small(request):
        return ToolMessage("ok", tool_call_id=request.tool_call["id"], name="get_metric_names")

    async def go():
        return [await fn(_Request(f"c{i}"), small) for i in range(2)]

    first, second = asyncio.run(go())
    assert first.content == "ok" and second.content.startswith("【重复调用，结果未变化】")
