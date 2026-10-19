"""A round that burns the whole output reserve with no action is retried once.

Live 2026-10-19: runs 1bbfc5ea (layer, 70 s), 3c052423-g1 (evidence, 102 s),
7e55538b (layer, 68 s), 4285ef7a (repair planning, 71 s) each lost a stage to one
reasoning-only round at max_tokens with zero tool calls.
"""

import asyncio
from types import SimpleNamespace

from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage

from app.core.aicall.client import RUNAWAY_ROUND_NOTE, AICall
from app.core.aicall.guards import AgentGuards
from app.core.aicall.output_budget import OutputBudget


def _client(retries=1):
    ai = AICall(
        model="openai/x",
        api_key="k",
        api_base="http://gw/v1",
        output_budget=OutputBudget(
            agent=4000, delivery=10000, compaction=3000, retry_multiplier=2
        ),
    )
    ai.agent_guards = AgentGuards(runaway_round_retries=retries)
    ai._guard_agent_model_request = lambda request, **kw: (request, {})
    return ai


def runaway():
    return AIMessage(
        content="",
        response_metadata={"finish_reason": "length"},
        usage_metadata={"input_tokens": 9000, "output_tokens": 4000, "total_tokens": 13000},
    )


def acting():
    return AIMessage(
        content="",
        tool_calls=[{"name": "kubectl_describe", "args": {}, "id": "c1"}],
        response_metadata={"finish_reason": "tool_calls"},
    )


def _run(ai, replies):
    seen, waits, events = [], [], []
    middleware = ai._build_context_hard_guard_middleware(
        node_id="layer", run_id="", on_waiting=waits.append, thinking_events=events
    )

    async def handler(request):
        seen.append(list(request.messages))
        return ModelResponse(result=[replies.pop(0)])

    request = ModelRequest(
        model=SimpleNamespace(),
        messages=[HumanMessage(content="q")],
        system_message=None,
        tool_choice=None,
        tools=[],
        response_format=None,
        state={},
        runtime=None,
        model_settings={},
    )
    response = asyncio.run(middleware.awrap_model_call(request, handler))
    return response, seen, waits, events


def test_runaway_round_is_retried_once_with_an_ephemeral_note():
    response, seen, waits, events = _run(_client(), [runaway(), acting()])
    assert response.result[0].tool_calls and len(seen) == 2
    assert seen[1][-1].content == RUNAWAY_ROUND_NOTE and len(seen[0]) == 1
    assert any("重试本轮" in w for w in waits)
    assert events == [{"type": "runaway_round_retry", "node": "layer", "request": 1}]


def test_productive_or_disabled_rounds_are_not_retried():
    assert len(_run(_client(), [acting()])[1]) == 1
    response, seen, _, _ = _run(_client(retries=0), [runaway()])
    assert len(seen) == 1 and not response.result[0].tool_calls
    # A second runaway after the single retry is returned as is (no loop).
    assert len(_run(_client(), [runaway(), runaway()])[1]) == 2
