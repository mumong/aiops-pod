import hashlib
import json
import logging
import os
import re
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import app.core.workflow.fact_contract as fact_contract_module
from app.core.skills.models import Layer
from app.core.workflow.entity_evidence_snapshot import build_selection_manifest
from app.core.workflow.schemas import EvidenceCollectionOutput, RCAOutput
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.root_cause_analyzer import (
    RCA_CONTEXT_MAX_CHARS,
    RCA_HANDOFF_MAX_CHARS,
    RCA_QUALITY_MAX_CHARS,
    RCA_SUPPLEMENTARY_MAX_CHARS,
    RCA_TOOL_CONTEXT_MAX_CHARS,
    RootCauseAnalyzerNode,
)


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


def _internally_authorized_tool_item(
    ledger,
    *,
    tool=None,
    status="query_succeeded",
    coverage="present",
    source_system=None,
    **extra,
):
    ledger_mapping = (
        ledger.model_dump(mode="json", exclude_none=True)
        if hasattr(ledger, "model_dump")
        else ledger
    )
    records = ledger_mapping.get("records") or []
    dimension = str((records[0] if records else {}).get("dimension") or "")
    selected_tool = tool or {
        "metrics": "execute_pod_promql",
        "tracing": "query_pod_tracing",
        "topology": "query_pod_topology",
    }.get(dimension, "query_pod_logs")
    normalized = fact_contract_module.normalize_fact_ledger(ledger_mapping)
    if normalized is not None:
        ledger_mapping = normalized.model_dump(
            mode="json",
            exclude_none=True,
        )
    return {
        **extra,
        "tool": selected_tool,
        "semantic_success": True,
        "fact_ledger": ledger_mapping,
    }


def _internally_authorized_agent_context_item(tool, context):
    ledger = fact_contract_module._fact_ledger_from_agent_context(context)
    assert ledger is not None
    return _internally_authorized_tool_item(
        ledger,
        tool=tool,
        status=context.get("status", "query_succeeded"),
        coverage=context.get("coverage", "present"),
        source_system=context.get("source_system"),
    )


def _t017_canonical_stage_fixture():
    sentinel = "T017_STAGE_SENTINEL_7f3c"
    record = _canonical_fact_record(
        value={"message": sentinel},
        evidence_refs=["logs:t017-stage-sentinel"],
    )
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "case-t017-stage-projection",
        "scope_entity_ids": [record["entity_id"]],
        "records": [record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    structured = {
        "status": "query_succeeded",
        "coverage": "present",
        "source_system": "elasticsearch",
        "dimension": "logging",
        "purpose": "capture projection sentinel",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-a",
        },
        "facts": [{
            "ref": "logs:t017-stage-sentinel",
            "value": {"message": sentinel},
            "source_system": "elasticsearch",
            "directness": "direct",
        }],
        "fact_ledger": ledger,
    }
    duplicated_item = {
        "tool": "query_pod_logs",
        "semantic_success": True,
        "data": json.dumps({"fact_ledger": ledger}, ensure_ascii=False),
        "agent_facts": f"QUERY_FACT value={sentinel}",
        "agent_context": json.dumps(structured, ensure_ascii=False),
        "fact_ledger": ledger,
        "raw_ref": "/archive/t017-stage.raw",
        "structured_ref": "/archive/t017-stage.structured.json",
        "summary_ref": "/archive/t017-stage.summary",
    }
    authority_item = next(
        item
        for item in EvidenceCollectorNode()._extract_tool_data_from_thinking([
            {
                "type": "tool_result",
                "status": "success",
                "semantic_success": True,
                "tool_name": "query_pod_logs",
                "tool_args": {
                    "namespace": "demo",
                    "pod": "api",
                    "purpose": "capture projection sentinel",
                },
                "result": json.dumps({"fact_ledger": ledger}),
                "structured": structured,
            },
            {
                "type": "tool_result",
                "status": "success",
                "semantic_success": True,
                "tool_name": "kubectl_describe",
                "tool_args": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                },
                "structured": {
                    "primary_entity": {
                        "kind": "Pod",
                        "namespace": "demo",
                        "name": "api",
                        "uid": "uid-a",
                    }
                },
            },
        ])
        if item.get("tool") == "query_pod_logs"
    )
    duplicated_item["fact_ledger"] = authority_item["fact_ledger"]
    return sentinel, record, ledger, structured, duplicated_item


def test_t017_evidence_provider_item_uses_one_canonical_ledger_projection():
    sentinel, record, ledger, structured, _ = _t017_canonical_stage_fixture()
    query_event = {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "query_pod_logs",
        "tool_args": {
            "namespace": "demo",
            "pod": "api",
            "purpose": "capture projection sentinel",
        },
        "result": json.dumps({"fact_ledger": ledger}, ensure_ascii=False),
        "structured": structured,
        "raw_ref": "/archive/t017-stage.raw",
        "structured_ref": "/archive/t017-stage.structured.json",
        "summary_ref": "/archive/t017-stage.summary",
    }
    independent_uid_event = {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "kubectl_describe",
        "tool_args": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
        },
        "structured": {
            "primary_entity": {
                "kind": "Pod",
                "namespace": "demo",
                "name": "api",
                "uid": "uid-a",
            }
        },
    }
    events = [query_event, independent_uid_event]
    archived_copy = json.loads(json.dumps(events))

    tool_data = EvidenceCollectorNode()._extract_tool_data_from_thinking(events)
    item = next(
        value for value in tool_data
        if value.get("tool") == "query_pod_logs"
    )
    rendered = json.dumps(item, ensure_ascii=False)

    assert rendered.count(sentinel) == 1
    assert rendered.count(record["fact_id"]) == 1
    assert item["fact_ledger"]["contract_version"] == ledger["contract_version"]
    assert item["fact_ledger"]["source"] == "mcp_canonical"
    assert item["fact_ledger"]["scope_entity_ids"] == ledger["scope_entity_ids"]
    assert item["fact_ledger"]["records"][0]["fact_id"] == record["fact_id"]
    assert "data" not in item
    assert "agent_facts" not in item
    assert "agent_context" not in item
    assert item["raw_ref"] == "/archive/t017-stage.raw"
    assert item["structured_ref"] == "/archive/t017-stage.structured.json"
    assert item["summary_ref"] == "/archive/t017-stage.summary"
    assert events == archived_copy


def test_t017_rca_provider_context_uses_one_canonical_ledger_projection():
    sentinel, record, _, _, duplicated_item = _t017_canonical_stage_fixture()

    context = RootCauseAnalyzerNode()._extract_tool_data_for_rca(
        json.dumps({"tool_data": [duplicated_item]}, ensure_ascii=False),
        max_chars=12000,
    )

    assert context.count(sentinel) == 1
    assert context.count(record["fact_id"]) == 1
    assert context.count('"contract_version":"aiops.fact-ledger.v1"') == 1


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

    assert result["layer"] == Layer.ABNORMAL
    assert not result.get("layer_full_analysis")
    assert result["layer_handoff"]["layer"] == "ABNORMAL"
    assert result["layer_handoff"]["primary_problem"] == "Pod app-1 OOMKilled"
    assert "primary_pod" not in result["layer_handoff"]
    assert result["layer_handoff"]["pod_status_keyword"] == "CrashLoopBackOff"
    assert result["layer_handoff"]["pod_abnormal_type"] == "OOMKilled"
    assert result["layer_handoff"]["derived_layer"] == "ABNORMAL"
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

    assert "# Runbook 上下文" in message
    assert "不在 plan 阶段重新选择" in message
    assert "pod_status_keyword" in message
    assert "pod_abnormal_type" in message
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


