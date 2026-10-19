"""Compaction budgets are shares of the model window, front-loaded on decisive facts.

2026-10-19 design: when compaction triggers, the recent verbatim tail is small (the
last 1-2 complete interactions, capped by a window share) and the working-memory
budget for the older, fact-bearing history is the larger, window-relative share.
"""

from app.core.aicall.working_context import partition_recent
from app.core.context import window_policy
from app.core.context.window_policy import WindowPolicy


def test_defaults_config_env_and_bounds():
    assert WindowPolicy.from_config(None, environ={}) == WindowPolicy(2, 0.06, 0.08)
    assert WindowPolicy.from_config(
        {"recent_keep_interactions": 1, "recent_keep_ratio": 0.1, "summary_output_ratio": 0.1},
        environ={},
    ) == WindowPolicy(1, 0.1, 0.1)
    assert (
        WindowPolicy.from_config(
            {"recent_keep_interactions": 1}, environ={"AICALL_RECENT_KEEP_INTERACTIONS": "3"}
        ).recent_keep_interactions
        == 3
    )
    assert WindowPolicy.from_config(
        {"recent_keep_interactions": "x", "recent_keep_ratio": 5, "summary_output_ratio": 0},
        environ={},
    ) == WindowPolicy(2, 0.5, 0.01)


def test_budgets_follow_the_window_and_favour_the_summary():
    policy = WindowPolicy(2, 0.06, 0.08)
    assert policy.recent_budget(54000) == 3240
    assert policy.summary_budget(54000) == 4320
    assert policy.recent_budget(30000) == 1800 and policy.summary_budget(30000) == 2400
    assert policy.recent_budget(70000) == 4200 and policy.summary_budget(70000) == 5600
    assert policy.summary_budget(5000) == 600  # floor for tiny windows
    assert policy.summary_budget(54000) > policy.recent_budget(54000)


def test_partition_recent_keeps_at_most_n_complete_interactions(monkeypatch):
    saved = window_policy.current()
    try:
        window_policy.configure(WindowPolicy(2, 0.5, 0.08))
        groups = [[{"role": "user", "content": "x" * 90}] for _ in range(5)]
        older, recent = partition_recent(groups, 54000)
        assert len(recent) == 2 and len(older) == 3 and recent == groups[3:]
    finally:
        window_policy.configure(saved)


def test_partition_recent_also_respects_the_window_share(monkeypatch):
    saved = window_policy.current()
    try:
        window_policy.configure(WindowPolicy(recent_keep_interactions=3, recent_keep_ratio=0.02))
        groups = [[{"role": "user", "content": "x" * 3000}] for _ in range(3)]  # ~1011 each
        older, recent = partition_recent(groups, 54000)  # 1080-token share fits one
        assert len(recent) == 1 and len(older) == 2
    finally:
        window_policy.configure(saved)


def test_newest_interaction_stays_verbatim_even_above_the_tail_share(monkeypatch):
    saved = window_policy.current()
    try:
        window_policy.configure(WindowPolicy(2, 0.02, 0.08))  # tail share 1080 at 54k
        groups = [[{"role": "user", "content": "x" * 6000}] for _ in range(3)]  # ~2011 each
        older, recent = partition_recent(groups, 54000)  # newest fits 15% (8100)
        assert recent == groups[-1:] and len(older) == 2
        huge = [[{"role": "user", "content": "x" * 30000}]]  # ~10k > 15% of 54k
        assert partition_recent(huge, 54000) == (huge, [])
    finally:
        window_policy.configure(saved)


def test_summary_prompt_front_loads_structured_decisive_facts():
    from app.core.prompts import CONTEXT_SUMMARY_PROMPT as prompt

    assert "summary_budget_tokens" in prompt and "protected_facts_available" in prompt
    assert prompt.index("决定性事实") < prompt.index("未解决项与下一步")
    for field in ("deletionTimestamp", "finalizers", "退出码", "raw_ref", "summary_selection"):
        assert field in prompt
    assert "原样保留键名和值" in prompt


def test_summarizer_is_bound_to_the_window_share(monkeypatch):
    import asyncio

    from langchain_core.messages import AIMessage

    from app.core.aicall.working_context import summarize_history

    bound = []

    class Model:
        def bind(self, **kw):
            bound.append(kw["max_tokens"])
            return self

        async def ainvoke(self, messages, config=None):
            assert '"summary_budget_tokens": 4320' in messages[-1].content
            return AIMessage(content="## demo/p\\n- 事实：reason=Error")

    saved = window_policy.current()
    try:
        window_policy.configure(WindowPolicy())
        out = asyncio.run(summarize_history(Model(), "q", "history", window=54000))
    finally:
        window_policy.configure(saved)
    assert out.startswith("## demo/p") and bound == [4320]
