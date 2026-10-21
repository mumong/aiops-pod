"""Center-side job client: poll through tunnel errors, never resubmit (spec FR-017)."""

import pytest

from aiops_edge.clusters import Cluster
from aiops_edge.jobs_client import RemoteJobs, RemoteResultUnknown
from aiops_edge.tunnel import EdgeError

EDGE = Cluster(
    name="vc-942nkkozc8o5fyb9q3bznb1ws", access="xnet", uuid="99eea57d-4cbe-4047-a7a0-ced9c658316c"
)


class FakeTunnel:
    def __init__(self, polls):
        self.polls = list(polls)
        self.submits = []

    def request(self, cluster, path, payload=None, *, method="POST", timeout=None):
        if method == "POST" and path == "/v1/jobs":
            self.submits.append(payload)
            return {"job_id": "j1", "status": "running"}
        if path == "/healthz":
            item = self.polls.pop(0) if self.polls else {"version": "1"}
            if isinstance(item, Exception):
                raise item
            return item
        item = self.polls.pop(0) if self.polls else {"status": "running"}
        if isinstance(item, Exception):
            raise item
        return item


class Clock:
    def __init__(self):
        self.now = 0.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def make(polls):
    tunnel, clock = FakeTunnel(polls), Clock()
    return RemoteJobs(tunnel, clock=clock.time, sleep=clock.sleep, poll_seconds=2), tunnel, clock


def test_success_after_transient_tunnel_errors():
    jobs, tunnel, _ = make(
        [
            EdgeError("cluster_unreachable", "x"),
            {"status": "running"},
            EdgeError("timeout", "x"),
            {"status": "succeeded", "exit_code": 0, "stdout": "pod deleted", "stderr": ""},
        ]
    )
    out = jobs.run(
        EDGE,
        ["kubectl", "delete", "pod", "x"],
        key="r1:a1:execute",
        approval_id="ap1",
        timeout_s=60,
        deadline_s=600,
    )
    assert out == "pod deleted"
    assert len(tunnel.submits) == 1
    assert tunnel.submits[0] == {
        "idempotency_key": "r1:a1:execute",
        "argv": ["kubectl", "delete", "pod", "x"],
        "approval_id": "ap1",
        "timeout_s": 60,
    }


def test_failed_job_raises_with_stderr():
    jobs, _, _ = make([{"status": "failed", "exit_code": 1, "stdout": "", "stderr": "NotFound"}])
    with pytest.raises(RuntimeError, match="NotFound"):
        jobs.run(EDGE, ["kubectl", "delete", "pod", "x"], key="k", timeout_s=60, deadline_s=600)


def test_deadline_gives_unknown_and_no_resubmission():
    jobs, tunnel, clock = make([EdgeError("cluster_unreachable", "x")] * 1000)
    with pytest.raises(RemoteResultUnknown) as exc:
        jobs.run(EDGE, ["kubectl", "delete", "pod", "x"], key="k", timeout_s=60, deadline_s=120)
    assert "结果未知" in str(exc.value) and "j1" in str(exc.value)
    assert len(tunnel.submits) == 1
    assert clock.now >= 120


def test_unknown_status_from_runner_restart_is_unknown():
    jobs, _, _ = make([{"status": "unknown", "stderr": "runner 重启，结果未知"}])
    with pytest.raises(RemoteResultUnknown):
        jobs.run(EDGE, ["kubectl", "delete", "pod", "x"], key="k", timeout_s=60, deadline_s=600)


def test_policy_refusal_on_submit_is_a_plain_error():
    class Refusing(FakeTunnel):
        def request(self, cluster, path, payload=None, *, method="POST", timeout=None):
            raise EdgeError("policy_denied", "reboot", {"rule": "denied_executables"})

    jobs = RemoteJobs(Refusing([]), clock=Clock().time, sleep=lambda s: None)
    with pytest.raises(RuntimeError, match="denied_executables"):
        jobs.run(
            EDGE, ["kubectl", "exec", "x", "--", "reboot"], key="k", timeout_s=60, deadline_s=600
        )


def test_submit_retries_through_tunnel_errors_with_the_same_key():
    class Flaky(FakeTunnel):
        def __init__(self):
            super().__init__(
                [{"status": "succeeded", "exit_code": 0, "stdout": "ok", "stderr": ""}]
            )
            self.failures = 2

        def request(self, cluster, path, payload=None, *, method="POST", timeout=None):
            if method == "POST" and self.failures:
                self.failures -= 1
                self.submits.append(payload)
                raise EdgeError("cluster_unreachable", "x")
            return super().request(cluster, path, payload, method=method, timeout=timeout)

    tunnel, clock = Flaky(), Clock()
    jobs = RemoteJobs(tunnel, clock=clock.time, sleep=clock.sleep, poll_seconds=2)
    assert (
        jobs.run(EDGE, ["kubectl", "delete", "pod", "x"], key="same", timeout_s=60, deadline_s=600)
        == "ok"
    )
    assert {s["idempotency_key"] for s in tunnel.submits} == {"same"}


def test_reachable():
    jobs, _, _ = make([EdgeError("cluster_unreachable", "x")])
    assert jobs.reachable(EDGE) is False
    assert jobs.reachable(EDGE) is True
