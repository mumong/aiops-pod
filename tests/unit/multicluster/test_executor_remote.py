"""Repair execution on a remote cluster (spec US5, FR-017, FR-018)."""

import shlex

import pytest

from app.core import multicluster
from app.core.remediation.approval import ApprovalStore
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.policy import CommandPolicy
from tests.unit.multicluster.test_scope_routing import CONFIG, EDGE88
from tests.unit.remediation.test_pod_executor import fixture

POLICY = CommandPolicy.from_config(
    {
        "denied_operations": ["edit"],
        "denied_executables": ["reboot"],
        "approval_required": {"executables": ["rm"]},
    }
)
CONTRACT = {
    "scope": "namespace",
    "namespaces": ["demo"],
    "clusters": [EDGE88],
    "cluster_mode": "single",
}


@pytest.fixture
def multi(tmp_path, monkeypatch):
    path = tmp_path / "clusters.yaml"
    path.write_text(CONFIG)
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(path))
    multicluster.reset()
    yield
    multicluster.reset()


class FakeJobs:
    def __init__(self, reachable=(True,), error=None):
        self.runs, self.reachable_answers, self.error = [], list(reachable), error

    def reachable(self, cluster):
        return (
            self.reachable_answers.pop(0)
            if len(self.reachable_answers) > 1
            else self.reachable_answers[0]
        )

    def run(self, cluster, argv, *, key, approval_id="", timeout_s=60, deadline_s=600):
        self.runs.append(
            {"cluster": cluster.name, "argv": argv, "key": key, "approval_id": approval_id}
        )
        if self.error:
            raise self.error
        return "ok"


def runner_with(calls):
    def runner(argv, cluster=None, approval_id=""):
        calls.append((argv, cluster))
        return "{}"

    return runner


def test_execute_stage_runs_as_remote_job_and_reads_go_through_the_shim(multi):
    draft, _, _, _ = fixture()
    calls, jobs = [], FakeJobs()
    events = list(
        PodRepairExecutor(ApprovalStore(), runner_with(calls), remote_jobs=jobs).run(
            "run1", draft, owner="alice", mode="auto", policy=POLICY, request_contract=CONTRACT
        )
    )
    assert events[-1]["status"] == "needs_followup", events[-1]
    assert jobs.runs == [
        {
            "cluster": EDGE88,
            "argv": shlex.split(draft["actions"][0]["execute_command"]),
            "key": "run1:a1:execute",
            "approval_id": "",
        }
    ]
    assert calls and all(cluster == EDGE88 for _, cluster in calls)  # verify stage via the shim


def test_approval_card_and_events_name_the_cluster(multi):
    draft, _, _, _ = fixture()
    store = ApprovalStore()
    stream = PodRepairExecutor(store, runner_with([]), remote_jobs=FakeJobs()).run(
        "run2", draft, owner="alice", mode="review", policy=POLICY, request_contract=CONTRACT
    )
    event = next(stream)
    assert event["type"] == "remediation_approval_required"
    assert event["payload"]["cluster"] == "edge-88" and event["cluster"] == "edge-88"
    store.resolve("run2", event["approval_id"], True, owner="alice")
    rest = list(stream)
    start = next(e for e in rest if e["type"] == "remediation_tool_start")
    assert start["cluster"] == "edge-88"


def test_approved_high_risk_command_carries_the_approval_id(multi):
    draft, _, _, _ = fixture()
    draft["actions"][0].update(
        execute_command="kubectl exec pod/api-1 -n demo -- rm -f /tmp/app.lock", verify_command=""
    )
    store, jobs = ApprovalStore(), FakeJobs()
    stream = PodRepairExecutor(store, runner_with([]), remote_jobs=jobs).run(
        "run3", draft, owner="alice", mode="auto", policy=POLICY, request_contract=CONTRACT
    )
    event = next(stream)
    store.resolve("run3", event["approval_id"], True, owner="alice")
    list(stream)
    assert jobs.runs[0]["approval_id"] == event["approval_id"]


def test_unknown_result_is_reported_not_retried(multi):
    from aiops_edge.jobs_client import RemoteResultUnknown

    draft, _, _, _ = fixture()
    jobs = FakeJobs(
        error=RemoteResultUnknown("命令已提交（任务 j1），在时限内无法确认结果，结果未知")
    )
    events = list(
        PodRepairExecutor(ApprovalStore(), runner_with([]), remote_jobs=jobs).run(
            "run4", draft, owner="alice", mode="auto", policy=POLICY, request_contract=CONTRACT
        )
    )
    assert len(jobs.runs) == 1
    assert events[-1]["status"] == "failed" and "结果未知" in events[-1]["reason"]
    assert events[-1].get("error_code") == "remote_result_unknown"


def test_offline_cluster_waits_before_executing(multi, monkeypatch):
    import app.core.remediation.pod_executor as pe

    monkeypatch.setattr(pe.time, "sleep", lambda s: None)
    draft, _, _, _ = fixture()
    jobs = FakeJobs(reachable=(False, False, True))
    events = list(
        PodRepairExecutor(ApprovalStore(), runner_with([]), remote_jobs=jobs).run(
            "run5", draft, owner="alice", mode="auto", policy=POLICY, request_contract=CONTRACT
        )
    )
    waits = [
        e
        for e in events
        if e.get("type") == "remediation_status" and "不可达" in e.get("message", "")
    ]
    assert waits and jobs.runs and events[-1]["status"] == "needs_followup"


def test_local_cluster_jobs_are_unchanged(multi):
    draft, _, _, _ = fixture()
    calls, jobs = [], FakeJobs()
    contract = {**CONTRACT, "clusters": ["vc-xnet-management"]}
    events = list(
        PodRepairExecutor(
            ApprovalStore(), lambda argv: calls.append(argv) or "{}", remote_jobs=jobs
        ).run("run6", draft, owner="alice", mode="auto", policy=POLICY, request_contract=contract)
    )
    assert events[-1]["status"] == "needs_followup" and jobs.runs == [] and calls


def test_job_surfaces_unreachable_note(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import app.core.remediation.pod_executor as module
    from tests.unit.remediation.test_jobs import setup

    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs._new_job("batch", owner, "d", {"group_id": "g1"})
    jobs.store.save(job["job_id"], owner, None, "plan", {"draft": fixture()[0]})
    notes = []

    class Executor:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, run_id, draft, **kwargs):
            yield {
                "type": "remediation_status",
                "run_id": run_id,
                "message": "集群 edge-88 当前不可达",
            }
            notes.append(jobs.detail(run_id, owner).get("status_note"))
            yield {
                "type": "remediation_finished",
                "run_id": run_id,
                "status": "blocked",
                "reason": "x",
            }

    monkeypatch.setattr(module, "PodRepairExecutor", Executor)
    jobs._execute(
        SimpleNamespace(workflow_config={"remediation": {"enabled": True, "mode": "auto"}}),
        owner,
        job,
    )
    assert notes == ["集群 edge-88 当前不可达"]
