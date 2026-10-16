"""Malformed streamed tool-call arguments must not be sent back to the provider."""

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.core.aicall.tool_call_repair import repair_tool_call_arguments


def _ai(raw_arguments, parsed_args=None, call_id="c1", content=""):
    kwargs = {
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": "execute_prometheus_instant_query",
                    "arguments": raw_arguments,
                },
            }
        ]
    }
    tool_calls = (
        [
            {
                "id": call_id,
                "name": "execute_prometheus_instant_query",
                "args": parsed_args,
                "type": "tool_call",
            }
        ]
        if parsed_args is not None
        else []
    )
    return AIMessage(content=content, additional_kwargs=kwargs, tool_calls=tool_calls)


def test_concatenated_arguments_become_the_executed_object():
    msg = _ai('{"query":"up"}{"query":"node_load1"}', parsed_args={"query": "up"})
    out, repaired = repair_tool_call_arguments(
        [HumanMessage("q"), msg, ToolMessage("ok", tool_call_id="c1")]
    )
    assert repaired == 1
    fixed = out[1].additional_kwargs["tool_calls"][0]["function"]["arguments"]
    assert json.loads(fixed) == {"query": "up"}
    assert out[1].tool_calls[0]["args"] == {"query": "up"}


def test_unanswered_invalid_call_is_dropped_and_message_keeps_a_note():
    msg = AIMessage(
        content="",
        additional_kwargs={
            "tool_calls": [
                {
                    "id": "c9",
                    "type": "function",
                    "function": {"name": "f", "arguments": '{"query":"up"} trailing junk'},
                }
            ]
        },
    )
    assert msg.invalid_tool_calls  # langchain could not parse it
    out, repaired = repair_tool_call_arguments([msg])
    assert repaired == 1
    assert "tool_calls" not in out[0].additional_kwargs and out[0].invalid_tool_calls == []
    assert out[0].content.strip()


def test_valid_history_is_returned_untouched():
    msg = _ai('{"query":"up"}', parsed_args={"query": "up"})
    messages = [HumanMessage("q"), msg, ToolMessage("ok", tool_call_id="c1")]
    out, repaired = repair_tool_call_arguments(messages)
    assert repaired == 0 and out[1] is msg
