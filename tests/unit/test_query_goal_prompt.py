"""Contract checks for the goal-driven Query prompt and its scoped rollback."""

import ast
from pathlib import Path

from app.core.prompts import DIAGNOSTIC_TOOL_GUIDANCE, QUERY_COLLECT_PROMPT

ROOT = Path(__file__).resolve().parents[2]


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


def test_query_backup_is_complete_and_new_prompt_is_compact():
    backup = ROOT / "docs/history/prompt_backups/query_collect_20261009.txt"
    tree = ast.parse(backup.read_text())
    assert len(tree.body) == 1
    assignment = tree.body[0]
    assert assignment.targets[0].id == "QUERY_COLLECT_PROMPT"
    original = ast.literal_eval(assignment.value)
    assert "execute_pod_promql" in original
    assert len(QUERY_COLLECT_PROMPT) < len(original) * 0.35
    assert "execute_pod_promql" not in QUERY_COLLECT_PROMPT
    assert "kubectl run" not in QUERY_COLLECT_PROMPT
