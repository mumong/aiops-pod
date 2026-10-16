"""llm.no_thinking_nodes: an agent node's tool loop uses the internal (no-thinking) settings."""

from app.core.aicall.client import AICall


def _extra_body(model):
    bound = getattr(model, "bound", model)
    return getattr(bound, "extra_body", None) or {}


def test_listed_node_gets_internal_extra_body_and_others_do_not(monkeypatch):
    ai = AICall(
        model="openai/x",
        api_key="sk-test",
        api_base="http://gateway/v1",
        internal_extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        no_thinking_nodes=["query_collect"],
    )
    created = {}
    original = ai._create_chat_model

    def spy(**kw):
        created[kw.get("node_id")] = kw.get("internal")
        return original(**kw)

    monkeypatch.setattr(ai, "_create_chat_model", spy)
    monkeypatch.setattr(ai, "_bind_session_metadata", lambda model, *a, **k: model)
    for node in ("query_collect", "layer"):
        try:
            ai._create_call_agent(
                system_prompt="s",
                question="q",
                tools=[],
                session_id=None,
                node_id=node,
                run_id="",
                stream_queue=None,
                thinking_events=[],
                response_format=None,
            )
        except Exception:
            pass  # create_agent may reject the empty fixture; the model was already created
    assert created == {"query_collect": True, "layer": False}
