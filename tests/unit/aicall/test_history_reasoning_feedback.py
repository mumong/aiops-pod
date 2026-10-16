"""In-loop reasoning goes back to the model under the configured request field."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.core.aicall.client import AICall
from app.core.aicall.model_streaming import VisibleChatOpenAI, feed_back_history_reasoning


def _loop():
    return [
        SystemMessage(content="sys"),
        HumanMessage(content="old question"),
        AIMessage(content="old answer", additional_kwargs={"reasoning_content": "old plan"}),
        HumanMessage(content="nodes cpu?"),
        AIMessage(
            content="",
            additional_kwargs={"reasoning_content": "get node list first, then query prometheus"},
            tool_calls=[{"id": "c1", "name": "kubectl", "args": {"kind": "nodes"}}],
        ),
        ToolMessage(content="master node1", tool_call_id="c1"),
        AIMessage(
            content="",
            additional_kwargs={"reasoning": "now prometheus"},
            tool_calls=[{"id": "c2", "name": "promql", "args": {"q": "up"}}],
        ),
        ToolMessage(content="{}", tool_call_id="c2"),
    ]


def test_only_turns_after_the_last_user_message_carry_reasoning():
    model = VisibleChatOpenAI(model="test", api_key="test", history_reasoning_field="reasoning")
    payload = model._get_request_payload(_loop())
    msgs = payload["messages"]
    assert "reasoning" not in msgs[2]  # previous conversation turn: template drops it anyway
    assert msgs[4]["reasoning"] == "get node list first, then query prometheus"
    assert msgs[6]["reasoning"] == "now prometheus"  # either provider key is accepted
    assert msgs[4]["tool_calls"][0]["function"]["name"] == "kubectl"
    assert all("reasoning" not in m for m in msgs if m["role"] != "assistant")


def test_default_keeps_requests_unchanged():
    model = VisibleChatOpenAI(model="test", api_key="test")
    msgs = model._get_request_payload(_loop())["messages"]
    assert all("reasoning" not in m and "reasoning_content" not in m for m in msgs)


def test_helper_tolerates_mismatched_or_empty_reasoning():
    messages = [
        HumanMessage(content="q"),
        AIMessage(content="x", additional_kwargs={"reasoning": " "}),
    ]
    dicts = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "x"}]
    assert feed_back_history_reasoning(messages, dicts, "reasoning") == 0
    assert feed_back_history_reasoning(messages, dicts[:1], "reasoning") == 0
    assert "reasoning" not in dicts[1]


def test_aicall_passes_the_field_to_every_chat_model():
    ai = AICall(
        model="openai/x", api_key="k", api_base="http://gw/v1", history_reasoning_field="reasoning"
    )
    assert ai._chat_model_kwargs["history_reasoning_field"] == "reasoning"
    assert (
        "history_reasoning_field" not in AICall(model="openai/x", api_key="k")._chat_model_kwargs
    )
