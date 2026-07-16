import hashlib
import json
import logging
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.skills.models import Layer
from app.core.workflow.schemas import RCAOutput
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode


def _canonical_fact_record(**overrides):
    record = {
        "entity_id": "k8s.pod:demo/api:uid-a",
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "logging",
        "fact_type": "log",
        "attribute": "log.message",
        "value": {"message": "request returned status 503"},
        "source_system": "elasticsearch",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["logs:target"],
    }
    record.update(overrides)
    identity = {
        key: value
        for key, value in record.items()
        if key != "fact_id"
        and value not in (None, {}, [])
    }
    identity["evidence_refs"] = sorted(set(identity["evidence_refs"]))
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    record["fact_id"] = (
        "fact-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    )
    return record


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
    assert "primary_pod" not in result["layer_handoff"]
    assert result["layer_handoff"]["pod_status_keyword"] == "CrashLoopBackOff"
    assert result["layer_handoff"]["pod_abnormal_type"] == "OOMKilled"
    assert result["layer_handoff"]["derived_layer"] == "L2"
    assert result["layer_handoff"]["status_category"] == "container_resource"
    assert "recommended_runbooks" not in result["layer_handoff"]
    assert "primary_pod" not in json.loads(result["layer_analysis"])
    assert result["layer_handoff"]["abnormal_pods"][0]["name"] == "app-1"
    assert result["layer_handoff"]["active_entities"][0]["name"] == "app-1"
    assert result["abnormal_groups"]
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
    assert "primary_pod" not in handoff


def test_layer_extract_runbook_id_prefers_tool_args_over_text():
    event = {
        "tool_name": "fetch_runbook",
        "tool_args": {"runbook_id": "pod-terminating-stuck.md"},
        "structured": {"title": "Pod Terminating Stuck"},
        "result": "<runbook>\n# Pod Terminating Stuck\n</runbook>",
    }

    assert LayerClassifierNode._extract_runbook_id(event) == "pod-terminating-stuck.md"


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


def test_conclusion_template_uses_pod_observability_coverage_for_completeness():
    node = ConclusionFormatterNode()
    evidence_analysis = json.dumps({
        "collection_summary": (
            "Pod 可观测性覆盖 2/2，完整度 100%；"
            "去重后证据计划 0/0，完整度 0%"
        ),
        "plan_total": 0,
        "plan_collected": 0,
        "plan_completeness": 0.0,
        "environment_evidence_total": 0,
        "environment_evidence_collected": 0,
        "environment_evidence_completeness": 0.0,
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
        "evidence_inventory": [],
    }, ensure_ascii=False)

    report = node._format_with_template(
        question="我的集群有什么问题",
        layer=Layer.L2,
        evidence_items=[],
        decision=None,
        root_cause="",
        causal_chain={},
        layer_analysis="{}",
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
        errors=[],
        warnings=[],
    )

    assert "| **证据完整度** | 2/2 (100%) |" in report
    assert "| **证据完整度** | 0/0 (0%) |" not in report


def test_rca_lite_puts_evidence_context_only_in_user_message(monkeypatch):
    node = RootCauseAnalyzerNode()
    captured = {}
    parsed = RCAOutput.model_validate({
        "phenomenon": "Pod ImagePullBackOff",
        "causal_chain": {
            "root_cause": "image pull auth",
            "propagation": "镜像无法下载",
            "direct_cause": "容器无法创建",
            "manifestation": "Pod ImagePullBackOff",
        },
        "root_cause_summary": "image pull auth",
        "confidence": 0.8,
        "confidence_reason": "镜像拉取事件与认证失败相互印证",
        "primary_runbooks": [],
    })

    def _fake_call_structured_agent(question, system_prompt, schema, **kwargs):
        captured["system_prompt"] = system_prompt
        captured["question"] = question
        return parsed, SimpleNamespace(result=parsed.model_dump_json(), structured_response=parsed), []

    node._call_structured_agent = _fake_call_structured_agent
    node.ai_call = object()
    evidence_summary = "# 问题定位结构化交接 layer_handoff\nSECRET_CONTEXT"

    result, _events = node._analyze_with_llm_lite(
        question="我的集群有什么问题",
        layer=Layer.L3,
        evidence_summary=evidence_summary,
    )

    assert result["root_cause"] == "image pull auth"
    assert "SECRET_CONTEXT" not in captured["system_prompt"]
    assert "SECRET_CONTEXT" in captured["question"]


def test_rca_lite_prefers_structured_output_when_available():
    node = RootCauseAnalyzerNode()
    captured = {}
    parsed = RCAOutput.model_validate({
        "phenomenon": "Pod ImagePullBackOff",
        "causal_chain": {
            "root_cause": "节点出口网络超时",
            "propagation": "镜像无法下载",
            "direct_cause": "容器无法创建",
            "manifestation": "Pod ImagePullBackOff",
        },
        "root_cause_summary": "节点出口网络超时导致镜像拉取失败",
        "confidence": 0.84,
        "confidence_reason": "镜像拉取事件中的网络超时直接支持该结论",
        "primary_runbooks": ["pod-imagepull-failed.md"],
    })

    def _fake_call_structured_agent(question, system_prompt, schema, **kwargs):
        captured["system_prompt"] = system_prompt
        captured["question"] = question
        captured["schema"] = schema
        return parsed, SimpleNamespace(result=parsed.model_dump_json(), structured_response=parsed), []

    node._call_structured_agent = _fake_call_structured_agent
    node.ai_call = object()

    result, _events = node._analyze_with_llm_lite(
        question="我的集群有什么问题",
        layer=Layer.L3,
        evidence_summary="# 已验证事实\nImagePullBackOff",
    )

    assert captured["schema"] is RCAOutput
    assert result["root_cause"] == "节点出口网络超时导致镜像拉取失败"
    assert result["confidence"] == 0.84
    assert result["primary_runbooks"] == ["pod-imagepull-failed.md"]


def test_rca_lite_uses_structured_agent_runtime():
    node = RootCauseAnalyzerNode()
    captured = {}
    parsed = RCAOutput.model_validate({
        "phenomenon": "Pod ImagePullBackOff",
        "root_cause": "节点无法访问 Docker Hub",
        "root_cause_summary": "镜像仓库网络不可达",
        "confidence": 0.86,
        "confidence_reason": "镜像拉取事件明确报告网络不可达",
    })

    class _NoDirectStructured:
        def call_structured(self, *args, **kwargs):
            raise AssertionError("RCA node should use _call_structured_agent, not ai_call.call_structured")

    node.ai_call = _NoDirectStructured()

    def _fake_call_structured_agent(question, system_prompt, schema, **kwargs):
        captured["schema"] = schema
        captured["use_tools"] = kwargs.get("use_tools")
        return parsed, SimpleNamespace(result=parsed.model_dump_json(), structured_response=parsed), []

    node._call_structured_agent = _fake_call_structured_agent

    result, events = node._analyze_with_llm_lite(
        question="我的集群有什么问题",
        layer=Layer.L3,
        evidence_summary="Failed to pull image",
    )

    assert captured["schema"] is RCAOutput
    assert captured["use_tools"] is False
    assert result["root_cause"] == "镜像仓库网络不可达"
    assert events == []


def test_rca_lite_does_not_call_llm_twice_when_structured_validation_fails():
    node = RootCauseAnalyzerNode()
    node.ai_call = object()

    def _fake_call_structured_agent(*args, **kwargs):
        return None, SimpleNamespace(result='{"phenomenon":"Pod 异常","confidence":0.9}'), []

    node._call_structured_agent = _fake_call_structured_agent

    result, _events = node._analyze_with_llm_lite(
        question="我的集群有什么问题",
        layer=Layer.L3,
        evidence_summary="# 已验证事实\nPod 异常",
    )

    assert result["confidence"] <= 0.2
    assert "不符合 RCA 结构化输出合同" in result["confidence_reason"]


def test_evidence_prompt_uses_layer_handoff_in_user_message_not_system_prompt(monkeypatch):
    node = EvidenceCollectorNode()
    node.workflow_config_override = {"evidence": {"agent_structured_output": False}}
    captured = {}

    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            captured["structured_question"] = question
            captured["structured_system_prompt"] = system_prompt
            return schema.model_validate({
                "layer": "L3",
                "evidence_plan": [
                    {
                        "id": "e1",
                        "description": "验证 Service Endpoints",
                        "level": "critical",
                        "tool": "run_bash_command",
                        "command": "kubectl get endpoints svc-a -n default -o wide",
                        "purpose": "确认 Endpoints 仍为空",
                    }
                ],
                "collection_strategy": "最小验证",
            }), "{}"

    node.ai_call = _StructuredAICall()

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured["question"] = question
        captured["system_prompt"] = system_prompt
        return SimpleNamespace(result="已执行"), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "run_bash_command",
                "result": "No resources found in default namespace.",
            }
        ]

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

    assert "上游定位结构化结果 layer_handoff" in captured["structured_question"]
    assert "Service svc-a 没有 Endpoints" in captured["structured_question"]
    assert "Service svc-a 没有 Endpoints" not in captured["structured_system_prompt"]
    assert "既有 evidence_plan" in captured["question"]
    assert plan[0]["id"] == "e1"
    assert events[0]["tool_name"] == "run_bash_command"


