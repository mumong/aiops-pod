import hashlib
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json

import pytest

from app.core.prompts import EVIDENCE_COLLECTOR_PROMPT
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.schemas import EvidenceCollectionOutput, EvidencePlanOutput
from app.core.skills.models import EvidenceItem, EvidenceLevel, Layer


def _canonical_fact_record(**overrides):
    record = {
        "entity_id": "k8s.pod:demo/api:uid-a",
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "logging",
        "fact_type": "log",
        "attribute": "log.message",
        "value": {"message": "observed event"},
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


def test_evidence_should_continue_when_important_item_is_still_missing():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
        {"id": "e2", "description": "检查 Deployment 配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment x -o yaml", "purpose": "确认配置"},
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "result": "Reason: Evicted",
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is False


def test_evidence_should_continue_when_any_critical_item_is_missing():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
        {"id": "e2", "description": "检查节点磁盘压力", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node x", "purpose": "确认节点状态"},
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "result": "Reason: Evicted",
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is False


def test_evidence_should_stop_when_critical_and_important_items_are_collected():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
        {"id": "e2", "description": "检查 Deployment 配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment x -o yaml", "purpose": "确认配置"},
        {"id": "e3", "description": "补充日志", "level": "optional", "tool": "kubectl_logs", "command": "kubectl logs x", "purpose": "补充上下文"},
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "result": "Reason: Evicted",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_yaml",
            "result": "kind: Deployment",
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is True


def test_evidence_execute_records_early_stop_metadata():
    node = EvidenceCollectorNode()
    node._plan_evidence_with_llm = lambda **kwargs: (
        [
            {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
            {"id": "e2", "description": "检查 Deployment 配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment x -o yaml", "purpose": "确认配置"},
        ],
        [
            {"type": "tool_result", "status": "success", "tool_name": "kubectl_describe", "result_preview": "Reason: Evicted", "result": "Reason: Evicted"},
            {"type": "tool_result", "status": "success", "tool_name": "kubectl_get_yaml", "result_preview": "kind: Deployment", "result": "kind: Deployment"},
        ],
        "已满足关键证据，提前停止",
    )
    node._extract_tool_data_from_thinking = lambda events: [
        {"tool": "kubectl_describe", "data": "Reason: Evicted", "duration_s": 0.1},
        {"tool": "kubectl_get_yaml", "data": "kind: Deployment", "duration_s": 0.1},
    ]
    node._save_thinking = lambda state, new_state, thinking_events: None
    node._early_stop_state = {
        "triggered": True,
        "reason": "critical 和 important 级证据均已满足，提前停止",
        "required_levels": ["critical", "important"],
    }

    result = node.execute({
        "question": "我的集群有什么问题",
        "layer": Layer.L0,
        "layer_analysis": "{}",
        "possible_scenarios": [],
        "key_entities": [],
    })

    analysis = json.loads(result["evidence_analysis"])
    assert analysis["early_stop"]["triggered"] is True
    assert "important" in analysis["early_stop"]["required_levels"]
    assert "提前停止" in analysis["early_stop"]["reason"]
    assert analysis["plan_total"] == len(analysis["evidence_plan"])
    assert analysis["plan_collected"] == 2
    assert analysis["environment_evidence_collected"] == 2
    assert analysis["evidence_inventory"][0]["id"] == "e1"


def test_evidence_builds_collection_output_with_pydantic_schema():
    node = EvidenceCollectorNode()
    output = node._build_evidence_collection_output(
        evidence_plan=[
            {
                "id": "e1",
                "description": "确认事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认失败原因",
            }
        ],
        tool_results=[],
        tool_data=[],
        llm_result_text="已完成采集",
        plan_total=1,
        plan_collected=1,
        plan_completeness=1.0,
        environment_total=1,
        environment_collected=1,
        environment_completeness=1.0,
        evidence_inventory=[
            {
                "id": "e1",
                "description": "确认事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认失败原因",
                "collected": True,
                "source": "thinking_match",
            }
        ],
        missing_reasons=[],
        early_stop={"triggered": True, "reason": "完成", "required_levels": ["critical"]},
    )

    assert isinstance(output, EvidenceCollectionOutput)
    assert output.plan_total == 1
    assert output.evidence_inventory[0]["collected"] is True


def test_evidence_normalizes_yaml_plan_away_from_get_by_name():
    plan = EvidenceCollectorNode._normalize_evidence_plan([
        {
            "id": "e1",
            "description": "确认 Pod deletionTimestamp 和 finalizers",
            "level": "critical",
            "tool": "kubectl_get_by_name",
            "command": "kubectl get pod rc-terminating-finalizer -n aiops-e2e -o yaml",
            "tool_args": {
                "name": "rc-terminating-finalizer",
                "namespace": "aiops-e2e",
                "output_format": "yaml",
            },
            "purpose": "确认 metadata.deletionTimestamp/finalizers",
            "evidence_type": "pod_yaml",
            "acceptable_tools": ["kubectl_get_by_name"],
        }
    ])

    assert plan[0]["tool"] == "kubectl_get_yaml"
    assert plan[0]["tool_args"] == {"kind": "pod", "name": "rc-terminating-finalizer", "namespace": "aiops-e2e"}
    assert "kubectl_get_yaml" in plan[0]["acceptable_tools"]


def test_evidence_normalizes_missing_kind_for_named_kubectl_tools():
    plan = EvidenceCollectorNode._normalize_evidence_plan([
        {
            "id": "e1",
            "description": "确认 Pod YAML",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod rc-terminating-finalizer -n aiops-e2e -o yaml",
            "tool_args": {"name": "rc-terminating-finalizer", "namespace": "aiops-e2e"},
            "purpose": "确认 deletionTimestamp/finalizers",
            "evidence_type": "yaml",
        },
        {
            "id": "e2",
            "description": "确认 describe",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod rc-terminating-finalizer -n aiops-e2e",
            "tool_args": {"name": "rc-terminating-finalizer", "namespace": "aiops-e2e"},
            "purpose": "确认 Killing 事件",
        },
        {
            "id": "e3",
            "description": "确认 Node YAML",
            "level": "important",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get node node1 -o yaml",
            "tool_args": {"name": "node1"},
            "purpose": "确认节点 Ready",
            "evidence_type": "yaml",
        },
    ])

    assert plan[0]["tool_args"] == {"kind": "pod", "name": "rc-terminating-finalizer", "namespace": "aiops-e2e"}
    assert plan[1]["tool_args"] == {"kind": "pod", "name": "rc-terminating-finalizer", "namespace": "aiops-e2e"}
    assert plan[2]["tool_args"] == {"kind": "node", "name": "node1"}


def test_yaml_plan_is_not_matched_by_tabular_get_by_name_output():
    matched = EvidenceCollectorNode._tool_result_matches_plan(
        plan_tool="kubectl_get_yaml",
        plan_cmd="kubectl get pod rc-terminating-finalizer -n aiops-e2e -o yaml",
        plan_desc="确认 Pod deletionTimestamp 和 finalizers",
        tool_name="kubectl_get_by_name",
        result=(
            "NAME                       READY   STATUS        RESTARTS   AGE\n"
            "rc-terminating-finalizer   0/1     Terminating   0          2m\n"
        ),
        structured={"status": "kept_small_output"},
        tool_args={"name": "rc-terminating-finalizer", "namespace": "aiops-e2e"},
        plan_intent="pod_yaml",
    )

    assert matched is False


def test_yaml_plan_matches_real_yaml_summary():
    matched = EvidenceCollectorNode._tool_result_matches_plan(
        plan_tool="kubectl_get_yaml",
        plan_cmd="kubectl get pod rc-terminating-finalizer -n aiops-e2e -o yaml",
        plan_desc="确认 Pod deletionTimestamp 和 finalizers",
        tool_name="kubectl_get_yaml",
        result=(
            "kubectl_get_yaml 关键字段摘要:\n"
            "kind: Pod\n"
            "name: rc-terminating-finalizer\n"
            "namespace: aiops-e2e\n"
            "deletionTimestamp: 2026-05-18T01:00:00Z\n"
            "finalizers: aiops.e2e/hold\n"
        ),
        structured={"status": "yaml_summarized", "kind": "Pod", "name": "rc-terminating-finalizer", "namespace": "aiops-e2e"},
        tool_args={"name": "rc-terminating-finalizer", "namespace": "aiops-e2e"},
        plan_intent="pod_yaml",
    )

    assert matched is True


def test_evidence_execute_retries_when_plan_exists_but_no_tool_results():
    node = EvidenceCollectorNode()
    calls = []

    first_plan = [
        {"id": "e1", "description": "确认 Pod YAML", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod x", "purpose": "确认状态"},
        {"id": "e2", "description": "确认 Events", "level": "important", "tool": "kubectl_events", "command": "kubectl events x", "purpose": "确认错误"},
    ]
    second_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_yaml",
            "result_preview": "kind: Pod",
            "result": "kind: Pod",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "result_preview": "Back-off pulling image",
            "result": "Back-off pulling image",
        },
    ]

    def _fake_plan(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return first_plan, [], "只输出了计划，没有执行工具"
        return first_plan, second_events, "第二次执行了工具"

    node._plan_evidence_with_llm = _fake_plan
    node._save_thinking = lambda state, new_state, thinking_events: None

    result = node.execute({
        "question": "我的集群有什么问题",
        "layer": Layer.L3,
        "layer_analysis": "{}",
        "possible_scenarios": [],
        "key_entities": [],
    })

    assert len(calls) == 2
    assert calls[1]["strict_mode"] is False
    assert calls[1]["existing_plan"] == first_plan
    assert "不要重新输出 evidence_plan" in calls[1]["failure_reason"]
    assert result["evidence_completeness"] == 1.0
    assert len(result["evidence_items"]) == 2


def test_evidence_execute_does_not_retry_when_pydantic_plan_has_effective_tool_result():
    node = EvidenceCollectorNode()
    calls = []

    first_events = [
        {
            "type": "tool_start",
            "tool_name": "kubectl_events",
            "tool_args": {"resource_type": "pod", "resource_name": "ham-wcc79", "namespace": "xnet"},
        },
        {
            "type": "ai_message",
            "full_content": "计划已由 Pydantic evidence_plan 生成，但工具被提前调用。",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "result_preview": "Failed to pull image",
            "result": "Failed to pull image",
        },
    ]
    second_plan = [
        {"id": "e1", "description": "确认 Pod 事件", "level": "critical", "tool": "kubectl_events", "command": "kubectl events ...", "purpose": "确认镜像拉取失败原因"}
    ]
    second_events = [
        {
            "type": "ai_message",
            "full_content": "沿用 Pydantic evidence_plan 后开始执行工具。",
        },
        {
            "type": "tool_start",
            "tool_name": "kubectl_events",
            "tool_args": {"resource_type": "pod", "resource_name": "ham-wcc79", "namespace": "xnet"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "result_preview": "Failed to pull image",
            "result": "Failed to pull image",
        },
    ]

    def _fake_plan(**kwargs):
        calls.append({"strict_mode": kwargs.get("strict_mode", False), "failure_reason": kwargs.get("failure_reason", "")})
        if len(calls) == 1:
            return second_plan, first_events, "先调了工具，再补 plan"
        return second_plan, second_events, "先输出 plan，再执行工具"

    node._plan_evidence_with_llm = _fake_plan
    node._save_thinking = lambda state, new_state, thinking_events: None

    result = node.execute({
        "question": "我的集群有什么问题",
        "layer": Layer.L3,
        "layer_analysis": "{}",
        "possible_scenarios": [],
        "key_entities": [],
    })

    assert len(calls) == 1
    assert calls[0]["strict_mode"] is False
    assert result["evidence_completeness"] == 1.0


def test_pydantic_external_plan_does_not_retry_when_execution_has_no_inband_plan():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "确认 Pod 事件",
            "level": "critical",
            "tool": "kubectl_events",
            "command": "kubectl events ...",
            "purpose": "确认镜像拉取失败原因",
        }
    ]
    events = [
        {
            "type": "tool_start",
            "tool_name": "kubectl_events",
            "tool_args": {"resource_type": "pod", "resource_name": "ham-wcc79", "namespace": "xnet"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "result_preview": "Failed to pull image",
            "result": "Failed to pull image",
        },
    ]

    assert node._get_plan_protocol_failure_reason(plan, events) == ""


def test_evidence_user_prompt_uses_pydantic_plan_contract_instead_of_in_band_json():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L3",
        layer_handoff='{"layer":"L3"}',
    )

    assert "EvidencePlanOutput" in message or "Pydantic evidence_plan" in message
    assert "第一条 assistant 消息必须只输出 evidence_plan JSON" not in message
    assert "在输出 evidence_plan JSON 之前，禁止调用任何工具" not in message
    assert "必须调用至少一个 critical 或 important 级真实工具" in message
    assert "evidence_plan 阶段不要重新选择 runbook" in message
    assert "evidence_plan 第一项必须是 fetch_runbook" not in message
    assert "Pod 异常状态的证据" in message


def test_evidence_user_prompt_prioritizes_live_observability_for_broad_multi_pod_question():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群现在有什么问题？",
        layer="L2",
        layer_handoff=json.dumps(
            {
                "active_entities": [
                    {
                        "type": "Pod",
                        "namespace": "ns-a",
                        "name": "pod-a",
                    },
                    {
                        "type": "Pod",
                        "namespace": "ns-b",
                        "name": "pod-b",
                    },
                ],
                "issue_groups": [],
            },
            ensure_ascii=False,
        ),
    )

    guidance = message.rsplit("# 实时可观测性证据优先", 1)[1]
    assert "ns-a/pod-a" in guidance
    assert "ns-b/pod-b" in guidance
    assert "`collect_aiops_case`" in guidance
    assert "高信息密度" in guidance
    assert "每个已确认异常 Pod" in guidance
    assert "必须优先执行" in guidance
    assert "kubectl" in guidance
    assert "降级" in guidance
    assert "80%" in guidance
    assert "用户同时要求 metrics" not in guidance
    assert "不是代码强制编排" not in guidance


def test_evidence_user_prompt_keeps_live_observability_guidance_generic():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="请分析这个异常。",
        layer="L3",
        layer_handoff=json.dumps(
            {
                "issue_groups": [
                    {
                        "group_id": "g1",
                        "entities": [
                            {
                                "kind": "Pod",
                                "namespace": "generic-ns",
                                "name": "generic-pod",
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
    )

    guidance = message.rsplit("# 实时可观测性证据优先", 1)[1]
    assert "generic-ns/generic-pod" in guidance
    assert "OOMKilled" not in guidance
    assert "ImagePullBackOff" not in guidance
    assert "CrashLoopBackOff" not in guidance
    assert "固定调用次数" not in guidance


def test_evidence_system_prompt_prioritizes_live_observability_independent_of_user_wording():
    assert "用户是否显式提到" in EVIDENCE_COLLECTOR_PROMPT
    assert "实时可观测性证据" in EVIDENCE_COLLECTOR_PROMPT
    assert "每个已确认异常 Pod" in EVIDENCE_COLLECTOR_PROMPT
    assert "mandatory" in EVIDENCE_COLLECTOR_PROMPT
    assert "80%" in EVIDENCE_COLLECTOR_PROMPT
    assert "若单一 kubectl 事实已足够回答问题" not in EVIDENCE_COLLECTOR_PROMPT


def test_evidence_user_prompt_with_existing_plan_skips_replanning():
    plan = [
        {
            "id": "e1",
            "description": "确认 Pod 状态",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod x -n ns",
            "purpose": "确认当前状态",
        }
    ]

    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L3",
        layer_handoff='{"layer":"L3"}',
        existing_plan=plan,
        failure_reason="不要重新输出 evidence_plan",
    )

    assert "既有 evidence_plan" in message
    assert "不要重新输出 evidence_plan" in message
    assert "第一条 assistant 消息必须只输出 evidence_plan JSON" not in message
    assert "直接执行既有 Pydantic evidence_plan 中的必要工具" in message


def test_evidence_user_prompt_keeps_context_archive_reference_compact():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L3",
        layer_handoff='{"layer":"L3"}',
        context_archive_ref="/tmp/aiops/reports/context_archives/run-1",
        layer_archive_ref={
            "full_analysis_ref": "/tmp/aiops/reports/context_archives/run-1/layer/full_analysis.md",
            "handoff_ref": "/tmp/aiops/reports/context_archives/run-1/layer/handoff.json",
        },
    )

    assert "/tmp/aiops/reports/context_archives/run-1" not in message
    assert "context archive 已落盘" in message
    assert "/tmp/aiops/reports/context_archives/run-1/budget/layer.json" not in message
    assert "/tmp/aiops/reports/context_archives/run-1/tools/" not in message
    assert "layer full_analysis_ref:" not in message
    assert "read_context_archive" not in message


def test_evidence_early_stop_disabled_does_not_pass_stop_checker():
    node = EvidenceCollectorNode()
    node.workflow_config_override = {"evidence": {"early_stop": {"enabled": False}}}
    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            return schema.model_validate({
                "layer": "L3",
                "evidence_plan": [
                    {
                        "id": "e1",
                        "description": "获取 Pod 事件",
                        "level": "critical",
                        "tool": "kubectl_events",
                        "command": "kubectl get events -n aaa",
                        "purpose": "确认异常原因",
                    }
                ],
                "collection_strategy": "最小验证",
            }), "{}"

    node.ai_call = _StructuredAICall()
    calls = []

    def _fake_call_llm(question, system_prompt, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(result='{"evidence_plan": []}'), []

    node._call_llm = _fake_call_llm

    node._plan_evidence_with_llm(
        question="我的集群有什么问题",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
    )

    assert calls[0]["stop_checker"] is None


def test_evidence_early_stop_enabled_by_default_passes_stop_checker():
    node = EvidenceCollectorNode()
    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            return schema.model_validate({
                "layer": "L3",
                "evidence_plan": [
                    {
                        "id": "e1",
                        "description": "获取 Pod 事件",
                        "level": "critical",
                        "tool": "kubectl_events",
                        "command": "kubectl get events -n aaa",
                        "purpose": "确认异常原因",
                    }
                ],
                "collection_strategy": "最小验证",
            }), "{}"

    node.ai_call = _StructuredAICall()
    calls = []

    def _fake_call_llm(question, system_prompt, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(result='{"evidence_plan": []}'), []

    node._call_llm = _fake_call_llm

    node._plan_evidence_with_llm(
        question="我的集群有什么问题",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
    )

    assert calls[0]["stop_checker"] == node._should_stop_collection_early


def test_evidence_plan_is_generated_with_structured_output_before_tool_execution():
    node = EvidenceCollectorNode()
    node.workflow_config_override = {"evidence": {"agent_structured_output": False}}
    calls = []

    class _StructuredAICall:
        def call_structured(self, system_prompt, question, schema, **kwargs):
            calls.append({
                "schema": schema,
                "node_id": kwargs.get("node_id"),
                "question": question,
            })
            return schema.model_validate({
                "layer": "L3",
                "evidence_plan": [
                    {
                        "id": "e1",
                        "description": "获取 Pod 事件",
                        "level": "critical",
                        "tool": "kubectl_events",
                        "command": "kubectl get events -n aaa",
                        "purpose": "确认异常原因",
                    }
                ],
                "collection_strategy": "最小验证",
            }), "{}"

    node.ai_call = _StructuredAICall()

    def _fake_call_llm(question, system_prompt, **kwargs):
        assert "既有 evidence_plan" in question
        return SimpleNamespace(result="已执行"), [
            {"type": "tool_result", "status": "success", "tool_name": "kubectl_events", "result": "Failed to pull image"}
        ]

    node._call_llm = _fake_call_llm

    plan, events, text = node._plan_evidence_with_llm(
        question="我的集群有什么问题",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
    )

    assert calls[0]["schema"] is EvidencePlanOutput
    assert calls[0]["node_id"] == "evidence_plan"
    assert plan[0]["id"] == "e1"
    assert events[0]["tool_name"] == "kubectl_events"


def test_evidence_preplanned_execution_collects_tools_without_agent_response_schema():
    node = EvidenceCollectorNode()
    captured = {}
    structured_plan = EvidencePlanOutput.model_validate({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认异常原因",
            }
        ],
        "collection_strategy": "先查事件",
    })

    class _PlanAICall:
        def call_structured(self, *args, **kwargs):
            captured["plan_schema"] = kwargs.get("schema")
            return structured_plan, structured_plan.model_dump_json()

    node.ai_call = _PlanAICall()

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured["response_schema"] = kwargs.get("response_schema")
        captured["stop_checker"] = kwargs.get("stop_checker")
        captured["question"] = question
        return SimpleNamespace(result="已确认镜像拉取失败"), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "kubectl_events",
                "result": "Failed to pull image",
            }
        ]

    node._call_llm = _fake_call_llm

    plan, events, text = node._plan_evidence_with_llm(
        question="我的集群有什么问题",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
    )

    assert captured["plan_schema"] is EvidencePlanOutput
    assert captured["response_schema"] is None
    assert captured["stop_checker"] == node._should_stop_collection_early
    assert "既有 evidence_plan" in captured["question"]
    assert plan[0]["id"] == "e1"
    assert events[0]["tool_name"] == "kubectl_events"
    assert text == "已确认镜像拉取失败"


def test_evidence_preplanned_execution_blocks_tools_outside_the_plan():
    node = EvidenceCollectorNode()
    node.tools = [
        SimpleNamespace(name="collect_aiops_case"),
        SimpleNamespace(name="kubectl_get_yaml"),
        SimpleNamespace(name="kubectl_describe"),
        SimpleNamespace(name="fetch_runbook"),
        SimpleNamespace(name="get_aiops_case_evidence"),
        SimpleNamespace(name="kubectl_get_by_kind_in_namespace"),
        SimpleNamespace(name="query_aiops_metrics"),
        SimpleNamespace(name="TodoWrite"),
        SimpleNamespace(name="read_context_archive"),
    ]
    plan = [
        {
            "id": "case-a",
            "description": "采集 pod-a 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-a", "scenario": "auto"},
            "acceptable_tools": ["collect_aiops_case"],
            "source": "mandatory_live_observability",
        },
        {
            "id": "pod-yaml",
            "description": "检查 Pod 配置",
            "level": "optional",
            "tool": "kubectl_get_yaml",
            "tool_args": {"kind": "pod", "namespace": "ns", "name": "pod-a"},
            "acceptable_tools": ["kubectl_describe"],
        },
    ]
    captured = []

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured.append({
            "question": question,
            "blocked_tool_names": set(kwargs.get("blocked_tool_names") or []),
        })
        return SimpleNamespace(result="已采集 pod-a"), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "collect_aiops_case",
                "tool_args": {"namespace": "ns", "pod": "pod-a", "scenario": "auto"},
                "semantic_success": True,
                "structured": {
                    "status": "case_collected",
                    "primary_entity": {"namespace": "ns", "name": "pod-a"},
                },
                "result": "case collected for pod-a",
            }
        ]

    node._call_llm = _fake_call_llm

    node._execute_existing_evidence_plan(
        question="我的集群有什么问题？",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=plan,
        failure_reason="执行既有计划",
    )

    collection_blocked = captured[0]["blocked_tool_names"]
    reconciliation_blocked = captured[1]["blocked_tool_names"]
    assert collection_blocked >= {
        "kubectl_get_by_kind_in_namespace",
        "query_aiops_metrics",
        "TodoWrite",
        "read_context_archive",
    }
    assert "get_aiops_case_evidence" not in collection_blocked
    assert collection_blocked.isdisjoint({
        "collect_aiops_case",
        "kubectl_get_yaml",
        "kubectl_describe",
        "fetch_runbook",
    })
    assert "fetch_runbook" not in reconciliation_blocked
    assert "collect_aiops_case" in reconciliation_blocked


