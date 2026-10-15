from app.core.aicall.client import AICall


def _extra_body(model):
    bound = getattr(model, "bound", model)
    return getattr(bound, "extra_body", None) or {}


def test_internal_calls_merge_internal_extra_body_and_main_calls_do_not():
    ai = AICall(
        model="openai/Qwen3.8-27B",
        api_key="sk-test",
        api_base="http://gateway/v1",
        chat_model_extra_body={"chat_template_kwargs": {"foo": 1}},
        internal_extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    main = ai._create_chat_model(node_id="layer")
    internal = ai.create_compaction_model(max_tokens=1234)
    assert _extra_body(main)["chat_template_kwargs"] == {"foo": 1}
    assert _extra_body(internal)["chat_template_kwargs"] == {"foo": 1, "enable_thinking": False}
    assert internal.kwargs["max_tokens"] == 1234
    assert internal.bound.streaming is False


def test_no_internal_extra_body_by_default():
    ai = AICall(model="openai/x", api_key="sk-test", api_base="http://gateway/v1")
    assert "chat_template_kwargs" not in _extra_body(ai.create_compaction_model())


def test_each_model_instance_gets_its_own_async_http_client():
    """A shared AsyncClient crossed event loops ('Event loop is closed' in production)."""
    ai = AICall(model="openai/x", api_key="sk-test", api_base="http://gateway/v1")
    first = ai._create_chat_model(node_id="a")
    second = ai._create_chat_model(node_id="b")
    assert first.root_async_client._client is not second.root_async_client._client
    assert str(first.root_async_client._client.base_url).startswith("http://gateway/v1")