def test_evidence_user_message_consumes_layer_matched_runbooks_without_hardcoded_recommendations():
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
    assert "evidence_plan 阶段不要重新选择 runbook" in message
    assert "pod_status_keyword" in message
    assert "pod_abnormal_type" in message
    assert "matched_runbooks" in message
    assert "evidence_plan 第一项必须是 fetch_runbook" not in message
    assert "recommended_runbooks" not in message


def test_evidence_user_message_highlights_current_abnormal_summary_without_archive_noise():
    layer_handoff = {
        "layer": "L3",
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
        "current_abnormal_summary": {
            "status_counts": {
                "ImagePullBackOff": 3,
                "ErrImagePull": 1,
                "Terminating": 1,
                "Running": 46,
            },
            "selected_rows": [
                "aaa test1-redis-master-0 0/1 ImagePullBackOff 0 30h",
                "aiops-e2e terminating-stuck 0/1 Terminating 0 8d",
            ],
            "raw_ref": "/data/redis/archive/raw.txt",
            "structured_ref": "/data/redis/archive/structured.json",
        },
        "issue_groups": [
            {
                "group_id": "g1",
                "status_keywords": ["ImagePullBackOff", "ErrImagePull"],
                "pod_abnormal_type": "ImagePullFailed",
                "compatible_layers": ["L3"],
                "entities": [{"kind": "Pod", "namespace": "aaa", "name": "test1-redis-master-0"}],
            },
            {
                "group_id": "g2",
                "status_keywords": ["Terminating"],
                "pod_abnormal_type": "TerminatingStuck",
                "compatible_layers": ["L1"],
                "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"}],
            },
        ],
        "active_signals": [
            {
                "source": "kubectl_get_by_kind_in_cluster",
                "signal": "status_counts={'ImagePullBackOff': 3, 'Terminating': 1}",
                "raw_ref": "/data/redis/archive/tools/raw.txt",
                "summary_ref": "/data/redis/archive/tools/summary.txt",
            }
        ],
        "archive_ref": "/data/redis/archive/layer/handoff.json",
    }

    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L3",
        layer_handoff=json.dumps(layer_handoff, ensure_ascii=False),
    )

    assert "# 当前异常结构化摘要（必须优先审查）" in message
    assert "ImagePullBackOff: 3" in message
    assert "Terminating: 1" in message
    assert "g2: statuses=Terminating" in message
    assert "非 Running/Completed/Succeeded/Ready/Bound/Active 的状态都需要至少最小验证" in message
    assert "/data/redis/archive" not in message