def test_evidence_reconciles_runbooks_once_after_live_cases_complete():
    node = EvidenceCollectorNode()
    node.tools = [
        SimpleNamespace(name="collect_aiops_case"),
        SimpleNamespace(name="get_aiops_case_evidence"),
        SimpleNamespace(name="fetch_runbook"),
        SimpleNamespace(name="kubectl_get_yaml"),
    ]
    plan = [
        {
            "id": "case-a",
            "description": "采集 pod-a 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-a", "scenario": "auto"},
            "source": "mandatory_live_observability",
        }
    ]
    calls = []

    def _fake_call_llm(question, system_prompt, **kwargs):
        calls.append({
            "question": question,
            "system_prompt": system_prompt,
            **kwargs,
        })
        if len(calls) == 1:
            return SimpleNamespace(result="case collected"), [
                {
                    "type": "tool_result",
                    "status": "success",
                    "tool_name": "collect_aiops_case",
                    "tool_args": {
                        "namespace": "ns",
                        "pod": "pod-a",
                        "scenario": "auto",
                    },
                    "semantic_success": True,
                    "structured": {
                        "status": "case_collected",
                        "primary_entity": {"namespace": "ns", "name": "pod-a"},
                    },
                    "result": (
                        "AIOPS_CASE case_id=case-a status=case_collected "
                        "error_code=CONFIG_MISSING "
                        'message="required config TOKEN is missing"'
                    ),
                }
            ]
        return SimpleNamespace(result="补充更具体的参考手册"), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "fetch_runbook",
                "tool_args": {"runbook_id": "pod-config-error.md"},
                "semantic_success": True,
                "result": "<runbook># Pod Config Error</runbook>",
            }
        ]

    node._call_llm = _fake_call_llm

    _, events, _ = node._execute_existing_evidence_plan(
        question="我的集群有什么问题？",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis=json.dumps({
            "matched_runbooks": ["pod-crashloop-runtime.md"],
            "abnormal_pods": [{"namespace": "ns", "name": "pod-a"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=plan,
        failure_reason="执行 mandatory plan",
    )

    assert len(calls) == 2
    reconciliation = calls[1]
    assert "action=post_case_runbook_reconciliation" in reconciliation["question"]
    assert "required config TOKEN is missing" in reconciliation["question"]
    assert "pod-crashloop-runtime.md" in reconciliation["question"]
    assert "fetch_runbook" not in reconciliation["blocked_tool_names"]
    assert reconciliation["blocked_tool_names"] >= {
        "collect_aiops_case",
        "get_aiops_case_evidence",
        "kubectl_get_yaml",
    }
    assert [
        event["tool_args"]["runbook_id"]
        for event in events
        if event.get("tool_name") == "fetch_runbook"
    ] == ["pod-config-error.md"]
    assert node._early_stop_state["reason"] == "post_case_reconciliation_complete"
    assert node._early_stop_state["post_case_reconciliation"] is True


def test_evidence_should_stop_when_required_item_has_diagnostic_negative_result():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {"id": "e1", "description": "检查节点到 Docker Hub 镜像仓库是否可达", "level": "critical", "tool": "run_bash_command", "command": "curl -v --connect-timeout 10 https://registry-1.docker.io/v2/", "purpose": "验证镜像仓库网络可达性"}
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stdout": "", "stderr": "命令执行超时 (60秒)", "returncode": -1}',
            "structured": {
                "status": "command_result",
                "success": False,
                "stderr_preview": "命令执行超时 (60秒)",
                "returncode": -1,
            },
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is True


def test_evidence_should_stop_when_kubectl_run_image_times_out_for_registry_probe():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {"id": "e1", "description": "运行临时 Pod 验证 redis 镜像是否可拉取", "level": "critical", "tool": "kubectl_run_image", "command": "kubectl run test-pull-redis --image=docker.io/bitnami/redis:5.0.7-debian-10-r32", "purpose": "验证镜像仓库访问和镜像拉取"}
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_run_image",
            "semantic_success": False,
            "result": '{"success": false, "stdout": "pod \\"test-pull-redis\\" deleted", "stderr": "error: timed out waiting for the condition", "returncode": 1}',
            "structured": {
                "status": "run_image_result",
                "success": False,
                "stderr": "error: timed out waiting for the condition",
                "signals": ["timeout"],
            },
        },
    ]

    assert node._should_stop_collection_early(thinking_events) is True


def test_evidence_waits_for_post_case_reconciliation_when_all_mandatory_cases_are_complete():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case",
            "description": "采集目标 Pod 的完整可观测性 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for pod trace-oom-api-abc "
                "in namespace aiops-traced-oom"
            ),
            "source": "mandatory_live_observability",
        }
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "AIOPS_CASE case_id=case-1",
            "structured": {
                "status": "case_collected",
                "primary_entity": {
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api-abc",
                },
                "coverage": {
                    "k8s": "present",
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "trace": "present",
                    "topology": "present",
                },
            },
        }
    ]

    assert node._should_stop_collection_early(thinking_events) is False
    assert node._early_stop_state["reason"] == "mandatory_live_observability_ready_for_reconciliation"
    assert node._early_stop_state["post_case_reconciliation"] is False


def test_preplanned_case_execution_allows_bounded_detail_evidence_tool():
    node = EvidenceCollectorNode()
    node.tools = [
        SimpleNamespace(name="collect_aiops_case"),
        SimpleNamespace(name="get_aiops_case_evidence"),
        SimpleNamespace(name="kubectl_get_yaml"),
    ]
    blocked = node._blocked_tools_for_preplanned_execution([
        {
            "id": "case",
            "tool": "collect_aiops_case",
            "source": "mandatory_live_observability",
        }
    ])

    assert "collect_aiops_case" not in blocked
    assert "get_aiops_case_evidence" not in blocked
    assert "kubectl_get_yaml" in blocked


def test_diagnostic_coverage_counts_real_dimension_details_not_only_case_success():
    node = EvidenceCollectorNode()
    stats = node._calculate_diagnostic_evidence_coverage([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "structured": {
                "status": "case_collected",
                "primary_entity": {"namespace": "ns", "name": "pod-a"},
                "coverage": {
                    "k8s": "present",
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "trace": "present",
                    "topology": "present",
                },
                "signals_summary": [
                    {
                        "dimension": "k8s",
                        "strength": "strong",
                        "observed": "Last terminated state: app=Error exit=78",
                    }
                ],
                "dimension_details": {
                    "metrics": {"highlights": [{"metric": "container_memory_working_set_bytes"}]},
                    "logs": {"samples": []},
                    "tracing": {
                        "flows": [{"request": "GET /checkout", "response_code": 500}],
                        "spans": [{"trace_id": "trace-1", "name": "GET /checkout"}],
                    },
                    "topology": {
                        "edges": [
                            {
                                "relationship": "Pod --owned_by--> ReplicaSet",
                                "source": "pod-a",
                                "target": "pod-a-rs",
                            }
                        ]
                    },
                },
            },
        }
    ])

    assert stats["dimension_coverage_total"] == 5
    assert stats["dimension_coverage_collected"] == 4
    assert stats["dimension_coverage"] == 0.8
    assert stats["diagnostic_evidence_missing"] == ["ns/pod-a:logs"]


def test_weak_sample_in_every_dimension_is_not_full_diagnostic_sufficiency():
    node = EvidenceCollectorNode()
    stats = node._calculate_diagnostic_evidence_coverage([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "structured": {
                "status": "case_collected",
                "primary_entity": {"namespace": "ns", "name": "pod-a"},
                "signals_summary": [
                    {
                        "dimension": "k8s",
                        "strength": "weak",
                        "observed": "Pod is not ready",
                    }
                ],
                "dimension_details": {
                    "metrics": {
                        "highlights": [
                            {
                                "metric": "container_memory_working_set_bytes",
                                "samples": ["08:22:40=4.2Mi"],
                            }
                        ]
                    },
                    "logs": {"samples": [{"message": "application started"}]},
                    "tracing": {
                        "flows": [{"request": "GET /health"}],
                        "spans": [],
                    },
                    "topology": {
                        "edges": [
                            {
                                "relationship": "Evidence --observes--> Pod",
                                "source": "prometheus",
                                "target": "pod-a",
                            }
                        ]
                    },
                },
            },
        }
    ])

    assert stats["dimension_coverage"] == 1.0
    assert stats["diagnostic_sufficiency"] < 1.0
    assert stats["diagnostic_sufficiency_label"] == "部分充分"


