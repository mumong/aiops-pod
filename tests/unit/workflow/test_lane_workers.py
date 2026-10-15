"""Lane fan-out is bounded by config first, env second, never unbounded."""

from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode


def _node(config_value, monkeypatch, env=None):
    node = AutonomousParallelNode()
    node.autonomous_parallel_workers = config_value
    if env is None:
        monkeypatch.delenv("AIOPS_AUTONOMOUS_PARALLEL_WORKERS", raising=False)
    else:
        monkeypatch.setenv("AIOPS_AUTONOMOUS_PARALLEL_WORKERS", env)
    return node


def test_config_wins_over_env_and_both_are_clamped(monkeypatch):
    assert _node(5, monkeypatch, env="2").lane_workers() == 5
    assert _node(None, monkeypatch, env="2").lane_workers() == 2
    assert _node(None, monkeypatch).lane_workers() == 3
    assert _node(50, monkeypatch).lane_workers() == 8
    assert _node("many", monkeypatch).lane_workers() == 3