def test_evidence_logs_user_prompt_input_only_once(monkeypatch, caplog):
    node = EvidenceCollectorNode()
    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            return schema.model_validate({
                "layer": "L0",
                "evidence_plan": [],
                "collection_strategy": "",
            }), "{}"

    node.ai_call = _StructuredAICall()

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

    assert "primary_pod" not in handoff
    assert handoff["abnormal_pods"] == [
        {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"}
    ]


def test_layer_handoff_builds_issue_groups_from_current_abnormal_pods():
    node = LayerClassifierNode()
    layer_result = {
        "layer": "L3",
        "derived_layer": "L3",
        "layers": ["L3", "L1"],
        "confidence": 0.92,
        "reasoning": "发现 ImagePull 和 Terminating 两类异常",
        "primary_pod": {"name": "redis-master-0", "namespace": "aaa"},
        "abnormal_pods": [
            {"name": "redis-master-0", "namespace": "aaa", "status": "ImagePullBackOff"},
            {"name": "redis-slave-0", "namespace": "aaa", "status": "ErrImagePull"},
            {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"},
        ],
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
        "status_category": "image_registry",
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE IP NODE LABELS",
                "selected_rows": [
                    "aaa redis-master-0 0/1 ImagePullBackOff 0 29h 172.16.166.186 node1 app=redis",
                    "aaa redis-slave-0 0/1 ErrImagePull 0 29h 172.16.166.164 node1 app=redis",
                    "aiops-e2e terminating-stuck 0/1 Terminating 0 8d <none> node1 pod_abnormal_type=TerminatingStuck,expected_layer=L1",
                ],
            },
            "result": "Pod table",
        }
    ]

    handoff = node._build_layer_handoff(
        question="我的集群有什么问题",
        layer_result=layer_result,
        layer=Layer.L3,
        layers=[Layer.L3, Layer.L1],
        thinking_events=events,
    )

    groups = handoff["issue_groups"]
    assert len(groups) == 2
    assert groups[0]["entities"] == [
        {"kind": "Pod", "namespace": "aaa", "name": "redis-master-0"},
        {"kind": "Pod", "namespace": "aaa", "name": "redis-slave-0"},
    ]
    assert "primary_entities" not in groups[0]
    assert "is_primary" not in groups[0]
    assert groups[0]["pod_abnormal_type"] == "ImagePullFailed"
    assert groups[0]["compatible_layers"] == ["L3"]
    assert groups[0]["status_keywords"] == ["ImagePullBackOff", "ErrImagePull"]
    terminating_group = next(group for group in groups if group["status_keywords"] == ["Terminating"])
    assert terminating_group["pod_abnormal_type"] == "TerminatingStuck"
    assert terminating_group["compatible_layers"] == ["L1"]
    assert terminating_group["possible_scenarios"]
    assert any("finalizer" in item["scenario"].lower() for item in terminating_group["possible_scenarios"])
    assert terminating_group["entities"] == [
        {"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"}
    ]
    summary = handoff["current_abnormal_summary"]
    assert summary["status_counts"] == {
        "ImagePullBackOff": 1,
        "ErrImagePull": 1,
        "Terminating": 1,
    }
    assert summary["total_abnormal"] == 3
    assert summary["source"] == "kubectl_get_by_kind_in_cluster"


def test_layer_handoff_includes_running_pod_marked_as_recent_restart():
    node = LayerClassifierNode()
    recent_row = (
        "aiops-traced-oom trace-oom-api-598dcf-x6v6n "
        "1/1 Running 234 (5m23s ago) 5d"
    )
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE",
                "status_counts": {"Running": 2},
                "recent_restart_count": 1,
                "recent_restart_rows": [recent_row],
                "selected_rows": [recent_row],
            },
        }
    ]

    handoff = node._build_layer_handoff(
        question="我的集群有什么问题",
        layer_result={
            "layer": "L2",
            "derived_layer": "L2",
            "confidence": 0.8,
            "reasoning": "集群状态扫描",
            "abnormal_pods": [],
        },
        layer=Layer.L2,
        layers=[Layer.L2],
        thinking_events=events,
    )

    assert handoff["abnormal_pods"] == [
        {
            "name": "trace-oom-api-598dcf-x6v6n",
            "namespace": "aiops-traced-oom",
            "status": "RecentRestart",
        }
    ]
    assert handoff["current_abnormal_summary"]["status_counts"] == {
        "RecentRestart": 1
    }
    assert handoff["current_abnormal_summary"]["total_abnormal"] == 1
    assert handoff["current_abnormal_summary"]["selected_rows"] == [recent_row]
    assert handoff["issue_groups"][0]["status_keywords"] == ["RecentRestart"]
    assert handoff["issue_groups"][0]["pod_abnormal_type"] == "CrashLoopBackOffRuntime"
    assert handoff["issue_groups"][0]["compatible_layers"] == ["L2"]


def test_layer_handoff_explicit_pod_scope_excludes_unrelated_global_abnormalities():
    node = LayerClassifierNode()
    target_namespace = "aiops-traced-oom"
    target_pod = "trace-oom-api-598dcf5996-x6v6n"
    layer_result = {
        "layer": "L2",
        "derived_layer": "L2",
        "confidence": 0.9,
        "reasoning": "目标 Pod 反复重启",
        "key_entities": [
            {"type": "pod", "name": target_pod, "namespace": target_namespace},
        ],
        "abnormal_pods": [
            {"name": target_pod, "namespace": target_namespace, "status": "CrashLoopBackOff"},
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
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE",
                "status_counts": {
                    "CrashLoopBackOff": 1,
                    "Pending": 3,
                    "Running": 60,
                },
                "selected_rows": [
                    f"{target_namespace} {target_pod} 0/1 CrashLoopBackOff 9 35m",
                    "monitor exporter-a 0/1 Pending 0 5d",
                    "monitor exporter-b 0/1 Pending 0 5d",
                    "monitor exporter-c 0/1 Pending 0 5d",
                ],
            },
        }
    ]

    handoff = node._build_layer_handoff(
        question=(
            f"请诊断 namespace {target_namespace} 中 Pod {target_pod} "
            "当前反复重启的问题"
        ),
        layer_result=layer_result,
        layer=Layer.L2,
        layers=[Layer.L2],
        thinking_events=events,
    )

    assert handoff["diagnosis_scope"] == "explicit_pod"
    assert handoff["abnormal_pods"] == [
        {
            "name": target_pod,
            "namespace": target_namespace,
            "status": "CrashLoopBackOff",
        }
    ]
    assert len(handoff["issue_groups"]) == 1
    assert handoff["issue_groups"][0]["entities"] == [
        {"kind": "Pod", "namespace": target_namespace, "name": target_pod}
    ]
    assert handoff["current_abnormal_summary"]["status_counts"] == {
        "CrashLoopBackOff": 1
    }
    assert handoff["current_abnormal_summary"]["total_abnormal"] == 1
    assert handoff["current_abnormal_summary"]["selected_rows"] == [
        f"{target_namespace} {target_pod} 0/1 CrashLoopBackOff 9 35m"
    ]