def test_single_metric_sample_with_limit_is_supporting_not_decisive():
    node = EvidenceCollectorNode()
    stats = node._calculate_diagnostic_evidence_coverage([
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "structured": {
                "status": "case_collected",
                "primary_entity": {"namespace": "ns", "name": "pod-a"},
                "signals_summary": [
                    {
                        "dimension": "k8s",
                        "strength": "strong",
                        "observed": "Last terminated state: app=Error exit=78",
                    }
                ],
                "dimension_details": {
                    "metrics": {
                        "highlights": [
                            {
                                "metric": "container_memory_working_set_bytes",
                                "max": "3.6Mi",
                                "last": "3.6Mi",
                                "limit": "96.0Mi",
                                "max_limit_ratio": 0.0377,
                                "samples": ["08:54:13=3.6Mi"],
                            }
                        ]
                    },
                    "logs": {
                        "samples": [
                            {
                                "level": "error",
                                "event": "config_missing",
                                "message": "required config TOKEN is missing",
                            }
                        ]
                    },
                    "tracing": {
                        "flows": [
                            {
                                "trace_id": "trace-1",
                                "request": "GET /checkout",
                                "response_code": 500,
                            }
                        ],
                        "spans": [
                            {
                                "trace_id": "trace-1",
                                "attributes": {"error.type": "CONFIG_MISSING"},
                            }
                        ],
                    },
                    "topology": {
                        "edges": [
                            {"relationship": "Pod --calls--> Pod"},
                            {"relationship": "Pod --owned_by--> ReplicaSet"},
                        ]
                    },
                },
            },
        }
    ])

    assert stats["dimension_coverage"] == 1.0
    assert stats["diagnostic_sufficiency"] == 0.9
    assert stats["diagnostic_sufficiency_label"] == "充分"


def test_evidence_waits_until_every_mandatory_case_target_is_complete():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case-a",
            "description": "采集 pod-a 的完整可观测性 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-a"},
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-b",
            "description": "采集 pod-b 的完整可观测性 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-b"},
            "source": "mandatory_live_observability",
        },
    ]
    thinking_events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "collect_aiops_case",
        "semantic_success": True,
        "tool_args": {"namespace": "ns", "pod": "pod-a"},
        "result": "AIOPS_CASE case_id=case-a",
        "structured": {
            "status": "case_collected",
            "primary_entity": {"namespace": "ns", "name": "pod-a"},
            "coverage": {
                "k8s": "present",
                "metrics": "present",
                "logs": "present",
                "tracing": "present",
                "trace": "present",
                "topology": "present",
            },
        },
    }]

    assert node._should_stop_collection_early(thinking_events) is False
    assert node._early_stop_state["triggered"] is False


def test_evidence_does_not_stop_when_coarse_aiops_case_has_missing_dimension():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case",
            "description": "采集目标 Pod 的完整可观测性 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for pod trace-oom-api-abc "
                "in namespace aiops-traced-oom"
            ),
        }
    ]
    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "AIOPS_CASE case_id=case-1",
            "structured": {
                "status": "case_collected",
                "primary_entity": {
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api-abc",
                },
                "coverage": {
                    "k8s": "present",
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "trace": "absent",
                    "topology": "present",
                },
            },
        }
    ]

    assert node._should_stop_collection_early(thinking_events) is False


def test_evidence_does_not_stop_after_kubectl_when_mandatory_case_is_pending():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case",
            "description": "采集异常 Pod 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod"},
            "source": "mandatory_live_observability",
        },
        {
            "id": "describe",
            "description": "确认 Pod 当前状态",
            "level": "critical",
            "tool": "kubectl_describe",
            "tool_args": {"namespace": "ns", "name": "pod"},
        },
    ]
    events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "kubectl_describe",
        "semantic_success": True,
        "tool_args": {"namespace": "ns", "name": "pod"},
        "result": "CrashLoopBackOff",
    }]

    assert node._should_stop_collection_early(events) is False


def test_evidence_stops_at_eighty_percent_context_and_records_remaining_targets():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case-a",
            "description": "采集 pod-a 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-a"},
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-b",
            "description": "采集 pod-b 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-b"},
            "source": "mandatory_live_observability",
        },
    ]
    events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "collect_aiops_case",
        "tool_args": {"namespace": "ns", "pod": "pod-a"},
        "context_usage_ratio": 0.81,
        "structured": {
            "status": "case_collected",
            "primary_entity": {"namespace": "ns", "name": "pod-a"},
        },
    }]

    assert node._should_stop_collection_early(events) is True
    assert node._early_stop_state["reason"] == "context_budget_stop"
    assert node._early_stop_state["uncollected_targets"] == ["ns/pod-b"]


def test_evidence_execution_continues_with_unattempted_mandatory_target():
    node = EvidenceCollectorNode()
    node._early_stop_state = {
        "triggered": False,
        "reason": "",
        "required_levels": ["mandatory_live_observability"],
    }
    plan = [
        {
            "id": "case-a",
            "description": "采集 pod-a 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-a", "scenario": "auto"},
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-b",
            "description": "采集 pod-b 多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-b", "scenario": "auto"},
            "source": "mandatory_live_observability",
        },
    ]
    calls = []

    def _case_event(pod):
        return {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": pod, "scenario": "auto"},
            "context_usage_ratio": 0.2,
            "semantic_success": True,
            "structured": {
                "status": "case_collected",
                "primary_entity": {"namespace": "ns", "name": pod},
            },
            "result": f"case collected for {pod}",
        }

    def _fake_call_llm(question, system_prompt, **kwargs):
        calls.append({"question": question, **kwargs})
        if "action=post_case_runbook_reconciliation" in question:
            return SimpleNamespace(
                result="runbook_reconciliation: keep_existing_or_none"
            ), []
        pod = "pod-a" if len(calls) == 1 else "pod-b"
        return SimpleNamespace(result=f"collected {pod}"), [_case_event(pod)]

    node._call_llm = _fake_call_llm

    returned_plan, events, _ = node._execute_existing_evidence_plan(
        question="我的集群有什么问题？",
        layer=Layer.L3,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis=json.dumps({
            "abnormal_pods": [
                {"namespace": "ns", "name": "pod-a"},
                {"namespace": "ns", "name": "pod-b"},
            ]
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=plan,
        failure_reason="执行 mandatory plan",
    )

    assert returned_plan == plan
    assert len(calls) == 3
    assert calls[1]["tool_result_sequence_start"] == 1
    assert "pod-b" in calls[1]["question"]
    assert "action=post_case_runbook_reconciliation" in calls[2]["question"]
    assert [
        event["tool_args"]["pod"]
        for event in events
        if event.get("tool_name") == "collect_aiops_case"
    ] == ["pod-a", "pod-b"]


def test_evidence_plan_normalization_drops_duplicate_probe_variants():
    plan = [
        {
            "id": "e1",
            "description": "使用 curl 检查 registry-1.docker.io 连通性",
            "level": "critical",
            "tool": "run_bash_command",
            "command": "curl -v https://registry-1.docker.io/v2/",
            "purpose": "验证镜像仓库网络可达性",
        },
        {
            "id": "e2",
            "description": "使用 telnet 检查 registry-1.docker.io 端口",
            "level": "important",
            "tool": "run_bash_command",
            "command": "telnet registry-1.docker.io 443",
            "purpose": "验证镜像仓库网络可达性",
        },
        {
            "id": "e3",
            "description": "使用 nc 检查 registry-1.docker.io 端口",
            "level": "important",
            "tool": "run_bash_command",
            "command": "nc -vz registry-1.docker.io 443",
            "purpose": "验证镜像仓库网络可达性",
        },
        {
            "id": "e4",
            "description": "获取 Pod YAML",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod test1-redis-master-0 -n aaa -o yaml",
            "purpose": "检查镜像和 imagePullSecrets",
        },
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(plan)

    assert [item["id"] for item in normalized] == ["e1", "e4"]


def test_evidence_plan_normalization_keeps_coarse_case_and_drops_same_pod_requeries():
    plan = [
        {
            "id": "case",
            "description": "采集目标 Pod 的多维可观测证据",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for pod trace-oom-api-abc in namespace "
                "aiops-traced-oom with scenario=auto"
            ),
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api-abc",
                "scenario": "auto",
            },
        },
        {
            "id": "yaml",
            "description": "获取同一 Pod YAML",
            "level": "important",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod trace-oom-api-abc -n aiops-traced-oom -o yaml",
        },
        {
            "id": "describe",
            "description": "Describe 同一 Pod",
            "level": "important",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod trace-oom-api-abc -n aiops-traced-oom",
        },
        {
            "id": "events",
            "description": "查询同一 Pod Events",
            "level": "important",
            "tool": "kubectl_events",
            "command": (
                "kubectl get events -n aiops-traced-oom "
                "--field-selector involvedObject.name=trace-oom-api-abc"
            ),
        },
        {
            "id": "logs",
            "description": "查询同一 Pod previous logs",
            "level": "important",
            "tool": "kubectl_previous_logs",
            "command": "kubectl logs trace-oom-api-abc -n aiops-traced-oom --previous",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-abc",
            },
        },
        {
            "id": "reload",
            "description": "重新读取刚采集的 case",
            "level": "important",
            "tool": "get_aiops_case",
            "command": "get_aiops_case after collect_aiops_case",
        },
        {
            "id": "runbook",
            "description": "读取 OOM runbook",
            "level": "reference",
            "tool": "fetch_runbook",
            "command": "fetch_runbook pod-oomkilled.md",
        },
        {
            "id": "other-pod",
            "description": "验证另一个 Pod",
            "level": "important",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod another-pod -n another-ns",
        },
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(plan)

    assert [item["id"] for item in normalized] == ["case", "runbook", "other-pod"]


def test_extract_plan_pod_target_accepts_target_scope_namespace_pod():
    target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "aiops-traced-config/trace-config-api-abc",
        "target_scope": "aiops-traced-config/trace-config-api-abc",
        "tool_args": {},
    })

    assert target == ("aiops-traced-config", "trace-config-api-abc")


def test_extract_plan_pod_target_accepts_qwen_target_parameter_aliases():
    command_target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "target_scope": "Pod",
        "command": (
            "collect_aiops_case with "
            "target_namespace='aiops-traced-oom' and "
            "target_pod='trace-oom-api-abc'"
        ),
        "tool_args": {},
    })
    tool_args_target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "target_scope": "Pod",
        "command": "collect_aiops_case",
        "tool_args": {
            "target_namespace": "aiops-traced-config",
            "target_pod": "trace-config-api-abc",
        },
    })

    assert command_target == ("aiops-traced-oom", "trace-oom-api-abc")
    assert tool_args_target == ("aiops-traced-config", "trace-config-api-abc")


def test_extract_plan_pod_target_accepts_explicit_pod_namespace_name_command():
    target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": (
            "get pod namespace=aiops-traced-config "
            "name=trace-config-api-abc"
        ),
        "tool_args": {},
    })

    assert target == ("aiops-traced-config", "trace-config-api-abc")


def test_extract_plan_pod_target_accepts_python_keyword_call_commands():
    single_quoted = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": (
            "get_pod_case(namespace='aiops-traced-config', "
            "name='trace-config-api-abc')"
        ),
        "tool_args": {},
    })
    double_quoted = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": (
            'get_pod_case(namespace="aiops-traced-oom", '
            'name="trace-oom-api-xyz")'
        ),
        "tool_args": {},
    })

    assert single_quoted == ("aiops-traced-config", "trace-config-api-abc")
    assert double_quoted == ("aiops-traced-oom", "trace-oom-api-xyz")


def test_extract_plan_pod_target_accepts_pod_name_namespace_colon_shorthand():
    target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "pod:trace-oom-api-xyz:aiops-traced-oom",
        "tool_args": {},
    })

    assert target == ("aiops-traced-oom", "trace-oom-api-xyz")


def test_prepare_evidence_plan_deduplicates_python_keyword_calls():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "get_pod_case(namespace='aiops-traced-config', "
                "name='trace-config-api-abc')"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                'get_pod_case(namespace="aiops-traced-oom", '
                'name="trace-oom-api-xyz")'
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }


def test_prepare_evidence_plan_deduplicates_colon_shorthand_commands():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "pod:trace-config-api-abc:aiops-traced-config",
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "pod:trace-oom-api-xyz:aiops-traced-oom",
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]


def test_extract_plan_pod_target_accepts_generic_entity_aliases_for_pods():
    target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "collect_aiops_case",
        "tool_args": {
            "namespace": "aiops-traced-oom",
            "entity_type": "Pod",
            "entity_name": "trace-oom-api-abc",
        },
    })
    non_pod_target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "collect_aiops_case",
        "tool_args": {
            "namespace": "aiops-traced-oom",
            "entity_type": "Deployment",
            "entity_name": "trace-oom-api",
        },
    })

    assert target == ("aiops-traced-oom", "trace-oom-api-abc")
    assert non_pod_target is None


def test_prepare_evidence_plan_deduplicates_qwen_entity_alias():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-abc",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-case",
            "description": "Collect the Pod observability case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "get the AIOps case for the pod entity",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "kind": "Pod",
                "entity": "trace-oom-api-abc",
            },
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-case"]
    assert EvidenceCollectorNode._extract_plan_pod_target(prepared[0]) == (
        "aiops-traced-oom",
        "trace-oom-api-abc",
    )


def test_extract_plan_pod_target_excludes_trailing_command_punctuation():
    parenthesized = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": (
            "collect_aiops_case("
            "target_namespace=aiops-traced-oom, "
            "target_pod=trace-oom-api-abc)"
        ),
    })
    terminated = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": (
            "collect_aiops_case target_namespace=aiops-traced-config "
            "target_pod=trace-config-api-abc;"
        ),
    })

    assert parenthesized == ("aiops-traced-oom", "trace-oom-api-abc")
    assert terminated == ("aiops-traced-config", "trace-config-api-abc")


def test_extract_plan_pod_target_accepts_qwen_bare_and_pod_shorthand_commands():
    bare_target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "aiops-traced-config/trace-config-api-abc",
        "tool_args": {},
    })
    prefixed_target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "collect_aiops_case for aiops-traced-oom/trace-oom-api-xyz",
        "tool_args": {},
    })
    shorthand_target = EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "kubectl_previous_logs",
        "command": "pod trace-config-api-abc -n aiops-traced-config --tail=100",
        "tool_args": {},
    })

    assert bare_target == ("aiops-traced-config", "trace-config-api-abc")
    assert prefixed_target == ("aiops-traced-oom", "trace-oom-api-xyz")
    assert shorthand_target == ("aiops-traced-config", "trace-config-api-abc")


def test_prepare_evidence_plan_deduplicates_pod_slash_name_in_namespace_syntax():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "pod/trace-config-api-abc "
                "in namespace aiops-traced-config"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "pod/trace-oom-api-xyz "
                "in namespace aiops-traced-oom"
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }


def test_prepare_evidence_plan_deduplicates_paired_prefixed_name_namespace_labels():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "get_pod_trace_config_name: trace-config-api-abc; "
                "get_pod_trace_config_namespace: aiops-traced-config"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "get_pod_trace_config_name: trace-oom-api-xyz; "
                "get_pod_trace_config_namespace: aiops-traced-oom"
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }


def test_prepare_evidence_plan_deduplicates_aiops_entity_pod_paths():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "aiops_entity=Pod/aiops-traced-config/"
                "trace-config-api-abc"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "aiops_entity=Pod/aiops-traced-oom/"
                "trace-oom-api-xyz"
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }
    assert EvidenceCollectorNode._extract_plan_pod_target({
        "tool": "collect_aiops_case",
        "command": "aiops_entity=Deployment/default/example-api",
        "tool_args": {},
    }) is None


def test_prepare_evidence_plan_binds_natural_language_to_handoff_pods():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for Pod trace-config-api-abc "
                "in aiops-traced-config"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for Pod trace-oom-api-xyz "
                "in aiops-traced-oom"
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert [item["tool_args"] for item in prepared] == [
        {
            "namespace": "aiops-traced-config",
            "pod": "trace-config-api-abc",
            "scenario": "auto",
        },
        {
            "namespace": "aiops-traced-oom",
            "pod": "trace-oom-api-xyz",
            "scenario": "auto",
        },
    ]


