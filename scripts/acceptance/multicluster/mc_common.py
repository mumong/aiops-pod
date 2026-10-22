"""Shared helpers for the multi-cluster acceptance scripts.

These scripts are operator/test tooling. They use ops-only kubeconfigs from
``$AIOPS_MC_KUBE_DIR`` (default ``~/.kube/aiops-mc``); nothing here is part of
the runtime path, which reaches edge clusters only through the xnet tunnel.
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

KUBE_DIR = Path(os.environ.get("AIOPS_MC_KUBE_DIR", str(Path.home() / ".kube" / "aiops-mc")))
CENTER_HOST = os.environ.get("AIOPS_MC_CENTER_HOST", "10.2.5.85")
VM_URL = os.environ.get("AIOPS_MC_VM_URL", f"http://{CENTER_HOST}:31500/select/0/prometheus")
VLOGS_URL = os.environ.get("AIOPS_MC_VLOGS_URL", f"http://{CENTER_HOST}:31700")
# Precision checks (P5-2): objects declared normal in deploy-edge/clusters.mc.yaml
# expected_states, and the xnet virtual nodes (named after the clusters).
DECLARED_NORMAL = (("xnet", "xnet-management-"),)
CLUSTER_NODES = (
    "vc-xnet-management",
    "vc-942nkkozc8o5fyb9q3bznb1ws",
    "vc-dluw0jousipr6h5co2bwpyqk2",
)
TUNNEL_URL = os.environ.get("AIOPS_MC_TUNNEL_URL", f"https://{CENTER_HOST}:30909/proxy")
EDGE_KUBECONFIGS = ("edge-88", "edge-89")
AGENT_ROLE_LABEL = "node-role.kubernetes.io/xnet-agent"
UUID_ANNOTATION = "xnet-cloud.agent/uuid"
SNAPSHOT_NAMESPACES = ("xnet", "monitor")

_results: List[Tuple[str, bool, str]] = []


def kubeconfig(name: str) -> str:
    path = KUBE_DIR / name
    if not path.is_file():
        sys.exit(f"missing ops kubeconfig {path}")
    return str(path)


def kubectl(name: str, *args: str, timeout: int = 30) -> str:
    out = subprocess.run(
        ["kubectl", "--kubeconfig", kubeconfig(name), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if out.returncode:
        raise RuntimeError(f"kubectl {' '.join(args)} on {name}: {out.stderr.strip()[:300]}")
    return out.stdout


def kubectl_json(name: str, *args: str) -> Dict[str, Any]:
    return json.loads(kubectl(name, *args, "-o", "json"))


def http_json(url: str, params: Optional[Dict[str, str]] = None, timeout: int = 20) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 - test tooling, fixed hosts
        return json.loads(resp.read().decode())


def http_lines(url: str, params: Dict[str, str], timeout: int = 20) -> List[Dict[str, Any]]:
    url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
        return [json.loads(line) for line in resp.read().decode().splitlines() if line.strip()]


def edge_clusters() -> List[Dict[str, str]]:
    """xnet virtual Nodes of edge clusters: name, uuid, ready."""
    nodes = kubectl_json("center", "get", "nodes", "-l", AGENT_ROLE_LABEL)["items"]
    clusters = []
    for node in nodes:
        meta = node["metadata"]
        uuid = (meta.get("annotations") or {}).get(UUID_ANNOTATION, "")
        if uuid == "xnet-management":
            continue
        ready = any(
            c["type"] == "Ready" and c["status"] == "True"
            for c in node["status"].get("conditions", [])
        )
        clusters.append({"name": meta["name"], "uuid": uuid, "ready": str(ready)})
    return sorted(clusters, key=lambda c: c["name"])


@contextmanager
def xnet_client_cert() -> Iterator[Tuple[str, str]]:
    """Materialise xnet's tunnel client cert from the center cluster into a temp dir."""
    secret = kubectl_json("center", "get", "secret", "xnet-client-cert", "-n", "xnet")["data"]
    with tempfile.TemporaryDirectory() as tmp:
        cert, key = Path(tmp, "cert.pem"), Path(tmp, "key.pem")
        cert.write_bytes(base64.b64decode(secret["cert.pem"]))
        key.write_bytes(base64.b64decode(secret["key.pem"]))
        key.chmod(0o600)
        yield str(cert), str(key)


def tunnel_get(
    uuid: str, address: str, cert: Optional[Tuple[str, str]], timeout: int = 25
) -> Tuple[int, bytes]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = (
        ssl.CERT_NONE
    )  # xnet serves a CN=localhost cert; we only test reachability here
    if cert:
        ctx.load_cert_chain(*cert)
    url = f"{TUNNEL_URL}?{urllib.parse.urlencode({'clientid': uuid, 'address': address})}"
    try:
        with urllib.request.urlopen(url, timeout=timeout, context=ctx) as resp:  # noqa: S310
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def check(case: str, ok: bool, evidence: str = "", unsure: bool = False) -> bool:
    """``unsure``: the evidence may include other runs (attribution by log window).

    Other runs can only add tool calls, so a pass stands; a failure is reported
    as INCONCLUSIVE (re-run when nobody else uses the env) and still not a pass.
    """
    if not ok and unsure:
        _results.append((case, False, "INCONCLUSIVE " + evidence))
        print(f"INCONCLUSIVE {case} {evidence}".rstrip(), flush=True)
        return False
    _results.append((case, ok, evidence))
    print(f"{'PASS' if ok else 'FAIL'} {case} {evidence}".rstrip(), flush=True)
    return ok


def finish() -> None:
    failed = [r for r in _results if not r[1]]
    print(f"\n{len(_results) - len(failed)}/{len(_results)} passed")
    sys.exit(1 if failed else 0)