def test_rca_handoff_keeps_all_abnormal_pod_entities_under_long_section_pressure():
    node = RootCauseAnalyzerNode()
    abnormal_pods = [
        {
            "namespace": f"team-{index}",
            "name": f"service-{index}",
            "status": "CrashLoopBackOff",
            "uid": f"uid-{index}",
        }
        for index in range(5)
    ]
    layer_handoff = {
        "layer": "L2",
        "abnormal_pods": abnormal_pods,
        "active_signals": [
            {
                "namespace": f"team-{index % 5}",
                "pod": f"service-{index % 5}",
                "detail": "signal " * 400,
            }
            for index in range(18)
        ],
        "primary_problem": "cluster has multiple abnormal pods " * 400,
        "issue_groups": [
            {
                "group_id": f"group-{index}",
                "entities": [{"kind": "Pod", **pod}],
                "observations": ["observation " * 400 for _ in range(4)],
            }
            for index, pod in enumerate(abnormal_pods)
        ],
        "current_abnormal_summary": {
            "source": "current_scan",
            "status_counts": {"CrashLoopBackOff": 5},
            "total_abnormal": 5,
            "selected_rows": [
                {**pod, "details": "summary " * 400}
                for pod in abnormal_pods
            ],
        },
    }

    compact_handoff = node._compact_layer_handoff_for_rca(layer_handoff)
    rca_context = node._build_rca_context({
        "layer_handoff": layer_handoff,
        "evidence_items": [],
        "evidence_analysis": "{}",
    })

    assert len(compact_handoff) <= RCA_HANDOFF_MAX_CHARS
    for pod in abnormal_pods:
        assert pod["namespace"] in compact_handoff
        assert pod["name"] in compact_handoff
        assert pod["status"] in compact_handoff
        assert pod["uid"] in compact_handoff
        assert pod["namespace"] in rca_context
        assert pod["name"] in rca_context
        assert pod["status"] in rca_context
        assert pod["uid"] in rca_context
    assert json.loads(compact_handoff)["abnormal_pod_entity_index"] == abnormal_pods
    assert '"abnormal_pod_entity_index"' in rca_context
    assert len(rca_context) <= RCA_CONTEXT_MAX_CHARS


def test_rca_handoff_keeps_thirty_abnormal_pod_identities_within_budget():
    abnormal_pods = [
        {
            "namespace": f"team-{index:02d}",
            "name": f"service-{index:02d}",
            "status": "CrashLoopBackOff",
            "uid": f"uid-{index:02d}",
        }
        for index in range(30)
    ]
    handoff = {
        "layer": "L2",
        "abnormal_pods": abnormal_pods,
        "active_signals": [
            {
                "entity": f"team-{index:02d}/service-{index:02d}",
                "detail": "signal " * 300,
            }
            for index in range(30)
        ],
        "issue_groups": [
            {
                "group_id": f"group-{index:02d}",
                "entities": [{"kind": "Pod", **pod}],
                "observations": ["observation " * 300],
            }
            for index, pod in enumerate(abnormal_pods)
        ],
        "current_abnormal_summary": {
            "source": "current_scan",
            "status_counts": {"CrashLoopBackOff": 30},
            "total_abnormal": 30,
            "selected_rows": abnormal_pods,
        },
    }

    compact_handoff = RootCauseAnalyzerNode._compact_layer_handoff_for_rca(
        handoff
    )
    parsed = json.loads(compact_handoff)

    assert len(compact_handoff) <= RCA_HANDOFF_MAX_CHARS
    assert parsed["abnormal_pod_entity_index"] == abnormal_pods


def test_rca_handoff_rejects_identity_index_that_cannot_fit_budget():
    abnormal_pods = [
        {
            "namespace": f"team-{index:02d}-" + ("n" * 180),
            "name": f"service-{index:02d}-" + ("p" * 180),
            "status": "CrashLoopBackOff-" + ("s" * 180),
            "uid": f"uid-{index:02d}-" + ("u" * 180),
        }
        for index in range(30)
    ]

    with pytest.raises(
        ValueError,
        match="abnormal Pod identity index exceeds RCA handoff budget",
    ):
        RootCauseAnalyzerNode._compact_layer_handoff_for_rca({
            "layer": "L2",
            "abnormal_pods": abnormal_pods,
        })


def test_rca_context_bounds_multi_entity_real_observability_evidence():
    node = RootCauseAnalyzerNode()
    tool_data = []
    expected_entities = []
    expected_direct_fact_ids = []
    for index in range(5):
        namespace = f"demo-{index}"
        pod = f"api-{index}"
        entity_id = f"k8s.pod:{namespace}/{pod}:uid-{index}"
        direct = _canonical_fact_record(
            entity_id=entity_id,
            namespace=namespace,
            entity_name=pod,
            value={
                "message": (
                    f"pod={pod} required config TOKEN_{index} is missing "
                    + ("direct-evidence " * 30)
                )
            },
            evidence_refs=[f"logs:{namespace}/{pod}"],
        )
        coverage = _canonical_fact_record(
            entity_id=entity_id,
            namespace=namespace,
            entity_name=pod,
            dimension="coverage",
            fact_type="coverage",
            attribute="coverage.tracing",
            value={"coverage": "present", "noise": "x" * 400},
            source_system="deepflow+tempo",
            directness="related_context",
            confidence="medium",
            strength="context",
            evidence_refs=[f"coverage:{namespace}/{pod}:tracing"],
        )
        tool_data.append(_internally_authorized_tool_item(
            {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": f"case-{index}",
                "scope_entity_ids": [entity_id],
                "records": [coverage, direct],
                "record_count": 2,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            },
            tool="query_pod_logs",
        ))
        expected_entities.append(entity_id)
        expected_direct_fact_ids.append(direct["fact_id"])

    for index in range(20):
        tool_data.append({
            "tool": "query_pod_tracing",
            "agent_context": json.dumps({
                "status": "query_succeeded",
                "entity": {
                    "namespace": f"demo-{index % 5}",
                    "pod": f"api-{index % 5}",
                },
                "dimension": "tracing",
                "coverage": "present",
                "facts": [
                    {
                        "ref": f"trace-{index}",
                        "value": "HTTP 500 " + ("trace-noise " * 600),
                    }
                ],
            }),
        })

    context = node._build_rca_context({
        "layer_handoff": {
            "layer": "L2",
            "primary_problem": "verbose reasoning " * 8000,
            "abnormal_pods": [
                {
                    "namespace": f"demo-{index}",
                    "name": f"api-{index}",
                    "status": "CrashLoopBackOff",
                }
                for index in range(5)
            ],
            "issue_groups": [
                {
                    "group_id": f"g-{index}",
                    "entities": [
                        {
                            "kind": "Pod",
                            "namespace": f"demo-{index}",
                            "name": f"api-{index}",
                        }
                    ],
                    "possible_scenarios": ["configuration failure " * 100],
                }
                for index in range(5)
            ],
        },
        "evidence_items": [],
        "evidence_analysis": json.dumps({
            "source_coverage": {
                "cases": [
                    {
                        "target": f"demo-{index}/api-{index}",
                        "dimensions": {
                            "metrics": "present",
                            "logging": "present",
                            "tracing": "present",
                        },
                    }
                    for index in range(5)
                ]
            },
            "unresolved_questions": ["missing scheduler event " * 400],
            "tool_data": tool_data,
        }),
    })

    assert len(context) <= 52000
    for entity_id in expected_entities:
        assert entity_id in context
    for fact_id in expected_direct_fact_ids:
        assert fact_id in context


