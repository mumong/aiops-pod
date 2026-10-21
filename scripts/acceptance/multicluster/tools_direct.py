#!/usr/bin/env python3
"""L2 tool-level acceptance: run cases inside the center's MCP Pod (real runtime path).

The ops kubeconfig is used only to `kubectl exec` into the MCP Pod; every case
then runs with the Pod's own runtime configuration (shim -> xnet tunnel ->
edge runner), so this exercises exactly what the tools use.

    tools_direct.py --phase p0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

EDGE88 = "vc-942nkkozc8o5fyb9q3bznb1ws"
EDGE89 = "vc-dluw0jousipr6h5co2bwpyqk2"


def pod_sh(script: str, timeout: int = 60) -> tuple[int, str, str]:
    import subprocess

    out = subprocess.run(
        [
            "kubectl",
            "--kubeconfig",
            mc.kubeconfig("center"),
            "-n",
            "mcp",
            "exec",
            "deploy/mcp-server-manager",
            "--",
            "sh",
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return out.returncode, out.stdout, out.stderr


def pod_py(code: str, timeout: int = 60) -> dict:
    script = "cd /app/servers && python3 - <<'PYEOF'\n" + code + "\nPYEOF"
    rc, out, err = pod_sh(script, timeout)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"rc": rc, "stdout": out[-300:], "stderr": err[-300:]}


RAW_RUNNER = r"""
import json, ssl, time, urllib.request, urllib.parse
from aiops_edge import signing
from aiops_edge.clusters import load_config
cfg = load_config(); acc = cfg.xnet; edge = cfg.resolve("edge-88")
key = open(acc.signing_key_file, "rb").read().strip()
ctx = ssl.create_default_context(cafile=acc.ca_file); ctx.check_hostname = False
ctx.load_cert_chain(acc.cert_file, acc.key_file)
def call(body, headers):
    url = acc.proxy_url + "?" + urllib.parse.urlencode({"clientid": edge.uuid, "address": acc.runner_url + "/v1/kubectl"})
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
body = json.dumps({"argv": ["kubectl", "get", "ns"], "mode": "read"}).encode()
res = {}
res["unsigned"] = call(body, {})[0]
res["wrong_key"] = call(body, signing.sign(b"x" * 32, "POST", "/v1/kubectl", body))[0]
res["expired"] = call(body, signing.sign(key, "POST", "/v1/kubectl", body, now=time.time() - 120))[0]
h = signing.sign(key, "POST", "/v1/kubectl", body)
res["first"] = call(body, h)[0]
res["replay"] = call(body, h)[0]
wbody = json.dumps({"argv": ["kubectl", "delete", "pod", "x", "-n", "aiops"], "mode": "read"}).encode()
st, js = call(wbody, signing.sign(key, "POST", "/v1/kubectl", wbody))
res["write_as_read"] = [st, js.get("error")]
print(json.dumps(res))
"""


def phase_p0() -> None:
    rc, out, err = pod_sh(f"AIOPS_CLUSTER={EDGE88} kubectl get pods -A")
    mc.check(
        "P0-3-remote-get", rc == 0 and "aiops-edge-runner" in out, f"rc={rc} {err.strip()[:120]}"
    )

    rc, out, err = pod_sh(
        "AIOPS_CLUSTER=edge-88 kubectl get pods -A -o json | jq '.items | length'"
    )
    mc.check(
        "P0-4-alias-and-local-pipe",
        rc == 0 and out.strip().isdigit() and int(out) > 0,
        f"items={out.strip()}",
    )

    for case, cmd, word in (
        ("P0-5-follow", "kubectl logs -n aiops deploy/aiops-edge-runner -f", "follow"),
        ("P0-5-watch", "kubectl get pods -w", "watch"),
        (
            "P0-5-interactive",
            "kubectl exec -it -n aiops deploy/aiops-edge-runner -- sh",
            "interactive",
        ),
    ):
        rc, out, err = pod_sh(f"AIOPS_CLUSTER=edge-88 {cmd}", timeout=30)
        mc.check(case, rc == 1 and word in err, err.strip()[:120])

    raw = pod_py(RAW_RUNNER)
    mc.check("P0-6-unsigned", raw.get("unsigned") == 401, str(raw))
    mc.check("P0-6-wrong-key", raw.get("wrong_key") == 401)
    mc.check("P0-6-expired", raw.get("expired") == 401)
    mc.check("P0-6-replay", raw.get("first") == 200 and raw.get("replay") == 401)
    mc.check(
        "P0-7-write-as-read",
        raw.get("write_as_read") == [403, "mode_denied"],
        str(raw.get("write_as_read")),
    )

    rc, out, _ = pod_sh("kubectl get ns -o name")
    mc.check(
        "P0-8-local-unchanged", rc == 0 and "namespace/xnet" in out and "namespace/mcp" in out
    )

    rc, out, err = pod_sh(f"AIOPS_CLUSTER={EDGE89} kubectl get pods", timeout=40)
    mc.check(
        "P0-9-edge-without-runner-unreachable",
        rc == 1 and "cluster_unreachable" in err,
        err.strip()[:140],
    )

    rc, out, err = pod_sh("AIOPS_CLUSTER=edge-99 kubectl get pods")
    mc.check("P0-10-unknown-cluster", rc == 1 and "cluster_unknown" in err and "edge-88" in err)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["p0"], required=True)
    args = parser.parse_args()
    {"p0": phase_p0}[args.phase]()
    mc.finish()


if __name__ == "__main__":
    main()
