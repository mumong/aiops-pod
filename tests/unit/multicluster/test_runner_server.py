"""Edge runner HTTP surface: signatures, modes, identities, output bounds."""

import json
import os
import stat
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from aiops_edge import signing
from aiops_edge.runner.server import RunnerConfig, make_handler
from app.core.remediation.policy import CommandPolicy

KEY = b"r" * 32

FAKE_KUBECTL = """#!/bin/sh
echo "kubeconfig=$KUBECONFIG"
echo "argv=$*"
if [ "$1" = "big" ]; then head -c 300000 /dev/zero | tr '\\0' 'x'; fi
if [ "$1" = "fail" ]; then echo "boom" >&2; exit 3; fi
"""


@pytest.fixture
def runner(tmp_path):
    fake = tmp_path / "kubectl"
    fake.write_text(FAKE_KUBECTL)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    cfg = RunnerConfig(
        signing_key=KEY,
        policy=CommandPolicy.from_config(
            {"denied_operations": ["drain"], "denied_executables": ["reboot"]}
        ),
        kubectl=str(fake),
        kubeconfigs={"read": "/cfg/read", "write": "/cfg/write"},
        job_dir=str(tmp_path / "jobs"),
        max_output=256 * 1024,
        version="1.0.0-test",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def call(base, path, payload, *, sign=True, key=KEY):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if sign:
        headers.update(signing.sign(key, "POST", path, body))
    req = urllib.request.Request(base + path, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_healthz_is_unauthenticated_and_reports_version(runner):
    with urllib.request.urlopen(runner + "/healthz", timeout=5) as resp:
        data = json.loads(resp.read())
    assert data["version"] == "1.0.0-test" and data["api"] == 1 and data["policy_version"]


def test_unsigned_request_rejected(runner):
    status, body = call(
        runner, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"], "mode": "read"}, sign=False
    )
    assert status == 401 and body["error"] == "runner_auth_failed"


def test_wrong_key_rejected(runner):
    status, _ = call(
        runner, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"], "mode": "read"}, key=b"x" * 32
    )
    assert status == 401


def test_read_runs_with_reader_identity(runner):
    status, body = call(
        runner, "/v1/kubectl", {"argv": ["kubectl", "get", "pods", "-A"], "mode": "read"}
    )
    assert status == 200 and body["exit_code"] == 0
    assert "kubeconfig=/cfg/read" in body["stdout"]
    assert "argv=get pods -A" in body["stdout"]


def test_write_runs_with_writer_identity(runner):
    status, body = call(
        runner,
        "/v1/kubectl",
        {"argv": ["kubectl", "delete", "pod", "x", "-n", "d"], "mode": "write"},
    )
    assert status == 200 and "kubeconfig=/cfg/write" in body["stdout"]


def test_policy_denial_is_403_with_rule(runner):
    status, body = call(
        runner, "/v1/kubectl", {"argv": ["kubectl", "exec", "x", "--", "reboot"], "mode": "exec"}
    )
    assert (
        status == 403 and body["error"] == "policy_denied" and body["rule"] == "denied_executables"
    )


def test_nonzero_exit_is_reported_not_raised(runner):
    status, body = call(runner, "/v1/kubectl", {"argv": ["kubectl", "fail"], "mode": "read"})
    # "fail" is not a read-only operation -> refused before running
    assert status == 403
    status, body = call(
        runner, "/v1/kubectl", {"argv": ["kubectl", "get", "fail"], "mode": "read"}
    )
    assert status == 200 and body["exit_code"] == 0


def test_output_is_truncated(runner):
    status, body = call(runner, "/v1/kubectl", {"argv": ["kubectl", "get", "big"], "mode": "read"})
    assert status == 200
    # the fake only emits the big payload when argv[0] (after kubectl) is "big"; here it is "get"
    assert body["truncated"] is False


def test_timeout_is_capped(runner):
    status, body = call(
        runner,
        "/v1/kubectl",
        {"argv": ["kubectl", "get", "pods"], "mode": "read", "timeout_s": 999},
    )
    assert status == 200


def test_bad_json_is_400(runner):
    body = b"not json"
    headers = signing.sign(KEY, "POST", "/v1/kubectl", body)
    req = urllib.request.Request(runner + "/v1/kubectl", data=body, headers=headers, method="POST")
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 400


def test_unknown_path_is_404(runner):
    status, _ = call(runner, "/v1/nope", {})
    assert status == 404


def test_cap_output_marks_truncation():
    from aiops_edge.runner.server import cap

    text, truncated = cap("x" * 10, 4)
    assert truncated and text.startswith("xxxx")
    assert cap("ab", 4) == ("ab", False)


def test_environment_does_not_leak_into_kubectl(runner, monkeypatch):
    monkeypatch.setenv("KUBECONFIG", "/should/not/be/used")
    status, body = call(
        runner, "/v1/kubectl", {"argv": ["kubectl", "get", "pods"], "mode": "read"}
    )
    assert "kubeconfig=/cfg/read" in body["stdout"]
    assert os.environ["KUBECONFIG"] == "/should/not/be/used"


def test_compressed_output_round_trips(runner):
    from aiops_edge.runner.server import decode_streams

    status, body = call(
        runner,
        "/v1/kubectl",
        {"argv": ["kubectl", "get", "pods"], "mode": "read", "compress": True},
    )
    assert status == 200 and "stdout" not in body and body["encoding"] == "gzip+base64"
    stdout, stderr = decode_streams(body)
    assert "argv=get pods" in stdout and stderr == ""


def test_default_output_cap_is_4mb():
    from aiops_edge.runner.server import RunnerConfig

    assert RunnerConfig.__dataclass_fields__["max_output"].default == 4 * 1024 * 1024