def test_rca_supplementary_tool_context_uses_shared_budget():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "tool_data": [
            _internally_authorized_agent_context_item(
                "query_pod_tracing",
                {
                        "status": "query_succeeded",
                        "source_system": "tempo",
                        "dimension": "tracing",
                        "entity": {
                            "namespace": "demo",
                            "pod": f"api-{index}",
                            "pod_uid": f"uid-{index}",
                        },
                        "purpose": "验证补充 tracing 上下文预算",
                        "coverage": "present",
                        "facts": [
                            {
                                "ref": f"trace-{index}",
                                "source_system": "tempo",
                                "name": "application_span",
                                "value": "HTTP 500 " + ("payload " * 3000),
                            }
                        ],
                        "evidence_refs": [f"trace-{index}"],
                    },
                )
            for index in range(30)
        ]
    })

    context = node._extract_tool_data_for_rca(
        evidence_analysis,
        max_chars=12000,
    )

    assert len(context) <= 12000
    assert "## AIOps Fact Ledger" in context
    assert "k8s.pod:demo/api-0" in context
    assert "k8s.pod:demo/api-29" in context


def test_rca_generic_query_ledgers_keep_decisive_facts_across_dimensions():
    entity = {
        "kind": "Pod",
        "namespace": "demo",
        "pod": "api",
        "pod_uid": "uid-a",
    }
    tool_data = [
        _internally_authorized_agent_context_item(
            "execute_pod_promql",
            {
                "status": "query_succeeded",
                "source_system": "prometheus",
                "dimension": "metrics",
                "entity": entity,
                "coverage": "present",
                "directness": "direct",
                "facts": [{
                    "ref": "metric-restarts",
                    "name": "prometheus_sample",
                    "value": {
                        "first": 0,
                        "max": 5,
                        "last": 1,
                    },
                    "source_system": "prometheus",
                    "directness": "direct",
                }],
            },
        ),
        _internally_authorized_agent_context_item(
            "query_pod_logs",
            {
                "status": "query_succeeded",
                "source_system": "elasticsearch",
                "dimension": "logging",
                "entity": entity,
                "coverage": "present",
                "directness": "direct",
                "facts": [{
                    "ref": "log-config",
                    "name": "log.message",
                    "value": (
                        "required config PAYMENT_GATEWAY_TOKEN is missing; "
                        "error_code=CONFIG_MISSING"
                    ),
                    "source_system": "elasticsearch",
                    "directness": "direct",
                }],
            },
        ),
        _internally_authorized_agent_context_item(
            "query_pod_tracing",
            {
                "status": "query_succeeded",
                "source_system": "deepflow+tempo",
                "dimension": "tracing",
                "entity": entity,
                "coverage": "present",
                "directness": "direct",
                "facts": [
                    {
                        "ref": "deepflow-config",
                        "name": "l7_flow",
                        "value": {
                            "trace_id": "trace-config",
                            "request_resource": "/checkout",
                            "response_code": 500,
                        },
                        "source_system": "deepflow",
                        "directness": "direct",
                    },
                    {
                        "ref": "tempo-config",
                        "name": "application_span",
                        "value": {
                            "trace_id": "trace-config",
                            "name": "GET /checkout",
                            "attributes": {
                                "error.type": "CONFIG_MISSING",
                                "config.key": "PAYMENT_GATEWAY_TOKEN",
                            },
                        },
                        "source_system": "tempo",
                        "directness": "direct",
                    },
                ],
            },
        ),
    ]

    context = RootCauseAnalyzerNode()._extract_tool_data_for_rca(
        json.dumps({"tool_data": tool_data}),
        max_chars=12000,
    )

    assert len(context) <= 12000
    assert "required config PAYMENT_GATEWAY_TOKEN is missing" in context
    assert "error_code=CONFIG_MISSING" in context
    assert context.count("trace-config") >= 2
    assert "response_code" in context
    assert "config.key" in context


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
    assert groups[0]["compatible_layers"] == []
    assert groups[0]["status_keywords"] == ["ImagePullBackOff", "ErrImagePull"]
    terminating_group = next(group for group in groups if group["status_keywords"] == ["Terminating"])
    assert terminating_group["pod_abnormal_type"] == "TerminatingStuck"
    assert terminating_group["compatible_layers"] == []
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
    assert handoff["issue_groups"][0]["compatible_layers"] == []


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


def test_layer_handoff_builds_all_explicit_pod_lanes_from_real_named_results():
    node = LayerClassifierNode()
    targets = [
        ("team-a", "api-a", "ImagePullBackOff"),
        ("team-b", "api-b", "CrashLoopBackOff"),
        ("team-c", "api-c", "Pending"),
    ]
    question = "请诊断 " + " ".join(
        f"{namespace}/{name}" for namespace, name, _ in targets
    )
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {
                "kind": "pod",
                "namespace": namespace,
                "name": name,
            },
            "result": f"NAME READY STATUS RESTARTS AGE\n{name} 0/1 {status} 3 10m",
            "raw_ref": f"raw/{name}",
        }
        for namespace, name, status in reversed(targets)
    ]
    events.append({
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "kubectl_get_by_kind_in_cluster",
        "structured": {
            "header": "NAMESPACE NAME READY STATUS RESTARTS AGE",
            "selected_rows": ["unrelated noisy-pod 0/1 Pending 0 2m"],
            "status_counts": {"Pending": 1},
        },
        "result": "global scan",
    })
    layer_result = {
        "layer": "L2",
        "derived_layer": "L2",
        "confidence": 0.8,
        "reasoning": "三个显式目标需要诊断",
        "key_entities": [],
        "abnormal_pods": [
            {"namespace": "unrelated", "name": "invented", "status": "Pending"}
        ],
        "pod_status_keyword": "Pending",
        "pod_abnormal_type": "Unknown",
    }

    handoff = node._build_layer_handoff(
        question=question,
        layer_result=layer_result,
        layer=Layer.L2,
        layers=[Layer.L2],
        thinking_events=events,
    )

    assert handoff["diagnosis_scope"] == "explicit_pods"
    assert handoff["explicit_pod_targets"] == [
        {"namespace": namespace, "name": name}
        for namespace, name, _ in targets
    ]
    assert {
        (pod["namespace"], pod["name"], pod["status"])
        for pod in handoff["abnormal_pods"]
    } == set(targets)
    assert len(handoff["explicit_pod_observations"]) == 3
    assert handoff["current_abnormal_summary"]["total_abnormal"] == 3
    assert all(
        entity["namespace"] != "unrelated"
        for group in handoff["issue_groups"]
        for entity in group["entities"]
    )


