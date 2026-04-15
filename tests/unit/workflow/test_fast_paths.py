import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.prompts import (
    EVIDENCE_COLLECTOR_PROMPT,
    LAYER_CLASSIFIER_PROMPT,
    LAYER_EXTRACT_PROMPT,
)
from app.core.skills.models import Layer
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode


class _FailingAICall:
    def call_simple(self, *args, **kwargs):
        raise AssertionError("call_simple should not be called")


class _RecordingAICall:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def call_simple(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        return self.content


def test_query_conclusion_uses_llm_structured_summary():
    node = ConclusionFormatterNode()
    node.ai_call = _RecordingAICall(
        """## 📊 查询结果

- **查询目标**: 查询当前异常 Pod 列表

## 📈 数据摘要
| 项目 | 数值 |
|------|------|
| 异常 Pod 数量 | 1 |

## 🔎 详情
- default/pod-a: CrashLoopBackOff
"""
    )

    state = {
        "question": "查询当前异常 Pod 列表",
        "layer": Layer.QUERY,
        "evidence_analysis": (
            '{"tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", '
            '"data": "NAMESPACE NAME STATUS\\ndefault pod-a CrashLoopBackOff"}]}'
        ),
        "thinking_events": [],
    }

    result = node.execute(state)

    assert len(node.ai_call.calls) == 1
    assert "查询结果" in result["conclusion"]
    assert "数据摘要" in result["conclusion"]
    assert "异常 Pod 数量" in result["conclusion"]
    assert "CrashLoopBackOff" in result["conclusion"]


def test_healthy_conclusion_uses_deterministic_fast_path():
    node = ConclusionFormatterNode()
    node.ai_call = _FailingAICall()

    state = {
        "question": "我的集群现在健康吗",
        "layer": Layer.HEALTHY,
        "layer_full_analysis": "所有 Pod Running，节点 Ready，未发现异常事件。",
        "thinking_events": [],
    }

    result = node.execute(state)

    assert "健康检查结果" in result["conclusion"]
    assert "当前集群运行正常" in result["conclusion"]
    assert "所有 Pod Running" in result["conclusion"]


def test_layer_stage1_structured_output_skips_second_extraction_and_keeps_full_analysis():
    node = LayerClassifierNode()
    structured_json = """
```json
{
  "layer": "QUERY",
  "layers": ["QUERY"],
  "layer_name": "直接查询",
  "confidence": 0.95,
  "reasoning": "用户在直接查询异常 Pod 列表",
  "key_entities": [{"type": "Resource", "value": "Pod"}],
  "possible_scenarios": [{"scenario": "直接查询", "probability": "高", "reason": "请求状态列表"}]
}
```
""".strip()

    thinking_events = [
        {
            "type": "tool_result",
            "status": "success",
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "result": "NAMESPACE NAME STATUS\ndefault pod-a CrashLoopBackOff",
        }
    ]

    node._call_llm = lambda question, prompt: (SimpleNamespace(result=structured_json), thinking_events)
    node._extract_classification = lambda analysis_text: (_ for _ in ()).throw(
        AssertionError("stage2 extraction should not run")
    )

    result, returned_events = node._analyze_with_llm("查询异常 Pod")

    assert result["layer"] == "QUERY"
    assert "full_analysis" in result
    assert "kubectl_get_by_kind_in_cluster" in result["full_analysis"]
    assert "CrashLoopBackOff" in result["full_analysis"]
    assert returned_events == thinking_events


def test_layer_prompts_prioritize_user_intent_for_query_requests():
    expected_phrases = [
        "先判断用户意图",
        "如果用户明确是在查询指标/状态/列表/资源使用率，优先判定为 QUERY",
        "QUERY 场景下，不要因为集群中存在其他异常 Pod 就自动转入故障诊断",
        "只有当用户明确问“有什么问题 / 为什么异常 / 帮我排查 / 根因是什么”时，才进入 L0-L4 定层诊断流程",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
        assert phrase in LAYER_EXTRACT_PROMPT


def test_query_prompt_boundaries_are_explicit_between_layer_and_evidence():
    layer_phrases = [
        "如果当前请求是 QUERY，你的任务只是在阶段1识别查询意图、提取查询对象、指标、范围和维度",
        "不要在 layer 节点中尝试直接回答用户问题",
        "不要在 layer 节点中做指标计算、结果聚合、脚本拼接、jq 处理、bash 推导或资源估算",
        "QUERY 模式下，真实数据采集统一交给 evidence 节点完成",
    ]
    evidence_phrases = [
        "layer=QUERY：你负责真实数据采集和返回查询结果所需的数据",
        "不要把 QUERY 请求再退回给 layer 节点处理",
    ]

    for phrase in layer_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
        assert phrase in LAYER_EXTRACT_PROMPT

    for phrase in evidence_phrases:
        assert phrase in EVIDENCE_COLLECTOR_PROMPT


def test_layer_prompts_prioritize_runbook_as_high_priority_reference():
    expected_phrases = [
        "如果当前问题与某个 runbook 明显相关，优先调用 fetch_runbook 获取参考",
        "runbook 是额外知识储备和诊断参考，优先级高于你自己的泛化经验判断",
        "在 DIAGNOSIS 场景下，只要已出现明确场景信号，就应尽早查看相关 runbook",
    ]

    for phrase in expected_phrases:
        assert phrase in LAYER_CLASSIFIER_PROMPT
        assert phrase in LAYER_EXTRACT_PROMPT
