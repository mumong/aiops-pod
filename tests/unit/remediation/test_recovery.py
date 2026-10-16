"""Recovery watch: status-only judgement, settle window, replacement Pods, timeout feedback."""

import json

from app.core.remediation.recovery import RecoveryConfig, RecoveryWatch, judge, pod_snapshot


def _pod(name="api-1", phase="Running", ready=True, restarts=0, waiting=None, deleting=False, uid="u1", created="2026-10-16T10:00:00Z"):
    state = {"waiting": {"reason": waiting}} if waiting else {"running": {}}
    meta = {"name": name, "uid": uid, "creationTimestamp": created}
    if deleting:
        meta["deletionTimestamp"] = "2026-10-16T10:05:00Z"
    return {"metadata": meta, "status": {"phase": phase,
            "conditions": [{"type": "Ready", "status": "True" if ready else "False"}],
            "containerStatuses": [{"restartCount": restarts, "state": state}]}}


def test_snapshot_reads_only_status_facts():
    snap = pod_snapshot(_pod(ready=False, restarts=3, waiting="CrashLoopBackOff"))
    assert snap["phase"] == "Running" and snap["ready"] is False
    assert snap["restarts"] == 3 and snap["reason"] == "CrashLoopBackOff"
    assert pod_snapshot(None) == {"exists": False}


def test_judgement_rules_are_generic():
    gone = {"exists": False}
    assert judge({"deletion_timestamp": "x", "exists": True}, gone, stable_seconds=0, settle_seconds=0)[0] == "recovered"
    assert judge({"exists": True}, gone, stable_seconds=0, settle_seconds=0)[0] == "pending"
    healthy = pod_snapshot(_pod())
    assert judge({"restarts": 0, "uid": "u1"}, healthy, stable_seconds=5, settle_seconds=20)[0] == "pending"
    assert judge({"restarts": 0, "uid": "u1"}, healthy, stable_seconds=25, settle_seconds=20)[0] == "recovered"
    assert judge({"restarts": 0, "uid": "u1"}, pod_snapshot(_pod(ready=False)), stable_seconds=99, settle_seconds=0)[0] == "pending"
    assert judge({"restarts": 0, "uid": "u1"}, pod_snapshot(_pod(restarts=1)), stable_seconds=99, settle_seconds=0)[0] == "pending"
    assert judge({}, pod_snapshot(_pod(phase="Succeeded")), stable_seconds=0, settle_seconds=0)[0] == "recovered"


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _watch(responses, clock, **cfg):
    calls = []

    def runner(argv):
        calls.append(" ".join(argv))
        key = " ".join(argv)
        value = responses(key, len(calls))
        if isinstance(value, Exception):
            raise value
        return json.dumps(value) if isinstance(value, dict) else value

    watch = RecoveryWatch(runner, RecoveryConfig(**cfg), clock=clock.time, sleep=clock.sleep)
    return watch, calls


def _drive(gen):
    events = []
    try:
        while True:
            events.append(next(gen))
    except StopIteration as stop:
        return events, stop.value


def test_terminating_target_recovers_when_gone():
    clock = _Clock()
    watch, calls = _watch(lambda key, n: RuntimeError('Error from server (NotFound): pods "api-1" not found'), clock, timeout_seconds=60, poll_seconds=5, settle_seconds=0)
    before = {"g1": {"exists": True, "deletion_timestamp": "x", "restarts": 0, "uid": "u1"}}
    events, summary = _drive(watch.run([{"group_id": "g1", "namespace": "demo", "pod": "api-1"}], before))
    assert summary["status"] == "recovered" and summary["targets"][0]["reason"] == "原 Pod 已完成删除"
    assert all(argv.startswith("kubectl get") for argv in calls)  # read-only


def test_controller_replacement_is_observed_and_settle_window_applies():
    clock = _Clock()

    def responses(key, n):
        if key == "kubectl get pod/api-old -n demo -o json":
            return RuntimeError("NotFound")
        if key == "kubectl get deployment/api -n demo -o json":
            return {"spec": {"selector": {"matchLabels": {"app": "api"}}}}
        if key.startswith("kubectl get pods -n demo -l app=api"):
            return {"items": [_pod("api-old", deleting=True), _pod("api-new", uid="u2", created="2026-10-16T11:00:00Z")]}
        raise AssertionError(key)

    watch, _ = _watch(responses, clock, timeout_seconds=120, poll_seconds=10, settle_seconds=20)
    target = {"group_id": "g1", "namespace": "demo", "pod": "api-old", "owner_kind": "Deployment", "owner_name": "api"}
    events, summary = _drive(watch.run([target], {"g1": {"exists": True, "restarts": 7, "uid": "u1"}}))
    assert summary["status"] == "recovered"
    assert summary["targets"][0]["after"]["pod"] == "api-new" and summary["targets"][0]["after"]["replaced"] == "api-old"
    assert events[0]["verdict"] == "pending" and "需稳定" in events[0]["reason"]
    assert events[-1]["verdict"] == "recovered" and summary["targets"][0]["elapsed_seconds"] >= 20


def test_timeout_is_reported_with_last_observation():
    clock = _Clock()
    watch, _ = _watch(lambda key, n: _pod(ready=False, restarts=n, waiting="CrashLoopBackOff"), clock, timeout_seconds=30, poll_seconds=10, settle_seconds=0)
    events, summary = _drive(watch.run([{"group_id": "g1", "namespace": "demo", "pod": "api-1"}], {"g1": {"exists": True, "restarts": 0, "uid": "u1"}}))
    assert summary["status"] == "not_recovered"
    item = summary["targets"][0]
    assert item["timed_out"] is True and "超时未恢复（30 秒）" in item["reason"]
    assert item["after"]["reason"] == "CrashLoopBackOff" and item["elapsed_seconds"] >= 30
    assert all(e["timeout_seconds"] == 30 for e in events)


def test_observation_failure_is_followup_not_success():
    clock = _Clock()
    watch, _ = _watch(lambda key, n: RuntimeError("Unauthorized"), clock, timeout_seconds=30, poll_seconds=5, settle_seconds=0)
    _, summary = _drive(watch.run([{"group_id": "g1", "namespace": "demo", "pod": "api-1"}], {"g1": {}}))
    assert summary["status"] == "needs_followup" and "无法观测" in summary["targets"][0]["reason"]


def test_config_bounds_and_disable():
    assert RecoveryConfig.from_config({}) is None
    assert RecoveryConfig.from_config({"recovery": {"timeout_seconds": 0}}) is None
    cfg = RecoveryConfig.from_config({"recovery": {"timeout_seconds": 99999, "poll_seconds": 0, "settle_seconds": "x"}})
    assert cfg == RecoveryConfig(timeout_seconds=3600, poll_seconds=1, settle_seconds=20)