def test_layer_guard_rejects_healthy_when_current_tool_scan_has_abnormal_pods():
    node = LayerClassifierNode()
    layer_result = {
        "layer": "HEALTHY",
        "derived_layer": "HEALTHY",
        "layers": ["HEALTHY"],
        "confidence": 0.5,
        "reasoning": "模型误判为健康",
        "abnormal_pods": [{"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"}],
        "pod_status_keyword": "Terminating",
        "pod_abnormal_type": "TerminatingStuck",
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE IP NODE LABELS",
                "status_counts": {"Running": 60, "Terminating": 1},
                "selected_rows": [
                    "aiops-e2e terminating-stuck 0/1 Terminating 0 42m 172.16.166.189 node1 pod_abnormal_type=TerminatingStuck"
                ],
            },
            "result": "Pod table",
        }
    ]
    handoff = node._build_layer_handoff(
        question="我的集群有什么问题",
        layer_result=layer_result,
        layer=Layer.HEALTHY,
        layers=[Layer.HEALTHY],
        thinking_events=events,
    )

    layer, layers = node._guard_healthy_with_active_abnormalities(
        layer_result=layer_result,
        layer_handoff=handoff,
        layer=Layer.HEALTHY,
        layers=[Layer.HEALTHY],
    )

    assert layer == Layer.L1
    assert layers == [Layer.L1]
    assert layer_result["layer"] == "L1"
    assert handoff["layer"] == "L1"
    assert handoff["current_abnormal_summary"]["total_abnormal"] == 1


def test_layer_handoff_merges_current_scan_when_lite_output_omits_secondary_issue():
    node = LayerClassifierNode()
    layer_result = {
        "layer": "L3",
        "derived_layer": "L3",
        "layers": ["L3"],
        "confidence": 0.95,
        "reasoning": "lite 只识别了 ImagePullBackOff",
        "primary_pod": {"name": "redis-master-0", "namespace": "aaa"},
        "abnormal_pods": [
            {"name": "redis-master-0", "namespace": "aaa", "status": "ImagePullBackOff"},
            {"name": "redis-slave-0", "namespace": "aaa", "status": "ImagePullBackOff"},
        ],
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE",
                "selected_rows": [
                    "aaa redis-master-0 0/1 ImagePullBackOff 0 32h",
                    "aaa redis-slave-0 0/1 ImagePullBackOff 0 32h",
                    "aiops-e2e terminating-stuck 0/1 Terminating 0 8d",
                ],
            },
        }
    ]

    handoff = node._build_layer_handoff(
        question="我的集群有什么问题",
        layer_result=layer_result,
        layer=Layer.L3,
        layers=[Layer.L3],
        thinking_events=events,
    )

    assert {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"} in handoff["abnormal_pods"]
    terminating_group = next(group for group in handoff["issue_groups"] if group["status_keywords"] == ["Terminating"])
    assert terminating_group["pod_abnormal_type"] == "TerminatingStuck"


def test_layer_handoff_abnormal_summary_uses_structured_status_counts_and_filters_normal_statuses():
    node = LayerClassifierNode()
    layer_result = {
        "layer": "L3",
        "primary_pod": {"name": "redis-master-0", "namespace": "aaa"},
        "abnormal_pods": [
            {"name": "redis-master-0", "namespace": "aaa", "status": "ImagePullBackOff"},
            {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"},
        ],
        "pod_status_keyword": "ImagePullBackOff",
        "pod_abnormal_type": "ImagePullFailed",
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE",
                "status_counts": {
                    "ImagePullBackOff": 3,
                    "ErrImagePull": 1,
                    "Terminating": 1,
                    "Running": 46,
                    "Completed": 2,
                    "Succeeded": 1,
                    "Ready": 3,
                    "Bound": 7,
                    "Active": 1,
                },
                "selected_rows": [
                    "aaa redis-master-0 0/1 ImagePullBackOff 0 31h",
                    "aiops-e2e terminating-stuck 0/1 Terminating 0 8d",
                    "xnet old-job 0/1 Completed 0 4d",
                ],
            },
        }
    ]

    handoff = node._build_layer_handoff(
        question="我的集群有什么问题",
        layer_result=layer_result,
        layer=Layer.L3,
        layers=[Layer.L3],
        thinking_events=events,
    )

    summary = handoff["current_abnormal_summary"]
    assert summary["status_counts"] == {
        "ImagePullBackOff": 3,
        "ErrImagePull": 1,
        "Terminating": 1,
    }
    assert "Completed" not in summary["status_counts"]
    assert "Running" not in summary["status_counts"]
    assert "Ready" not in summary["status_counts"]
    assert summary["selected_rows"] == [
        "aaa redis-master-0 0/1 ImagePullBackOff 0 31h",
        "aiops-e2e terminating-stuck 0/1 Terminating 0 8d",
    ]


def test_evidence_conflicts_mark_abnormal_pod_notfound_as_critical():
    conflicts = EvidenceCollectorNode._build_evidence_conflicts(
        [
            {
                "tool": "kubectl_get_yaml",
                "data": 'Error from server (NotFound): pods "memhog-84859d84db-pn4l2" not found',
            }
        ],
        {
            "abnormal_pods": [
                {
                    "name": "memhog-84859d84db-pn4l2",
                    "namespace": "aiops-e2e",
                }
            ]
        },
    )

    assert conflicts[0]["severity"] == "critical"
    assert conflicts[0]["object_missing"] is True
    assert conflicts[0]["object"] == {
        "kind": "Pod",
        "name": "memhog-84859d84db-pn4l2",
        "namespace": "aiops-e2e",
    }


def test_evidence_conflicts_do_not_mark_container_notfound_as_abnormal_pod_missing():
    conflicts = EvidenceCollectorNode._build_evidence_conflicts(
        [
            {
                "tool": "run_bash_command",
                "data": (
                    'Error from server (BadRequest): previous terminated container "test1-redis" '
                    'in pod "test1-redis-master-0" not found'
                ),
            }
        ],
        {
            "abnormal_pods": [
                {
                    "name": "test1-redis-master-0",
                    "namespace": "aaa",
                }
            ]
        },
    )

    assert conflicts[0]["severity"] == "warning"
    assert conflicts[0]["object_missing"] is False
    assert "object" not in conflicts[0]


