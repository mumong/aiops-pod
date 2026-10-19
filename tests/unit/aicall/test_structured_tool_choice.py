"""Structured delivery as an ordinary tool call (tool_choice=auto), not a named one.

Live 2026-10-19 (run 6ec40015e1024f8a): under a named tool_choice vLLM grammar-decodes
the arguments and Qwen3.6 leaves inner double quotes unescaped, so the string ends at
`-p='[{"` and `actions` vanishes. The gateway probe reproduced it with named/required
and not with auto. These tests pin the transport and what is kept when a reply is
rejected.
"""

from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from app.core.aicall.client import AICall
from app.core.aicall.output_budget import OutputBudget
from app.core.aicall.structured_transport import (
    coerce_json_strings,
    normalize_tool_choice,
    parse_structured_tool_message,
)


class _Action(BaseModel):
    execute_command: str


class _Plan(BaseModel):
    intent: str
    answer: str = ""
    actions: list[_Action] = Field(default_factory=list)


CMD = 'kubectl patch deployment workload -n demo --type=\'json\' -p=\'[{"op":"replace","path":"/x","value":"y"}]\''


def _tool_reply(args, finish="tool_calls", raw=None):
    return AIMessage(
        content="",
        tool_calls=[{"name": "_Plan", "args": args, "id": "call-1", "type": "tool_call"}],
        additional_kwargs={
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "_Plan", "arguments": raw or "{}"},
                }
            ]
        },
        response_metadata={"finish_reason": finish},
        usage_metadata={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
    )


# ---- parser ---------------------------------------------------------------------


def test_tool_call_with_quoted_command_validates_intact():
    parsed, error, record = parse_structured_tool_message(
        _tool_reply(
            {"intent": "fix", "answer": f"run {CMD}", "actions": [{"execute_command": CMD}]}
        ),
        _Plan,
    )
    assert error == "" and parsed.actions[0].execute_command == CMD
    assert record["finish_reason"] == "tool_calls" and record["usage"]["output_tokens"] == 20


def test_length_truncation_is_rejected_even_when_partial_json_parsed():
    # LangChain repairs a cut arguments string into a partial dict; that is not a plan.
    parsed, error, record = parse_structured_tool_message(
        _tool_reply({"intent": "fix", "answer": "kubectl patch ... -p='[{"}, finish="length"),
        _Plan,
    )
    assert parsed is None and "finish_reason=length" in error and "截断" in error
    assert record["error"] == error


def test_list_field_written_as_json_string_is_decoded():
    args = {"intent": "fix", "actions": '[{"execute_command": "kubectl get pods"}]'}
    coerced, changed = coerce_json_strings(args, _Plan)
    assert (
        changed == ["actions"] and coerced["actions"][0]["execute_command"] == "kubectl get pods"
    )
    parsed, error, record = parse_structured_tool_message(_tool_reply(args), _Plan)
    assert error == "" and parsed.actions[0].execute_command == "kubectl get pods"
    assert record["coerced_fields"] == ["actions"]


def test_malformed_list_string_is_left_for_validation_to_report():
    args = {"intent": "fix", "actions": '[{"execute_command": "kubectl patch -p=\'[{"op"}]'}
    parsed, error, _ = parse_structured_tool_message(_tool_reply(args), _Plan)
    assert parsed is None and "actions" in error


def test_invalid_tool_call_json_names_the_escaping_rule():
    message = AIMessage(
        content="",
        invalid_tool_calls=[
            {
                "name": "_Plan",
                "args": '{"intent": "x", "answer": "a "b" c"}',
                "id": "c",
                "error": "Extra data",
                "type": "invalid_tool_call",
            }
        ],
        response_metadata={"finish_reason": "tool_calls"},
    )
    parsed, error, record = parse_structured_tool_message(message, _Plan)
    assert parsed is None and "不是合法 JSON" in error and '\\"' in error
    assert record["invalid_tool_calls"][0].startswith('{"intent"')


def test_text_reply_is_parsed_as_json_or_rejected_with_the_function_name():
    ok = AIMessage(
        content='```json\n{"intent": "fix", "answer": "done"}\n```',
        response_metadata={"finish_reason": "stop"},
    )
    parsed, error, _ = parse_structured_tool_message(
        ok, _Plan, text_fallback=AICall.extract_json_payload
    )
    assert error == "" and parsed.intent == "fix"
    prose = AIMessage(
        content="I would patch the deployment.", response_metadata={"finish_reason": "stop"}
    )
    parsed, error, record = parse_structured_tool_message(
        prose, _Plan, text_fallback=AICall.extract_json_payload
    )
    assert parsed is None and "_Plan" in error and record["content_head"].startswith("I would")
    empty = AIMessage(content="", response_metadata={"finish_reason": "stop"})
    assert parse_structured_tool_message(empty, _Plan)[1].startswith("模型没有返回任何内容")


