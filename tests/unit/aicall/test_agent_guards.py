"""Tool-loop guards and provider-safe error text."""

import httpx
from openai import BadRequestError

from app.core.aicall.errors import ModelStreamStalled, public_error_text
from app.core.aicall.guards import AgentGuards


def test_guards_from_config_env_and_defaults():
    assert AgentGuards.from_config(None, environ={}) == AgentGuards(16, 3)
    assert AgentGuards.from_config({"max_identical_calls": 5}, environ={}) == AgentGuards(16, 5)
    assert (
        AgentGuards.from_config(
            {"max_identical_calls": 5}, environ={"AICALL_MAX_IDENTICAL_CALLS": "2"}
        ).max_identical_calls
        == 2
    )
    assert (
        AgentGuards.from_config(
            {"max_tool_calls_per_turn": "x"}, environ={}
        ).max_tool_calls_per_turn
        == 16
    )


def test_public_error_text_hides_provider_bodies_but_keeps_our_messages():
    response = httpx.Response(400, request=httpx.Request("POST", "http://gw"))
    exc = BadRequestError(
        "litellm.BadRequestError: Extra data: line 1 column 105 Received Model Group=secret",
        response=response,
        body=None,
    )
    text = public_error_text(exc)
    assert "HTTP 400" in text and "BadRequestError" in text
    assert "Extra data" not in text and "Model Group" not in text
    stalled = ModelStreamStalled(180.0, waiting_on="第 5 次模型请求")
    assert public_error_text(stalled) == str(stalled)
