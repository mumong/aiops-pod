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
            "primary_pod": {"name": "app-1", "namespace": "aiops-e2e"},
            "abnormal_pods": [{"name": "app-1", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}],
            "pod_status_keyword": "CrashLoopBackOff",
            "pod_abnormal_type": "OOMKilled",
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
    assert result["layer_handoff"]["primary_pod"] == {"name": "app-1", "namespace": "aiops-e2e"}
    assert result["layer_handoff"]["pod_status_keyword"] == "CrashLoopBackOff"
    assert result["layer_handoff"]["pod_abnormal_type"] == "OOMKilled"
    assert result["layer_handoff"]["derived_layer"] == "L2"
    assert result["layer_handoff"]["status_category"] == "container_resource"
    assert "recommended_runbooks" not in result["layer_handoff"]
    assert result["layer_handoff"]["abnormal_pods"][0]["name"] == "app-1"
    assert result["layer_handoff"]["active_entities"][0]["name"] == "app-1"
    assert result["primary_pod"] == {"name": "app-1", "namespace": "aiops-e2e"}
    assert result["pod_status_keyword"] == "CrashLoopBackOff"
    assert result["pod_abnormal_type"] == "OOMKilled"
    assert "archive_ref" in result["layer_handoff"]
    assert (tmp_path / "handoff-run" / "layer" / "full_analysis.md").exists()
    assert (tmp_path / "handoff-run" / "layer" / "handoff.json").exists()


def test_rca_legacy_layer_analysis_to_handoff_preserves_pod_status_fields():
    handoff = RootCauseAnalyzerNode._layer_analysis_to_handoff(json.dumps({
        "layer": "L3",
        "derived_layer": "L3",
        "confidence": 0.88,
        "reasoning": "Pod imagepull-1 ImagePullBackOff",
        "primary_pod": {"name": "imagepull-1", "namespace": "xnet"},
        "abnormal_pods": [{"name": "imagepull-1", "namespace": "xnet", "status": "ImagePullBackOff"}],
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
        "status_category": "image_registry",
        "key_entities": [{"type": "Pod", "value": "imagepull-1"}],
        "possible_scenarios": [],
    }, ensure_ascii=False))

    assert handoff["derived_layer"] == "L3"
    assert handoff["pod_abnormal_type"] == "ImagePullFailed"
    assert handoff["status_category"] == "image_registry"
    assert "recommended_runbooks" not in handoff


def test_conclusion_template_reports_pod_abnormal_status_before_compat_layer():
    node = ConclusionFormatterNode()
    layer_analysis = json.dumps({
        "layer": "L2",
        "derived_layer": "L2",
        "layer_name": "工作负载层",
        "confidence": 0.9,
        "reasoning": "Pod app-1 OOMKilled",
        "primary_pod": {"name": "app-1", "namespace": "default"},
        "pod_status_keyword": "CrashLoopBackOff",
        "pod_abnormal_type": "OOMKilled",
        "status_category": "container_resource",
        "key_entities": [{"type": "Pod", "value": "app-1"}],
    }, ensure_ascii=False)

    report = node._format_with_template(
        question="我的集群有什么问题",
        layer=Layer.L2,
        evidence_items=[],
        decision=None,
        root_cause="",
        causal_chain={},
        layer_analysis=layer_analysis,
        evidence_analysis="{}",
        rca_analysis="{}",
        errors=[],
        warnings=[],
    )

    assert "**Pod异常状态**" in report
    assert "CrashLoopBackOff / OOMKilled" in report
    assert "**兼容归因层**" in report
    assert "L2 - 工作负载层" in report
    assert "阶段一：Pod异常状态定位" in report


def test_rca_lite_puts_evidence_context_only_in_user_message(monkeypatch):
    node = RootCauseAnalyzerNode()
    captured = {}

    class _FakeAICall:
        def call_simple_json(self, system_prompt, question, **kwargs):
            captured["system_prompt"] = system_prompt
            captured["question"] = question
            return {
                "root_cause": "image pull auth",
                "causal_chain": {},
                "confidence": 0.8,
                "primary_runbooks": [],
            }, '{"root_cause":"image pull auth","causal_chain":{},"confidence":0.8,"primary_runbooks":[]}'

    node.ai_call = _FakeAICall()
    evidence_summary = "# 问题定位结构化交接 layer_handoff\nSECRET_CONTEXT"

    result, _events = node._analyze_with_llm_lite(
        question="我的集群有什么问题",
        layer=Layer.L3,
        evidence_summary=evidence_summary,
    )

    assert result["root_cause"] == "image pull auth"
    assert "SECRET_CONTEXT" not in captured["system_prompt"]
    assert "SECRET_CONTEXT" in captured["question"]


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


