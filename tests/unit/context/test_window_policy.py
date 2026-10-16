"""Recent-tail retention is window-relative configuration, not a literal."""

from app.core.aicall.working_context import partition_recent
from app.core.context import window_policy
from app.core.context.window_policy import WindowPolicy


def test_defaults_config_env_and_bounds():
    assert WindowPolicy.from_config(None, environ={}) == WindowPolicy(8000, 0.15)
    assert WindowPolicy.from_config(
        {"recent_keep_tokens": 16000, "recent_keep_ratio": 0.2}, environ={}
    ) == WindowPolicy(16000, 0.2)
    assert (
        WindowPolicy.from_config(
            {"recent_keep_tokens": 16000}, environ={"AICALL_RECENT_KEEP_TOKENS": "12000"}
        ).recent_keep_tokens
        == 12000
    )
    assert WindowPolicy.from_config(
        {"recent_keep_tokens": "x", "recent_keep_ratio": 5}, environ={}
    ) == WindowPolicy(8000, 0.9)


def test_recent_budget_scales_with_the_window_up_to_the_cap():
    policy = WindowPolicy(8000, 0.15)
    assert policy.recent_budget(54000) == 8000
    assert policy.recent_budget(20000) == 3000
    assert WindowPolicy(16000, 0.15).recent_budget(131072) == 16000


def test_partition_recent_reads_the_installed_policy(monkeypatch):
    saved = window_policy.current()
    try:
        window_policy.configure(WindowPolicy(recent_keep_tokens=600, recent_keep_ratio=0.5))
        groups = [[{"role": "user", "content": "x" * 900}] for _ in range(3)]
        older, recent = partition_recent(groups, 54000)
        assert len(recent) == 1 and len(older) == 2
    finally:
        window_policy.configure(saved)
