"""Executor + recovery watch: baseline before commands, read-only polling after, timeouts explicit."""

import json

import app.core.remediation.pod_executor as module
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.recovery import RecoveryConfig, RecoveryWatch
from tests.unit.remediation.test_pod_executor import fixture


def _pod(ready, restarts=0, waiting=None):
    state = {"waiting": {"reason": waiting}} if waiting else {"running": {}}
    return json.dumps({"metadata": {"name": "api-1", "uid": "p1"}, "status": {
        "phase": "Running", "conditions": [{"type": "Ready", "status": "True" if ready else "False"}],
        "containerStatuses": [{"restartCount": restarts, "state": state}]}})


class _Clock:
    def __init__(self):
        self.now = 0.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _factory(clock):
    return lambda runner, config: RecoveryWatch(runner, config, clock=clock.time, sleep=clock.sleep)


def test_recovery_is_observed_after_commands_and_reported():
    draft, _, _, _ = fixture()
    clock = _Clock()
    gets = []

    def runner(argv):
        if argv[1] == "get":
            gets.append(" ".join(argv))
            return _pod(ready=len(gets) > 2)  # unhealthy at baseline, healthy after the second poll
        return "deployment.apps/api resource requirements updated"

    events = list(PodRepairExecutor(runner=runner).run(
        "rec", draft, mode="auto", recovery=RecoveryConfig(timeout_seconds=60, poll_seconds=5, settle_seconds=10),
        watch_factory=_factory(clock)))
    kinds = [e["type"] for e in events]
    assert kinds[0] == "remediation_tool_start" and "remediation_recovery" in kinds
    final = events[-1]
    assert final["type"] == "remediation_finished" and final["status"] == "recovered"
    assert final["recovery"]["targets"][0]["before"]["ready"] is False
    assert final["recovery"]["targets"][0]["after"]["ready"] is True
    assert "目标已恢复" in final["reason"] and "未经人工审批" in final["reason"]
    assert all(call.startswith("kubectl get pod/api-1") for call in gets)
    # Progress events carry the budget so the UI can show "35/180 秒".
    progress = [e for e in events if e["type"] == "remediation_recovery"]
    assert progress[0]["timeout_seconds"] == 60 and progress[0]["verdict"] == "pending"


def test_not_recovered_within_timeout_is_a_timeout_verdict_not_success():
    draft, _, _, _ = fixture()
    clock = _Clock()
    runner = lambda argv: _pod(ready=False, restarts=5, waiting="CrashLoopBackOff") if argv[1] == "get" else "ok"  # noqa: E731
    events = list(PodRepairExecutor(runner=runner).run(
        "rec-timeout", draft, mode="auto", recovery=RecoveryConfig(timeout_seconds=20, poll_seconds=10, settle_seconds=0),
        watch_factory=_factory(clock)))
    final = events[-1]
    assert final["status"] == "not_recovered"
    assert final["recovery"]["targets"][0]["timed_out"] is True
    assert "20 秒内未观察到恢复" in final["reason"] and "CrashLoopBackOff" in final["reason"]


def test_without_recovery_config_behaviour_is_unchanged():
    draft, _, _, _ = fixture()
    events = list(PodRepairExecutor(runner=lambda argv: "ok").run("plain", draft, mode="auto"))
    assert events[-1]["status"] == "needs_followup" and "recovery" not in events[-1]


def test_overall_deadline_stops_before_the_next_action(monkeypatch):
    draft, _, _, _ = fixture()
    draft["actions"].append({**draft["actions"][0], "id": "a2"})
    clock = {"now": 0.0}
    monkeypatch.setattr(module.time, "time", lambda: clock["now"])
    calls = []

    def runner(argv):
        calls.append(argv)
        if argv[1] == "set":  # the first write takes "long"
            clock["now"] = 1000.0
        return "ok"

    events = list(PodRepairExecutor(runner=runner).run("deadline", draft, mode="auto", max_duration=300))
    final = events[-1]
    assert final["status"] == "timeout" and final["error_code"] == "execution_deadline"
    assert "已完成 1/2 个动作" in final["reason"]
    assert len([c for c in calls if c[1] == "set"]) == 1  # second action never started