def test_tool_choice_mode_normalisation():
    assert normalize_tool_choice(None) == "auto"
    assert normalize_tool_choice(" Named ") == "named"
    assert normalize_tool_choice("required") == "auto"


# ---- client wiring ----------------------------------------------------------------


class _ToolModel:
    def __init__(self, replies, seen):
        self.replies, self.seen = replies, seen

    def invoke(self, messages, config=None):
        self.seen.append(messages[-1].content)
        return self.replies.pop(0)


class _Model:
    """Fake chat model recording how structured delivery binds the schema."""

    def __init__(self, replies, seen, binds):
        self.replies, self.seen, self.binds = replies, seen, binds

    def bind_tools(self, tools, tool_choice=None):
        self.binds.append(("bind_tools", [t.__name__ for t in tools], tool_choice))
        return _ToolModel(self.replies, self.seen)

    def with_structured_output(self, schema, method=None):
        self.binds.append(("with_structured_output", schema.__name__, method))
        return _ToolModel(self.replies, self.seen)


def _client(monkeypatch, replies, seen, binds, tool_choice="auto", archive=None):
    ai = AICall(
        model="openai/x",
        api_key="k",
        api_base="http://gw/v1",
        internal_extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        output_budget=OutputBudget(
            agent=4000, delivery=10000, compaction=3000, retry_multiplier=2
        ),
        structured_tool_choice=tool_choice,
    )
    monkeypatch.setattr(ai, "_create_chat_model", lambda **kw: _Model(replies, seen, binds))
    monkeypatch.setattr(ai, "_bind_session_metadata", lambda model, *a, **k: model)
    guard = {"context_window": 54000, "final_input_tokens": 14000, "safety_tokens": 2000}
    monkeypatch.setattr(
        ai,
        "_prepare_structured_call_context",
        lambda **kw: (kw["system_prompt"], kw["question"], guard, {}, {}),
    )
    if archive is not None:
        monkeypatch.setattr(
            ai,
            "_archive_structured_rejection",
            lambda run_id, node, record: archive.append((run_id, node, record)),
        )
    return ai


def test_auto_mode_binds_schema_as_the_only_tool_with_tool_choice_auto(monkeypatch):
    seen, binds = [], []
    ai = _client(
        monkeypatch,
        [_tool_reply({"intent": "fix", "actions": [{"execute_command": CMD}]})],
        seen,
        binds,
    )
    parsed, raw = ai.call_structured(
        "sys", "plan", _Plan, node_id="remediation", internal_model=True
    )
    assert parsed.actions[0].execute_command == CMD and '"intent":"fix"' in raw
    assert binds == [("bind_tools", ["_Plan"], "auto")]


def test_named_mode_keeps_with_structured_output(monkeypatch):
    seen, binds = [], []
    ai = _client(monkeypatch, [_Plan(intent="fix")], seen, binds, tool_choice="named")
    parsed, _ = ai.call_structured("sys", "plan", _Plan, node_id="rca", internal_model=True)
    assert parsed.intent == "fix" and binds[0][0] == "with_structured_output"


def test_rejected_reply_is_archived_and_fed_back_then_accepted(monkeypatch):
    seen, binds, archive = [], [], []
    truncated = _tool_reply(
        {"intent": "fix", "answer": "kubectl patch -p='[{"},
        finish="length",
        raw='{"intent": "fix", "answer": "kubectl patch -p=\'[{',
    )
    good = _tool_reply({"intent": "fix", "actions": [{"execute_command": CMD}]})
    ai = _client(monkeypatch, [truncated, good], seen, binds, archive=archive)
    parsed, _ = ai.call_structured(
        "sys", "plan", _Plan, node_id="remediation", run_id="run-1", internal_model=True
    )
    assert parsed is not None and len(seen) == 2
    assert "上次结构化输出未通过校验" in seen[1] and "finish_reason=length" in seen[1]
    assert archive == [("run-1", "remediation", archive[0][2])]
    assert archive[0][2]["finish_reason"] == "length" and archive[0][2]["arguments"].startswith(
        '{"intent"'
    )


def test_rejection_archive_path_and_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    ai = AICall(model="openai/x", api_key="k", api_base="http://gw/v1")
    ai._archive_structured_rejection("run-9", "remediation", {"schema": "_Plan", "error": "boom"})
    ai._archive_structured_rejection("run-9", "remediation", {"schema": "_Plan", "error": "again"})
    files = sorted(p.name for p in (tmp_path / "run-9" / "structured").iterdir())
    assert files == ["remediation-rejected-001.json", "remediation-rejected-002.json"]
    assert '"error": "boom"' in (tmp_path / "run-9" / "structured" / files[0]).read_text(
        encoding="utf-8"
    )