def test_layer_handoff_does_not_fabricate_failed_or_healthy_explicit_targets():
    node = LayerClassifierNode()
    question = "请诊断 team-a/api-a team-b/api-b team-c/api-c"
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {"kind": "pod", "namespace": "team-a", "name": "api-a"},
            "result": "NAME READY STATUS\napi-a 1/1 Running",
        },
        {
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {"kind": "pod", "namespace": "team-b", "name": "api-b"},
            "result": "NAME READY STATUS\napi-b 0/1 Running",
        },
        {
            "type": "tool_result",
            "status": "error",
            "semantic_success": False,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {"kind": "pod", "namespace": "team-c", "name": "api-c"},
            "result": "Error from server (NotFound)",
        },
    ]
    layer_result = {
        "layer": "L2",
        "derived_layer": "L2",
        "confidence": 0.8,
        "reasoning": "模型字段不具权威性",
        "abnormal_pods": [
            {"namespace": "team-a", "name": "api-a", "status": "CrashLoopBackOff"},
            {"namespace": "team-c", "name": "api-c", "status": "Pending"},
        ],
        "pod_status_keyword": "Pending",
        "pod_abnormal_type": "Unknown",
    }

    handoff = node._build_layer_handoff(
        question=question,
        layer_result=layer_result,
        layer=Layer.L2,
        layers=[Layer.L2],
        thinking_events=events,
    )

    assert handoff["abnormal_pods"] == [
        {"namespace": "team-b", "name": "api-b", "status": "NotReady"}
    ]
    states = {
        (item["namespace"], item["name"]): item["state"]
        for item in handoff["explicit_pod_observations"]
    }
    assert states == {
        ("team-a", "api-a"): "healthy",
        ("team-b", "api-b"): "abnormal",
        ("team-c", "api-c"): "error",
    }
    assert [
        (group["entities"][0]["namespace"], group["entities"][0]["name"])
        for group in handoff["issue_groups"]
    ] == [
        ("team-a", "api-a"),
        ("team-b", "api-b"),
        ("team-c", "api-c"),
    ]


def test_layer_explicit_running_pod_with_recent_restart_gets_terminal_lane():
    node = LayerClassifierNode()
    row = "api-a 1/1 Running 5 (91s ago) 4m"
    handoff = node._build_layer_handoff(
        question="请诊断 namespace team-a 中 Pod api-a",
        layer_result={
            "layer": "L2",
            "reasoning": "当前表格需要结构化判定",
            "abnormal_pods": [],
            "pod_abnormal_type": "Unknown",
        },
        layer=Layer.L2,
        layers=[Layer.L2],
        thinking_events=[{
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "kubectl_get_by_name",
            "tool_args": {
                "kind": "pod",
                "namespace": "team-a",
                "name": "api-a",
            },
            "result": f"NAME READY STATUS RESTARTS AGE\n{row}",
            "structured": {
                "selected_rows": [row],
                "recent_restart_rows": [row],
            },
        }],
    )

    assert handoff["explicit_pod_observations"][0]["state"] == "abnormal"
    assert handoff["explicit_pod_observations"][0]["status"] == "RecentRestart"
    assert handoff["abnormal_pods"] == [{
        "namespace": "team-a",
        "name": "api-a",
        "status": "RecentRestart",
    }]
    assert len(handoff["issue_groups"]) == 1
    assert handoff["issue_groups"][0]["status_keywords"] == ["RecentRestart"]


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

    assert layer == Layer.ABNORMAL
    assert layers == [Layer.ABNORMAL]
    assert layer_result["layer"] == "ABNORMAL"
    assert handoff["layer"] == "ABNORMAL"
    assert handoff["current_abnormal_summary"]["total_abnormal"] == 1


def test_layer_guard_keeps_healthy_when_scan_is_clean_despite_llm_noise_fields():
    """真实缺陷复现（run 77a5dd3e44ee411d）：集群扫描 61 Pod 全 Running、
    total_abnormal=0，LLM 判定 HEALTHY 正确，但把历史重启的控制面 Pod
    手填进 abnormal_pods。守卫只能信确定性扫描信号，不得用 LLM 手写
    字段推翻正确的 HEALTHY 判定。"""
    node = LayerClassifierNode()
    layer_result = {
        "layer": "HEALTHY",
        "derived_layer": "HEALTHY",
        "layers": ["HEALTHY"],
        "confidence": 0.5,
        "reasoning": "61 pods all Running, 0 abnormal, 0 recent restarts",
        "abnormal_pods": [
            {"name": "etcd-master", "namespace": "kube-system"},
            {"name": "kube-apiserver-master", "namespace": "kube-system"},
            {"name": "calico-node", "namespace": "kube-system"},
        ],
        "abnormal_groups": [{
            "group_id": "g1",
            "status_keywords": ["Unknown"],
            "pod_abnormal_type": "Unknown",
            "entities": [
                {"kind": "Pod", "namespace": "kube-system", "name": "etcd-master"},
            ],
        }],
        "pod_status_keyword": "",
        "pod_abnormal_type": "",
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "structured": {
                "header": "NAMESPACE NAME READY STATUS RESTARTS AGE IP NODE LABELS",
                "status_counts": {"Running": 61},
                "selected_rows": [],
                "recent_restart_rows": [],
            },
            "result": "Pod table: all Running",
        }
    ]
    handoff = node._build_layer_handoff(
        question="我的集群现在有什么问题",
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

    assert layer == Layer.HEALTHY
    assert layers == [Layer.HEALTHY]
    assert layer_result["layer"] == "HEALTHY"
    assert handoff.get("layer") != "ABNORMAL"


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
                "agent_context": json.dumps({
                    "dimension_details": {
                        "tracing": {
                            "flows": [
                                {
                                    "trace_id": "ordinary-context-must-not-win",
                                    "duration_us": 999999,
                                }
                            ]
                        }
                    }
                }),
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
    assert "ordinary-context-must-not-win" not in context


def test_rca_supplementary_semantic_groups_share_single_budget():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "tool_data": [
            {
                "tool": "facts-tool",
                "agent_facts": "FACT_MARKER\n" + ("deterministic fact " * 1200),
            },
            {
                "tool": "context-tool",
                "agent_context": json.dumps({
                    "marker": "CONTEXT_MARKER",
                    "payload": "structured context " * 1200,
                }),
            },
            {
                "tool": "raw-tool",
                "data": "RAW_MARKER\n" + ("raw result " * 1200),
            },
        ],
    })

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "## AIOps 确定性可观测事实" in context
    assert "## AIOps 结构化可观测性上下文" in context
    assert "## 工具原始输出" in context
    assert "FACT_MARKER" in context
    assert "CONTEXT_MARKER" in context
    assert "RAW_MARKER" in context
    assert len(context) <= RCA_SUPPLEMENTARY_MAX_CHARS


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