def test_normalize_evidence_plan_does_not_bind_ambiguous_handoff_pod_name():
    handoff = {
        "abnormal_pods": [
            {"kind": "Pod", "namespace": "team-a", "name": "worker-abc"},
            {"kind": "Pod", "namespace": "team-b", "name": "worker-abc"},
        ]
    }
    plan = [
        {
            "id": "ambiguous",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "collect observability for Pod worker-abc",
            "tool_args": {},
        },
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(
        plan,
        layer_handoff=handoff,
    )

    assert normalized[0]["tool_args"] == {}
    assert EvidenceCollectorNode._extract_plan_pod_target(normalized[0]) is None


def test_qwen_bare_case_targets_remove_same_pod_shorthand_requeries():
    plan = [
        {
            "id": "case-config",
            "tool": "collect_aiops_case",
            "command": "aiops-traced-config/trace-config-api-abc",
            "tool_args": {},
        },
        {
            "id": "case-oom",
            "tool": "collect_aiops_case",
            "command": "aiops-traced-oom/trace-oom-api-xyz",
            "tool_args": {},
        },
        {
            "id": "config-logs",
            "tool": "kubectl_previous_logs",
            "command": "pod trace-config-api-abc -n aiops-traced-config --tail=100",
            "tool_args": {},
        },
        {
            "id": "config-events",
            "tool": "kubectl_events",
            "command": "pod trace-config-api-abc -n aiops-traced-config",
            "tool_args": {"namespace": "aiops-traced-config"},
        },
        {
            "id": "oom-logs",
            "tool": "kubectl_previous_logs",
            "command": "pod trace-oom-api-xyz -n aiops-traced-oom --tail=100",
            "tool_args": {},
        },
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(plan)

    assert [item["id"] for item in normalized] == ["case-config", "case-oom"]


def test_prepare_evidence_plan_drops_fine_requeries_after_mandatory_injection():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {"kind": "Pod", "namespace": "ns-a", "name": "pod-a"},
            {"kind": "Pod", "namespace": "ns-b", "name": "pod-b"},
        ]
    }
    fine_only_plan = [
        {
            "id": "describe-a",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod pod-a -n ns-a",
            "tool_args": {"kind": "pod", "name": "pod-a", "namespace": "ns-a"},
        },
        {
            "id": "logs-a",
            "tool": "kubectl_previous_logs",
            "command": "kubectl logs pod-a -n ns-a --previous",
            "tool_args": {},
        },
        {
            "id": "describe-b",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod pod-b -n ns-b",
            "tool_args": {"kind": "pod", "name": "pod-b", "namespace": "ns-b"},
        },
    ]

    prepared = node._prepare_evidence_plan(fine_only_plan, handoff)

    assert [item["tool"] for item in prepared] == [
        "collect_aiops_case",
        "collect_aiops_case",
    ]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {("ns-a", "pod-a"), ("ns-b", "pod-b")}


def test_prepare_evidence_plan_keeps_all_mandatory_targets_beyond_regular_limit():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {"kind": "Pod", "namespace": "ns", "name": f"pod-{index}"}
            for index in range(12)
        ]
    }

    prepared = node._prepare_evidence_plan([], handoff)

    assert len(prepared) == 12
    assert all(item["source"] == "mandatory_live_observability" for item in prepared)


def test_qwen_target_parameter_aliases_deduplicate_coarse_plan_and_pod_requeries():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-abc",
            }
        ]
    }
    plan = [
        {
            "id": "qwen-case",
            "description": "采集目标 Pod 的多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "target_scope": "Pod",
            "command": (
                "collect_aiops_case with "
                "target_namespace='aiops-traced-oom' and "
                "target_pod='trace-oom-api-abc'"
            ),
            "tool_args": {},
        },
        {
            "id": "describe",
            "description": "Describe 同一 Pod",
            "level": "important",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod trace-oom-api-abc -n aiops-traced-oom",
        },
        {
            "id": "logs",
            "description": "查询同一 Pod 日志",
            "level": "important",
            "tool": "kubectl_logs",
            "command": "kubectl logs trace-oom-api-abc -n aiops-traced-oom",
        },
    ]

    normalized = node._normalize_evidence_plan(plan, layer_handoff=handoff)
    ensured = node._ensure_mandatory_aiops_case_plan(normalized, handoff)

    assert [item["id"] for item in normalized] == ["qwen-case"]
    assert [item["id"] for item in ensured] == ["qwen-case"]
    assert ensured[0]["source"] == "mandatory_live_observability"
    assert ensured[0]["tool_args"] == {
        "namespace": "aiops-traced-oom",
        "pod": "trace-oom-api-abc",
        "scenario": "auto",
    }


def test_mandatory_aiops_case_plan_deduplicates_same_target_across_qwen_variants():
    class _Tool:
        name = "collect_aiops_case"

    node = EvidenceCollectorNode()
    node.tools = [_Tool()]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            }
        ]
    }
    plan = [
        {
            "id": "qwen-case-1",
            "description": "采集目标 Pod 的多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "aiops-traced-config/trace-config-api-abc",
            "target_scope": "aiops-traced-config/trace-config-api-abc",
            "tool_args": {},
        },
        {
            "id": "qwen-case-duplicate",
            "description": "再次采集同一目标 Pod",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case namespace=aiops-traced-config pod=trace-config-api-abc",
            "tool_args": {
                "namespace": "aiops-traced-config",
                "pod": "trace-config-api-abc",
            },
        },
    ]

    result = node._ensure_mandatory_aiops_case_plan(plan, handoff)

    assert len(result) == 1
    assert result[0]["id"] == "qwen-case-1"
    assert result[0]["source"] == "mandatory_live_observability"
    assert result[0]["tool_args"] == {
        "namespace": "aiops-traced-config",
        "pod": "trace-config-api-abc",
        "scenario": "auto",
    }


def test_prepare_evidence_plan_deduplicates_prefixed_namespace_pod_commands():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "description": "采集配置异常 Pod case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for "
                "aiops-traced-config/trace-config-api-abc"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "description": "采集 OOM 异常 Pod case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for "
                "aiops-traced-oom/trace-oom-api-xyz"
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }


def test_prepare_evidence_plan_deduplicates_explicit_pod_namespace_name_commands():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "description": "采集配置异常 Pod case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "get pod namespace=aiops-traced-config "
                "name=trace-config-api-abc"
            ),
            "tool_args": {},
        },
        {
            "id": "qwen-oom",
            "description": "采集 OOM 异常 Pod case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "get pod namespace=aiops-traced-oom "
                "name=trace-oom-api-xyz"
            ),
            "tool_args": {},
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }


def test_prepare_evidence_plan_deduplicates_entity_alias_against_mandatory_targets():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {
                "kind": "Pod",
                "namespace": "aiops-traced-config",
                "name": "trace-config-api-abc",
            },
            {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-xyz",
            },
        ]
    }
    plan = [
        {
            "id": "qwen-config",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case namespace=aiops-traced-config pod=trace-config-api-abc",
            "tool_args": {
                "namespace": "aiops-traced-config",
                "pod": "trace-config-api-abc",
            },
        },
        {
            "id": "qwen-oom",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case namespace=aiops-traced-oom pod=trace-oom-api-xyz",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api-xyz",
            },
        },
        {
            "id": "qwen-oom-entity-alias",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case for the OOM entity",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "entity_type": "Pod",
                "entity_name": "trace-oom-api-xyz",
            },
        },
    ]

    prepared = node._prepare_evidence_plan(plan, handoff)

    assert [item["id"] for item in prepared] == ["qwen-config", "qwen-oom"]
    assert {
        EvidenceCollectorNode._extract_plan_pod_target(item)
        for item in prepared
    } == {
        ("aiops-traced-config", "trace-config-api-abc"),
        ("aiops-traced-oom", "trace-oom-api-xyz"),
    }


def test_observability_target_coverage_counts_unique_successful_case_targets():
    plan = [
        {
            "id": "case-config",
            "tool": "collect_aiops_case",
            "target_scope": "aiops-traced-config/trace-config-api-abc",
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-oom",
            "tool": "collect_aiops_case",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api-xyz",
            },
            "source": "mandatory_live_observability",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "tool_args": {
                "namespace": "aiops-traced-config",
                "pod": "trace-config-api-abc",
            },
            "structured": {
                "status": "case_collected",
                "primary_entity": {
                    "namespace": "aiops-traced-config",
                    "name": "trace-config-api-abc",
                },
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api-xyz",
            },
            "structured": {
                "status": "case_collected",
                "primary_entity": {
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api-xyz",
                },
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api-xyz",
            },
            "structured": {
                "status": "case_collected",
                "primary_entity": {
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api-xyz",
                },
            },
        },
    ]

    stats = EvidenceCollectorNode._calculate_observability_target_coverage(
        plan,
        events,
    )

    assert stats == {
        "observability_target_total": 2,
        "observability_target_collected": 2,
        "observability_target_completeness": 1.0,
    }


def test_observability_target_coverage_accepts_tool_event_target_aliases():
    plan = [
        {
            "id": "case-config",
            "tool": "collect_aiops_case",
            "tool_args": {
                "target_namespace": "aiops-traced-config",
                "target_pod": "trace-config-api-abc",
            },
            "source": "mandatory_live_observability",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "tool_args": {
                "target_namespace": "aiops-traced-config",
                "target_pod": "trace-config-api-abc",
            },
            "structured": {
                "status": "case_collected",
            },
        },
    ]

    stats = EvidenceCollectorNode._calculate_observability_target_coverage(
        evidence_plan=plan,
        thinking_events=events,
    )

    assert stats == {
        "observability_target_total": 1,
        "observability_target_collected": 1,
        "observability_target_completeness": 1.0,
    }


def test_alias_only_case_plans_match_the_correct_tool_result_target():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "case-a",
            "description": "采集 Pod A 的多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case",
            "tool_args": {
                "target_namespace": "ns-a",
                "target_pod": "pod-a",
            },
        },
        {
            "id": "case-b",
            "description": "采集 Pod B 的多维 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case",
            "tool_args": {
                "target_namespace": "ns-b",
                "target_pod": "pod-b",
            },
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "tool_args": {
                "namespace": "ns-b",
                "pod": "pod-b",
            },
            "result": "case B collected",
            "structured": {
                "status": "case_collected",
                "primary_entity": {
                    "namespace": "ns-b",
                    "name": "pod-b",
                },
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert [(item.id, item.collected) for item in items] == [
        ("case-a", False),
        ("case-b", True),
    ]


def test_observability_target_coverage_rejects_mismatched_returned_entity():
    plan = [
        {
            "id": "case-a",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns-a", "pod": "pod-a"},
            "source": "mandatory_live_observability",
        }
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "tool_args": {"namespace": "ns-a", "pod": "pod-a"},
            "structured": {
                "status": "case_collected",
                "primary_entity": {"namespace": "ns-b", "name": "pod-b"},
            },
        }
    ]

    stats = EvidenceCollectorNode._calculate_observability_target_coverage(
        plan,
        events,
    )

    assert stats == {
        "observability_target_total": 1,
        "observability_target_collected": 0,
        "observability_target_completeness": 0.0,
    }


def test_mandatory_aiops_case_plan_preserves_unique_non_handoff_target():
    class _Tool:
        name = "collect_aiops_case"

    node = EvidenceCollectorNode()
    node.tools = [_Tool()]
    handoff = {
        "abnormal_pods": [
            {"kind": "Pod", "namespace": "ns-a", "name": "pod-a"},
        ]
    }
    plan = [
        {
            "id": "case-a",
            "tool": "collect_aiops_case",
            "target_scope": "ns-a/pod-a",
        },
        {
            "id": "case-x",
            "tool": "collect_aiops_case",
            "target_scope": "ns-x/pod-x",
        },
    ]

    result = node._ensure_mandatory_aiops_case_plan(plan, handoff)

    assert [item["id"] for item in result] == ["case-a", "case-x"]
    assert result[0]["source"] == "mandatory_live_observability"
    assert result[1].get("source") != "mandatory_live_observability"


def test_handoff_pod_targets_prefer_confirmed_abnormal_pods_over_active_context():
    handoff = {
        "active_entities": [
            {"type": "Pod", "namespace": "related", "name": "healthy-context"},
        ],
        "abnormal_pods": [
            {"kind": "Pod", "namespace": "broken", "name": "failed-pod"},
        ],
    }

    assert EvidenceCollectorNode._collect_handoff_pod_targets(handoff) == [
        ("broken", "failed-pod"),
    ]


def test_evidence_plan_normalization_drops_duplicate_runtime_info_grep_variants():
    plan = [
        {
            "id": "e25",
            "description": "获取节点 Docker Labels",
            "level": "important",
            "tool": "run_bash_command",
            "command": "kubectl exec -n aaa -it node1 -- docker info | grep 'Labels'",
            "purpose": "确认节点上的 Docker 守护进程的标签信息",
        },
        {
            "id": "e26",
            "description": "获取节点 Docker Logging",
            "level": "important",
            "tool": "run_bash_command",
            "command": "kubectl exec -n aaa -it node1 -- docker info | grep 'Logging'",
            "purpose": "确认节点上的 Docker 守护进程的日志配置",
        },
        {
            "id": "e27",
            "description": "获取节点 Docker Runtimes",
            "level": "important",
            "tool": "run_bash_command",
            "command": "kubectl exec -n aaa -it node1 -- docker info | grep 'Runtimes'",
            "purpose": "确认节点上的 Docker 守护进程的运行时配置",
        },
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(plan)

    assert [item["id"] for item in normalized] == ["e25"]


def test_evidence_plan_normalization_does_not_add_missing_abnormal_group_coverage():
    layer_handoff = {
        "abnormal_groups": [
            {
                "group_id": "g1",
                "status_keywords": ["ImagePullBackOff"],
                "pod_abnormal_type": "ImagePullFailed",
                "entities": [
                    {"kind": "Pod", "namespace": "aaa", "name": "redis-master-0"},
                    {"kind": "Pod", "namespace": "xnet", "name": "redis-master-0"},
                ],
            },
            {
                "group_id": "g2",
                "status_keywords": ["Terminating"],
                "pod_abnormal_type": "TerminatingStuck",
                "entities": [
                    {"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"},
                ],
            },
        ],
        "current_abnormal_summary": {
            "status_counts": {"ImagePullBackOff": 4, "Terminating": 1},
            "total_abnormal": 5,
        },
    }
    plan = [
        {
            "id": "e1",
            "description": "验证 Terminating Pod finalizers",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
            "purpose": "确认 finalizer 是否阻塞删除",
            "evidence_type": "pod_lifecycle",
            "target_scope": "group:g2",
            "acceptable_tools": ["kubectl_get_yaml"],
        }
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(plan, layer_handoff=layer_handoff)

    assert [item["id"] for item in normalized] == ["e1"]
    assert not any(item.get("id", "").startswith("auto_") for item in normalized)
    assert not any(item.get("target_scope") == "group:g1" for item in normalized)
    assert any(item["target_scope"] == "group:g2" for item in normalized)


def test_evidence_user_prompt_injects_layer_matched_runbook_context(tmp_path, monkeypatch):
    runbook_dir = tmp_path / "runbooks"
    runbook_dir.mkdir()
    (runbook_dir / "pod-terminating-stuck.md").write_text(
        "# Pod TerminatingStuck / 删除卡住\n\n"
        "## Evidence 节点推荐计划\n"
        "1. `kubectl get pod <pod> -n <namespace> -o yaml`\n"
        "2. `kubectl describe pod <pod> -n <namespace>`\n\n"
        "## 判定规则\n"
        "| 条件 | 结论 |\n| deletionTimestamp + finalizers | finalizer 清理卡住 |\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AIOPS_RUNBOOK_DIRS", str(runbook_dir))
    layer_handoff = {
        "layer": "L1",
        "matched_runbooks": ["pod-terminating-stuck.md"],
        "pod_status_keyword": "Terminating",
        "pod_abnormal_type": "TerminatingStuck",
    }

    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L1",
        layer_handoff=json.dumps(layer_handoff, ensure_ascii=False),
    )

    assert "# Layer 已确认 Runbook 上下文" in message
    assert "pod-terminating-stuck.md" in message
    assert "Evidence 节点推荐计划" in message
    assert "kubectl get pod <pod>" in message
    assert "finalizer 清理卡住" in message


def test_evidence_plan_normalization_derives_tool_args_for_kubectl_events_command():
    plan = [
        {
            "id": "e1",
            "description": "验证 Pod 事件",
            "level": "critical",
            "tool": "kubectl_events",
            "command": "kubectl get events -n aaa --field-selector involvedObject.name=test1-redis-master-0",
            "purpose": "确认 ImagePullBackOff 事件",
        }
    ]

    normalized = EvidenceCollectorNode._normalize_evidence_plan(plan)

    assert normalized[0]["tool_args"] == {
        "resource_type": "pod",
        "resource_name": "test1-redis-master-0",
        "namespace": "aaa",
    }


def test_evidence_injects_mandatory_case_for_every_unique_abnormal_pod():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "active_entities": [
            {"type": "Pod", "namespace": "ns-a", "name": "pod-a"},
        ],
        "issue_groups": [
            {
                "entities": [
                    {"kind": "Pod", "namespace": "ns-b", "name": "pod-b"},
                    {"kind": "Pod", "namespace": "ns-a", "name": "pod-a"},
                ]
            }
        ],
        "abnormal_pods": [
            {"namespace": "ns-c", "name": "pod-c"},
        ],
    }

    result = node._ensure_mandatory_aiops_case_plan(
        [{"id": "events", "level": "critical", "tool": "kubectl_events"}],
        handoff,
    )

    coarse = [item for item in result if item["tool"] == "collect_aiops_case"]
    assert [
        (item["tool_args"]["namespace"], item["tool_args"]["pod"])
        for item in coarse
    ] == [
        ("ns-a", "pod-a"),
        ("ns-b", "pod-b"),
        ("ns-c", "pod-c"),
    ]
    assert all(item["level"] == "critical" for item in coarse)
    assert all(item["tool_args"]["scenario"] == "auto" for item in coarse)


def test_evidence_does_not_inject_case_when_tool_is_unavailable():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="kubectl_describe")]

    result = node._ensure_mandatory_aiops_case_plan(
        [],
        {"abnormal_pods": [{"namespace": "ns", "name": "pod"}]},
    )

    assert result == []


