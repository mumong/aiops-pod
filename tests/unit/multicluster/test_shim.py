"""kubectl shim: local passthrough, remote forwarding, refusal messages (spec §4.3)."""

import io

import pytest

from aiops_edge import shim
from aiops_edge.clusters import load_config
from aiops_edge.tunnel import EdgeError

CONFIG = """
clusters:
  center: vc-xnet-management
  items:
    - name: vc-xnet-management
      aliases: [center]
      access: local
    - name: vc-942nkkozc8o5fyb9q3bznb1ws
      aliases: [edge-88]
      access: xnet
  access:
    xnet:
      proxy_url: https://x/proxy
      runner_url: http://r:8090
"""


class FakeTunnel:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    def request(self, cluster, path, payload, timeout=None):
        self.calls.append((cluster.name, path, payload, timeout))
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def cfg(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(CONFIG)
    return load_config(str(p))


def run(argv, env, cfg, tunnel=None, execs=None):
    out, err = io.StringIO(), io.StringIO()
    code = shim.main(
        argv,
        env=env,
        config=cfg,
        tunnel_factory=lambda: tunnel,
        exec_local=lambda real, args: execs.append((real, args)) or 0,
        stdout=out,
        stderr=err,
    )
    return code, out.getvalue(), err.getvalue()


def test_no_cluster_runs_real_kubectl(cfg):
    execs = []
    code, _, _ = run(["kubectl", "get", "ns"], {}, cfg, execs=execs)
    assert code == 0 and execs == [(shim.REAL_KUBECTL, ["kubectl", "get", "ns"])]


def test_local_cluster_and_center_alias_run_real_kubectl(cfg):
    for name in ("local", "center", "vc-xnet-management"):
        execs = []
        run(["kubectl", "get", "ns"], {"AIOPS_CLUSTER": name}, cfg, execs=execs)
        assert execs, name


def test_remote_cluster_is_forwarded(cfg):
    tunnel = FakeTunnel(
        result={"exit_code": 0, "stdout": "NAME\npod-a\n", "stderr": "", "truncated": False}
    )
    code, out, _ = run(
        ["kubectl", "get", "pods", "-A"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel
    )
    assert code == 0 and out == "NAME\npod-a\n"
    name, path, payload, timeout = tunnel.calls[0]
    assert name == "vc-942nkkozc8o5fyb9q3bznb1ws" and path == "/v1/kubectl"
    assert payload == {
        "argv": ["kubectl", "get", "pods", "-A"],
        "mode": "read",
        "timeout_s": 15,
        "compress": True,
    }


def test_remote_exit_code_and_stderr_preserved(cfg):
    tunnel = FakeTunnel(
        result={"exit_code": 1, "stdout": "", "stderr": "NotFound\n", "truncated": False}
    )
    code, _, err = run(
        ["kubectl", "get", "pod", "x"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel
    )
    assert code == 1 and "NotFound" in err


def test_truncation_is_announced(cfg):
    tunnel = FakeTunnel(result={"exit_code": 0, "stdout": "x", "stderr": "", "truncated": True})
    _, _, err = run(["kubectl", "logs", "p"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel)
    assert "truncated" in err


def test_refused_arguments_never_reach_tunnel(cfg):
    tunnel = FakeTunnel(result={})
    code, _, err = run(
        ["kubectl", "logs", "p", "-f"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel
    )
    assert code == 1 and "follow" in err and tunnel.calls == []


def test_unknown_cluster(cfg):
    code, _, err = run(["kubectl", "get", "pods"], {"AIOPS_CLUSTER": "edge-99"}, cfg)
    assert code == 1 and "cluster_unknown" in err and "edge-88" in err


def test_edge_error_is_reported_with_code(cfg):
    tunnel = FakeTunnel(error=EdgeError("cluster_unreachable", "The side client is not online"))
    code, _, err = run(
        ["kubectl", "get", "pods"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel
    )
    assert code == 1 and "cluster_unreachable" in err


def test_approval_id_is_forwarded(cfg):
    tunnel = FakeTunnel(result={"exit_code": 0, "stdout": "", "stderr": "", "truncated": False})
    run(
        ["kubectl", "exec", "p", "--", "rm", "/tmp/a"],
        {"AIOPS_CLUSTER": "edge-88", "AIOPS_APPROVAL_ID": "ab12"},
        cfg,
        tunnel=tunnel,
    )
    assert tunnel.calls[0][2]["approval_id"] == "ab12" and tunnel.calls[0][2]["mode"] == "exec"


def test_full_path_argv0_is_normalised(cfg):
    # Invoked through PATH, argv[0] is the shim's absolute path.
    tunnel = FakeTunnel(result={"exit_code": 0, "stdout": "ok", "stderr": "", "truncated": False})
    code, out, _ = run(
        ["/usr/local/bin/kubectl", "get", "pods"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel
    )
    assert code == 0 and out == "ok"
    assert tunnel.calls[0][2]["argv"] == ["kubectl", "get", "pods"]


def test_shim_requests_and_decodes_compressed_output(cfg):
    import base64
    import gzip

    blob = lambda s: base64.b64encode(gzip.compress(s.encode())).decode()  # noqa: E731
    tunnel = FakeTunnel(
        result={
            "exit_code": 0,
            "encoding": "gzip+base64",
            "stdout_b64": blob("big json"),
            "stderr_b64": blob(""),
            "truncated": False,
        }
    )
    code, out, _ = run(
        ["kubectl", "get", "pods", "-o", "json"], {"AIOPS_CLUSTER": "edge-88"}, cfg, tunnel=tunnel
    )
    assert code == 0 and out == "big json"
    assert tunnel.calls[0][2]["compress"] is True