def test_rca_quality_contract_keeps_all_top_level_fields_under_pressure():
    node = RootCauseAnalyzerNode()
    quality_contract = {
        "source_coverage": {
            "cases": [
                {
                    "target": f"demo/api-{index}",
                    "dimensions": {
                        "metrics": "present",
                        "logging": "present",
                        "tracing": "present",
                    },
                    "noise": "coverage " * 500,
                }
                for index in range(40)
            ]
        },
        "case_target_coverage": {
            "total": 40,
            "collected": 38,
            "rate": 0.95,
        },
        "detail_retrieval": {
            "evaluated": True,
            "requested": 8,
            "collected": 6,
            "refs": [f"detail-ref-{index}" for index in range(80)],
        },
        "diagnostic_sufficiency_summary": {
            "score": 0.75,
            "status": "partially_sufficient",
        },
        "unresolved_questions": [
            f"demo/api-{index}: " + ("question " * 500)
            for index in range(40)
        ],
    }

    rendered = node._compact_quality_contract(
        quality_contract,
        max_chars=RCA_QUALITY_MAX_CHARS,
    )
    parsed = json.loads(rendered)

    assert len(rendered) <= RCA_QUALITY_MAX_CHARS
    assert list(parsed) == [
        "source_coverage",
        "case_target_coverage",
        "detail_retrieval",
        "diagnostic_sufficiency_summary",
        "unresolved_questions",
    ]
    assert parsed["case_target_coverage"]["rate"] == 0.95
    assert parsed["detail_retrieval"]["collected"] == 6
    assert parsed["diagnostic_sufficiency_summary"]["score"] == 0.75


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
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-facts",
                    "scope_entity_ids": [entity_id],
                    "records": [fact_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
                data="DUPLICATE COARSE SUMMARY",
                agent_facts="DUPLICATE AGENT FACTS",
                agent_context=(
                    '{"dimension_details":{"logs":{"samples":[]}}}'
                ),
            ),
            {
                "tool": "kubectl_describe",
                "data": "Name: api\nStatus: Running",
            },
        ],
    })

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "AIOps Fact Ledger" in context
    assert "## 补充工具输出" in context
    assert "case-facts" in context
    assert fact_record["fact_id"] in context
    assert "kubectl_describe" in context
    assert "DUPLICATE COARSE SUMMARY" not in context
    assert "DUPLICATE AGENT FACTS" not in context
    assert "dimension_details" not in context


def test_evidence_handoff_excludes_llm_analysis_while_full_archive_retains_it(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    node = EvidenceCollectorNode()
    node.current_run_id = "evidence-authority-boundary"
    output = EvidenceCollectionOutput.model_validate({
        "tool_data": [
            {
                "tool": "kubectl_describe",
                "fact_ledger": {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-evidence-authority-boundary",
                    "scope_entity_ids": ["k8s.pod:demo/api:uid-a"],
                    "records": [],
                    "record_count": 0,
                    "truncated": False,
                    "source": "robusta_legacy_adapter",
                    "legacy_contract": True,
                },
            }
        ],
        "llm_analysis": (
            "Model-only analysis incorrectly says mib=309012 means 309GB."
        ),
        "collection_summary": "Collected source-backed evidence.",
        "plan_total": 1,
        "plan_collected": 1,
        "plan_completeness": 1.0,
        "environment_evidence_total": 1,
        "environment_evidence_collected": 1,
        "environment_evidence_completeness": 1.0,
    })

    handoff_json = node._publish_evidence_analysis(output)
    handoff = json.loads(handoff_json)
    archived = json.loads(
        (
            tmp_path
            / "evidence-authority-boundary"
            / "node_outputs"
            / "evidence.full.json"
        ).read_text(encoding="utf-8")
    )

    assert archived["llm_analysis"].endswith("means 309GB.")
    assert archived["tool_data"] == output.tool_data
    assert "llm_analysis" not in handoff
    assert "309GB" not in handoff_json
    assert handoff["tool_data"] == output.tool_data


def test_rca_context_excludes_llm_analysis_when_fact_ledger_exists():
    node = RootCauseAnalyzerNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    fact_record = _canonical_fact_record(
        entity_id=entity_id,
        value={"message": "container restarted"},
        evidence_refs=["kubernetes:restart"],
    )
    evidence_analysis = json.dumps({
        "llm_analysis": (
            "日志明确出现 Cannot allocate memory，"
            "因此一定是业务内存泄漏。"
        ),
        "tool_data": [_internally_authorized_tool_item(
            {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": "case-ledger-authoritative",
                "scope_entity_ids": [entity_id],
                "records": [fact_record],
                "record_count": 1,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            },
            tool="query_pod_logs",
        )],
    }, ensure_ascii=False)

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "## AIOps Fact Ledger" in context
    assert fact_record["fact_id"] in context
    assert "Cannot allocate memory" not in context
    assert "业务内存泄漏" not in context
    assert "## LLM 证据分析" not in context


def test_rca_context_keeps_llm_analysis_for_legacy_input_without_fact_ledger():
    node = RootCauseAnalyzerNode()
    evidence_analysis = json.dumps({
        "llm_analysis": "Legacy evidence summary remains available.",
        "tool_data": [],
    })

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "## LLM 证据分析" in context
    assert "Legacy evidence summary remains available." in context


def test_rca_provider_input_excludes_llm_analysis_when_fact_ledger_exists():
    node = RootCauseAnalyzerNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    fact_record = _canonical_fact_record(
        entity_id=entity_id,
        value={"message": "container restarted"},
        evidence_refs=["kubernetes:restart"],
    )
    captured = {}
    parsed = RCAOutput.model_validate({
        "diagnostic_status": "inconclusive",
        "phenomenon": "Pod restarted",
        "root_cause": "证据不足，无法确认根因",
        "supporting_fact_ids": [],
        "contradicting_fact_ids": [],
        "unknowns": ["缺少决定性错误原文"],
        "hypotheses": [],
        "confidence": 0.2,
        "confidence_reason": "Fact Ledger 只证明容器发生重启",
    })

    def _capture_provider_call(question, system_prompt, schema, **kwargs):
        captured["question"] = question
        return (
            parsed,
            SimpleNamespace(
                result=parsed.model_dump_json(),
                structured_response=parsed,
            ),
            [],
        )

    node.ai_call = object()
    node._call_structured_agent = _capture_provider_call
    node._save_thinking = lambda state, new_state, thinking_events: None
    evidence_analysis = json.dumps({
        "llm_analysis": (
            "日志明确出现 Cannot allocate memory，"
            "因此一定是业务内存泄漏。"
        ),
        "tool_data": [_internally_authorized_tool_item(
            {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": "case-provider-boundary",
                "scope_entity_ids": [entity_id],
                "records": [fact_record],
                "record_count": 1,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            },
            tool="query_pod_logs",
        )],
    }, ensure_ascii=False)

    node.execute({
        "question": "我的集群有什么问题？",
        "layer": Layer.L2,
        "evidence_items": [],
        "evidence_analysis": evidence_analysis,
        "thinking_events": [],
    })

    assert "## AIOps Fact Ledger" in captured["question"]
    assert fact_record["fact_id"] in captured["question"]
    assert "Cannot allocate memory" not in captured["question"]
    assert "业务内存泄漏" not in captured["question"]
    assert "## LLM 证据分析" not in captured["question"]


def test_rca_mixed_ledger_and_legacy_supplementary_preserves_case_identity():
    node = RootCauseAnalyzerNode()
    canonical_entity = "k8s.pod:demo/canonical-api:uid-canonical"
    canonical_fact = _canonical_fact_record(
        entity_id=canonical_entity,
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-canonical",
                    "scope_entity_ids": [canonical_entity],
                    "records": [canonical_fact],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
            ),
            {
                "tool": "collect_aiops_case",
                "agent_context": json.dumps({
                    "case_id": "case-legacy-config",
                    "primary_entity": {
                        "kind": "Pod",
                        "namespace": "legacy-ns",
                        "name": "legacy-api",
                        "uid": "uid-legacy-api",
                    },
                }),
                "agent_facts": (
                    "LEGACY_CONFIG_FACT required config TOKEN is missing"
                ),
            },
        ],
    })

    context = node._extract_tool_data_for_rca(evidence_analysis)

    assert "AIOps Fact Ledger" in context
    assert "LEGACY_CONFIG_FACT" in context
    assert "case-legacy-config" in context
    assert "legacy-ns" in context
    assert "legacy-api" in context
    assert "uid-legacy-api" in context