def test_evidence_keeps_all_mandatory_cases_beyond_regular_plan_limit():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {"namespace": "ns", "name": f"pod-{index}"}
            for index in range(12)
        ]
    }

    result = node._ensure_mandatory_aiops_case_plan([], handoff)

    assert len(result) == 12
    assert all(item["source"] == "mandatory_live_observability" for item in result)


def test_evidence_existing_plan_prompt_includes_pydantic_tool_args():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L3",
        layer_handoff="{}",
        existing_plan=[
            {
                "id": "e1",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa --field-selector involvedObject.name=test1-redis-master-0",
                "purpose": "确认事件",
                "tool_args": {
                    "resource_type": "pod",
                    "resource_name": "test1-redis-master-0",
                    "namespace": "aaa",
                },
            }
        ],
        failure_reason="沿用计划执行",
    )

    assert "tool_args=" in message
    assert '"resource_type": "pod"' in message
    assert "应优先复用其中的 namespace/name/kind 等目标参数" in message
    assert "选择更符合诊断意图的真实工具" in message
    assert "kubectl_get_yaml" in message


def test_plan_completeness_uses_countable_planned_items_not_extra_layer_inventory():
    node = EvidenceCollectorNode()
    planned_items = [
        EvidenceItem(
            id="e1",
            description="验证 ImagePull 事件",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            value="Failed to pull image",
            source="thinking_match",
        ),
        EvidenceItem(
            id="e2",
            description="验证 Terminating finalizer",
            level=EvidenceLevel.IMPORTANT,
            collected=False,
            value=None,
            source="planned",
        ),
    ]
    upstream_items = [
        EvidenceItem(
            id="e2",
            description="Layer 工具碰巧与未采集计划同 ID",
            level=EvidenceLevel.IMPORTANT,
            collected=True,
            value="layer result",
            source="layer_verified",
        ),
        EvidenceItem(
            id="layer_1",
            description="上游已验证工具结果: kubectl_get_by_kind_in_cluster",
            level=EvidenceLevel.IMPORTANT,
            collected=True,
            value="status_counts={'ImagePullBackOff': 4, 'Terminating': 1}",
            source="layer_verified",
        ),
        EvidenceItem(
            id="layer_2",
            description="上游已验证工具结果: kubectl_events",
            level=EvidenceLevel.IMPORTANT,
            collected=True,
            value="Failed to pull image",
            source="layer_verified",
        ),
    ]

    stats = node._calculate_plan_completeness(planned_items, upstream_items)

    assert stats == {"plan_total": 2, "plan_collected": 1, "plan_completeness": 0.5}


def test_sufficient_mandatory_cases_skip_only_uncollected_noncritical_supplements():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "case-a",
            "level": "critical",
            "tool": "collect_aiops_case",
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-b",
            "level": "critical",
            "tool": "collect_aiops_case",
            "source": "mandatory_live_observability",
        },
        {
            "id": "supplement",
            "level": "important",
            "tool": "kubectl_get_by_name",
        },
        {
            "id": "critical-followup",
            "level": "critical",
            "tool": "kubectl_get_yaml",
        },
    ]
    items = [
        EvidenceItem(
            id="case-a",
            description="采集 Pod A case",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            source="thinking_match",
        ),
        EvidenceItem(
            id="case-b",
            description="采集 Pod B case",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            source="thinking_match",
        ),
        EvidenceItem(
            id="supplement",
            description="检查补充配置",
            level=EvidenceLevel.IMPORTANT,
            collected=False,
            source="planned",
        ),
        EvidenceItem(
            id="critical-followup",
            description="必须验证工作负载配置",
            level=EvidenceLevel.CRITICAL,
            collected=False,
            source="planned",
        ),
    ]

    skipped = node._classify_sufficient_evidence_skips(
        evidence_plan=plan,
        evidence_items=items,
        early_stop={
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
    )

    assert skipped == ["supplement"]
    assert items[2].source == "skipped_sufficient_evidence"
    assert items[2].outcome == "skipped"
    assert items[3].source == "planned"
    assert node._calculate_plan_completeness(items, []) == {
        "plan_total": 3,
        "plan_collected": 2,
        "plan_completeness": 2 / 3,
    }


def test_sufficient_mandatory_cases_never_skip_conditional_critical_fallback():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "case-a",
            "level": "critical",
            "tool": "collect_aiops_case",
            "source": "mandatory_live_observability",
        },
        {
            "id": "conditional-fallback",
            "description": "If case-a is error/absent, use kubectl_describe",
            "level": "critical",
            "tool": "kubectl_describe",
        },
        {
            "id": "critical-followup",
            "description": "必须验证工作负载配置",
            "level": "critical",
            "tool": "kubectl_get_yaml",
        },
    ]
    items = [
        EvidenceItem(
            id="case-a",
            description="采集 Pod A case",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            source="thinking_match",
        ),
        EvidenceItem(
            id="conditional-fallback",
            description="If case-a is error/absent, use kubectl_describe",
            level=EvidenceLevel.CRITICAL,
            collected=False,
            source="planned",
        ),
        EvidenceItem(
            id="critical-followup",
            description="必须验证工作负载配置",
            level=EvidenceLevel.CRITICAL,
            collected=False,
            source="planned",
        ),
    ]

    skipped = node._classify_sufficient_evidence_skips(
        evidence_plan=plan,
        evidence_items=items,
        early_stop={
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
    )

    assert skipped == []
    assert items[1].source == "planned"
    assert items[1].outcome != "skipped"
    assert items[2].source == "planned"
    assert items[2].outcome != "skipped"
    assert node._calculate_plan_completeness(items, []) == {
        "plan_total": 3,
        "plan_collected": 1,
        "plan_completeness": 1 / 3,
    }


def test_sufficient_evidence_skip_never_hides_duplicate_id_critical_item():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "dup",
            "level": "critical",
            "tool": "kubectl_get_yaml",
        },
        {
            "id": "dup",
            "level": "important",
            "tool": "kubectl_get_by_name",
        },
    ]
    items = [
        EvidenceItem(
            id="dup",
            description="必须验证工作负载配置",
            level=EvidenceLevel.CRITICAL,
            collected=False,
            source="planned",
        ),
        EvidenceItem(
            id="dup",
            description="可选补充状态",
            level=EvidenceLevel.IMPORTANT,
            collected=False,
            source="planned",
        ),
    ]

    skipped = node._classify_sufficient_evidence_skips(
        evidence_plan=plan,
        evidence_items=items,
        early_stop={
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
    )

    assert skipped == []
    assert items[0].source == "planned"
    assert items[0].outcome != "skipped"
    assert items[1].source == "planned"
    assert items[1].outcome != "skipped"
    assert node._calculate_plan_completeness(items, []) == {
        "plan_total": 2,
        "plan_collected": 0,
        "plan_completeness": 0.0,
    }


def test_plan_index_preserves_critical_metadata_for_duplicate_id():
    indexed = EvidenceCollectorNode._index_evidence_plan_by_id([
        {
            "id": "dup",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod pod-a -n ns-a -o yaml",
        },
        {
            "id": "dup",
            "level": "important",
            "tool": "kubectl_get_by_name",
            "command": "kubectl get pod pod-a -n ns-a",
        },
    ])

    assert indexed["dup"]["level"] == "critical"
    assert indexed["dup"]["tool"] == "kubectl_get_yaml"
    assert indexed["dup"]["command"].endswith("-o yaml")


def test_sufficient_mandatory_cases_make_skipped_supplements_non_missing():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "case-a",
            "level": "critical",
            "tool": "collect_aiops_case",
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-b",
            "level": "critical",
            "tool": "collect_aiops_case",
            "source": "mandatory_live_observability",
        },
        {
            "id": "supplement",
            "level": "important",
            "tool": "kubectl_get_by_name",
        },
    ]
    items = [
        EvidenceItem(
            id="case-a",
            description="采集 Pod A case",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            source="thinking_match",
        ),
        EvidenceItem(
            id="case-b",
            description="采集 Pod B case",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            source="thinking_match",
        ),
        EvidenceItem(
            id="supplement",
            description="检查补充配置",
            level=EvidenceLevel.IMPORTANT,
            collected=False,
            source="planned",
        ),
    ]

    skipped = node._classify_sufficient_evidence_skips(
        evidence_plan=plan,
        evidence_items=items,
        early_stop={
            "triggered": True,
            "reason": "mandatory_live_observability_complete",
        },
    )

    assert skipped == ["supplement"]
    assert node._calculate_plan_completeness(items, []) == {
        "plan_total": 2,
        "plan_collected": 2,
        "plan_completeness": 1.0,
    }
    assert node._calculate_completeness(items) == 1.0


def test_evidence_tool_stats_exclude_upstream_layer_matches():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod pod-a -n ns-a",
        }
    ]
    upstream = [
        EvidenceItem(
            id="e1",
            description="Layer 已执行同类工具",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            value="layer result",
            source="layer_verified",
        )
    ]

    stats = node._calculate_evidence_tool_stats(
        evidence_plan=plan,
        thinking_events=[],
        evidence_items=[],
        upstream_evidence_items=upstream,
    )

    assert stats == {
        "executed_tool_count": 0,
        "matched_tool_count": 0,
        "unplanned_tool_count": 0,
        "case_tool_count": 0,
        "supplemental_tool_count": 0,
    }


def test_evidence_tool_stats_separate_case_and_supplemental_calls():
    node = EvidenceCollectorNode()
    plan = [
        {"id": "case-a", "tool": "collect_aiops_case"},
        {"id": "case-b", "tool": "collect_aiops_case"},
        {"id": "describe", "tool": "kubectl_describe"},
    ]
    items = [
        EvidenceItem(
            id=item["id"],
            description=item["id"],
            level=EvidenceLevel.CRITICAL,
            collected=True,
            source="thinking_match",
        )
        for item in plan
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
        },
    ]

    stats = node._calculate_evidence_tool_stats(
        evidence_plan=plan,
        thinking_events=events,
        evidence_items=items,
        upstream_evidence_items=[],
    )

    assert stats == {
        "executed_tool_count": 3,
        "matched_tool_count": 3,
        "unplanned_tool_count": 0,
        "case_tool_count": 2,
        "supplemental_tool_count": 1,
    }


def test_evidence_does_not_count_failed_or_wrong_intent_tool_results():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "检查 registry ConfigMap",
            "level": "important",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get configmap registry-config -n kube-system -o yaml",
        },
        {
            "id": "e2",
            "description": "检查 Pod 日志",
            "level": "important",
            "tool": "kubectl_get_yaml",
            "command": "kubectl logs ham-wcc79 -n xnet",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_yaml",
            "semantic_success": False,
            "result": "Command failed (exit 1): configmaps registry-config not found",
            "structured": {"status": "command_failed"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_yaml",
            "semantic_success": True,
            "result": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: ham-wcc79",
            "structured": {"status": "yaml_summarized", "kind": "Pod", "name": "ham-wcc79"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 2
    assert items[0].collected is True
    assert items[0].source == "thinking_negative_match"
    assert items[1].collected is False
    assert node._calculate_completeness(items) == 0.5


def test_evidence_counts_logs_collected_by_run_bash_command():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "检查 Pod 日志",
            "level": "important",
            "tool": "run_bash_command",
            "command": "kubectl logs ham-wcc79 -n xnet --previous --tail=200",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": True,
            "result": "run_bash_command 输出摘要:\nsuccess: True\nstdout: application started",
            "structured": {
                "status": "command_result",
                "success": True,
                "stdout_preview": "application started",
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is True
    assert items[0].source == "thinking_match"
    assert node._calculate_completeness(items) == 1


def test_evidence_counts_collect_aiops_case_as_planned_evidence():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "case",
            "description": "采集异常 Pod 的 metrics/logs/traces/topology case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": "collect_aiops_case namespace=aiops-temp pod=aiops-oom-business",
            "tool_args": {"namespace": "aiops-temp", "pod": "aiops-oom-business"},
            "purpose": "实时采集多模态可观测证据",
            "acceptable_tools": ["collect_aiops_case"],
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "collect_aiops_case 摘要: case_id=oom-aiops-temp-aiops-oom-business\ncoverage=metrics=observed logging=observed tracing=weak_context topology=observed",
            "structured": {
                "status": "case_collected",
                "case_id": "oom-aiops-temp-aiops-oom-business",
                "coverage": {
                    "metrics": "observed",
                    "logging": "observed",
                    "tracing": "weak_context",
                    "topology": "observed",
                },
                "primary_entity": {
                    "namespace": "aiops-temp",
                    "name": "aiops-oom-business",
                },
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is True
    assert items[0].source == "thinking_match"
    assert node._calculate_completeness(items) == 1


def test_evidence_partial_adjudication_falls_back_to_rule_match_for_aiops_case():
    def adjudicate(_plan, _candidates):
        return {
            "matches": [
                {
                    "plan_id": "pod-yaml",
                    "tool_result_index": 1,
                    "matched": True,
                    "confidence": 0.9,
                }
            ]
        }

    node = EvidenceCollectorNode(plan_match_adjudicator=adjudicate)
    plan = [
        {
            "id": "case",
            "description": "采集异常 Pod 的 metrics/logs/traces/topology case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": (
                "collect_aiops_case for pod trace-oom-api in namespace "
                "aiops-traced-oom with scenario=auto"
            ),
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api",
                "scenario": "auto",
            },
            "purpose": "实时采集多模态可观测证据",
            "evidence_type": "multi_dimension",
        },
        {
            "id": "pod-yaml",
            "description": "获取 Pod YAML",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod trace-oom-api -n aiops-traced-oom -o yaml",
            "purpose": "确认资源限制",
            "evidence_type": "pod_spec",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "pod": "trace-oom-api",
                "scenario": "auto",
            },
            "result": (
                "Pod trace-oom-api 因 OOMKilled 终止。"
                "Metrics max=69Mi limit=80Mi; tracing present; topology present"
            ),
            "structured": {
                "status": "case_collected",
                "case_id": "auto-aiops-traced-oom-trace-oom-api",
                "coverage": {
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "topology": "present",
                },
                "primary_entity": {
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api",
                },
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_yaml",
            "semantic_success": True,
            "tool_args": {
                "kind": "Pod",
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api",
            },
            "result": (
                "kind: Pod\nmetadata:\n  name: trace-oom-api\n"
                "  namespace: aiops-traced-oom\nspec:\n  containers: []"
            ),
            "structured": {
                "status": "yaml_summarized",
                "kind": "Pod",
                "name": "trace-oom-api",
                "namespace": "aiops-traced-oom",
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert [item.collected for item in items] == [True, True]
    assert [item.source for item in items] == ["thinking_match", "thinking_match"]


def test_evidence_tool_data_preserves_bounded_aiops_agent_context():
    node = EvidenceCollectorNode()
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "compact summary",
            "structured": {
                "status": "case_collected",
                "case_id": "case-1",
                "primary_entity": {
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api",
                },
                "coverage": {
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "topology": "present",
                },
                "topology_summary": {
                    "entity_count": 11,
                    "edge_count": 10,
                },
                "dimension_details": {
                    "metrics": {
                        "highlights": [
                            {"start": "3.8Mi", "max": "69.0Mi", "limit": "80.0Mi"}
                        ]
                    },
                    "logs": {
                        "samples": [
                            {
                                "message": (
                                    "trace_id=42ea12f3f50fe8b2e759a221ff0f3f4a "
                                    "allocated_mib=62"
                                )
                            }
                        ]
                    },
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
                                "source": "trace-oom-driver",
                                "target": "trace-oom-api",
                                "directness": "direct",
                                "confidence": "high",
                            },
                            {
                                "relationship": "Service --selects--> Pod",
                                "source": "trace-oom-api",
                                "target": "trace-oom-api-pod",
                                "directness": "direct",
                                "confidence": "high",
                            },
                        ]
                    },
                },
                "root_cause": "evaluator-only-answer",
                "expected_remediation": "evaluator-only-remediation",
            },
        }
    ]

    tool_data = node._extract_tool_data_from_thinking(events)

    assert len(tool_data) == 1
    agent_context = tool_data[0]["agent_context"]
    assert "42ea12f3f50fe8b2e759a221ff0f3f4a" in agent_context
    assert "aiops.allocated_mib.before" in agent_context
    assert "Pod --calls--> Pod" in agent_context
    assert "Service --selects--> Pod" in agent_context
    assert "evaluator-only-answer" not in agent_context
    assert "evaluator-only-remediation" not in agent_context
    assert len(agent_context) < 12000


def test_evidence_legacy_context_raises_when_mandatory_identity_exceeds_budget():
    oversized_case_id = "case-" + ("x" * 12000)

    with pytest.raises(ValueError, match="mandatory.*identity|identity.*budget"):
        EvidenceCollectorNode._build_aiops_agent_context(
            tool_name="collect_aiops_case",
            structured={
                "case_id": oversized_case_id,
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-a",
                },
                "dimension_details": {
                    "custom": {"optional": "value"},
                },
            },
        )


def test_evidence_tool_data_attaches_bounded_valid_fact_ledger_json():
    node = EvidenceCollectorNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    records = [
        _canonical_fact_record(
            entity_id=entity_id,
            value={"message": f"line-{index}-" + ("x" * 300)},
            evidence_refs=[f"logs:{index}"],
        )
        for index in range(48)
    ]
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "case-facts",
        "scope_entity_ids": [entity_id],
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "compact summary",
            "structured": {
                "status": "case_collected",
                "case_id": "case-facts",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-a",
                },
                "fact_ledger": ledger,
            },
        }
    ]

    tool_data = node._extract_tool_data_from_thinking(events)

    assert len(tool_data) == 1
    assert tool_data[0]["fact_ledger"]["case_id"] == "case-facts"
    agent_context = tool_data[0]["agent_context"]
    parsed = json.loads(agent_context)
    assert parsed["fact_ledgers"][0]["case_id"] == "case-facts"
    assert len(agent_context) <= 12000


