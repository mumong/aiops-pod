import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.context.usage_probe import OpenAIUsageProbe


def test_openai_usage_probe_reads_prompt_tokens(monkeypatch):
    captured = {}

    class _Response:
        status_code = 200
        text = ""

        def json(self):
            return {
                "usage": {
                    "prompt_tokens": 123,
                    "completion_tokens": 1,
                    "total_tokens": 124,
                }
            }

    def _fake_post(url, data=None, headers=None, timeout=0):
        captured["url"] = url
        captured["payload"] = json.loads(data.decode("utf-8"))
        captured["headers"] = headers
        return _Response()

    monkeypatch.setattr("app.core.context.usage_probe.requests.post", _fake_post)

    result = OpenAIUsageProbe("http://llm.example/v1", "sk-test").count_prompt_tokens(
        "openai/Qwen3-32B-AWQ",
        messages=[
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
        ],
    )

    assert result.prompt_tokens == 123
    assert result.total_tokens == 124
    assert result.accuracy == "exact"
    assert captured["url"] == "http://llm.example/v1/chat/completions"
    assert captured["payload"]["model"] == "Qwen3-32B-AWQ"
    assert captured["payload"]["max_tokens"] == 1
    assert captured["payload"]["stream"] is False
    assert captured["headers"]["Authorization"] == "Bearer sk-test"


def test_openai_usage_probe_reports_unknown_without_prompt_tokens(monkeypatch):
    class _Response:
        status_code = 200
        text = ""

        def json(self):
            return {"usage": {"completion_tokens": 1, "total_tokens": 1}}

    monkeypatch.setattr(
        "app.core.context.usage_probe.requests.post",
        lambda *args, **kwargs: _Response(),
    )

    result = OpenAIUsageProbe("http://llm.example/v1").count_prompt_tokens(
        "Qwen3-32B-AWQ",
        messages=[{"role": "user", "content": "u"}],
    )

    assert result.prompt_tokens is None
    assert result.accuracy == "unknown"
    assert "prompt_tokens missing" in result.error
