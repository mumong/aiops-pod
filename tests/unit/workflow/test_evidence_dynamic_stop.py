import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json

from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.skills.models import EvidenceItem, EvidenceLevel, Layer


def test_evidence_should_continue_when_important_item_is_still_missing():
    node = EvidenceCollectorNode()
    thinking_events = [
        {
            "type": "ai_message",
            "full_content": """
```json
{
  "layer": "L0",
  "evidence_plan": [
    {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
    {"id": "e2", "description": "检查 Deployment 配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment x -o yaml", "purpose": "确认配置"}
  ]
}
```
""",
        },
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
    thinking_events = [
        {
            "type": "ai_message",
            "full_content": """
```json
{
  "layer": "L0",
  "evidence_plan": [
    {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
    {"id": "e2", "description": "检查节点磁盘压力", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node x", "purpose": "确认节点状态"}
  ]
}
```
""",
        },
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
    thinking_events = [
        {
            "type": "ai_message",
            "full_content": """
```json
{
  "layer": "L0",
  "evidence_plan": [
    {"id": "e1", "description": "确认驱逐原因", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod x", "purpose": "确认 Evicted 原因"},
    {"id": "e2", "description": "检查 Deployment 配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment x -o yaml", "purpose": "确认配置"},
    {"id": "e3", "description": "补充日志", "level": "optional", "tool": "kubectl_logs", "command": "kubectl logs x", "purpose": "补充上下文"}
  ]
}
```
""",
        },
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


def test_evidence_execute_retries_when_plan_exists_but_no_tool_results():
    node = EvidenceCollectorNode()
    calls = {"count": 0}

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
        calls["count"] += 1
        if calls["count"] == 1:
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

    assert calls["count"] == 2
    assert result["evidence_completeness"] == 1.0
    assert len(result["evidence_items"]) == 2


def test_evidence_execute_retries_when_tools_run_before_plan():
    node = EvidenceCollectorNode()
    calls = []

    first_events = [
        {
            "type": "tool_start",
            "tool_name": "kubectl_describe",
            "tool_args": {"resource_type": "pod", "resource_name": "ham-wcc79", "namespace": "xnet"},
        },
        {
            "type": "ai_message",
            "full_content": """
```json
{
  "layer": "L3",
  "evidence_plan": [
    {"id": "e1", "description": "确认 Pod 事件", "level": "critical", "tool": "kubectl_events", "command": "kubectl events ...", "purpose": "确认镜像拉取失败原因"}
  ]
}
```
""",
        },
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_describe",
            "result_preview": "ImagePullBackOff",
            "result": "ImagePullBackOff",
        },
    ]
    second_plan = [
        {"id": "e1", "description": "确认 Pod 事件", "level": "critical", "tool": "kubectl_events", "command": "kubectl events ...", "purpose": "确认镜像拉取失败原因"}
    ]
    second_events = [
        {
            "type": "ai_message",
            "full_content": """
```json
{
  "layer": "L3",
  "evidence_plan": [
    {"id": "e1", "description": "确认 Pod 事件", "level": "critical", "tool": "kubectl_events", "command": "kubectl events ...", "purpose": "确认镜像拉取失败原因"}
  ]
}
```
""",
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

    assert len(calls) == 2
    assert calls[0]["strict_mode"] is False
    assert calls[1]["strict_mode"] is True
    assert "evidence_plan 前就开始调用工具" in calls[1]["failure_reason"]
    assert result["evidence_completeness"] == 1.0


def test_evidence_user_prompt_requires_first_assistant_message_to_be_plan_json():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群有什么问题",
        layer="L3",
        layer_handoff='{"layer":"L3"}',
    )

    assert "第一条 assistant 消息必须只输出 evidence_plan JSON" in message
    assert "在输出 evidence_plan JSON 之前，禁止调用任何工具" in message
    assert "输出 evidence_plan 后不能结束" in message
    assert "必须继续调用至少一个 critical 或 important 级真实工具" in message
    assert "根据 Available Runbooks/catalog 的 description" in message
    assert "evidence_plan 第一项必须是 fetch_runbook" not in message
    assert "Pod 异常状态的证据" in message


def test_evidence_user_prompt_includes_context_archive_entrypoints():
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

    assert "context_archive_ref: /tmp/aiops/reports/context_archives/run-1" in message
    assert "/tmp/aiops/reports/context_archives/run-1/budget/layer.json" in message
    assert "layer full_analysis_ref:" in message


def test_evidence_early_stop_disabled_does_not_pass_stop_checker():
    node = EvidenceCollectorNode()
    node.workflow_config_override = {"evidence": {"early_stop": {"enabled": False}}}
    node.ai_call = object()
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

    assert len(items) == 3
    assert items[0].collected is False
    assert items[1].collected is False
    assert items[2].source == "thinking_extra"
    assert node._calculate_completeness(items) == 1 / 3
