import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json

from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.schemas import EvidenceCollectionOutput
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
    assert "直接执行既有 evidence_plan 中的必要工具" in message


def test_evidence_plan_parser_validates_with_pydantic_schema():
    text = """```json
{
  "layer": "L3",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 事件",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl get events -n aaa",
      "purpose": "确认镜像拉取失败原因"
    }
  ],
  "collection_strategy": "先确认当前异常 Pod。"
}
```"""

    plan = EvidenceCollectorNode()._parse_llm_evidence_plan(text)

    assert plan == [
        {
            "id": "e1",
            "description": "获取 Pod 事件",
            "level": "critical",
            "tool": "kubectl_events",
            "command": "kubectl get events -n aaa",
            "purpose": "确认镜像拉取失败原因",
        }
    ]


def test_evidence_plan_parser_rejects_invalid_pydantic_plan():
    text = """```json
{
  "layer": "L3",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 事件",
      "level": "critical",
      "tool": "kubectl_events",
      "purpose": "确认镜像拉取失败原因"
    }
  ],
  "collection_strategy": "缺少 command，应拒绝。"
}
```"""

    assert EvidenceCollectorNode()._parse_llm_evidence_plan(text) == []


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

    assert "context_archive_ref: /tmp/aiops/reports/context_archives/run-1" in message
    assert "/tmp/aiops/reports/context_archives/run-1/budget/layer.json" not in message
    assert "/tmp/aiops/reports/context_archives/run-1/tools/" not in message
    assert "layer full_analysis_ref:" not in message
    assert "read_context_archive" not in message


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

    assert len(items) == 2
    assert items[0].collected is False
    assert items[1].collected is False
    assert node._calculate_completeness(items) == 0


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


def test_evidence_plan_match_llm_uses_structured_schema():
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

    assert matched == {"e1": 0}
    assert node.ai_call.calls[0]["schema"].__name__ == "EvidenceMatchOutput"
