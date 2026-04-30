import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.service import HolmesService, ThinkStreamFilter, configure_model_context_window, configure_token_counter


def test_think_stream_filter_full_mode_preserves_think_tokens():
    flt = ThinkStreamFilter(mode="full", max_chars=5)

    assert flt.filter_token("<think>abcdef</think>答案") == "<think>abcdef</think>答案"
    assert flt.filter_message("<think>abcdef</think>答案") == "<think>abcdef</think>答案"


def test_think_stream_filter_hidden_mode_removes_think_tokens_across_chunks():
    flt = ThinkStreamFilter(mode="hidden")

    assert flt.filter_token("<think>abc") == ""
    assert flt.filter_token("def</think>答案") == "答案"
    assert flt.filter_message("<think>abcdef</think>答案") == "答案"


def test_think_stream_filter_truncated_mode_shows_limited_think_content():
    flt = ThinkStreamFilter(mode="truncated", max_chars=5)

    visible = (
        flt.filter_token("<think>abc")
        + flt.filter_token("defgh")
        + flt.filter_token("</think>答案")
    )

    assert "<think>abcde" in visible
    assert "fgh" not in visible
    assert "think 已截断" in visible
    assert visible.endswith("</think>答案")


def test_holmes_service_think_stream_config_defaults_to_full(monkeypatch):
    monkeypatch.delenv("AIOPS_THINK_STREAM_MODE", raising=False)
    svc = HolmesService()
    svc.workflow_config = {}

    assert svc.get_think_stream_config() == ("full", 1200)


def test_holmes_service_think_stream_config_env_overrides(monkeypatch):
    monkeypatch.setenv("AIOPS_THINK_STREAM_MODE", "hidden")
    monkeypatch.setenv("AIOPS_THINK_STREAM_MAX_CHARS", "321")
    svc = HolmesService()
    svc.workflow_config = {"think_stream": {"mode": "full", "max_chars": 999}}

    assert svc.get_think_stream_config() == ("hidden", 321)


def test_configure_model_context_window_uses_llm_config_when_env_missing(monkeypatch):
    monkeypatch.delenv("MODEL_CONTEXT_WINDOW", raising=False)

    assert configure_model_context_window({"context_window": 49152}) == 49152
    assert os.environ["MODEL_CONTEXT_WINDOW"] == "49152"


def test_configure_model_context_window_preserves_explicit_env(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32768")

    assert configure_model_context_window({"context_window": 49152}) == 32768
    assert os.environ["MODEL_CONTEXT_WINDOW"] == "32768"


def test_configure_token_counter_uses_llm_config_when_env_missing(monkeypatch):
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    monkeypatch.delenv("AIOPS_TIKTOKEN_ENCODING", raising=False)

    configure_token_counter({"tokenizer_json_path": "/models/qwen/tokenizer.json"})

    assert os.environ["AIOPS_TOKENIZER_JSON_PATH"] == "/models/qwen/tokenizer.json"


def test_configure_token_counter_preserves_explicit_env(monkeypatch):
    monkeypatch.setenv("AIOPS_TOKENIZER_JSON_PATH", "/env/tokenizer.json")
    monkeypatch.delenv("AIOPS_TIKTOKEN_ENCODING", raising=False)

    configure_token_counter({"tokenizer_json_path": "/config/tokenizer.json"})

    assert os.environ["AIOPS_TOKENIZER_JSON_PATH"] == "/env/tokenizer.json"


def test_holmes_service_observation_summary_config_defaults_to_rule(monkeypatch):
    monkeypatch.delenv("AIOPS_OBSERVATION_SUMMARY_MODE", raising=False)
    monkeypatch.delenv("AIOPS_OBSERVATION_SUMMARY_MAX_CHARS", raising=False)
    svc = HolmesService()
    svc.workflow_config = {}

    assert svc.get_observation_summary_config() == ("rule", 3000)


def test_holmes_service_observation_summary_config_ignores_env(monkeypatch):
    monkeypatch.setenv("AIOPS_OBSERVATION_SUMMARY_MODE", "ai")
    monkeypatch.setenv("AIOPS_OBSERVATION_SUMMARY_MAX_CHARS", "777")
    svc = HolmesService()
    svc.workflow_config = {"observation_summary": {"mode": "rule", "max_chars": 3000}}

    assert svc.get_observation_summary_config() == ("rule", 3000)