def test_rca_does_not_block_entire_root_cause_when_one_abnormal_pod_is_missing():
    node = RootCauseAnalyzerNode()
    state = {
        "question": "我的集群有什么问题",
        "layer": Layer.L2,
        "layer_handoff": {
            "abnormal_pods": [{"name": "memhog-84859d84db-pn4l2", "namespace": "aiops-e2e"}],
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

    assert "当前不存在" not in result["root_cause"]
    assert rca["confidence"] <= 0.7


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


def test_rca_context_bounds_tool_output_and_preserves_key_prefix():
    node = RootCauseAnalyzerNode()
    long_raw = "name: current-pod\nstatus: ImagePullBackOff\n" + ("normal pod running\n" * 200)
    evidence_analysis = json.dumps({
        "tool_data": [
            {"tool": "kubectl_describe", "data": long_raw},
        ],
    }, ensure_ascii=False)

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "kubectl_describe" in context
    assert "status: ImagePullBackOff" in context
    assert "normal pod running" in context
    assert len(context) < len(long_raw)
    assert "截断" in context


def test_rca_context_includes_aiops_agent_context():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "compact summary",
                "agent_context": json.dumps({
                    "dimension_details": {
                        "tracing": {
                            "flows": [
                                {
                                    "request": "GET /allocate?mib=2&step=674",
                                    "duration_us": "5752",
                                    "trace_id": "42ea12f3f50fe8b2e759a221ff0f3f4a",
                                }
                            ],
                            "spans": [
                                {
                                    "trace_id": "42ea12f3f50fe8b2e759a221ff0f3f4a",
                                    "attributes": {
                                        "aiops.allocated_mib.before": 60,
                                        "aiops.allocated_mib.after": 62,
                                    },
                                }
                            ],
                        },
                        "topology": {
                            "edges": [
                                {
                                    "relationship": "Pod --calls--> Pod",
                                    "directness": "direct",
                                    "confidence": "high",
                                }
                            ]
                        },
                    }
                }, ensure_ascii=False),
            }
        ],
    }, ensure_ascii=False)

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "AIOps 结构化可观测性上下文" in context
    assert "42ea12f3f50fe8b2e759a221ff0f3f4a" in context
    assert "aiops.allocated_mib.before" in context
    assert "Pod --calls--> Pod" in context


def test_rca_context_prefers_deterministic_aiops_agent_facts():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "compact summary",
                "agent_context": '{"dimension_details":{"tracing":{"flows":[]}}}',
                "agent_facts": (
                    "K8S_SIGNAL signal_id=sig-k8s-present strength=strong "
                    "observed=\"Last terminated state: business-api=OOMKilled exit=137\" "
                    "evidence_refs=[\"k8s.trace-oom-api.last-terminated\"]\n"
                    "TRACE_CORRELATION log_tempo_trace_ids=[\"369c929229004108c4066c41656d49e8\"] "
                    "deepflow_trace_ids=[\"4faac0ec561b6b6febe9e0d73dc68a86\"] "
                    "do_not_merge=true\n"
                    "DEEPFLOW_SEMANTICS duration_us=0 is_not_failure_evidence=true\n"
                    "METRIC metric=container_memory_working_set_bytes "
                    "start=3.8Mi max=69.0Mi limit=80.0Mi\n"
                    "DEEPFLOW src=172.16.104.8 dst=172.16.104.13 "
                    "duration_us=0 trace_id=4faac0ec561b6b6febe9e0d73dc68a86\n"
                    "TOPOLOGY relationship=\"Pod --calls--> Pod\" "
                    "source=driver target=api directness=direct confidence=high"
                ),
            }
        ],
    }, ensure_ascii=False)

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "AIOps 确定性可观测事实" in context
    assert "duration_us=0" in context
    assert "4faac0ec561b6b6febe9e0d73dc68a86" in context
    assert 'relationship="Pod --calls--> Pod"' in context
    assert "do_not_merge=true" in context
    assert "is_not_failure_evidence=true" in context


def test_conclusion_context_includes_aiops_agent_context():
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "compact summary",
                "agent_context": json.dumps({
                    "coverage": {
                        "metrics": "present",
                        "logs": "present",
                        "tracing": "present",
                        "topology": "present",
                    },
                    "dimension_details": {
                        "tracing": {
                            "flows": [
                                {
                                    "trace_id": "42ea12f3f50fe8b2e759a221ff0f3f4a",
                                    "request": "GET /allocate?mib=2&step=674",
                                }
                            ]
                        },
                        "topology": {
                            "edges": [
                                {
                                    "relationship": "ReplicaSet --owned_by--> Deployment",
                                    "source": "trace-oom-api-rs",
                                    "target": "trace-oom-api",
                                    "directness": "direct",
                                    "confidence": "high",
                                }
                            ]
                        },
                    },
                }, ensure_ascii=False),
            }
        ],
    }, ensure_ascii=False)

    context = ConclusionFormatterNode._build_structured_diagnosis_context(
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
    )

    assert "aiops_observability_context" in context
    assert "42ea12f3f50fe8b2e759a221ff0f3f4a" in context
    assert "ReplicaSet --owned_by--> Deployment" in context


def test_conclusion_context_includes_deterministic_aiops_agent_facts():
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "compact summary",
                "agent_facts": (
                    "K8S_SIGNAL signal_id=sig-k8s-present strength=strong "
                    "observed=\"Last terminated state: business-api=OOMKilled exit=137\" "
                    "evidence_refs=[\"k8s.trace-oom-api.last-terminated\"]\n"
                    "TRACE_CORRELATION log_tempo_trace_ids=[\"369c929229004108c4066c41656d49e8\"] "
                    "deepflow_trace_ids=[\"4faac0ec561b6b6febe9e0d73dc68a86\"] "
                    "do_not_merge=true\n"
                    "LOG event=allocate trace_id=369c929229004108c4066c41656d49e8 "
                    "path=/allocate?mib=2&step=855 allocated_mib=62\n"
                    "TEMPO trace_id=369c929229004108c4066c41656d49e8 "
                    "span=\"GET /allocate\" aiops.allocated_mib.before=60 "
                    "aiops.allocated_mib.after=62"
                ),
            }
        ],
    }, ensure_ascii=False)

    context = ConclusionFormatterNode._build_structured_diagnosis_context(
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
    )

    assert "aiops_observability_facts" in context
    assert "Last terminated state: business-api=OOMKilled exit=137" in context
    assert "REPORT_MUST_QUOTE_K8S_SIGNAL_VERBATIM=true" in context
    assert "REPORT_MUST_QUOTE_OBSERVABILITY_FACTS_VERBATIM=true" in context
    assert "IGNORE_UNSUPPORTED_LAYER_NUMERIC_FACTS=true" in context
    assert "allocated_mib=62" in context
    assert "aiops.allocated_mib.before=60" in context
    assert "do_not_merge=true" in context


