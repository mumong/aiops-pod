"""A node whose first round is blank is re-run once (run fa69b5a268454d9f).

The model returned only whitespace, no tool call and no structured result; with
nothing to finalize from, the node delivered nothing. One fresh retry, not more.
"""

from types import SimpleNamespace

from langchain_core.messages import AIMessage

from app.core.aicall.client import AICall


def _run(*, text="\n\n", tools=0, structured=None, cancelled=False):
    event = SimpleNamespace(is_set=lambda: cancelled)
    return SimpleNamespace(
        structured_response=structured,
        tool_call_count=tools,
        emitted_ai_messages=[(AIMessage(content=text), text)],
        tool_observation_contents=[],
        cancel_event=event,
    )


def test_blank_start_predicate():
    assert AICall._blank_start(_run()) is True
    assert AICall._blank_start(_run(text="<think>只有思考</think>\n")) is True
    assert AICall._blank_start(_run(text="已经有分析")) is False
    assert AICall._blank_start(_run(tools=1)) is False
    assert AICall._blank_start(_run(structured=object())) is False
    assert AICall._blank_start(_run(cancelled=True)) is False
    observed = _run()
    observed.tool_observation_contents = ["rows"]
    assert AICall._blank_start(observed) is False


def test_blank_run_is_retried_once(monkeypatch):
    ai = AICall.__new__(AICall)
    executed, pushed = [], []
    outcomes = [_run(), _run(text="正常的分析")]

    monkeypatch.setattr(ai, "_build_observation_processor", lambda: None, raising=False)
    monkeypatch.setattr(ai, "_agent_response_format", lambda *a, **k: (None, []), raising=False)
    monkeypatch.setattr(ai, "_build_agent_input_messages", lambda q: [], raising=False)
    monkeypatch.setattr(ai, "_build_agent_run_config", lambda *a: {}, raising=False)
    monkeypatch.setattr(ai, "_normalize_langfuse_session_id", lambda r: r, raising=False)
    monkeypatch.setattr(ai, "_max_runtime_compactions_per_call", lambda: 0, raising=False)
    monkeypatch.setattr(ai, "_push", lambda *a, **k: pushed.append(k), raising=False)
    monkeypatch.setattr(ai, "_finalize_structured_delivery", lambda run, **k: None, raising=False)
    monkeypatch.setattr(ai, "_finish_agent_call", lambda run, **k: run, raising=False)
    ai.agent_guards = SimpleNamespace(structured_validation_retries=2)

    def execute(run, **kwargs):
        result = outcomes.pop(0)
        run.__dict__.update(
            structured_response=result.structured_response,
            tool_call_count=result.tool_call_count,
            emitted_ai_messages=result.emitted_ai_messages,
            tool_observation_contents=[],
        )
        executed.append(run)

    monkeypatch.setattr(ai, "_execute_agent_run", execute, raising=False)
    final = ai.call(
        system_prompt="s",
        question="q",
        tools=[object()],
        static_context_components=[],
        node_id="query_collect",
        run_id="r",
    )
    assert len(executed) == 2 and executed[0] is not executed[1]
    assert final is executed[1]
    assert any("重新" in str(event.get("content")) for event in pushed)


def test_second_blank_run_is_not_retried_again(monkeypatch):
    ai = AICall.__new__(AICall)
    executed = []
    for name, value in {
        "_build_observation_processor": lambda: None,
        "_agent_response_format": lambda *a, **k: (None, []),
        "_build_agent_input_messages": lambda q: [],
        "_build_agent_run_config": lambda *a: {},
        "_normalize_langfuse_session_id": lambda r: r,
        "_max_runtime_compactions_per_call": lambda: 0,
        "_push": lambda *a, **k: None,
        "_finalize_structured_delivery": lambda run, **k: None,
        "_finish_agent_call": lambda run, **k: run,
    }.items():
        monkeypatch.setattr(ai, name, value, raising=False)
    ai.agent_guards = SimpleNamespace(structured_validation_retries=2)

    def execute(run, **kwargs):
        run.__dict__.update(
            structured_response=None,
            tool_call_count=0,
            emitted_ai_messages=[(AIMessage(content=""), "")],
            tool_observation_contents=[],
        )
        executed.append(run)

    monkeypatch.setattr(ai, "_execute_agent_run", execute, raising=False)
    ai.call(
        system_prompt="s",
        question="q",
        tools=[object()],
        static_context_components=[],
        node_id="n",
        run_id="r",
    )
    assert len(executed) == 2
