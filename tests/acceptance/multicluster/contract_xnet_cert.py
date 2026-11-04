#!/usr/bin/env python3
"""A16: the tunnel client certificate is AIOps's own, issued by xnet's registry API.

Run after make mc-init / deploy-mc, and after every xnet upgrade:
- Secret aiops-xnet-client-cert is the same in mcp and aiops, matches the local ops copy
  ($AIOPS_MC_KUBE_DIR/xnet-cert) and is NOT xnet-management's own xnet/xnet-client-cert;
- it chains to xnet's CA, is a clientAuth certificate with 30+ days left;
- the running MCP and AIOps pods mount exactly this certificate;
- with it, /proxy reaches our runner on every edge (signed /v1/kubectl included);
- issuing a fresh certificate through POST /api/v1/registry/certificate works and leaves
  the center's Nodes and every object in the xnet namespace unchanged (throwaway cert).
"""

from __future__ import annotations

import importlib.util
import json
import os
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("xnet_cert", ROOT / "deploy-edge/xnet_cert.py")
xnet_cert = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(xnet_cert)
sys.path.insert(0, str(ROOT))
from aiops_edge import signing  # noqa: E402

RUNNER = "http://aiops-edge-runner.aiops.svc:8090"
POD_MOUNTS = (("aiops", "deployment/aiops-copilot"), ("mcp", "deployment/mcp-server-manager"))


def write(directory: Path, files: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (directory / name).write_bytes(data)
    (directory / "key.pem").chmod(0o600)
    return directory


def snapshot() -> list:
    """Center Nodes and every xnet object we could have touched, with resourceVersions."""
    out = []
    for args in (("get", "nodes"), ("-n", "xnet", "get", "secret,configmap,deployment,service")):
        for item in mc.kubectl_json("center", *args)["items"]:
            meta = item["metadata"]
            out.append(
                (
                    item["kind"],
                    meta["name"],
                    meta.get("resourceVersion") if item["kind"] != "Node" else "",
                )
            )
    return sorted(out)


def proxy(cert_dir: Path, uuid: str, path: str, body: bytes = b"", method: str = "GET"):
    ctx = ssl.create_default_context(cafile=str(cert_dir / "ca.pem"))
    ctx.check_hostname = False  # xnet serves CN=localhost; trust comes from its CA
    ctx.load_cert_chain(str(cert_dir / "cert.pem"), str(cert_dir / "key.pem"))
    url = f"{mc.TUNNEL_URL}?{urllib.parse.urlencode({'clientid': uuid, 'address': RUNNER + path})}"
    headers = {"Content-Type": "application/json"}
    if method == "POST":
        key = mc.KUBE_DIR.joinpath("runner.key").read_bytes().strip()
        headers.update(signing.sign(key, method, path, body))
    request = urllib.request.Request(url, data=body or None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=25, context=ctx) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read()[:200].decode(errors="replace")}


def main() -> None:
    edges = mc.edge_clusters()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ours = {
            ns: mc.secret_data("center", ns, "aiops-xnet-client-cert") for ns in ("aiops", "mcp")
        }
        mc.check("A16-secret-same-in-mcp-and-aiops", ours["aiops"] == ours["mcp"])
        cert_dir = write(tmp / "ours", ours["aiops"])

        xnet_own = mc.secret_data("center", "xnet", "xnet-client-cert")["cert.pem"]
        (tmp / "xnet-own.pem").write_bytes(xnet_own)
        (tmp / "xnet-ca.pem").write_bytes(
            mc.secret_data("center", "xnet", "xnet-ca-cert")["cert.pem"]
        )
        mc.check("A16-not-xnet-managements-cert", ours["aiops"]["cert.pem"] != xnet_own)

        summary, problems = xnet_cert.inspect(cert_dir, not_same_as=tmp / "xnet-own.pem")
        mc.check("A16-usable-clientauth-30d", not problems, "; ".join(problems) or str(summary))
        mc.check(
            "A16-ca-is-xnets",
            ours["aiops"]["ca.pem"] == (tmp / "xnet-ca.pem").read_bytes(),
        )

        local = mc.KUBE_DIR / "xnet-cert"
        if (local / "cert.pem").is_file():
            meta = (
                json.loads((local / "meta.json").read_text())
                if (local / "meta.json").is_file()
                else {}
            )
            mc.check(
                "A16-matches-issued-local-copy",
                (local / "cert.pem").read_bytes() == ours["aiops"]["cert.pem"],
                f"clientid={meta.get('clientid', '?')} source={meta.get('source', '?')}",
            )

        expected = xnet_cert.fingerprint(cert_dir / "cert.pem")
        for ns, target in POD_MOUNTS:
            mounted = mc.kubectl(
                "center", "-n", ns, "exec", target, "--", "cat", "/etc/aiops-xnet/cert.pem"
            )
            (tmp / f"{ns}-mounted.pem").write_text(mounted)
            mc.check(
                f"A16-pod-mounts-it-{ns}",
                xnet_cert.fingerprint(tmp / f"{ns}-mounted.pem") == expected,
            )

        for edge in edges:
            status, body = proxy(cert_dir, edge["uuid"], "/healthz")
            mc.check(
                f"A16-proxy-healthz-{edge['name']}",
                status == 200 and body.get("api") == 1,
                f"http={status}",
            )
            payload = json.dumps(
                {
                    "argv": ["kubectl", "get", "ns", "aiops", "-o", "name"],
                    "mode": "read",
                    "timeout_s": 15,
                }
            ).encode()
            status, body = proxy(cert_dir, edge["uuid"], "/v1/kubectl", payload, method="POST")
            mc.check(
                f"A16-proxy-signed-kubectl-{edge['name']}",
                status == 200
                and body.get("exit_code") == 0
                and "namespace/aiops" in str(body.get("stdout")),
                f"http={status} exit={body.get('exit_code')} {body.get('error', '')}",
            )

        # A throwaway issuance proves the API path and that it changes nothing in xnet.
        account = mc.secret_data("center", "xnet", "xnet-account")
        api = os.environ.get("AIOPS_MC_XNET_API", f"http://{mc.CENTER_HOST}:30808")
        before = snapshot()
        data = xnet_cert.issue(
            api, account["username"].decode().strip(), account["password"].decode().strip()
        )
        xnet_cert.store(tmp / "probe", data, api)
        after = snapshot()
        mc.check("A16-issue-leaves-xnet-unchanged", before == after, f"objects={len(before)}")
        _, problems = xnet_cert.inspect(tmp / "probe")
        mc.check("A16-issued-cert-usable", not problems, "; ".join(problems))
        status, _ = proxy(tmp / "probe", edges[0]["uuid"], "/healthz")
        mc.check("A16-issued-cert-reaches-edge", status == 200, f"http={status}")
    mc.finish()


if __name__ == "__main__":
    main()
