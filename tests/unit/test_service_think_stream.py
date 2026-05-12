import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.service import (
    HolmesService,
    ThinkStreamFilter,
    configure_model_context_window,
    configure_token_counter,
    format_evidence_plan_output,
)


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


def test_format_evidence_plan_output_renders_plan_and_missing_reasons():
    evidence_analysis = {
        "evidence_plan": [
            {
                "id": "e1",
                "level": "critical",
                "tool": "kubectl_get_yaml",
                "command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
                "description": "获取 Pod YAML",
                "purpose": "验证 deletionTimestamp/finalizers",
            },
            {
                "id": "e2",
                "level": "important",
                "tool": "kubectl_find_resource",
                "command": "kubectl get pvc -n aiops-e2e",
                "description": "获取 PVC/PV 信息",
                "purpose": "确认卷卸载是否卡住",
            },
        ],
        "evidence_inventory": [
            {"id": "e1", "collected": True},
            {"id": "e2", "collected": False},
        ],
        "missing_reasons": [
            "e2(获取 PVC/PV 信息): 已规划但工具执行失败或无匹配结果",
        ],
    }

    text = format_evidence_plan_output(json.dumps(evidence_analysis, ensure_ascii=False))

    assert "📋 证据采集计划" in text
    assert "| e1 | critical | ✅ | kubectl_get_yaml |" in text
    assert "kubectl get pod terminating-stuck" in text
    assert "| e2 | important | ❌ | kubectl_find_resource |" in text
    assert "未采集原因" in text
    assert "已规划但工具执行失败或无匹配结果" in text


def test_holmes_service_health_check_includes_model_when_initialized():
    svc = HolmesService()
    svc.config = type("Config", (), {"model": "openai/Qwen3-32B-AWQ"})()
    svc.ai_call = object()

    health = svc.health_check()

    assert health["status"] == "healthy"
    assert health["model"] == "openai/Qwen3-32B-AWQ"


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


def test_holmes_service_context_compaction_config_defaults():
    svc = HolmesService()
    svc.workflow_config = {}

    assert svc.get_context_compaction_config() == {
        "enabled": True,
        "nodes": ["evidence"],
        "max_context_window": 35000,
        "trigger_ratio": 0.70,
        "max_compactions_per_call": 1,
        "summary_max_tokens": 1200,
    }


def test_holmes_service_context_compaction_config_uses_workflow_config(monkeypatch):
    monkeypatch.setenv("AIOPS_CONTEXT_COMPACTION_ENABLED", "false")
    svc = HolmesService()
    svc.workflow_config = {
        "context_compaction": {
            "enabled": False,
            "nodes": "evidence",
            "max_context_window": "32000",
            "trigger_ratio": "0.65",
            "max_compactions_per_call": "2",
            "summary_max_tokens": "900",
        }
    }

    assert svc.get_context_compaction_config() == {
        "enabled": False,
        "nodes": ["evidence"],
        "max_context_window": 32000,
        "trigger_ratio": 0.65,
        "max_compactions_per_call": 2,
        "summary_max_tokens": 900,
    }