def test_conclusion_context_builds_immutable_exact_topology_contract():
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "compact summary",
                "agent_context": json.dumps({
                    "topology_summary": {
                        "entity_count": 11,
                        "edge_count": 10,
                    },
                    "dimension_details": {
                        "topology": {
                            "edges": [
                                {
                                    "relationship": "Pod --calls--> Pod",
                                    "source": "trace-oom-driver",
                                    "target": "trace-oom-api",
                                    "source_system": "deepflow+kubernetes",
                                    "directness": "direct",
                                    "confidence": "high",
                                }
                            ]
                        }
                    },
                }, ensure_ascii=False),
                "agent_facts": "\n".join([
                    (
                        'TOPOLOGY relationship="Pod --calls--> Pod" '
                        "source=trace-oom-driver target=trace-oom-api "
                        "directness=direct confidence=high"
                    ),
                    (
                        'TOPOLOGY relationship="Service --selects--> Pod" '
                        "source=trace-oom-api target=trace-oom-api-pod "
                        "directness=direct confidence=high"
                    ),
                    (
                        'TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" '
                        "source=trace-oom-api-pod target=trace-oom-api-rs "
                        "directness=direct confidence=high"
                    ),
                    (
                        'TOPOLOGY relationship="ReplicaSet --owned_by--> Deployment" '
                        "source=trace-oom-api-rs target=trace-oom-api "
                        "directness=direct confidence=high"
                    ),
                ]),
            }
        ],
    }, ensure_ascii=False)

    context = ConclusionFormatterNode._build_structured_diagnosis_context(
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
    )

    assert "TOPOLOGY_ENTITY_COUNT value=11" in context
    assert "TOPOLOGY_EXACT_EDGES count=4" in context
    assert "REPORT_MUST_QUOTE_TOPOLOGY_VERBATIM=true" in context
    assert "FORBID_RELATIONSHIP_REVERSAL=true" in context
    assert "TOPOLOGY_SCOPE relationships_only=true" in context
    assert "health_not_proven=true" in context
    assert "complete_call_chain_not_proven=true" in context
    assert "METRIC_SCOPE supporting_evidence_only=true" in context
    assert "EXIT_CODE_SCOPE symbolic_name_requires_explicit_evidence=true" in context
    assert (
        'TOPOLOGY relationship="Pod --owned_by--> ReplicaSet" '
        "source=trace-oom-api-pod target=trace-oom-api-rs "
        "directness=direct confidence=high"
    ) in context
    assert (
        'TOPOLOGY relationship="ReplicaSet --owned_by--> Deployment" '
        "source=trace-oom-api-rs target=trace-oom-api "
        "directness=direct confidence=high"
    ) in context


def test_conclusion_context_keeps_per_case_topology_counts_for_multiple_cases():
    def tool_item(case_id, entity_count, edge_count, pod):
        return {
            "tool": "collect_aiops_case",
            "data": "compact summary",
            "agent_context": json.dumps({
                "case_id": case_id,
                "topology_summary": {
                    "entity_count": entity_count,
                    "edge_count": edge_count,
                },
                "dimension_details": {
                    "topology": {
                        "edges": [
                            {
                                "relationship": "Pod --owned_by--> Deployment",
                                "source": pod,
                                "target": f"{pod}-deployment",
                                "source_system": "kubernetes",
                                "directness": "direct",
                                "confidence": "high",
                            }
                        ]
                    }
                },
            }, ensure_ascii=False),
        }

    evidence_analysis = json.dumps({
        "tool_data": [
            tool_item("case-a", 13, 12, "pod-a"),
            tool_item("case-b", 11, 10, "pod-b"),
        ],
    }, ensure_ascii=False)

    context = ConclusionFormatterNode._build_structured_diagnosis_context(
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
    )

    assert "TOPOLOGY_CASE_COUNT case_id=case-a entities=13 edges=12" in context
    assert "TOPOLOGY_CASE_COUNT case_id=case-b entities=11 edges=10" in context
    assert "TOPOLOGY_ENTITY_COUNT value=" not in context
    assert "exact_edges_are_diagnostic_subset=true" in context


def test_conclusion_context_marks_aiops_case_as_not_collected_without_coarse_tool():
    evidence_analysis = json.dumps(
        {
            "tool_data": [
                {
                    "tool": "kubectl_describe",
                    "data": "Reason: OOMKilled, Exit Code: 137",
                },
                {
                    "tool": "execute_prometheus_instant_query",
                    "data": "83886080",
                },
            ]
        },
        ensure_ascii=False,
    )

    context = ConclusionFormatterNode._build_structured_diagnosis_context(
        evidence_analysis=evidence_analysis,
        rca_analysis="{}",
    )

    assert "aiops_observability_status: not_collected" in context
    assert "禁止声称本轮基于 collect_aiops_case" in context
    assert "aiops_observability_facts:" not in context


def test_rca_execute_sanitizes_large_evidence_fields_before_handoff():
    node = RootCauseAnalyzerNode()
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    raw_blob = "raw event line\n" * 500
    rca_payload = {
        "phenomenon": "Pod ImagePullBackOff",
        "evidence_inventory": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "raw_data": raw_blob,
                "data": raw_blob,
                "collected": True,
            }
        ],
        "evidence_analysis": [
            {
                "evidence_id": "e1",
                "raw_data": raw_blob,
                "interpretation": "镜像拉取失败",
            }
        ],
        "causal_chain": {"root_cause": "节点出口网络超时"},
        "root_cause": "节点出口网络超时导致镜像拉取失败",
        "root_cause_summary": "节点出口网络超时导致镜像拉取失败",
        "confidence": 0.86,
        "primary_runbooks": ["pod-imagepull-failed.md"],
        "limitations": "",
    }

    node._analyze_with_llm = lambda question, layer, evidence_summary: (rca_payload, [])

    result = node.execute({
        "question": "我的集群有什么问题",
        "layer": Layer.L3,
        "evidence_items": [],
        "evidence_analysis": "{}",
    })

    serialized = result["rca_analysis"]
    parsed = json.loads(serialized)
    assert parsed["root_cause"] == "节点出口网络超时导致镜像拉取失败"
    assert "raw event line\nraw event line\nraw event line" not in serialized
    assert len(serialized) < 3000
    assert "截断" in parsed["evidence_inventory"][0]["raw_data"]
    assert "截断" in parsed["evidence_analysis"][0]["raw_data"]