def test_evidence_excludes_deduplicated_case_replay_from_data_and_counts():
    node = EvidenceCollectorNode()
    entity_id = "k8s.pod:demo/api:uid-a"
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "case-facts",
        "scope_entity_ids": [entity_id],
        "records": [],
        "record_count": 0,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    original = {
        "type": "tool_result",
        "status": "success",
        "tool_name": "collect_aiops_case",
        "semantic_success": True,
        "result": "compact summary",
        "structured": {
            "status": "case_collected",
            "case_id": "case-facts",
            "primary_entity": {
                "namespace": "demo",
                "name": "api",
            },
            "fact_ledger": ledger,
        },
    }
    replay = {
        **original,
        "deduplicated": True,
        "original_tool_call_id": "tool-call-1",
    }

    tool_data = node._extract_tool_data_from_thinking([original, replay])
    stats = node._calculate_evidence_tool_stats(
        evidence_plan=[],
        thinking_events=[original, replay],
        evidence_items=[],
        upstream_evidence_items=[],
    )

    assert len(tool_data) == 1
    assert stats["executed_tool_count"] == 1
    assert stats["case_tool_count"] == 1


def test_evidence_tool_data_builds_deterministic_aiops_agent_facts():
    node = EvidenceCollectorNode()
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "compact summary",
            "structured": {
                "status": "case_collected",
                "case_id": "case-1",
                "abnormal_type": "oomkilled",
                "primary_entity": {
                    "kind": "Pod",
                    "namespace": "aiops-traced-oom",
                    "name": "trace-oom-api-abc",
                    "node": "node2",
                    "pod_ip": "172.16.104.13",
                },
                "coverage": {
                    "k8s": "present",
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "trace": "present",
                    "topology": "present",
                },
                "signals_summary": [
                    {
                        "signal_id": "sig-k8s-present",
                        "dimension": "k8s",
                        "strength": "strong",
                        "observed": "Last terminated state: business-api=OOMKilled exit=137",
                        "evidence_refs": [
                            "k8s.trace-oom-api.pod-yaml",
                            "k8s.trace-oom-api.last-terminated",
                            "k8s.trace-oom-api.events",
                        ],
                    }
                ],
                "dimension_details": {
                    "metrics": {
                        "highlights": [
                            {
                                "metric": "container_memory_working_set_bytes",
                                "pod": "trace-oom-api-abc",
                                "container": "business-api",
                                "start": "3.8Mi",
                                "max": "69.0Mi",
                                "last": "69.0Mi",
                                "limit": "80.0Mi",
                                "max_limit_ratio": 0.862,
                                "samples": ["04:31:23=41.0Mi", "04:31:53=69.0Mi"],
                            }
                        ]
                    },
                    "logs": {
                        "samples": [
                            {
                                "message": json.dumps({
                                    "event": "allocate",
                                    "trace_id": "369c929229004108c4066c41656d49e8",
                                    "span_id": "8b728fc9972e7af8",
                                    "path": "/allocate?mib=2&step=855",
                                    "alloc_mib": 2,
                                    "allocated_mib": 62,
                                    "service": "aiops-traced-oom-api",
                                }),
                                "role": "target",
                            }
                        ]
                    },
                    "tracing": {
                        "flows": [
                            {
                                "timestamp": "2026-07-13 12:44:22",
                                "src": "172.16.104.8",
                                "dst": "172.16.104.13",
                                "protocol": "HTTP",
                                "request": "GET /allocate?mib=2&step=856",
                                "duration_us": "0",
                                "trace_id": "4faac0ec561b6b6febe9e0d73dc68a86",
                                "span_id": "af346995afda6e0f",
                            }
                        ],
                        "spans": [
                            {
                                "trace_id": "369c929229004108c4066c41656d49e8",
                                "service": "aiops-traced-oom-api",
                                "name": "GET /allocate",
                                "attributes": {
                                    "aiops.allocated_mib.before": 60,
                                    "aiops.allocated_mib.after": 62,
                                    "aiops.alloc_mib": 2,
                                    "url.path": "/allocate?mib=2&step=855",
                                },
                            }
                        ],
                    },
                    "topology": {
                        "edges": [
                            {
                                "relationship": "Pod --calls--> Pod",
                                "source": "trace-oom-driver-xyz",
                                "target": "trace-oom-api-abc",
                                "source_system": "deepflow+kubernetes",
                                "directness": "direct",
                                "confidence": "high",
                            },
                            {
                                "relationship": "Service --selects--> Pod",
                                "source": "trace-oom-api",
                                "target": "trace-oom-api-abc",
                                "source_system": "kubernetes",
                                "directness": "direct",
                                "confidence": "high",
                            },
                            {
                                "relationship": "Pod --owned_by--> ReplicaSet",
                                "source": "trace-oom-api-abc",
                                "target": "trace-oom-api-rs",
                                "source_system": "kubernetes",
                                "directness": "direct",
                                "confidence": "high",
                            },
                            {
                                "relationship": "ReplicaSet --owned_by--> Deployment",
                                "source": "trace-oom-api-rs",
                                "target": "trace-oom-api",
                                "source_system": "kubernetes",
                                "directness": "direct",
                                "confidence": "high",
                            },
                        ]
                    },
                },
                "root_cause": "must-not-leak",
            },
        }
    ]

    tool_data = node._extract_tool_data_from_thinking(events)

    facts = tool_data[0]["agent_facts"]
    assert (
        'K8S_SIGNAL signal_id=sig-k8s-present strength=strong '
        'observed="Last terminated state: business-api=OOMKilled exit=137"'
    ) in facts
    assert (
        'evidence_refs=["k8s.trace-oom-api.pod-yaml",'
        '"k8s.trace-oom-api.last-terminated","k8s.trace-oom-api.events"]'
    ) in facts
    assert "METRIC metric=container_memory_working_set_bytes" in facts
    assert "start=3.8Mi max=69.0Mi last=69.0Mi limit=80.0Mi" in facts
    assert "LOG role=target event=allocate" in facts
    assert "trace_id=369c929229004108c4066c41656d49e8" in facts
    assert "allocated_mib=62" in facts
    assert "DEEPFLOW src=172.16.104.8 dst=172.16.104.13" in facts
    assert "duration_us=0" in facts
    assert "trace_id=4faac0ec561b6b6febe9e0d73dc68a86" in facts
    assert "TEMPO trace_id=369c929229004108c4066c41656d49e8" in facts
    assert "aiops.allocated_mib.before=60" in facts
    assert "TOPOLOGY relationship=\"Pod --calls--> Pod\"" in facts
    assert "TOPOLOGY relationship=\"Service --selects--> Pod\"" in facts
    assert "TOPOLOGY relationship=\"Pod --owned_by--> ReplicaSet\"" in facts
    assert "TOPOLOGY relationship=\"ReplicaSet --owned_by--> Deployment\"" in facts
    assert facts.count("directness=direct confidence=high") == 4
    assert (
        'TRACE_CORRELATION log_tempo_trace_ids=["369c929229004108c4066c41656d49e8"] '
        'deepflow_trace_ids=["4faac0ec561b6b6febe9e0d73dc68a86"] '
        "do_not_merge=true"
    ) in facts
    assert "DEEPFLOW_SEMANTICS duration_us=0 is_not_failure_evidence=true" in facts
    assert "MEMORY_PATTERN" not in facts
    assert (
        "DIMENSION_DETAILS complete=true "
        "action=post_case_reconciliation"
    ) in facts
    assert "do_not_guess_evidence_refs=true" in facts
    assert "must-not-leak" not in facts
    assert "duration_us=xxx" not in facts


def test_evidence_tool_data_preserves_generic_application_error_facts():
    node = EvidenceCollectorNode()
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "collect_aiops_case",
            "semantic_success": True,
            "result": "compact summary",
            "structured": {
                "status": "case_collected",
                "case_id": "config-crashloop",
                "abnormal_type": "crashloopbackoff",
                "coverage": {
                    "k8s": "present",
                    "metrics": "present",
                    "logs": "present",
                    "tracing": "present",
                    "trace": "present",
                    "topology": "present",
                },
                "dimension_details": {
                    "metrics": {"highlights": []},
                    "logs": {
                        "samples": [
                            {
                                "message": json.dumps({
                                    "event": "config_missing",
                                    "level": "error",
                                    "message": "required config is missing",
                                    "error_code": "CONFIG_MISSING",
                                    "missing_config": "PAYMENT_GATEWAY_TOKEN",
                                    "http_status": 500,
                                    "trace_id": "trace-config-1",
                                    "path": "/checkout",
                                    "exit_code": 78,
                                }),
                                "role": "target",
                                "evidence_ref": "log-config",
                            }
                        ]
                    },
                    "tracing": {
                        "flows": [],
                        "spans": [
                            {
                                "trace_id": "trace-config-1",
                                "service": "config-api",
                                "name": "GET /checkout",
                                "attributes": {
                                    "http.response.status_code": 500,
                                    "error.type": "CONFIG_MISSING",
                                    "config.key": "PAYMENT_GATEWAY_TOKEN",
                                    "config.present": False,
                                },
                                "evidence_ref": "tempo-config",
                            }
                        ],
                    },
                    "topology": {"edges": []},
                },
            },
        }
    ]

    tool_data = node._extract_tool_data_from_thinking(events)

    facts = tool_data[0]["agent_facts"]
    assert "LOG role=target event=config_missing" in facts
    assert "error_code=CONFIG_MISSING" in facts
    assert "missing_config=PAYMENT_GATEWAY_TOKEN" in facts
    assert "http_status=500" in facts
    assert "exit_code=78" in facts
    assert "TEMPO trace_id=trace-config-1" in facts
    assert "http.response.status_code=500" in facts
    assert "error.type=CONFIG_MISSING" in facts
    assert "config.key=PAYMENT_GATEWAY_TOKEN" in facts
    assert "config.present=false" in facts
    assert "MEMORY_PATTERN" not in facts


def test_aiops_trace_contract_marks_fully_mismatched_sources_non_mergeable():
    contract = EvidenceCollectorNode._build_aiops_trace_contract({
        "logs": {
            "samples": [
                {
                    "message": json.dumps({
                        "trace_id": "log-trace",
                        "path": "/allocate?step=2",
                    })
                }
            ]
        },
        "tracing": {
            "flows": [
                {
                    "trace_id": "network-trace",
                    "request": "GET /allocate?step=1",
                }
            ],
            "spans": [
                {
                    "trace_id": "network-trace",
                    "name": "GET /allocate",
                }
            ],
        },
    })

    assert contract["log_trace_ids"] == ["log-trace"]
    assert contract["tempo_trace_ids"] == ["network-trace"]
    assert contract["deepflow_trace_ids"] == ["network-trace"]
    assert contract["shared_trace_ids"] == []
    assert contract["do_not_merge"] is True