def test_evidence_user_message_uses_semantic_runbook_matching_without_hardcoded_recommendations():
    layer_handoff = {
        "layer": "L1",
        "primary_pod": {"name": "terminating-stuck", "namespace": "aiops-e2e"},
        "pod_status_keyword": "Terminating",
        "pod_abnormal_type": "TerminatingStuck",
    }

    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L1",
        layer_handoff=json.dumps(layer_handoff, ensure_ascii=False),
    )

    assert "# Runbook 语义匹配要求" in message
    assert "根据 Available Runbooks/catalog 的 description" in message
    assert "pod_status_keyword" in message
    assert "pod_abnormal_type" in message
    assert "不要依赖代码注入的 runbook 推荐字段" in message
    assert "evidence_plan 第一项必须是 fetch_runbook" not in message
    assert "recommended_runbooks" not in message


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


def test_layer_handoff_primary_pod_must_come_from_current_abnormal_pod_scan():
    node = LayerClassifierNode()
    layer_result = {
        "layer": "L2",
        "derived_layer": "L2",
        "confidence": 0.9,
        "reasoning": "历史 Event 提到 memhog OOMKilled",
        "primary_pod": {"name": "memhog-84859d84db-pn4l2", "namespace": "aiops-e2e"},
        "abnormal_pods": [
            {"name": "memhog-84859d84db-pn4l2", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"},
            {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"},
        ],
        "pod_status_keyword": "CrashLoopBackOff",
        "pod_abnormal_type": "OOMKilled",
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE IP NODE",
                "selected_rows": [
                    "aiops-e2e terminating-stuck 0/1 Terminating 0 16m 172.16.166.153 node1",
                    "xnet old-job 0/1 Completed 0 4d 172.16.219.79 master",
                ],
            },
            "result": "Pod table",
        }
    ]

    handoff = node._build_layer_handoff(
        question="我的集群有什么问题",
        layer_result=layer_result,
        layer=Layer.L1,
        layers=[Layer.L1],
        thinking_events=events,
    )

    assert handoff["primary_pod"] == {"name": "terminating-stuck", "namespace": "aiops-e2e"}
    assert handoff["abnormal_pods"] == [
        {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"}
    ]


def test_evidence_conflicts_mark_primary_pod_notfound_as_critical():
    conflicts = EvidenceCollectorNode._build_evidence_conflicts(
        [
            {
                "tool": "kubectl_get_yaml",
                "data": 'Error from server (NotFound): pods "memhog-84859d84db-pn4l2" not found',
            }
        ],
        {
            "primary_pod": {
                "name": "memhog-84859d84db-pn4l2",
                "namespace": "aiops-e2e",
            }
        },
    )

    assert conflicts[0]["severity"] == "critical"
    assert conflicts[0]["object_missing"] is True
    assert conflicts[0]["object"] == {
        "kind": "Pod",
        "name": "memhog-84859d84db-pn4l2",
        "namespace": "aiops-e2e",
    }


def test_rca_blocks_current_root_cause_when_primary_pod_is_missing():
    node = RootCauseAnalyzerNode()
    state = {
        "question": "我的集群有什么问题",
        "layer": Layer.L2,
        "layer_handoff": {
            "primary_pod": {"name": "memhog-84859d84db-pn4l2", "namespace": "aiops-e2e"},
            "pod_status_keyword": "CrashLoopBackOff",
            "pod_abnormal_type": "OOMKilled",
        },
        "evidence_items": [],
        "evidence_conflicts": [
            {
                "severity": "critical",
                "object_missing": True,
                "object": {
                    "kind": "Pod",
                    "name": "memhog-84859d84db-pn4l2",
                    "namespace": "aiops-e2e",
                },
            }
        ],
    }

    result = node.execute(state)
    rca = json.loads(result["rca_analysis"])

    assert "当前不存在" in result["root_cause"]
    assert rca["confidence"] == 0.2
    assert "OOMKilled" not in rca["root_cause"]


def test_evidence_does_not_count_archive_reads_as_positive_evidence():
    node = EvidenceCollectorNode()
    evidence_items = node._build_evidence_items_from_thinking(
        evidence_plan=[
            {
                "id": "e1",
                "description": "确认 Pod 当前状态",
                "level": "critical",
                "tool": "kubectl_describe",
                "command": "kubectl describe pod current -n aiops-e2e",
                "purpose": "确认当前异常",
            }
        ],
        thinking_events=[
            {
                "type": "tool_result",
                "status": "success",
                "semantic_success": True,
                "tool_name": "read_context_archive",
                "result": "历史 Event: old-pod BackOff 24 次",
            }
        ],
    )

    assert len(evidence_items) == 1
    assert evidence_items[0].id == "e1"
    assert evidence_items[0].collected is False


def test_rca_context_filters_archive_and_runbook_tool_outputs():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "llm_analysis": "",
        "tool_data": [
            {"tool": "read_context_archive", "data": "历史 Event: old-pod BackOff 24 次"},
            {"tool": "fetch_runbook", "data": "OOM runbook"},
            {"tool": "kubectl_get_yaml", "data": "kind: Pod\nmetadata:\n  name: current"},
        ],
    }, ensure_ascii=False)

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "old-pod BackOff" not in context
    assert "OOM runbook" not in context
    assert "kubectl_get_yaml" in context
    assert "kind: Pod" in context


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
