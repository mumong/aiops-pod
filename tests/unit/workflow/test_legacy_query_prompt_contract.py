"""Freeze the legacy query summarizer's text before relocating its policy."""

from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode


EXPECTED = """你是 K8s 查询结果总结器。

任务：把输入中的 `QUERY 结构化结果` 和真实工具数据总结为面向用户的 Markdown。
输出契约：只输出一个 JSON 对象，schema 为 `{"markdown_report": "..."}`，不要输出 ```json 代码块之外的任何文字。
边界：
- 只回答用户明确询问的对象、维度和指标。
- 必须使用表格展示已获取的数据。
- 必须说明数据来源和单位。
- 不要做根因分析，不要写修复建议，除非用户明确要求。
- 不要编造、补算、猜测缺失值；缺失项写“未获取到”。
- 输出必须是中文。"""


def test_legacy_query_summary_prompt_bytes():
    # Arrange: no model or cluster dependency is needed to construct this policy.
    node = ConclusionFormatterNode()

    # Act: retain the compatibility method used by the legacy workflow.
    actual = node._get_query_conclusion_prompt()

    # Assert: schema punctuation, whitespace and instructions are unchanged.
    assert actual == EXPECTED
