"""In-loop structured retries are bounded and their feedback names the real problem.

Live run e72fba2398fb4a27 (repair job 5f585d7b51e44b9c): the model left ``targets``
empty six times; each RepairDraft was rejected with "动作必须绑定已列出的 group_id", the
model kept re-checking group_id (already "g1"), and LangChain's ToolStrategy retried
without limit - 11 rounds, 329 s. The retry feedback now says what is missing, the
retries stop after ``structured_validation_retries`` and the stage finalizes.
"""

import pytest
from pydantic import ValidationError

from app.core.aicall.client import AICall
from app.core.aicall.errors import StructuredRetryLimitReached
from app.core.workflow.nodes.remediation import RepairDraft

_ACTION = {
    "id": "a1",
    "group_id": "g1",
    "description": "fix",
    "risk": "low",
    "execute_command": "kubectl rollout restart deployment workload -n ns",
    "rollback_advice": "undo",
}


def _draft(**extra):
    return {"intent": "repair", "scope": "ns", "status": "answered", "answer": "x", **extra}


def test_actions_without_targets_say_targets_is_empty():
    with pytest.raises(ValidationError) as err:
        RepairDraft.model_validate(_draft(actions=[_ACTION]))
    assert "targets 为空" in str(err.value)
    assert "g1" in str(err.value)


def test_action_group_not_in_targets_names_both_sides():
    with pytest.raises(ValidationError) as err:
        RepairDraft.model_validate(
            _draft(
                targets=[
                    {"namespace": "ns", "pod": "p", "group_id": "g2"},
                    {"namespace": "ns", "pod": "q", "group_id": "g3"},
                ],
                actions=[dict(_ACTION, group_id="g9")],
            )
        )
    text = str(err.value)
    assert "g9" in text and "g2, g3" in text


def test_targets_field_tells_the_model_it_is_needed_with_actions():
    description = RepairDraft.model_json_schema()["properties"]["targets"].get("description", "")
    assert "actions" in description and "group_id" in description


def test_structured_error_summary_keeps_the_reason_only():
    raw = (
        "Error: Failed to parse structured output for tool 'RepairDraft': Failed to parse data to "
        "RepairDraft: 1 validation error for RepairDraft\n  Value error, targets 为空：动作 g1 "
        "[type=value_error, input_value={'intent': '...'}, input_type=dict]\n"
        "    For further information visit https://errors.pydantic.dev/2.12/v/value_error.\n"
        " Please fix your mistakes."
    )
    summary = AICall.structured_error_summary(raw)
    assert summary == "targets 为空：动作 g1"
    missing = (
        "Failed to parse data to RepairDraft: 2 validation errors for RepairDraft\nintent\n"
        "  Field required [type=missing, input_value={}, input_type=dict]\nscope\n"
        "  Field required [type=missing, input_value={}, input_type=dict]"
    )
    assert (
        AICall.structured_error_summary(missing) == "intent: Field required；scope: Field required"
    )


def test_in_loop_retries_stop_after_the_limit():
    response_format, names = AICall._agent_response_format(RepairDraft, retry_limit=2)
    assert names == {"RepairDraft"}
    handle = response_format.handle_errors
    exc = ValueError(
        "1 validation error for RepairDraft\n  Value error, targets 为空：动作 g1 [type=value_error]"
    )
    first = handle(exc)
    assert "targets 为空" in first and "1/2" in first
    assert "2/2" in handle(exc)
    with pytest.raises(StructuredRetryLimitReached) as stop:
        handle(exc)
    assert "targets 为空" in str(stop.value)


def test_each_call_gets_its_own_retry_budget():
    a, _ = AICall._agent_response_format(RepairDraft, retry_limit=1)
    b, _ = AICall._agent_response_format(RepairDraft, retry_limit=1)
    a.handle_errors(ValueError("x"))
    b.handle_errors(ValueError("x"))  # independent counter
    with pytest.raises(StructuredRetryLimitReached):
        a.handle_errors(ValueError("x"))


def test_limit_ends_a_real_create_agent_loop():
    """The raise inside handle_errors leaves LangChain's loop instead of being swallowed."""
    import asyncio
    from typing import Any

    from langchain.agents import create_agent
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from pydantic import BaseModel

    class Answer(BaseModel):
        answer: str

    calls = {"n": 0}

    class AlwaysInvalid(GenericFakeChatModel):
        def bind_tools(self, tools: Any, **kwargs: Any):
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            from langchain_core.outputs import ChatGeneration, ChatResult

            calls["n"] += 1
            msg = AIMessage(
                content="",
                tool_calls=[
                    {"name": "Answer", "args": {}, "id": f"c{calls['n']}", "type": "tool_call"}
                ],
            )
            return ChatResult(generations=[ChatGeneration(message=msg)])

    response_format, _ = AICall._agent_response_format(Answer, retry_limit=2)
    agent = create_agent(
        model=AlwaysInvalid(messages=iter([])), tools=[], response_format=response_format
    )
    with pytest.raises(StructuredRetryLimitReached):
        asyncio.run(
            agent.ainvoke(
                {"messages": [{"role": "user", "content": "q"}]}, {"recursion_limit": 40}
            )
        )
    assert calls["n"] == 3  # two fed-back rejections, then the stop
