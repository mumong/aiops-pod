import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json

from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.skills.models import Layer


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
