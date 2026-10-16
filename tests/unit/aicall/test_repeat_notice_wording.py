"""A repeat notice tells the model to answer when data is complete, not to try other tools."""

from app.core.aicall.client import AICall


def test_repeat_notice_points_to_answering_not_tool_switching():
    text = AICall.repeat_call_notice("kubectl_get_by_kind_in_cluster", "call-1", same_turn=False)
    assert "结果未变化" in text and "call-1" in text
    assert "已齐全" in text and "直接" in text
    assert "改用其它工具" not in text