def test_rca_multiple_legacy_cases_preserve_every_identity_under_shared_budget():
    node = RootCauseAnalyzerNode()
    tool_data = []
    for index in range(10):
        tool_data.append({
            "tool": "collect_aiops_case",
            "agent_context": json.dumps({
                "case_id": f"case-legacy-{index}",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": f"namespace-{index}",
                    "name": f"legacy-pod-{index}",
                    "uid": f"uid-legacy-{index}",
                },
            }),
            "agent_facts": (
                f"LEGACY_FACT_{index} "
                + ("diagnostic evidence " * 1000)
            ),
        })
    context = node._extract_tool_data_for_rca(
        json.dumps({"tool_data": tool_data})
    )

    assert len(context) <= RCA_SUPPLEMENTARY_MAX_CHARS
    for index in range(10):
        assert f"case-legacy-{index}" in context
        assert f"namespace-{index}" in context
        assert f"legacy-pod-{index}" in context
        assert f"uid-legacy-{index}" in context


def test_rca_more_than_supplementary_limit_preserves_every_identity_with_ledger():
    canonical_entity = "k8s.pod:demo/canonical-api:uid-canonical"
    tool_data = [
        {
            "tool": "collect_aiops_case",
            "fact_ledger": {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": "case-canonical",
                "scope_entity_ids": [canonical_entity],
                "records": [
                    _canonical_fact_record(entity_id=canonical_entity)
                ],
                "record_count": 1,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            },
        }
    ]
    for index in range(12):
        tool_data.append({
            "tool": "collect_aiops_case",
            "agent_context": json.dumps({
                "case_id": f"case-over-limit-{index}",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": f"ns-{index}",
                    "name": f"pod-{index}",
                    "uid": f"uid-{index}",
                },
            }),
            "agent_facts": f"FACT_OVER_LIMIT_{index}",
        })

    context = RootCauseAnalyzerNode()._extract_tool_data_for_rca(
        json.dumps({"tool_data": tool_data})
    )

    assert len(context) <= RCA_TOOL_CONTEXT_MAX_CHARS
    for index in range(12):
        assert f"case-over-limit-{index}" in context
        assert f"pod-{index}" in context
        assert f"uid-{index}" in context
    assert "FACT_OVER_LIMIT_9" in context
    assert "FACT_OVER_LIMIT_10" not in context
    assert "FACT_OVER_LIMIT_11" not in context


def test_rca_more_than_supplementary_limit_preserves_every_identity_without_ledger():
    tool_data = []
    for index in range(12):
        tool_data.append({
            "tool": "collect_aiops_case",
            "agent_context": json.dumps({
                "case_id": f"case-no-ledger-{index}",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": f"ns-{index}",
                    "name": f"pod-{index}",
                    "uid": f"uid-{index}",
                },
            }),
            "agent_facts": f"FACT_NO_LEDGER_{index}",
        })

    context = RootCauseAnalyzerNode()._extract_tool_data_for_rca(
        json.dumps({"tool_data": tool_data})
    )

    assert len(context) <= RCA_SUPPLEMENTARY_MAX_CHARS
    for index in range(12):
        assert f"case-no-ledger-{index}" in context
        assert f"pod-{index}" in context
        assert f"uid-{index}" in context
    assert "FACT_NO_LEDGER_9" in context
    assert "FACT_NO_LEDGER_10" not in context
    assert "FACT_NO_LEDGER_11" not in context


def test_rca_supplementary_identity_index_fails_when_minimum_cannot_fit():
    items = [
        {
            "tool": "collect_aiops_case",
            "identity_envelope": {
                "case_id": "case-impossible",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-impossible",
                },
            },
            "agent_facts": "required config TOKEN is missing",
        }
    ]

    with pytest.raises(
        ValueError,
        match="supplementary identity",
    ):
        RootCauseAnalyzerNode._compact_supplementary_tool_sections(
            items,
            max_chars=32,
        )


def test_rca_supplementary_without_identity_can_drop_optional_data_at_tiny_budget():
    rendered = RootCauseAnalyzerNode._compact_supplementary_tool_data(
        [
            {
                "tool": "kubectl_describe",
                "data": "large optional output " * 100,
            }
        ],
        max_chars=2,
    )

    assert rendered == "{}"


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

    assert "AIOps 确定性可观测事实" in context
    assert "TEXT FACT REPRESENTATION" in context
    assert "STRUCTURED CONTEXT REPRESENTATION" not in context
    assert "RAW REPRESENTATION" not in context
    assert context.count("TEXT FACT REPRESENTATION") == 1


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
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-facts",
                    "scope_entity_ids": [entity_id],
                    "records": [fact_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
                data="compact summary",
            )
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


def test_rca_derives_single_lane_authoritative_identity_from_ledgers():
    node = RootCauseAnalyzerNode()
    authoritative = "k8s.pod:demo/api:uid-authoritative"
    mutated = "k8s.pod:demo/api:uid-authoritativf"
    fact_record = _canonical_fact_record(entity_id=authoritative)
    evidence_analysis = json.dumps({
        "tool_data": [
            _internally_authorized_tool_item({
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": "single-authoritative-lane",
                "scope_entity_ids": [authoritative],
                "records": [fact_record],
                "record_count": 1,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            })
        ]
    })
    claim = {
        "diagnostic_status": "diagnosed",
        "root_cause": "Evidence-backed candidate",
        "supporting_fact_ids": [fact_record["fact_id"]],
        "hypotheses": [{
            "hypothesis_id": "hyp-single",
            "entity_id": mutated,
            "summary": "Evidence-backed candidate",
            "supporting_fact_ids": [fact_record["fact_id"]],
            "confidence": 0.9,
        }],
        "confidence": 0.9,
        "confidence_reason": "Direct source-backed fact",
    }

    result = node._validate_rca_result_against_evidence(
        claim,
        evidence_analysis,
        question="What is wrong?",
        layer=Layer.L2,
    )

    assert result["diagnostic_status"] == "diagnosed"
    assert result["hypotheses"][0]["entity_id"] == authoritative
    assert result["claim_validation"]["model_entity_overrides"][0][
        "model_entity_id"
    ] == mutated


