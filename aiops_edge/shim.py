"""``kubectl`` shim: run locally, or forward to an edge cluster's runner.

Installed in place of kubectl in the AIOps and MCP images. With
``AIOPS_CLUSTER`` unset (or naming the local/center cluster) it execs the real
kubectl, so single-cluster behaviour is unchanged. Otherwise the argv is sent
through the xnet tunnel and stdout, stderr and the exit code are reproduced,
so existing tool templates (including pipes into jq) keep working.
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Mapping, Optional, TextIO

from aiops_edge import kubectl_args
from aiops_edge.clusters import EdgeConfig, load_config
from aiops_edge.streams import decode_streams
from aiops_edge.tunnel import MAX_CALL_SECONDS, EdgeError, TunnelClient

REAL_KUBECTL = os.environ.get("AIOPS_REAL_KUBECTL", "/usr/local/bin/kubectl.real")
CLUSTER_ENV = "AIOPS_CLUSTER"
APPROVAL_ENV = "AIOPS_APPROVAL_ID"


def _exec_real(real: str, argv: List[str]) -> int:
    os.execv(real, [real, *argv[1:]])
    return 127  # not reached


def main(
    argv: List[str],
    *,
    env: Optional[Mapping[str, str]] = None,
    config: Optional[EdgeConfig] = None,
    tunnel_factory: Optional[Callable[[], TunnelClient]] = None,
    exec_local: Callable[[str, List[str]], int] = _exec_real,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    env = os.environ if env is None else env
    argv = ["kubectl", *argv[1:]]  # argv[0] may be the shim's absolute path
    target = (env.get(CLUSTER_ENV) or "").strip()
    if not target:
        return exec_local(REAL_KUBECTL, argv)
    config = config or load_config()
    cluster = config.resolve(target)
    if cluster is None:
        stderr.write(
            f"aiops: cluster_unknown: no cluster named {target!r}; available: {', '.join(config.names())}\n"
        )
        return 1
    if not cluster.remote:
        return exec_local(REAL_KUBECTL, argv)
    mode, reason = kubectl_args.classify(argv)
    if mode is None:
        stderr.write(f"aiops: refused on cluster {cluster.name}: {reason}\n")
        return 1
    payload = {"argv": list(argv), "mode": mode, "timeout_s": MAX_CALL_SECONDS, "compress": True}
    approval = (env.get(APPROVAL_ENV) or "").strip()
    if approval:
        payload["approval_id"] = approval
    try:
        tunnel = tunnel_factory() if tunnel_factory else TunnelClient.from_access(config.xnet)
        result = tunnel.request(cluster, "/v1/kubectl", payload, timeout=MAX_CALL_SECONDS)
    except EdgeError as exc:
        rule = exc.detail.get("rule")
        stderr.write(
            f"aiops: {exc.code} on cluster {cluster.name}: {exc.message}"
            + (f" (rule {rule})" if rule else "")
            + "\n"
        )
        return 1
    out, err = decode_streams(result)
    stdout.write(out)
    if result.get("truncated"):
        err += f"aiops: output truncated by the edge runner on cluster {cluster.name}\n"
    stderr.write(err)
    return int(result.get("exit_code") or 0)


def entrypoint() -> None:
    sys.exit(main(sys.argv))


if __name__ == "__main__":
    entrypoint()
