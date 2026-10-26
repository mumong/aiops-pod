"""Provider reasoning configuration belongs to the shared model transport."""

from unittest.mock import patch

from app.core.aicall.client import AICall


def test_unset_reasoning_effort_preserves_provider_default(monkeypatch):
    monkeypatch.delenv("LLM_REASONING_EFFORT", raising=False)
    with patch("app.core.aicall.client.ChatOpenAI") as model:
        AICall(model="openai/Qwen3.8-27B", api_key="test")._create_chat_model()
    assert "reasoning_effort" not in model.call_args.kwargs


def test_low_effort_reaches_streaming_and_nonstreaming_models(monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", " low ")
    client = AICall(model="openai/example-model", api_key="test")
    with patch("app.core.aicall.client.ChatOpenAI") as model:
        client._create_chat_model(node_id="remediation")
        client._create_chat_model(node_id="context_compaction", disable_streaming=True)
    assert len(model.call_args_list) == 2
    assert all(c.kwargs["reasoning_effort"] == "low" for c in model.call_args_list)
    assert model.call_args_list[1].kwargs["disable_streaming"] is True


def test_blank_effort_does_not_send_an_empty_provider_option(monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "  ")
    client = AICall(model="deepseek/deepseek-chat", api_key="test")
    assert "reasoning_effort" not in client._chat_model_kwargs
