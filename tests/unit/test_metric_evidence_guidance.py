"""Generic metric semantics are shared, not a compulsory acquisition plan."""

import pytest

from app.core import prompts


@pytest.mark.parametrize(
    "name",
    [
        "QUERY_COLLECT_PROMPT",
        "DIAGNOSTIC_TOOL_GUIDANCE",
        "DEEP_RCA_PROMPT",
        "QUERY_CONCLUSION_PROMPT",
    ],
)
def test_metric_contract_shared_once_per_stage(name):
    prompt = getattr(prompts, name)
    assert prompt.count(prompts.METRIC_EVIDENCE_GUIDANCE) == 1
    for part in (
        "原始标签",
        "labels/metadata",
        "单位和时间",
        "按指标定义",
        "信息指标的 1 不代表健康",
        "只证明抓取失败",
        "不是独立证据",
    ):
        assert part in prompt


def test_no_mandatory_query_plan_or_tool_name_in_shared_guidance():
    guidance = prompts.METRIC_EVIDENCE_GUIDANCE
    assert "不为凑维度查询" in guidance
    assert "摘要省略时说明边界" in guidance
    assert "execute_" not in guidance
    assert "必须调用" not in guidance
    assert (
        "原始指标标签需结合指标定义和值解释，不能一概当作背景" in prompts.QUERY_CONCLUSION_PROMPT
    )
