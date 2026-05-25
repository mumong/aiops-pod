import json
import logging
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.skills.models import Layer
from app.core.workflow.schemas import RCAOutput
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
        "confidence_score": 0.86,
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
