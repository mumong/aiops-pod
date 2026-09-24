"""Characterize the exact model inputs shared by RCA's lite/full paths."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.skills.models import Layer
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.schemas import RCACompactOutput, RCAOutput


@pytest.mark.parametrize("mode", ["lite", "full"])
@pytest.mark.parametrize("schema", [RCACompactOutput, RCAOutput])
@pytest.mark.parametrize("layer", [None, Layer.L2])
@pytest.mark.parametrize(
    ("question", "evidence"),
    [
        ("为什么 Pod 异常？", "已采集证据：退出码 1\n来源：日志"),
        ("", ""),
        ("  question\n{literal}\t", '\n{"message": "原样保留"}\n  '),
    ],
)
def test_rca_model_input_bytes(monkeypatch, mode, schema, layer, question, evidence):
    # Arrange: capture the real branch's model boundary without calling a model.
    node = RootCauseAnalyzerNode()
    node.ai_call = object()
    monkeypatch.setattr(
        node, "_get_rca_prompt", lambda: "layer={layer}\nevidence={evidence_summary}"
    )
    monkeypatch.setattr(node, "_model_rca_schema", lambda: schema)
    monkeypatch.setattr(
        node, "_rca_schema_contract", lambda selected: "\nSCHEMA:" + selected.__name__
    )
    parsed = {"root_cause": "unchanged structured result"}
    events = [{"type": "thinking", "content": "unchanged event"}]
    monkeypatch.setattr(node, "_expand_model_rca_output", lambda structured: parsed)
    call = Mock(return_value=(object(), SimpleNamespace(result="model output"), events))
    monkeypatch.setattr(node, "_call_structured_agent", call)
    expected_message = (
        "# 用户问题\n" + question + "\n\n# 已采集证据\n" + evidence
        + "\n\n请直接基于以上证据进行根因分析，并通过运行时 Pydantic schema 生成结构化结果。"
    )
    expected_system = "layer=" + (layer.value if layer else "ABNORMAL") + "\nevidence="
    expected_system += (
        "证据上下文只在 user message 中提供，system prompt 不承载动态证据。"
        if mode == "lite" else evidence
    )
    expected_system += "\nSCHEMA:" + schema.__name__
    if mode == "full":
        expected_system += (
            "\n\n# ⚠️ 重要：不要重复采集数据\n"
            "上面的「已采集证据」和「工具采集的原始数据」已经包含了所有需要的信息。\n"
            "请直接基于这些数据进行分析，**不要重新调用工具采集数据**。\n"
            "如果数据不足，在 limitations 中说明即可。"
        )

    # Act: exercise both production entry points, not a newly introduced helper.
    result = getattr(node, "_analyze_with_llm_" + mode)(question, layer, evidence)

    # Assert: exact UTF-8 bytes, schema, tool policy and returned data are preserved.
    call.assert_called_once()
    assert call.call_args.kwargs == {
        "schema": schema,
        "system_prompt": expected_system,
        "question": expected_message,
        "use_tools": False,
        "allow_text_fallback": True,
    }
    assert call.call_args.kwargs["question"].encode("utf-8") == expected_message.encode("utf-8")
    assert result == (parsed, events)
