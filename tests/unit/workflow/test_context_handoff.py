import json
import logging
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.skills.models import Layer
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode


def test_layer_execute_archives_full_analysis_and_publishes_handoff(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    node = LayerClassifierNode()
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._analyze_with_llm = lambda question: (
        {
            "layer": "L2",
            "layers": ["L2"],
            "layer_name": "工作负载层",
            "confidence": 0.91,
            "reasoning": "Pod app-1 OOMKilled",
            "key_entities": [{"type": "Pod", "value": "app-1"}, {"type": "Namespace", "value": "aiops-e2e"}],
            "possible_scenarios": [{"scenario": "OOMKilled", "probability": "高", "reason": "Exit Code 137"}],
            "full_analysis": "raw layer analysis\n" + ("OOMKilled\n" * 1000),
        },
        [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "kubectl_describe",
                "result": "Name: app-1\nNamespace: aiops-e2e\nReason: OOMKilled\n",
                "raw_ref": "/tmp/raw.txt",
            }
        ],
    )

    result = node.execute({"question": "我的集群有什么问题", "run_id": "handoff-run"})

    assert result["layer"] == Layer.L2
    assert not result.get("layer_full_analysis")
    assert result["layer_handoff"]["layer"] == "L2"
    assert result["layer_handoff"]["primary_problem"] == "Pod app-1 OOMKilled"
    assert result["layer_handoff"]["active_entities"][0]["name"] == "app-1"
    assert "archive_ref" in result["layer_handoff"]
    assert (tmp_path / "handoff-run" / "layer" / "full_analysis.md").exists()
    assert (tmp_path / "handoff-run" / "layer" / "handoff.json").exists()


def test_evidence_prompt_uses_layer_handoff_in_user_message_not_system_prompt(monkeypatch):
    node = EvidenceCollectorNode()
    node.ai_call = object()
    captured = {}

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured["question"] = question
        captured["system_prompt"] = system_prompt
        return SimpleNamespace(result='{"evidence_plan": []}'), []

    node._call_llm = _fake_call_llm

    layer_handoff = {
        "layer": "L3",
        "primary_problem": "Service svc-a 没有 Endpoints",
        "active_entities": [{"type": "Service", "name": "svc-a", "namespace": "default"}],
        "must_verify": ["确认 Endpoints 仍为空"],
    }
    plan, events, text = node._plan_evidence_with_llm(
        question="我的集群有什么问题",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
    )

    assert "上游定位结构化结果 layer_handoff" in captured["question"]
    assert "Service svc-a 没有 Endpoints" in captured["question"]
    assert "Service svc-a 没有 Endpoints" not in captured["system_prompt"]
    assert plan == []
    assert events == []


def test_evidence_logs_user_prompt_input_only_once(monkeypatch, caplog):
    node = EvidenceCollectorNode()
    node.ai_call = object()

    def _fake_call_llm(question, system_prompt, **kwargs):
        return SimpleNamespace(result='{"evidence_plan": []}'), []

    node._call_llm = _fake_call_llm
    layer_handoff = {
        "layer": "L0",
        "primary_problem": "EmptyDir logs 超过 30Mi",
        "active_entities": [{"type": "Pod", "name": "logfill-1", "namespace": "aiops-e2e"}],
    }

    with caplog.at_level(logging.INFO):
        for _ in range(2):
            node._plan_evidence_with_llm(
                question="我的集群有什么问题",
                layer=Layer.L0,
                possible_scenarios=[],
                key_entities=[],
                layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
            )

    log_text = caplog.text
    assert log_text.count("📨 [evidence] LLM user prompt") == 1
    assert "上游定位结构化结果 layer_handoff" in log_text
    assert "EmptyDir logs 超过 30Mi" in log_text


def test_rca_summary_prefers_layer_handoff_over_full_layer_text():
    node = RootCauseAnalyzerNode()
    evidence = []
    state = {
        "question": "我的集群有什么问题",
        "layer": Layer.L3,
        "layer_full_analysis": "SHOULD_NOT_APPEAR " * 1000,
        "layer_handoff": {
            "layer": "L3",
            "primary_problem": "ImagePullBackOff x509",
            "active_entities": [{"type": "Pod", "name": "pod-a", "namespace": "xnet"}],
        },
        "evidence_items": evidence,
        "evidence_analysis": "{}",
    }

    summary = node._build_rca_context(state)

    assert "ImagePullBackOff x509" in summary
    assert "SHOULD_NOT_APPEAR" not in summary


def test_conclusion_uses_handoff_not_full_layer_analysis():
    node = ConclusionFormatterNode()
    layer_analysis = node._select_layer_context(
        {
            "layer_full_analysis": "SHOULD_NOT_APPEAR " * 1000,
            "layer_analysis": '{"layer":"L3"}',
            "layer_handoff": {
                "layer": "L3",
                "primary_problem": "ImagePullBackOff x509",
            },
        }
    )

    assert "ImagePullBackOff x509" in layer_analysis
    assert "SHOULD_NOT_APPEAR" not in layer_analysis
