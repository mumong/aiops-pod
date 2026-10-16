"""Request trace: compact, lossless about structure, silent about content."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.core.diagnostics.request_trace import describe_messages, repeated_call_digests


def test_describe_messages_keeps_structure_not_content():
    rows = describe_messages([
        HumanMessage(content="secret question"),
        AIMessage(content="", additional_kwargs={"reasoning_content": "plan"},
                  tool_calls=[{"id": "c1", "name": "kubectl", "args": {"kind": "pod"}}]),
        ToolMessage(content="x" * 50, tool_call_id="c1", name="kubectl",
                    additional_kwargs={"aiops_repeat_notice": True}),
        AIMessage(content="", tool_calls=[{"id": "c2", "name": "kubectl", "args": {"kind": "pod"}}]),
    ])
    assert [r["role"] for r in rows] == ["human", "ai", "tool", "ai"]
    assert "secret question" not in str(rows)
    assert rows[1]["reasoning_chars"] == 4 and "reasoning_chars" not in rows[3]
    assert rows[2]["guard"] == ["aiops_repeat_notice"] and rows[2]["chars"] == 50
    assert rows[1]["tool_calls"][0]["args"] == rows[3]["tool_calls"][0]["args"]
    assert list(repeated_call_digests(rows).values()) == [2]
