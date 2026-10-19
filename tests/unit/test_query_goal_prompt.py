"""Contract checks for the goal-driven Query prompt and its scoped rollback."""

from app.core.prompts import DIAGNOSTIC_TOOL_GUIDANCE, QUERY_COLLECT_PROMPT


def test_query_goal_sections_and_structured_completion():
    for section in ("Role", "Goal", "Decision Policy", "Boundaries", "Completion", "Output"):
        assert f"# {section}" in QUERY_COLLECT_PROMPT
    assert "QueryAnswer" in QUERY_COLLECT_PROMPT
    assert "missing" in QUERY_COLLECT_PROMPT
    assert "当前用户明确授权" in QUERY_COLLECT_PROMPT
    assert "历史数据不冒充当前观测" in QUERY_COLLECT_PROMPT
    assert "空结果不等于零" in QUERY_COLLECT_PROMPT
    assert "Runbook" in QUERY_COLLECT_PROMPT
    assert DIAGNOSTIC_TOOL_GUIDANCE not in QUERY_COLLECT_PROMPT
