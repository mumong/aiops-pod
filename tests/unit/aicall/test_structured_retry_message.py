"""LangChain's structured-output retry prompt is not a tool result for people."""

from types import SimpleNamespace

from app.core.aicall.client import AICall


def _run(known=("c1",)):
    return SimpleNamespace(
        structured_output_tool_names={"RepairDraft"}, tool_args_by_call_id={k: {} for k in known}
    )


def test_unnamed_tool_message_for_an_unknown_call_is_the_retry_prompt():
    msg = SimpleNamespace(
        tool_call_id="c9",
        content="Error: Failed to parse structured output for tool 'RepairDraft': ... Please fix your mistakes.",
    )
    assert AICall._is_structured_retry_message(_run(), msg, "") is True
    assert AICall._is_structured_retry_message(_run(known=("c9",)), msg, "") is False
    real = SimpleNamespace(tool_call_id="c1", content="apiVersion: v1")
    assert AICall._is_structured_retry_message(_run(), real, "kubectl_get_yaml") is False
    assert AICall._is_structured_retry_message(_run(), real, "") is False  # a known call
    no_schema = SimpleNamespace(structured_output_tool_names=set(), tool_args_by_call_id={})
    assert AICall._is_structured_retry_message(no_schema, msg, "") is False