def test_rca_context_includes_evidence_quality_contract():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "source_coverage": {
            "cases": [
                {
                    "target": "demo/api",
                    "case_id": "case-demo-api",
                    "dimensions": {
                        "k8s": "present",
                        "metrics": "present",
                        "logs": "present",
                        "tracing": "present",
                        "topology": "present",
                    },
                }
            ]
        },
        "case_target_coverage": {
            "total": 1,
            "collected": 1,
            "rate": 1.0,
        },
        "detail_retrieval": {
            "evaluated": True,
            "requested": 1,
            "collected": 1,
            "refs": ["logs.target.previous"],
        },
        "diagnostic_sufficiency_summary": {
            "score": 0.5,
            "label": "部分充分",
        },
        "unresolved_questions": [
            "demo/api: 指标只有单点样本，无法确认异常时间窗趋势",
        ],
        "tool_data": [],
    }, ensure_ascii=False)

    context = node._build_rca_context({
        "layer_analysis": "{}",
        "evidence_items": [],
        "evidence_analysis": evidence_analysis,
    })

    assert "# 证据质量合同" in context
    assert '"rate": 1.0' in context
    assert '"score": 0.5' in context
    assert "logs.target.previous" in context
    assert "指标只有单点样本" in context
    assert "source_coverage" in context


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


def test_rca_context_uses_fact_ledgers_without_duplicate_aiops_representations():
    node = RootCauseAnalyzerNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    fact_record = _canonical_fact_record(entity_id=entity_id)
    evidence_analysis = json.dumps({
        "source_coverage": {
            "cases": [{"target": "demo/api", "case_id": "case-facts"}],
        },
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "DUPLICATE COARSE SUMMARY",
                "agent_facts": "DUPLICATE AGENT FACTS",
                "agent_context": '{"dimension_details":{"logs":{"samples":[]}}}',
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-facts",
                    "scope_entity_ids": [entity_id],
                    "records": [fact_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
            },
            {
                "tool": "kubectl_describe",
                "data": "Name: api\nStatus: Running",
            },
        ],
    })

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "AIOps Fact Ledger" in context
    assert "case-facts" in context
    assert fact_record["fact_id"] in context
    assert "kubectl_describe" in context
    assert "DUPLICATE COARSE SUMMARY" not in context
    assert "DUPLICATE AGENT FACTS" not in context
    assert "dimension_details" not in context


def test_rca_persisted_no_ledger_aiops_item_uses_one_representation():
    node = RootCauseAnalyzerNode()
    structured_context = json.dumps({
        "status": "partial",
        "dimension_details": {
            "logs": {
                "samples": [
                    {"message": "STRUCTURED CONTEXT REPRESENTATION"}
                ]
            }
        },
    })
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "RAW REPRESENTATION",
                "agent_facts": "TEXT FACT REPRESENTATION",
                "agent_context": structured_context,
            }
        ],
    })

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "STRUCTURED CONTEXT REPRESENTATION" in context
    assert "TEXT FACT REPRESENTATION" not in context
    assert "RAW REPRESENTATION" not in context
    assert context.count("STRUCTURED CONTEXT REPRESENTATION") == 1


def test_rca_execute_validates_fact_references_before_handoff():
    node = RootCauseAnalyzerNode()
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    entity_id = "k8s.pod:demo/api:uid-a"
    fact_record = _canonical_fact_record(entity_id=entity_id)
    node._analyze_with_llm = lambda question, layer, evidence_summary: (
        {
            "diagnostic_status": "diagnosed",
            "phenomenon": "Scoped entity is abnormal",
            "root_cause": "Unsupported model claim",
            "root_cause_summary": "Unsupported model claim",
            "supporting_fact_ids": ["fact-ffffffffffff"],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "hypotheses": [
                {
                    "hypothesis_id": "hyp-a",
                    "entity_id": entity_id,
                    "summary": "Unsupported model claim",
                    "supporting_fact_ids": ["fact-ffffffffffff"],
                    "contradicting_fact_ids": [],
                    "unknowns": [],
                    "confidence": 0.95,
                }
            ],
            "confidence": 0.95,
            "confidence_reason": "Model asserted unsupported evidence",
        },
        [],
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "data": "compact summary",
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-facts",
                    "scope_entity_ids": [entity_id],
                    "records": [fact_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
            }
        ],
    })

    result = node.execute({
        "question": "What is wrong with the scoped entity?",
        "layer": Layer.L2,
        "evidence_items": [],
        "evidence_analysis": evidence_analysis,
        "thinking_events": [],
    })
    rca = json.loads(result["rca_analysis"])

    assert rca["diagnostic_status"] == "inconclusive"
    assert rca["supporting_fact_ids"] == []
    assert rca["claim_validation"]["invalid_fact_ids"] == ["fact-ffffffffffff"]
    assert result["root_cause"] != "Unsupported model claim"