def test_rca_validation_preserves_cross_ledger_collision_diagnostics(
    monkeypatch,
):
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
    monkeypatch.setattr(
        fact_contract_module,
        "_canonical_fact_id",
        lambda _record: first_record["fact_id"],
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-first",
                    "scope_entity_ids": [entity_id],
                    "records": [first_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
            ),
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-second",
                    "scope_entity_ids": [entity_id],
                    "records": [second_record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
            ),
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
        entity_kind="Service",
        namespace="demo",
        entity_name="api",
        dimension="topology",
        fact_type="relationship",
        attribute="topology.relationship",
        value=topology_value,
        source_system="kubernetes",
        directness="direct",
        confidence="high",
        strength="strong",
        evidence_refs=["topology:reviewer-probe"],
    )
    control = _canonical_fact_record(
        entity_id=required_entity_id,
        value={"message": "source-backed control"},
        evidence_refs=["logs:source-backed-control"],
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-topology-control",
                    "scope_entity_ids": [required_entity_id],
                    "records": [control],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
            ),
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-topology-reviewer-probe",
                    "scope_entity_ids": [required_entity_id],
                    "records": [record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_topology",
            ),
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
    control = _canonical_fact_record(
        entity_id=entity_id,
        value={"message": "source-backed control"},
        evidence_refs=["logs:source-backed-control"],
    )
    evidence_analysis = json.dumps({
        "tool_data": [
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-contaminated-control",
                    "scope_entity_ids": [entity_id],
                    "records": [control],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
            ),
            _internally_authorized_tool_item(
                {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": "case-contaminated",
                    "scope_entity_ids": [entity_id],
                    "records": [contaminated],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                },
                tool="query_pod_logs",
            ),
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
    assert "AIOps 确定性可观测事实" in rca_context
    assert "ENTITY kind=Pod" in rca_context
    assert '"case_id":"case-identity-envelope"' in rca_context
    assert '"kind":"Pod"' in rca_context
    assert '"namespace":"demo"' in rca_context
    assert '"name":"api"' in rca_context
    assert '"uid":"uid-a"' in rca_context
    assert "optional-0000" not in rca_context
    assert len(rca_context) <= RCA_SUPPLEMENTARY_MAX_CHARS




def test_layer_extracts_running_but_not_ready_pod_as_abnormal():
    """readiness 探针失败：STATUS=Running 但 READY 0/1 必须识别为异常（c09 实测教训）。"""
    events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "kubectl_get_by_kind_in_cluster",
        "structured": {
            "header": "NAMESPACE  NAME  READY  STATUS  RESTARTS  AGE",
            "selected_rows": [
                "aiops-case-09  workload-5f4fb9ff45-fhgnk  0/1  Running  0  5m",
                "kube-system  coredns-abc  1/1  Running  0  10d",
                "batch  job-done-xyz  0/1  Completed  0  1h",
            ],
            "recent_restart_rows": [],
            "status_counts": {},
        },
    }]
    pods = LayerClassifierNode._extract_current_abnormal_pods_from_events(events)
    assert pods == [{
        "name": "workload-5f4fb9ff45-fhgnk",
        "namespace": "aiops-case-09",
        "status": "NotReady",
    }], f"0/1 Running 未被识别为异常: {pods}"

    summary = LayerClassifierNode._extract_current_abnormal_summary_from_events(events)
    assert any("workload-5f4fb9ff45-fhgnk" in row for row in summary["selected_rows"])
    assert not any("coredns" in row for row in summary["selected_rows"])
    assert not any("job-done" in row for row in summary["selected_rows"])


def _selection_fact(
    fact_id,
    *,
    dimension,
    value,
    evidence_role="symptom",
    confidence="high",
    strength="strong",
    fact_type="measurement",
    attribute="observation.value",
    directness="direct",
):
    return {
        "fact_id": fact_id,
        "entity_id": "k8s.pod:scope/unit:uid-1",
        "entity_kind": "Pod",
        "namespace": "scope",
        "entity_name": "unit",
        "dimension": dimension,
        "fact_type": fact_type,
        "attribute": attribute,
        "value": value,
        "source_system": f"source-{dimension}",
        "directness": directness,
        "confidence": confidence,
        "strength": strength,
        "evidence_role": evidence_role,
    }


def test_selection_manifest_overflow_v2_is_deterministic_and_accounts_for_all_facts():
    dimensions = ("kubernetes", "metrics", "logging", "tracing")
    records = [
        _selection_fact(
            f"fact-{dimension}-{index:02d}",
            dimension=dimension,
            value={"sample": index},
            evidence_role="causal_candidate" if index == 0 else "symptom",
        )
        for dimension in dimensions
        for index in range(16)
    ]
    fact_index = {record["fact_id"]: record for record in records}

    manifest = build_selection_manifest(fact_index, max_facts=48).to_dict()
    reversed_manifest = build_selection_manifest(
        dict(reversed(list(fact_index.items()))),
        max_facts=48,
    ).to_dict()

    assert manifest == reversed_manifest
    assert manifest["contract_version"] == "aiops.selection-manifest.v2"
    assert manifest["max_facts"] == 48
    assert manifest["total_fact_count"] == 64
    assert manifest["overflowed"] is True
    assert len(manifest["rca_input_fact_ids"]) == 48
    selected = set(manifest["rca_input_fact_ids"])
    omitted = set(manifest["omitted_fact_ids"])
    assert selected.isdisjoint(omitted)
    assert selected | omitted == set(fact_index)
    assert {
        fact_index[fact_id]["dimension"]
        for fact_id in manifest["rca_input_fact_ids"]
    } >= set(dimensions)
    assert set(manifest) >= {
        "eligible_support_fact_ids",
        "direct_causal_candidate_fact_ids",
        "required_context_fact_ids",
        "rca_input_fact_ids",
        "omitted_fact_ids",
        "omission_reasons",
        "representative_of",
        "unselected_higher_priority_causal_fact_ids",
    }
    assert set(manifest["eligible_support_fact_ids"]) <= selected
    assert set(manifest["direct_causal_candidate_fact_ids"]) <= selected
    assert set(manifest["required_context_fact_ids"]) <= selected


def test_selection_manifest_overflow_preserves_required_dimensions_under_extra_dimension_pressure():
    records = [
        _selection_fact(
            f"fact-{dimension}",
            dimension=dimension,
            value={"sample": dimension},
            evidence_role=(
                "symptom" if dimension == "tracing" else "causal_candidate"
            ),
        )
        for dimension in (
            "kubernetes",
            "metrics",
            "logging",
            "tracing",
            "topology",
        )
    ]
    fact_index = {record["fact_id"]: record for record in records}

    manifest = build_selection_manifest(fact_index, max_facts=4).to_dict()

    assert {
        fact_index[fact_id]["dimension"]
        for fact_id in manifest["rca_input_fact_ids"]
    } == {"kubernetes", "metrics", "logging", "tracing"}


@pytest.mark.parametrize("max_facts", [1, 2, 3])
def test_selection_manifest_overflow_small_budget_prefers_direct_causal_signature(
    max_facts,
):
    records = [
        _selection_fact(
            f"fact-{dimension}-symptom",
            dimension=dimension,
            value={"sample": dimension},
            confidence="medium",
            strength="context",
            directness="derived",
        )
        for dimension in ("kubernetes", "metrics", "logging")
    ]
    records.append(_selection_fact(
        "fact-tracing-causal",
        dimension="tracing",
        value={"sample": "causal"},
        evidence_role="causal_candidate",
    ))
    fact_index = {record["fact_id"]: record for record in records}

    manifest = build_selection_manifest(
        fact_index,
        max_facts=max_facts,
    ).to_dict()

    assert "fact-tracing-causal" in manifest["rca_input_fact_ids"]


@pytest.mark.parametrize(
    ("first", "second", "expected_fact_id"),
    [
        (
            {
                "fact_id": "fact-direct-strong",
                "dimension": "tracing",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
            },
            {
                "fact_id": "fact-derived-critical",
                "dimension": "logging",
                "directness": "derived",
                "confidence": "high",
                "strength": "critical",
            },
            "fact-direct-strong",
        ),
        (
            {
                "fact_id": "fact-high-supporting",
                "dimension": "tracing",
                "directness": "direct",
                "confidence": "high",
                "strength": "supporting",
            },
            {
                "fact_id": "fact-medium-critical",
                "dimension": "logging",
                "directness": "direct",
                "confidence": "medium",
                "strength": "critical",
            },
            "fact-high-supporting",
        ),
        (
            {
                "fact_id": "fact-tracing-tie",
                "dimension": "tracing",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
            },
            {
                "fact_id": "fact-kubernetes-tie",
                "dimension": "kubernetes",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
            },
            "fact-kubernetes-tie",
        ),
        (
            {
                "fact_id": "fact-z-tie",
                "dimension": "logging",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
            },
            {
                "fact_id": "fact-a-tie",
                "dimension": "logging",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
            },
            "fact-a-tie",
        ),
    ],
)
def test_selection_manifest_overflow_causal_phase_priority_matrix(
    first,
    second,
    expected_fact_id,
):
    records = [
        _selection_fact(
            item["fact_id"],
            dimension=item["dimension"],
            value={"sample": item["fact_id"]},
            evidence_role="causal_candidate",
            directness=item["directness"],
            confidence=item["confidence"],
            strength=item["strength"],
        )
        for item in (first, second)
    ]

    manifests = [
        build_selection_manifest(
            {record["fact_id"]: record for record in ordered_records},
            max_facts=1,
        ).to_dict()
        for ordered_records in (records, list(reversed(records)))
    ]

    assert [
        manifest["rca_input_fact_ids"]
        for manifest in manifests
    ] == [[expected_fact_id], [expected_fact_id]]


