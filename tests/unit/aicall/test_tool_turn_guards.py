"""Deterministic guards against degenerate tool-call repetition (live Qwen run 3248a3d833f84803:
292 calls in one turn, 17 distinct calls x 17 repeats)."""
import asyncio
from types import SimpleNamespace

from langchain_core.messages import AIMessage, ToolMessage

from app.core.aicall.client import AICall


def _turn(calls):
    message = AIMessage(content="", tool_calls=[
        {"id": cid, "name": name, "args": args} for cid, name, args in calls])
    return {"messages": [message]}


def _request(state, cid, name, args):
    return SimpleNamespace(tool_call={"id": cid, "name": name, "args": args}, state=state)


def test_identical_calls_in_one_turn_run_once_and_the_rest_get_a_notice():
    middleware = AICall._build_tool_dedup_middleware()
    executions = []
    calls = [(f"c{i}", "query_pod_lifecycle", {"namespace": "a"}) for i in range(5)]
    state = _turn(calls)

    async def handler(request):
        executions.append(request.tool_call["id"])
        await asyncio.sleep(0.05)
        return ToolMessage(content="FULL RESULT", tool_call_id=request.tool_call["id"], name="query_pod_lifecycle")

    async def main():
        return await asyncio.gather(*[
            middleware.awrap_tool_call(_request(state, cid, name, args), handler) for cid, name, args in calls])

    results = asyncio.run(main())
    assert executions == ["c0"]
    assert [r.content for r in results].count("FULL RESULT") == 1
    notices = [r for r in results if r.content != "FULL RESULT"]
    assert len(notices) == 4 and all("本轮中另一调用" in r.content for r in notices)
    assert all(r.tool_call_id == f"c{i}" for i, r in enumerate(results))


def test_calls_beyond_the_per_turn_cap_are_not_executed(monkeypatch):
    monkeypatch.setenv("AICALL_MAX_TOOL_CALLS_PER_TURN", "3")
    middleware = AICall._build_tool_dedup_middleware()
    calls = [(f"c{i}", "query_pod_lifecycle", {"pod": f"p{i}"}) for i in range(5)]
    state = _turn(calls)
    executions = []

    async def handler(request):
        executions.append(request.tool_call["id"])
        return ToolMessage(content="ok", tool_call_id=request.tool_call["id"], name="query_pod_lifecycle")

    async def main():
        return [await middleware.awrap_tool_call(_request(state, cid, name, args), handler)
                for cid, name, args in calls]

    results = asyncio.run(main())
    assert executions == ["c0", "c1", "c2"]
    assert all("未执行：本轮工具调用过多" in r.content for r in results[3:])
    assert results[4].additional_kwargs["aiops_turn_cap"] is True


def test_cap_disabled_with_zero(monkeypatch):
    monkeypatch.setenv("AICALL_MAX_TOOL_CALLS_PER_TURN", "0")
    middleware = AICall._build_tool_dedup_middleware()
    calls = [(f"c{i}", "t", {"i": i}) for i in range(30)]
    state = _turn(calls)

    async def handler(request):
        return ToolMessage(content="ok", tool_call_id=request.tool_call["id"], name="t")

    async def main():
        return [await middleware.awrap_tool_call(_request(state, *call), handler) for call in calls]

    assert all(r.content == "ok" for r in asyncio.run(main()))
