"""An identical call past max_identical_calls ends the loop deterministically."""

import asyncio

from langchain_core.messages import ToolMessage

from app.core.aicall.client import AICall
from app.core.aicall.errors import RepeatLimitReached, public_error_text
from app.core.aicall.guards import AgentGuards


class _Request:
    def __init__(self, call_id):
        self.tool_call = {
            "id": call_id,
            "name": "kubernetes_tabular_query",
            "args": {"kind": "nodes"},
        }
        self.messages = []


async def _handler(request):
    return ToolMessage(
        "NAME\nmaster", tool_call_id=request.tool_call["id"], name="kubernetes_tabular_query"
    )


def _run(limit):
    middleware = AICall._build_tool_dedup_middleware(0, guards=AgentGuards(16, limit))
    fn = middleware.awrap_tool_call

    async def go():
        out = []
        for i in range(limit + 2):
            out.append(await fn(_Request(f"c{i}"), _handler))
        return out

    return asyncio.run(go())


def test_notice_at_the_limit_then_a_hard_stop():
    try:
        results = _run(2)
    except RepeatLimitReached as exc:
        assert exc.repeats == 3 and exc.limit == 2 and "kubernetes_tabular_query" in str(exc)
        assert public_error_text(exc) == str(exc)
        return
    raise AssertionError(f"expected RepeatLimitReached, got {[r.content[:20] for r in results]}")