def test_rca_validation_preserves_cross_ledger_collision_diagnostics():
    node = RootCauseAnalyzerNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    first_record = _canonical_fact_record(
        entity_id=entity_id,
        value={"message": "first observation"},
        evidence_refs=["logs:first"],
    )
    second_record = {
        **_canonical_fact_record(
            entity_id=entity_id,
            value={"message": "second observation"},
            evidence_refs=["logs:second"],
        ),
        "fact_id": first_record["fact_id"],
    }
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-first",
                    "scope_entity_ids": [entity_id],
                    "records": [first_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
            },
            {
                "tool": "get_aiops_case",
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-second",
                    "scope_entity_ids": [entity_id],
                    "records": [second_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
            },
        ],
    })
    claim = {
        "diagnostic_status": "diagnosed",
        "phenomenon": "Scoped entity is abnormal",
        "root_cause": "Candidate",
        "root_cause_summary": "Candidate",
        "supporting_fact_ids": [first_record["fact_id"]],
        "contradicting_fact_ids": [],
        "unknowns": [],
        "hypotheses": [
            {
                "hypothesis_id": "hyp-collision",
                "entity_id": entity_id,
                "summary": "Candidate",
                "supporting_fact_ids": [first_record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        "confidence": 0.9,
        "confidence_reason": "Claimed support",
    }

    result = node._validate_rca_result_against_evidence(
        claim,
        evidence_analysis,
        question="What is wrong with the scoped entity?",
        layer=Layer.L2,
    )

    assert result["diagnostic_status"] == "inconclusive"
    assert first_record["fact_id"] in result["claim_validation"]["invalid_fact_ids"]
    assert any(
        "collision" in reason
        for reason in result["claim_validation"]["reasons"]
    )


def _validate_topology_record_through_rca(
    *,
    topology_value,
    required_entity_id="k8s.pod:demo/api:uid-a",
):
    node = RootCauseAnalyzerNode()
    owner_id = "k8s.service:demo/api"
    record = _canonical_fact_record(
        entity_id=owner_id,
        entity_kind="TopologyEdge",
        namespace="demo",
        entity_name="api",
        dimension="topology",
        fact_type="relationship",
        attribute="topology.relationship",
        value=topology_value,
        source_system="topology",
        directness="direct",
        confidence="high",
        strength="strong",
        evidence_refs=["topology:reviewer-probe"],
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-topology-reviewer-probe",
                    "scope_entity_ids": [required_entity_id],
                    "records": [record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
            }
        ],
    })
    claim = {
        "diagnostic_status": "diagnosed",
        "phenomenon": "Scoped entity is abnormal",
        "root_cause": "Topology-backed candidate",
        "root_cause_summary": "Topology-backed candidate",
        "supporting_fact_ids": [record["fact_id"]],
        "contradicting_fact_ids": [],
        "unknowns": [],
        "hypotheses": [
            {
                "hypothesis_id": "hyp-topology-reviewer-probe",
                "entity_id": required_entity_id,
                "summary": "Topology-backed candidate",
                "supporting_fact_ids": [record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        "confidence": 0.9,
        "confidence_reason": "Claimed complete typed topology support",
    }
    return node._validate_rca_result_against_evidence(
        claim,
        evidence_analysis,
        question="What is wrong with the scoped entity?",
        layer=Layer.L2,
    )


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "diagnosisReason",
        "causalRole",
        "causalRoleState",
        "prefixCausalRoleSuffix",
        "PREFIX.CAUSAL/ROLE-SUFFIX",
        "diagnosticRole",
        "diagnosticRoleState",
        "prefixDiagnosticRoleSuffix",
        "PREFIX.DIAGNOSTIC/ROLE-SUFFIX",
    ],
)
def test_rca_real_entry_rejects_evaluator_role_supporting_fact(forbidden_key):
    node = RootCauseAnalyzerNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    contaminated = _canonical_fact_record(
        entity_id=entity_id,
        value={
            "nested": [
                {
                    forbidden_key: "must not authorize diagnosed",
                }
            ]
        },
        evidence_refs=["logs:contaminated"],
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "collect_aiops_case",
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-contaminated",
                    "scope_entity_ids": [entity_id],
                    "records": [contaminated],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
            }
        ],
    })
    claim = {
        "diagnostic_status": "diagnosed",
        "phenomenon": "Scoped entity is abnormal",
        "root_cause": "Contaminated candidate",
        "root_cause_summary": "Contaminated candidate",
        "supporting_fact_ids": [contaminated["fact_id"]],
        "contradicting_fact_ids": [],
        "unknowns": [],
        "hypotheses": [
            {
                "hypothesis_id": "hyp-contaminated",
                "entity_id": entity_id,
                "summary": "Contaminated candidate",
                "supporting_fact_ids": [contaminated["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        "confidence": 0.9,
        "confidence_reason": "Claimed contaminated support",
    }

    result = node._validate_rca_result_against_evidence(
        claim,
        evidence_analysis,
        question="What is wrong with the scoped entity?",
        layer=Layer.L2,
    )

    assert result["diagnostic_status"] == "inconclusive"
    assert result["claim_validation"]["valid"] is False


@pytest.mark.parametrize(
    "topology_value",
    [
        {
            "target_entity_id": "k8s.pod:demo/api:uid-a",
            "relationship": "selects",
        },
        {
            "source_entity_id": "k8s.pod:demo/api:uid-a",
            "relationship": "owned_by",
        },
        {
            "source_entity_id": "k8s.service:demo/api",
            "target_entity_id": "k8s.pod:demo/api:uid-a",
        },
        {
            "source": {
                "entity_id": "k8s.service:demo/api",
                "kind": "ConfigMap",
            },
            "target": {
                "entity_id": "k8s.pod:demo/api:uid-a",
                "kind": "Pod",
            },
            "relation": "selects",
        },
        {
            "source_entity_id": "k8s.service:demo/api",
            "target_entity_id": "k8s.pod:demo/api:uid-wrong",
            "relationship": "selects",
        },
    ],
)
def test_rca_real_entry_rejects_incomplete_malformed_or_wrong_uid_topology(
    topology_value,
):
    result = _validate_topology_record_through_rca(
        topology_value=topology_value,
    )

    assert result["diagnostic_status"] == "inconclusive"
    assert result["claim_validation"]["valid"] is False


@pytest.mark.parametrize(
    "topology_value",
    [
        {
            "source_entity_id": "k8s.service:demo/api",
            "target_entity_id": "k8s.pod:demo/api:uid-a",
            "relationship": "selects",
        },
        {
            "source_entity_id": "k8s.pod:demo/api:uid-a",
            "target_entity_id": "k8s.service:demo/api",
            "relation": "selected_by",
        },
    ],
)
def test_rca_real_entry_accepts_forward_and_reversed_complete_topology(
    topology_value,
):
    result = _validate_topology_record_through_rca(
        topology_value=topology_value,
    )

    assert result["diagnostic_status"] == "diagnosed"
    assert result["claim_validation"]["valid"] is True


def test_evidence_to_rca_legacy_context_preserves_mandatory_identity_under_budget():
    evidence = EvidenceCollectorNode()
    tool_data = evidence._extract_tool_data_from_thinking([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "oversized legacy case",
            "structured": {
                "status": "case_collected",
                "case_id": "case-identity-envelope",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-a",
                },
                "dimension_details": {
                    "custom": {
                        f"optional-{index:04d}": "x" * 200
                        for index in range(500)
                    }
                },
            },
        }
    ])

    agent_context = tool_data[0]["agent_context"]
    parsed = json.loads(agent_context)
    rca_context = RootCauseAnalyzerNode()._extract_tool_data_for_rca(
        json.dumps({"tool_data": tool_data})
    )

    assert parsed != {}
    assert len(agent_context) <= 12000
    assert parsed["case_id"] == "case-identity-envelope"
    assert parsed["primary_entity"] == {
        "kind": "Pod",
        "namespace": "demo",
        "name": "api",
        "uid": "uid-a",
    }
    assert "case-identity-envelope" in rca_context
    assert '"namespace":"demo"' in rca_context
    assert '"name":"api"' in rca_context
    assert '"uid":"uid-a"' in rca_context