@pytest.mark.parametrize(
    (
        "causal_directness",
        "causal_confidence",
        "causal_strength",
        "counter_role",
        "expected_fact_id",
        "expected_unselected_causal",
    ),
    [
        (
            "derived",
            "high",
            "critical",
            "contradicting",
            "fact-direct-counter",
            [],
        ),
        (
            "related_context",
            "high",
            "critical",
            "negative_observation",
            "fact-direct-counter",
            [],
        ),
        (
            "direct",
            "low",
            "critical",
            "contradicting",
            "fact-direct-counter",
            [],
        ),
        (
            "direct",
            "medium",
            "strong",
            "contradicting",
            "fact-causal",
            [],
        ),
        (
            "direct",
            "medium",
            "supporting",
            "causal_candidate",
            "fact-direct-counter",
            ["fact-causal"],
        ),
    ],
)
def test_selection_manifest_overflow_phase_eligibility_matrix(
    causal_directness,
    causal_confidence,
    causal_strength,
    counter_role,
    expected_fact_id,
    expected_unselected_causal,
):
    records = [
        _selection_fact(
            "fact-causal",
            dimension="logging",
            value={"sample": "causal"},
            evidence_role="causal_candidate",
            directness=causal_directness,
            confidence=causal_confidence,
            strength=causal_strength,
        ),
        _selection_fact(
            "fact-direct-counter",
            dimension="tracing",
            value={"sample": "counter"},
            evidence_role=counter_role,
            directness="direct",
            confidence="high",
            strength="strong",
        ),
    ]

    manifests = [
        build_selection_manifest(
            {record["fact_id"]: record for record in ordered_records},
            max_facts=1,
        ).to_dict()
        for ordered_records in (records, list(reversed(records)))
    ]

    assert [
        manifest["rca_input_fact_ids"]
        for manifest in manifests
    ] == [[expected_fact_id], [expected_fact_id]]
    assert [
        manifest["unselected_higher_priority_causal_fact_ids"]
        for manifest in manifests
    ] == [expected_unselected_causal, expected_unselected_causal]


def test_selection_manifest_overflow_represents_distinct_causal_signature_before_second_value():
    records = [
        _selection_fact(
            "fact-shared-a",
            dimension="logging",
            value={"sample": 1},
            evidence_role="causal_candidate",
            attribute="observation.shared",
        ),
        _selection_fact(
            "fact-shared-b",
            dimension="logging",
            value={"sample": 2},
            evidence_role="causal_candidate",
            attribute="observation.shared",
        ),
        _selection_fact(
            "fact-distinct",
            dimension="logging",
            value={"sample": 3},
            evidence_role="causal_candidate",
            confidence="medium",
            strength="supporting",
            attribute="observation.distinct",
        ),
    ]
    fact_index = {record["fact_id"]: record for record in records}

    bounded = build_selection_manifest(fact_index, max_facts=2).to_dict()
    ordered = build_selection_manifest(fact_index, max_facts=3).to_dict()

    assert set(bounded["rca_input_fact_ids"]) == {
        "fact-shared-a",
        "fact-distinct",
    }
    assert ordered["rca_input_fact_ids"].index("fact-distinct") < (
        ordered["rca_input_fact_ids"].index("fact-shared-b")
    )


def test_selection_manifest_overflow_preserves_required_dimensions_when_coverage_is_feasible():
    records = [
        _selection_fact(
            f"fact-{dimension}-symptom",
            dimension=dimension,
            value={"sample": dimension},
            confidence="medium",
            strength="context",
            directness="derived",
        )
        for dimension in ("kubernetes", "metrics", "logging", "tracing")
    ]
    records.extend(
        _selection_fact(
            f"fact-topology-causal-{index}",
            dimension="topology",
            value={"sample": index},
            evidence_role="causal_candidate",
            attribute=f"observation.causal-{index}",
        )
        for index in range(3)
    )
    fact_index = {record["fact_id"]: record for record in records}

    manifest = build_selection_manifest(fact_index, max_facts=4).to_dict()

    assert {
        fact_index[fact_id]["dimension"]
        for fact_id in manifest["rca_input_fact_ids"]
    } == {"kubernetes", "metrics", "logging", "tracing"}


def test_selection_manifest_equivalent_observations_keep_one_projection_representative():
    equivalent_ids = ["fact-equivalent-a", "fact-equivalent-b", "fact-equivalent-c"]
    fact_index = {
        "fact-equivalent-a": _selection_fact(
            "fact-equivalent-a",
            dimension="metrics",
            value={"sample": 7},
            confidence="high",
            strength="strong",
        ),
        "fact-equivalent-b": _selection_fact(
            "fact-equivalent-b",
            dimension="metrics",
            value={"sample": 7},
            confidence="medium",
            strength="supporting",
        ),
        "fact-equivalent-c": _selection_fact(
            "fact-equivalent-c",
            dimension="metrics",
            value={"sample": 7},
            confidence="low",
            strength="context",
        ),
    }
    fact_index["fact-distinct"] = _selection_fact(
        "fact-distinct",
        dimension="logging",
        value={"sample": 8},
    )
    original = json.loads(json.dumps(fact_index))

    manifest = build_selection_manifest(fact_index, max_facts=2).to_dict()

    selected_equivalent = set(equivalent_ids) & set(
        manifest["rca_input_fact_ids"]
    )
    omitted_equivalent = set(equivalent_ids) & set(manifest["omitted_fact_ids"])
    assert selected_equivalent == {"fact-equivalent-a"}
    assert omitted_equivalent == {
        "fact-equivalent-b",
        "fact-equivalent-c",
    }
    assert set(manifest["eligible_support_fact_ids"]) <= set(
        manifest["rca_input_fact_ids"]
    )
    assert {
        fact_id: manifest["omission_reasons"][fact_id]
        for fact_id in omitted_equivalent
    } == {
        fact_id: "equivalent_observation"
        for fact_id in omitted_equivalent
    }
    assert fact_index == original


def test_selection_manifest_equivalent_representative_maps_to_complete_class():
    equivalent_ids = ["fact-equivalent-a", "fact-equivalent-b", "fact-equivalent-c"]
    fact_index = {
        fact_id: _selection_fact(
            fact_id,
            dimension="metrics",
            value={"sample": 7},
        )
        for fact_id in equivalent_ids
    }

    manifest = build_selection_manifest(fact_index, max_facts=1).to_dict()

    assert manifest["representative_of"] == {
        "fact-equivalent-a": equivalent_ids,
    }