def test_evidence_matches_real_pod_describe_events_and_previous_logs_tools():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "describe",
            "description": "确认 Last State 和 Exit Code",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod trace-oom-api-abc -n aiops-traced-oom",
        },
        {
            "id": "events",
            "description": "获取 Pod Events",
            "level": "important",
            "tool": "kubectl_events",
            "command": (
                "kubectl get events -n aiops-traced-oom "
                "--field-selector involvedObject.name=trace-oom-api-abc"
            ),
        },
        {
            "id": "logs",
            "description": "获取上一次崩溃日志",
            "level": "important",
            "tool": "kubectl_logs",
            "command": "kubectl logs trace-oom-api-abc -n aiops-traced-oom --previous",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "tool_args": {
                "kind": "pod",
                "name": "trace-oom-api-abc",
                "namespace": "aiops-traced-oom",
            },
            "result": (
                "name: trace-oom-api-abc\nnamespace: aiops-traced-oom\n"
                "Last State: Terminated\nReason: OOMKilled\nExit Code: 137"
            ),
            "structured": {
                "name": "trace-oom-api-abc",
                "namespace": "aiops-traced-oom",
                "status": "Running",
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "semantic_success": True,
            "tool_args": {
                "resource_type": "pod",
                "resource_name": "trace-oom-api-abc",
                "namespace": "aiops-traced-oom",
            },
            "result": (
                "Warning BackOff Pod/trace-oom-api-abc "
                "Back-off restarting failed container business-api"
            ),
            "structured": {
                "status": "events_found",
                "warning_count": 1,
            },
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_previous_logs",
            "semantic_success": True,
            "tool_args": {
                "namespace": "aiops-traced-oom",
                "name": "trace-oom-api-abc",
            },
            "result": (
                '{"event":"allocate","trace_id":"369c929229004108c4066c41656d49e8",'
                '"path":"/allocate?mib=2&step=855","allocated_mib":62}'
            ),
            "structured": {
                "status": "logs_summarized",
                "line_count": 31,
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert {item.id: item.collected for item in items} == {
        "describe": True,
        "events": True,
        "logs": True,
    }
    assert all(item.source == "thinking_match" for item in items)


def test_post_case_refinement_uses_real_refs_and_only_aiops_detail_tools():
    node = EvidenceCollectorNode()
    node.tools = [
        SimpleNamespace(name="collect_aiops_case"),
        SimpleNamespace(name="get_aiops_case_evidence"),
        SimpleNamespace(name="query_aiops_metrics"),
        SimpleNamespace(name="query_aiops_logs"),
        SimpleNamespace(name="kubectl_describe"),
        SimpleNamespace(name="fetch_runbook"),
    ]
    case_event = {
        "type": "tool_result",
        "status": "success",
        "tool_name": "collect_aiops_case",
        "tool_args": {"namespace": "demo", "pod": "api-abc"},
        "context_usage_ratio": 0.42,
        "structured": {
            "status": "case_collected",
            "case_id": "case-demo-api",
            "primary_entity": {
                "namespace": "demo",
                "name": "api-abc",
            },
            "coverage": {
                "k8s": "present",
                "metrics": "present",
                "logs": "present",
                "tracing": "present",
                "topology": "present",
            },
            "signals_summary": [
                {
                    "dimension": "k8s",
                    "strength": "strong",
                    "observed": "container exited with code 78",
                }
            ],
            "dimension_details": {
                "metrics": {
                    "coverage": "present",
                    "highlights": [{"metric": "container_cpu_usage_seconds_total"}],
                },
                "logs": {
                    "coverage": "present",
                    "samples": [{"message": "application stopped"}],
                },
                "tracing": {
                    "coverage": "present",
                    "flows": [],
                    "spans": [{"trace_id": "trace-1", "name": "GET /checkout"}],
                },
                "topology": {
                    "coverage": "present",
                    "edges": [
                        {
                            "relationship": "Pod --owned_by--> ReplicaSet",
                            "source": "api-abc",
                            "target": "api-rs",
                        }
                    ],
                },
            },
            "recommended_refs_by_dimension": {
                "logs": ["logs.target.previous"],
                "tracing": ["traces.tempo"],
            },
        },
        "result": "case collected",
    }
    captured = {}

    def _fake_call_llm(question, system_prompt, **kwargs):
        captured.update({
            "question": question,
            "system_prompt": system_prompt,
            **kwargs,
        })
        return SimpleNamespace(result="展开最相关日志证据"), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "get_aiops_case_evidence",
                "tool_args": {
                    "case_id": "case-demo-api",
                    "evidence_ref": "logs.target.previous",
                },
                "result": "required config PAYMENT_GATEWAY_TOKEN is missing",
            }
        ]

    node._call_llm = _fake_call_llm

    response, events = node._run_post_case_evidence_refinement(
        question="我的集群有什么问题？",
        thinking_events=[case_event],
        tool_result_sequence_start=1,
    )

    assert response.result == "展开最相关日志证据"
    assert events[0]["tool_name"] == "get_aiops_case_evidence"
    assert "action=post_case_evidence_refinement" in captured["question"]
    assert "case-demo-api" in captured["question"]
    assert "logs.target.previous" in captured["question"]
    assert "diagnostic_sufficiency" in captured["question"]
    assert "get_aiops_case_evidence" not in captured["blocked_tool_names"]
    assert "query_aiops_metrics" not in captured["blocked_tool_names"]
    assert "query_aiops_logs" not in captured["blocked_tool_names"]
    assert captured["blocked_tool_names"] >= {
        "collect_aiops_case",
        "kubectl_describe",
        "fetch_runbook",
    }


def test_post_case_refinement_stops_at_context_budget_threshold():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="get_aiops_case_evidence")]
    node._call_llm = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("context pressure must prevent another model/tool round")
    )

    response, events = node._run_post_case_evidence_refinement(
        question="我的集群有什么问题？",
        thinking_events=[
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "collect_aiops_case",
                "context_usage_ratio": 0.81,
                "structured": {
                    "status": "case_collected",
                    "case_id": "case-pressure",
                    "primary_entity": {"namespace": "demo", "name": "api"},
                    "recommended_refs_by_dimension": {
                        "logs": ["logs.target.previous"],
                    },
                },
            }
        ],
        tool_result_sequence_start=1,
    )

    assert response is None
    assert events == []
    assert node._early_stop_state["reason"] == "context_budget_stop"
    assert node._early_stop_state["detail_retrieval"]["skipped"] is True


