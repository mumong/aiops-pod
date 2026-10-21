"""Edge runner async jobs: idempotent, persisted, honest after a restart (spec FR-017)."""

import json
import stat
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from aiops_edge import signing
from aiops_edge.runner.jobs import JobStore
from aiops_edge.runner.server import RunnerConfig, make_handler
from app.core.remediation.policy import CommandPolicy

KEY = b"j" * 32
FAKE = """#!/bin/sh
echo "ran $*" >> "$JOBLOG"
echo "done $*"
if [ "$2" = "slow" ]; then sleep 2; fi
"""


@pytest.fixture
def runner(tmp_path, monkeypatch):
    fake = tmp_path / "kubectl"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("JOBLOG", str(tmp_path / "joblog"))
    cfg = RunnerConfig(
        signing_key=KEY,
        policy=CommandPolicy.from_config(
            {
                "denied_operations": ["edit"],
                "denied_executables": ["reboot"],
                "approval_required": {"executables": ["rm"]},
            }
        ),
        kubectl=str(fake),
        kubeconfigs={"read": "/r", "write": "/w"},
        job_dir=str(tmp_path / "jobs"),
        version="t",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}", tmp_path
    server.shutdown()


def call(base, method, path, payload=None):
    body = b"" if payload is None else json.dumps(payload).encode()
    headers = signing.sign(KEY, method, path, body)
    req = urllib.request.Request(base + path, data=body or None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def wait_done(base, job_id):
    for _ in range(100):
        status, job = call(base, "GET", f"/v1/jobs/{job_id}")
        if job.get("status") != "running":
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


DELETE = ["kubectl", "delete", "pod", "x", "-n", "d"]


def test_submit_runs_once_and_is_idempotent(runner):
    base, tmp = runner
    s1, j1 = call(base, "POST", "/v1/jobs", {"idempotency_key": "job1:a1:execute", "argv": DELETE})
    s2, j2 = call(base, "POST", "/v1/jobs", {"idempotency_key": "job1:a1:execute", "argv": DELETE})
    assert s1 == 202 and s2 == 202 and j1["job_id"] == j2["job_id"]
    job = wait_done(base, j1["job_id"])
    assert (
        job["status"] == "succeeded"
        and job["exit_code"] == 0
        and "done delete pod x" in job["stdout"]
    )
    assert (tmp / "joblog").read_text().count("ran delete") == 1


def test_jobs_are_gated_like_sync_writes(runner):
    base, _ = runner
    rm = ["kubectl", "exec", "x", "-n", "d", "--", "rm", "-f", "/tmp/a"]
    status, body = call(base, "POST", "/v1/jobs", {"idempotency_key": "k-rm", "argv": rm})
    assert status == 403 and body["rule"] == "approval_required"
    status, body = call(
        base, "POST", "/v1/jobs", {"idempotency_key": "k-rm2", "argv": rm, "approval_id": "ap1"}
    )
    assert status == 202
    reboot = ["kubectl", "exec", "x", "--", "reboot"]
    status, body = call(
        base, "POST", "/v1/jobs", {"idempotency_key": "k-rb", "argv": reboot, "approval_id": "ap1"}
    )
    assert status == 403 and body["rule"] == "denied_executables"


def test_read_commands_are_not_jobs(runner):
    base, _ = runner
    status, body = call(
        base, "POST", "/v1/jobs", {"idempotency_key": "k-get", "argv": ["kubectl", "get", "pods"]}
    )
    assert status == 400


def test_missing_key_or_unknown_job(runner):
    base, _ = runner
    assert call(base, "POST", "/v1/jobs", {"argv": DELETE})[0] == 400
    assert call(base, "GET", "/v1/jobs/nope")[0] == 404


def test_store_survives_restart_and_reports_interrupted_jobs_as_unknown(tmp_path):
    store = JobStore(str(tmp_path))
    done = store.create("k1", ["kubectl", "delete", "pod", "a"], "")
    store.finish(
        done["job_id"], {"exit_code": 0, "stdout": "ok", "stderr": "", "truncated": False}
    )
    interrupted = store.create("k2", ["kubectl", "delete", "pod", "b"], "")
    reloaded = JobStore(str(tmp_path))
    assert reloaded.get(done["job_id"])["status"] == "succeeded"
    lost = reloaded.get(interrupted["job_id"])
    assert lost["status"] == "unknown" and "重启" in lost["stderr"]
    assert (
        reloaded.by_key("k2")["job_id"] == interrupted["job_id"]
    )  # never re-run under the same key


def test_failed_exit_code_is_failed(tmp_path):
    store = JobStore(str(tmp_path))
    job = store.create("k", ["kubectl", "delete", "pod", "a"], "")
    store.finish(
        job["job_id"], {"exit_code": 1, "stdout": "", "stderr": "NotFound", "truncated": False}
    )
    assert store.get(job["job_id"])["status"] == "failed"
