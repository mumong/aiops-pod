import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json

from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.schemas import EvidenceCollectionOutput, EvidencePlanOutput
from app.core.skills.models import EvidenceItem, EvidenceLevel, Layer


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
    )

    data = output.model_dump()
    assert data["executed_tool_count"] == 2
    assert data["matched_tool_count"] == 1
    assert data["unplanned_tool_count"] == 1
    assert "实际执行工具 2 个，匹配计划 1 个，未规划证据 1 个" in data["collection_summary"]


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