def test_evidence_output_separates_source_coverage_from_diagnostic_sufficiency():
    output = EvidenceCollectorNode._build_evidence_collection_output(
        evidence_plan=[],
        tool_results=[],
        tool_data=[],
        llm_result_text="",
        plan_total=0,
        plan_collected=0,
        plan_completeness=0.0,
        environment_total=0,
        environment_collected=0,
        environment_completeness=0.0,
        evidence_inventory=[],
        missing_reasons=[],
        early_stop={},
        observability_target_total=1,
        observability_target_collected=1,
        observability_target_completeness=1.0,
        dimension_coverage_total=5,
        dimension_coverage_collected=5,
        dimension_coverage=1.0,
        diagnostic_sufficiency=0.5,
        diagnostic_sufficiency_label="部分充分",
        source_coverage={
            "cases": [
                {
                    "target": "demo/api",
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
        detail_retrieval={
            "evaluated": True,
            "requested": 1,
            "collected": 1,
            "refs": ["logs.target.previous"],
        },
        unresolved_questions=[
            "demo/api: 指标只有单点样本，无法确认异常时间窗趋势",
        ],
    )

    data = output.model_dump()
    assert data["source_coverage"]["cases"][0]["target"] == "demo/api"
    assert data["case_target_coverage"]["rate"] == 1.0
    assert data["detail_retrieval"]["refs"] == ["logs.target.previous"]
    assert data["diagnostic_sufficiency_summary"] == {
        "score": 0.5,
        "label": "部分充分",
    }
    assert data["unresolved_questions"]
    assert data["dimension_coverage"] == 1.0
    assert data["diagnostic_sufficiency"] == 0.5


def test_evidence_counts_diagnostic_negative_connectivity_result():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取 Pod 所在节点的网络连通性信息，检查是否可以访问 docker.io",
            "level": "important",
            "tool": "run_bash_command",
            "command": "curl -v https://registry-1.docker.io/v2/",
            "purpose": "验证节点到 docker.io 镜像仓库的网络连通性",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": (
                '{"success": false, "stdout": "", '
                '"stderr": "curl: (56) Recv failure: Connection reset by peer", '
                '"returncode": 56}'
            ),
            "structured": {
                "status": "command_result",
                "success": False,
                "returncode": 56,
                "stderr_preview": "curl: (56) Recv failure: Connection reset by peer",
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is True
    assert items[0].source == "thinking_negative_match"
    assert items[0].outcome == "negative"
    assert "Connection reset by peer" in items[0].value
    assert node._calculate_completeness(items) == 1


def test_evidence_merges_layer_verified_tools_into_inventory():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取 Pod YAML 验证镜像地址",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod test1-redis-master-0 -n aaa -o yaml",
            "purpose": "确认镜像地址和 imagePullSecrets",
        },
        {
            "id": "e2",
            "description": "获取 Terminating Pod 状态",
            "level": "important",
            "tool": "kubectl_get_by_name",
            "command": "kubectl get pod terminating-stuck -n aiops-e2e",
            "purpose": "确认删除卡住状态",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "node": "layer",
            "status": "success",
            "tool_name": "kubectl_get_yaml",
            "semantic_success": True,
            "result": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test1-redis-master-0\nnamespace: aaa\nimage=docker.io/bitnami/redis:5.0.7",
            "structured": {"status": "yaml_summarized", "kind": "Pod", "name": "test1-redis-master-0", "namespace": "aaa"},
        },
        {
            "type": "tool_result",
            "node": "layer",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stderr": "curl: (35) Recv failure: Connection reset by peer"}',
            "structured": {"status": "command_result", "success": False, "stderr_preview": "Connection reset by peer"},
        },
    ]

    upstream = node._build_upstream_evidence_items(plan, events)
    merged = node._merge_evidence_items(
        node._build_evidence_items_from_thinking(plan, []),
        upstream,
    )

    assert any(item.id == "e1" and item.collected and item.source == "layer_verified" for item in merged)
    assert any(item.id.startswith("layer_") and item.collected for item in merged)
    assert node._calculate_completeness(merged) >= 2 / 3


def test_merging_upstream_evidence_does_not_mutate_planned_completeness():
    node = EvidenceCollectorNode()
    planned = [
        EvidenceItem(
            id="e1",
            description="采集异常 Pod 实时可观测性 case",
            level=EvidenceLevel.CRITICAL,
            collected=False,
            source="planned",
        )
    ]
    upstream = [
        EvidenceItem(
            id="e1",
            description="采集异常 Pod 实时可观测性 case",
            level=EvidenceLevel.CRITICAL,
            collected=True,
            value="layer result",
            source="layer_verified",
            outcome="positive",
        )
    ]

    merged = node._merge_evidence_items(planned, upstream)

    assert merged[0].collected is True
    assert merged[0].source == "layer_verified"
    assert planned[0].collected is False
    assert planned[0].source == "planned"
    assert node._calculate_completeness(planned) == 0.0
    assert node._calculate_plan_completeness(planned, upstream) == {
        "plan_total": 1,
        "plan_collected": 0,
        "plan_completeness": 0.0,
    }


def test_evidence_intent_matching_counts_matched_over_planned_not_always_full():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "验证镜像拉取 Pod 当前状态",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod redis-0 -n aaa",
            "evidence_type": "pod_status",
            "target_scope": "group:g1",
            "acceptable_tools": ["kubectl_describe", "kubectl_get_by_name"],
        },
        {
            "id": "e2",
            "description": "验证镜像地址和 imagePullSecrets",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod redis-0 -n aaa -o yaml",
            "evidence_type": "pod_spec",
            "target_scope": "group:g1",
            "acceptable_tools": ["kubectl_get_yaml"],
        },
        {
            "id": "e3",
            "description": "验证 Terminating Pod finalizers",
            "level": "important",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
            "evidence_type": "pod_lifecycle",
            "target_scope": "group:g2",
            "acceptable_tools": ["kubectl_get_yaml", "kubectl_describe"],
        },
        {
            "id": "e4",
            "description": "验证节点到镜像仓库网络",
            "level": "important",
            "tool": "run_bash_command",
            "command": "curl -v https://registry-1.docker.io/v2/",
            "evidence_type": "registry_connectivity",
            "target_scope": "group:g1",
            "acceptable_tools": ["run_bash_command", "kubectl_run_image"],
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": "name: redis-0\nnamespace: aaa\nReason: ImagePullBackOff\nBack-off pulling image",
            "structured": {"status": "describe_summarized", "kind": "Pod", "name": "redis-0", "namespace": "aaa"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stderr": "curl: (35) Recv failure: Connection reset by peer"}',
            "structured": {"status": "command_result", "success": False, "stderr_preview": "Connection reset by peer"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": True,
            "result": "NAME READY STATUS\nunrelated 1/1 Running",
            "structured": {"status": "kept_small_output"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)
    measurable = node._measurable_evidence_items(items)

    assert len(measurable) == 4
    assert sum(1 for item in measurable if item.collected) == 2
    assert node._calculate_completeness(items) == 0.5


def test_evidence_prefers_pydantic_intent_matching_over_exact_command_parameters():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "验证异常 Pod 当前状态",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod <abnormal-pod>",
            "evidence_type": "pod_status",
            "target_scope": "group:g1",
            "acceptable_tools": ["kubectl_describe", "kubectl_get_by_name"],
        },
        {
            "id": "e2",
            "description": "验证镜像仓库连通性",
            "level": "important",
            "tool": "run_bash_command",
            "command": "curl <registry>",
            "evidence_type": "registry_connectivity",
            "target_scope": "group:g1",
            "acceptable_tools": ["run_bash_command", "kubectl_run_image"],
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": True,
            "result": "NAME READY STATUS\nredis-0 0/1 ImagePullBackOff",
            "structured": {"status": "kept_small_output"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stderr": "curl: (28) Operation timed out"}',
            "structured": {"status": "command_result", "success": False, "stderr_preview": "Operation timed out"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert [item.collected for item in items] == [True, True]
    assert node._calculate_completeness(items) == 1.0


def test_evidence_pydantic_intent_rejects_incompatible_tool_category():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "验证 Pod spec",
            "level": "critical",
            "tool": "kubectl_get_yaml",
            "command": "kubectl get pod <abnormal-pod> -o yaml",
            "evidence_type": "pod_spec",
            "target_scope": "group:g1",
            "acceptable_tools": ["kubectl_get_yaml"],
        }
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "semantic_success": True,
            "result": "Failed to pull image",
            "structured": {"status": "events_found"},
        }
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is False
    assert node._calculate_completeness(items) == 0.0


def test_evidence_collection_output_exposes_execution_and_match_counts():
    output = EvidenceCollectorNode._build_evidence_collection_output(
        evidence_plan=[
            {
                "id": "e1",
                "description": "验证 Pod 状态",
                "level": "critical",
                "tool": "kubectl_describe",
                "command": "kubectl describe pod redis-0 -n aaa",
                "purpose": "",
                "evidence_type": "pod_status",
            },
            {
                "id": "e2",
                "description": "验证 Pod 配置",
                "level": "critical",
                "tool": "kubectl_get_yaml",
                "command": "kubectl get pod redis-0 -n aaa -o yaml",
                "purpose": "",
                "evidence_type": "pod_spec",
            },
        ],
        tool_results=[],
        tool_data=[{"tool": "kubectl_describe"}, {"tool": "run_bash_command"}],
        llm_result_text="",
        plan_total=2,
        plan_collected=1,
        plan_completeness=0.5,
        environment_total=2,
        environment_collected=1,
        environment_completeness=0.5,
        evidence_inventory=[
            {"id": "e1", "collected": True, "source": "thinking_match"},
            {"id": "e2", "collected": False, "source": "planned"},
            {"id": "layer_1", "collected": True, "source": "layer_verified"},
        ],
        missing_reasons=["e2: 未采集"],
        early_stop={"triggered": False},
        executed_tool_count=2,
        matched_tool_count=1,
        unplanned_tool_count=1,
        case_tool_count=0,
        supplemental_tool_count=2,
        skipped_plan_count=1,
        observability_target_total=2,
        observability_target_collected=2,
        observability_target_completeness=1.0,
    )

    data = output.model_dump()
    assert data["executed_tool_count"] == 2
    assert data["matched_tool_count"] == 1
    assert data["unplanned_tool_count"] == 1
    assert data["case_tool_count"] == 0
    assert data["supplemental_tool_count"] == 2
    assert data["skipped_plan_count"] == 1
    assert data["observability_target_total"] == 2
    assert data["observability_target_collected"] == 2
    assert data["observability_target_completeness"] == 1.0
    assert "Pod 可观测性覆盖 2/2，完整度 100%" in data["collection_summary"]
    assert "补充计划 1 项因实时 case 已完整而跳过" in data["collection_summary"]
    assert "evidence 节点实际执行工具 2 个，其中核心 case 0 个、补充证据 2 个" in data["collection_summary"]
    assert "已满足计划项 1 个，计划外补证 1 个" in data["collection_summary"]


def test_evidence_counts_diagnostic_negative_result_when_adjudicator_misses():
    def fake_adjudicator(evidence_plan, tool_candidates):
        return {
            "matches": [
                {
                    "plan_id": "e1",
                    "tool_result_index": 0,
                    "matched": False,
                    "confidence": 0.92,
                    "reason": "失败结果不是成功采集",
                }
            ],
            "unmatched_plan_ids": ["e1"],
            "unplanned_tool_result_indexes": [0],
        }

    node = EvidenceCollectorNode(plan_match_adjudicator=fake_adjudicator)
    plan = [
        {
            "id": "e1",
            "description": "检查节点是否可以访问 registry-1.docker.io",
            "level": "important",
            "tool": "run_bash_command",
            "command": "curl -v https://registry-1.docker.io/v2/",
            "purpose": "验证镜像仓库网络可达性",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stderr": "curl: (28) Connection timed out"}',
            "structured": {
                "status": "command_result",
                "success": False,
                "stderr_preview": "curl: (28) Connection timed out",
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is True
    assert items[0].source == "thinking_negative_match"
    assert items[0].outcome == "negative"


def test_evidence_counts_chinese_curl_timeout_as_network_unreachable():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "检查节点到 Docker Hub 镜像仓库是否可达",
            "level": "critical",
            "tool": "run_bash_command",
            "command": "curl -v --connect-timeout 10 https://registry-1.docker.io/v2/",
            "purpose": "验证节点到 registry-1.docker.io:443 的 HTTPS 连通性",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stdout": "", "stderr": "命令执行超时 (60秒)", "returncode": -1}',
            "structured": {
                "status": "command_result",
                "success": False,
                "stderr_preview": "命令执行超时 (60秒)",
                "returncode": -1,
            },
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is True
    assert items[0].source == "thinking_negative_match"
    assert items[0].outcome == "negative"
    assert "命令执行超时" in items[0].value
    assert node._calculate_completeness(items) == 1


def test_evidence_does_not_match_empty_controller_lookup():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取与 Pod 相关的控制器信息",
            "level": "important",
            "tool": "kubectl_get_by_name",
            "command": "kubectl get deployment,replicaset,daemonset -n aiops-e2e",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": False,
            "result": "工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。",
            "structured": {"status": "empty"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is False
    assert node._calculate_completeness(items) == 0


def test_evidence_does_not_match_unrelated_resource_output_with_same_tool():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取 Pod 关联 PVC 和卷挂载信息",
            "level": "important",
            "tool": "kubectl_get_by_name",
            "command": "kubectl get pvc -n aiops-e2e",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": True,
            "result": (
                "NAMESPACE NAME STATUS VOLUME CAPACITY AGE\n"
                "dify upload-pvc Bound pvc-aaa 8Gi 2d\n"
                "test data-pvc Bound pvc-bbb 8Gi 2d\n"
            ),
            "structured": {"status": "kept_small_output"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is False
    assert node._calculate_completeness(items) == 0


def test_evidence_plan_match_adjudicator_overrides_rough_tool_match():
    def fake_adjudicator(evidence_plan, tool_candidates):
        assert evidence_plan[0]["id"] == "e1"
        assert tool_candidates[0]["tool_name"] == "kubectl_get_by_kind_in_namespace"
        return {
            "matches": [
                {
                    "plan_id": "e1",
                    "tool_result_index": 0,
                    "matched": False,
                    "confidence": 0.93,
                    "reason": "计划查询 NetworkPolicy，但工具结果是 Secret 表，resource kind 不一致",
                }
            ],
            "unmatched_plan_ids": ["e1"],
            "unplanned_tool_result_indexes": [0],
        }

    node = EvidenceCollectorNode(plan_match_adjudicator=fake_adjudicator)
    plan = [
        {
            "id": "e1",
            "description": "获取所有节点的网络策略，检查是否存在防火墙或网络策略阻止镜像拉取。",
            "level": "important",
            "tool": "kubectl_get_by_kind_in_namespace",
            "command": "kubectl get networkpolicy -n aaa",
            "purpose": "检查是否存在网络策略阻止镜像拉取。",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_namespace",
            "semantic_success": True,
            "result": (
                "kubectl_get_by_kind_in_namespace Secret 表摘要: rows=2 abnormal=0\n"
                "docker_secret_count: 0\n"
                "未发现 type 为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg 的 Secret。"
            ),
            "structured": {
                "status": "table_summarized",
                "resource_kind": "Secret",
                "docker_secret_count": 0,
            },
            "tool_args": {"resource_type": "Secret", "namespace": "aaa"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is False
    assert items[0].source == "planned"
    assert node._calculate_completeness(items) == 0


def test_evidence_plan_match_adjudicator_accepts_semantic_match():
    def fake_adjudicator(evidence_plan, tool_candidates):
        return {
            "matches": [
                {
                    "plan_id": "e1",
                    "tool_result_index": 0,
                    "matched": True,
                    "confidence": 0.91,
                    "reason": "计划和结果都在 aaa 命名空间查询 test1-redis-master-0 Pod 事件",
                }
            ],
            "unmatched_plan_ids": [],
            "unplanned_tool_result_indexes": [],
        }

    node = EvidenceCollectorNode(plan_match_adjudicator=fake_adjudicator)
    plan = [
        {
            "id": "e1",
            "description": "获取镜像拉取失败的事件详细信息。",
            "level": "critical",
            "tool": "kubectl_events",
            "command": "kubectl get events -n aaa --field-selector involvedObject.name=test1-redis-master-0",
            "purpose": "查看镜像拉取失败事件，确认失败原因。",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_events",
            "semantic_success": True,
            "result": "Warning Failed Pod/test1-redis-master-0 Failed to pull image: i/o timeout",
            "structured": {
                "status": "events_found",
                "selected_events": ["Warning Failed Pod/test1-redis-master-0 Failed to pull image: i/o timeout"],
            },
            "tool_args": {"namespace": "aaa", "name": "test1-redis-master-0"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert len(items) == 1
    assert items[0].collected is True
    assert items[0].source == "thinking_match"
    assert "i/o timeout" in items[0].value
    assert node._calculate_completeness(items) == 1


def test_evidence_rule_match_accepts_event_table_for_event_plan_by_default():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取 primary_pod 的相关事件",
            "level": "critical",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl get events -n aaa --field-selector=involvedObject.name=test1-redis-master-0",
            "purpose": "确认镜像拉取失败的事件原因",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "semantic_success": True,
            "result": (
                "NAMESPACE LAST SEEN TYPE REASON OBJECT MESSAGE\n"
                "aaa 3m Normal BackOff pod/test1-redis-master-0 "
                "Back-off pulling image docker.io/bitnami/redis:5.0.7"
            ),
            "structured": {"status": "table_summarized"},
            "tool_args": {"resource_type": "Event"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert items[0].collected is True
    assert items[0].source == "thinking_match"


def test_evidence_rule_match_rejects_describe_result_for_different_pod_object():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "检查 xnet namespace 的 ImagePullBackOff Pod 当前状态和事件",
            "level": "important",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod -n xnet test1-redis-master-0",
            "purpose": "确认 xnet/redis-master 的当前状态和事件",
        },
        {
            "id": "e2",
            "description": "确认 terminating-stuck Pod 当前状态和 deletionTimestamp",
            "level": "important",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod -n aiops-e2e terminating-stuck",
            "purpose": "验证 Terminating 卡住 Pod 当前状态",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": (
                "kubectl_describe 摘要:\n"
                "name: terminating-stuck\n"
                "namespace: aiops-e2e\n"
                "status: Terminating (lasts 8d)"
            ),
            "structured": {"kind": "Pod", "name": "terminating-stuck", "namespace": "aiops-e2e"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": (
                "kubectl_describe 摘要:\n"
                "name: test1-redis-master-0\n"
                "namespace: xnet\n"
                "status: Pending\n"
                "Reason: ErrImagePull"
            ),
            "structured": {"kind": "Pod", "name": "test1-redis-master-0", "namespace": "xnet"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert items[0].collected is True
    assert "namespace: xnet" in items[0].value
    assert "test1-redis-master-0" in items[0].value
    assert items[1].collected is True
    assert "namespace: aiops-e2e" in items[1].value
    assert "terminating-stuck" in items[1].value


def test_evidence_rule_match_uses_command_intent_when_model_tool_field_is_wrong():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取主异常组的详细事件，确认镜像拉取失败的具体原因",
            "level": "critical",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl describe pod test1-redis-master-0 -n aaa",
            "purpose": "查看 Pod 事件，确认是否因镜像地址错误、认证失败或网络问题导致镜像拉取失败",
        },
        {
            "id": "e2",
            "description": "检查主异常组的 Pod 配置，确认镜像名称和 imagePullSecrets 是否正确",
            "level": "critical",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl get pod test1-redis-master-0 -n aaa -o jsonpath='{.spec.containers[0].image} {spec.imagePullSecrets}'",
            "purpose": "验证镜像名称和 imagePullSecrets",
        },
        {
            "id": "e3",
            "description": "获取非主异常组（Terminating）的详细事件",
            "level": "important",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl describe pod terminating-stuck -n aiops-e2e",
            "purpose": "查看 Pod 事件，确认删除卡住的原因",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": (
                "kubectl_describe 摘要:\n"
                "name: test1-redis-master-0\n"
                "namespace: aaa\n"
                "status: Pending\n"
                "Reason: ImagePullBackOff\n"
                "Back-off pulling image \"docker.io/bitnami/redis:5.0.7-debian-10-r32\""
            ),
            "structured": {"name": "test1-redis-master-0", "namespace": "aaa", "status": "Pending"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": True,
            "result": (
                "NAME                   READY   STATUS             RESTARTS   AGE\n"
                "test1-redis-master-0   0/1     ImagePullBackOff   0          2d5h"
            ),
            "structured": {"status": "kept_small_output"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": (
                "kubectl_describe 摘要:\n"
                "name: terminating-stuck\n"
                "namespace: aiops-e2e\n"
                "status: Terminating (lasts 9d)\n"
                "Warning FailedMount object \"aiops-e2e\"/\"kube-root-ca.crt\" not registered"
            ),
            "structured": {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert items[0].collected is True
    assert items[0].source == "thinking_match"
    assert items[1].collected is False
    assert items[2].collected is True
    assert "terminating-stuck" in items[2].value
    assert node._calculate_completeness(items) == 2 / 3


def test_evidence_rule_match_replays_ce6df_style_plan_without_fake_zero_completeness():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "获取主异常组的详细事件，确认镜像拉取失败的具体原因",
            "level": "critical",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl describe pod test1-redis-master-0 -n aaa",
            "purpose": "查看 Pod 事件，确认是否因镜像地址错误、认证失败或网络问题导致镜像拉取失败",
        },
        {
            "id": "e2",
            "description": "检查主异常组的 Pod 配置，确认镜像名称和 imagePullSecrets 是否正确",
            "level": "critical",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl get pod test1-redis-master-0 -n aaa -o jsonpath='{.spec.containers[0].image} {spec.imagePullSecrets}'",
            "purpose": "验证镜像名称和拉取策略是否正确，以及是否配置了正确的 imagePullSecrets",
        },
        {
            "id": "e3",
            "description": "检查主异常组 Pod 所在节点的网络连接，确认是否能够访问镜像仓库",
            "level": "important",
            "tool": "run_bash_command",
            "command": "kubectl exec -n aaa test1-redis-master-0 -- curl -v https://registry.example.com",
            "purpose": "验证节点到镜像仓库的网络连通性、DNS 解析和 TLS 证书是否正常",
        },
        {
            "id": "e4",
            "description": "获取非主异常组（Terminating）的详细事件，确认删除卡住的具体原因",
            "level": "important",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl describe pod terminating-stuck -n aiops-e2e",
            "purpose": "查看 Pod 事件，确认删除卡住的原因，如 finalizers 未清理或节点侧删除流程卡住",
        },
        {
            "id": "e5",
            "description": "检查主异常组的镜像仓库认证信息",
            "level": "critical",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl get secret -n aaa",
            "purpose": "确认是否存在与镜像拉取相关的 Secret，并检查其内容是否正确",
        },
        {
            "id": "e6",
            "description": "参考 Pod ImagePullFailed / ImagePullBackOff 的 runbook",
            "level": "reference",
            "tool": "fetch_runbook",
            "command": "fetch_runbook --runbook_id=PodImagePullFailed",
            "purpose": "获取参考的 runbook，以指导镜像拉取失败的诊断流程",
        },
        {
            "id": "e7",
            "description": "检查非主异常组（Terminating）的 metadata.finalizers 和 deletionTimestamp",
            "level": "important",
            "tool": "kubectl_get_by_kind_in_cluster",
            "command": "kubectl get pod terminating-stuck -n aiops-e2e -o jsonpath='{.metadata.finalizers} {metadata.deletionTimestamp}'",
            "purpose": "确认是否由于 finalizers 未清理或 deletionTimestamp 设置导致删除卡住",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": (
                "kubectl_describe 摘要:\n"
                "name: test1-redis-master-0\n"
                "namespace: aaa\n"
                "status: Pending\n"
                "Reason: ImagePullBackOff\n"
                "Back-off pulling image \"docker.io/bitnami/redis:5.0.7-debian-10-r32\""
            ),
            "structured": {"name": "test1-redis-master-0", "namespace": "aaa", "status": "Pending"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": True,
            "result": (
                "NAME                   READY   STATUS             RESTARTS   AGE\n"
                "test1-redis-master-0   0/1     ImagePullBackOff   0          2d5h"
            ),
            "structured": {"status": "kept_small_output"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "run_bash_command",
            "semantic_success": False,
            "result": '{"success": false, "stdout": "", "stderr": "error: unable to upgrade connection: container not found (\\"test1-redis\\")\\n", "returncode": 1}',
            "structured": {"status": "command_failed", "raw_preview": "container not found"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": True,
            "result": (
                "kubectl_describe 摘要:\n"
                "name: terminating-stuck\n"
                "namespace: aiops-e2e\n"
                "status: Terminating (lasts 9d)\n"
                "Warning FailedMount object \"aiops-e2e\"/\"kube-root-ca.crt\" not registered"
            ),
            "structured": {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": True,
            "result": (
                "NAME                READY   STATUS        RESTARTS   AGE\n"
                "terminating-stuck   0/1     Terminating   0          9d"
            ),
            "structured": {"status": "kept_small_output"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)
    collected_by_id = {item.id: item.collected for item in items}

    assert collected_by_id == {
        "e1": True,
        "e2": False,
        "e3": False,
        "e4": True,
        "e5": False,
        "e6": False,
        "e7": False,
    }
    assert node._calculate_completeness(items) == 2 / 6


def test_evidence_counts_k8s_negative_mount_evidence_for_volume_mount_plan():
    node = EvidenceCollectorNode()
    plan = [
        {
            "id": "e1",
            "description": "Describe Pod to check events related to volume mounting",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "kubectl describe pod volume-mount-failed -n aiops-e2e",
            "purpose": "Verify FailedMount or MountVolume.SetUp failed events",
            "evidence_type": "event",
        },
        {
            "id": "e2",
            "description": "Check referenced ConfigMap from volume",
            "level": "critical",
            "tool": "kubectl_get_by_name",
            "command": "kubectl get configmap definitely-missing-configmap -n aiops-e2e",
            "purpose": "Confirm whether the ConfigMap referenced by Pod volume exists",
            "evidence_type": "resource_status",
        },
    ]
    events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "semantic_success": False,
            "result": (
                "Name: volume-mount-failed\n"
                "Namespace: aiops-e2e\n"
                "State: Waiting\n"
                "Reason: ContainerCreating\n"
                "Events:\n"
                "Warning FailedMount Pod/volume-mount-failed "
                "MountVolume.SetUp failed for volume \"missing-config\" : "
                "configmap \"definitely-missing-configmap\" not found\n"
            ),
            "structured": {"status": "describe_summarized", "kind": "Pod", "name": "volume-mount-failed", "namespace": "aiops-e2e"},
            "tool_args": {"kind": "Pod", "name": "volume-mount-failed", "namespace": "aiops-e2e"},
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_name",
            "semantic_success": False,
            "result": (
                "Command failed (exit 1):\n"
                "kubectl get --show-labels -o wide configmap definitely-missing-configmap -n aiops-e2e\n"
                "Error from server (NotFound): configmaps \"definitely-missing-configmap\" not found"
            ),
            "structured": {"status": "command_failed"},
            "tool_args": {"kind": "ConfigMap", "name": "definitely-missing-configmap", "namespace": "aiops-e2e"},
        },
    ]

    items = node._build_evidence_items_from_thinking(plan, events)

    assert {item.id: item.collected for item in items} == {"e1": True, "e2": True}
    assert all(item.source == "thinking_negative_match" for item in items)
    assert node._calculate_completeness(items) == 1.0


def test_evidence_plan_match_does_not_call_llm_by_default():
    class _StructuredAICall:
        def __init__(self):
            self.calls = []

        def call_structured(self, system_prompt, question, schema, **kwargs):
            self.calls.append({
                "system_prompt": system_prompt,
                "question": question,
                "schema": schema,
                "kwargs": kwargs,
            })
            return schema.model_validate({
                "matches": [
                    {
                        "plan_id": "e1",
                        "tool_result_index": 0,
                        "matched": True,
                        "confidence": 0.91,
                        "reason": "对象、namespace、工具意图一致",
                    }
                ],
                "unmatched_plan_ids": [],
                "unplanned_tool_result_indexes": [],
            }), "{}"

    node = EvidenceCollectorNode()
    node.ai_call = _StructuredAICall()

    matched = node._adjudicate_plan_tool_matches(
        evidence_plan=[
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认镜像拉取失败原因",
            }
        ],
        successful_tools=[
            {
                "tool_name": "kubectl_events",
                "result": "Warning Failed Pod/test1-redis-master-0 Failed to pull image",
                "tool_args": {"namespace": "aaa"},
                "structured": {"status": "events_found"},
            }
        ],
    )

    assert matched is None
    assert node.ai_call.calls == []
