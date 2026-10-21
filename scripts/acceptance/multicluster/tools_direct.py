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


# Calls the MCP handlers in-process inside the MCP Pod, through the same entry
# points the servers use (scope activation, result annotation).
TOOL_CALL = r"""
import json, sys
sys.path.insert(0, "/app")
from holmes_tools import aiops_observability_query as q
from holmes_tools import prometheus, kubernetes_core
from holmes_tools.server_adapter import call_text_tool
import cluster_scope
noop = lambda *a, **k: None
def text(handler, name, args):
    return call_text_tool("acceptance", name, args, handler, log_call=noop, log_result=noop)[0].text
import base64
CASES = json.loads(base64.b64decode("__CASES__"))
out = {}
for key, kind, name, args in CASES:
    if kind == "obs":
        out[key] = json.loads(q.call_tool(name, args))
    elif kind == "prom":
        out[key] = text(prometheus.call_tool, name, args)
    elif kind == "k8s":
        out[key] = text(kubernetes_core.call_tool, name, args)
    elif kind == "clusters":
        out[key] = json.loads(cluster_scope.list_clusters_text())
print(json.dumps(out, ensure_ascii=False))
"""


def run_tools(cases: list) -> dict:
    import base64

    blob = base64.b64encode(json.dumps(cases).encode()).decode()
    return pod_py(TOOL_CALL.replace("__CASES__", blob), timeout=180)


def edge_pod(kubeconfig: str, namespace: str) -> str:
    pods = mc.kubectl_json(
        kubeconfig, "get", "pods", "-n", namespace, "-l", "app.kubernetes.io/name=workload"
    )
    names = [p["metadata"]["name"] for p in pods["items"]]
    if not names:
        names = [
            p["metadata"]["name"]
            for p in mc.kubectl_json(kubeconfig, "get", "pods", "-n", namespace)["items"]
            if p["metadata"]["name"].startswith("workload")
        ]
    return names[0]


def phase_p1() -> None:
    p06 = edge_pod("edge-88", "aiops-case-06")
    p08 = edge_pod("edge-88", "aiops-case-08")
    twin = edge_pod(
        "edge-89", "aiops-case-06"
    )  # same namespace and workload name as p06, other cluster
    # The OOM container restarts constantly, so ask for its peak over the window, not the current sample.
    mem = (
        'max_over_time(container_memory_working_set_bytes{namespace="aiops-case-08",pod="%s",container="app"}[30m])'
        % p08
    )
    cases = [
        (
            "A1",
            "obs",
            "execute_pod_promql",
            {
                "cluster": "edge-88",
                "namespace": "aiops-case-08",
                "pod": p08,
                "purpose": "memory of the OOM case",
                "promql": mem,
                "query_type": "instant",
            },
        ),
        (
            "A2",
            "obs",
            "execute_pod_promql",
            {
                "cluster": "edge-88",
                "namespace": "aiops-case-08",
                "pod": p08,
                "purpose": "cross-cluster attempt",
                "promql": mem.replace("bytes{", 'bytes{cluster="%s",' % EDGE89, 1),
                "query_type": "instant",
            },
        ),
        (
            "A2b",
            "obs",
            "query_pod_topology",
            {
                "cluster": "edge-88",
                "namespace": "aiops-case-06",
                "pod": twin,
                "purpose": "other cluster's pod",
            },
        ),
        (
            "A3",
            "obs",
            "query_pod_logs",
            {
                "cluster": "edge-88",
                "namespace": "aiops-case-06",
                "pod": p06,
                "purpose": "why is it restarting",
                "window_minutes": 120,
            },
        ),
        (
            "A4",
            "obs",
            "query_pod_tracing",
            {
                "cluster": "edge-88",
                "namespace": "aiops-case-06",
                "pod": p06,
                "purpose": "slow requests",
            },
        ),
        (
            "A4b",
            "obs",
            "query_pod_topology",
            {
                "cluster": "edge-88",
                "namespace": "aiops-case-06",
                "pod": p06,
                "purpose": "owner and services",
            },
        ),
        ("A8", "clusters", "", {}),
        ("P1-1", "prom", "get_label_values", {"cluster": "edge-89", "label_name": "namespace"}),
        (
            "P1-1b",
            "prom",
            "execute_prometheus_instant_query",
            {"cluster": "center", "query": "count(up)"},
        ),
        (
            "P1-req",
            "obs",
            "query_pod_topology",
            {"namespace": "aiops-case-06", "pod": p06, "purpose": "no cluster"},
        ),
    ]
    r = run_tools(cases)
    if "A1" not in r:
        mc.check("P1-tools-ran", False, str(r)[:400])
        return
    a1 = r["A1"]
    mc.check(
        "A1-promql-on-edge",
        a1.get("ok")
        and a1.get("cluster") == EDGE88
        and a1.get("backend") == "victoriametrics"
        and a1.get("coverage") == "present",
        f"ok={a1.get('ok')} cluster={a1.get('cluster')} coverage={a1.get('coverage')}",
    )
    a2 = r["A2"]
    mc.check(
        "A2-cross-cluster-promql-empty",
        a2.get("coverage") in ("empty", None) and not a2.get("samples"),
        f"coverage={a2.get('coverage')} error={(a2.get('error') or {}).get('code')}",
    )
    a2b = r["A2b"]
    mc.check(
        "A2b-other-cluster-pod-not-found",
        not a2b.get("ok"),
        f"error={(a2b.get('error') or {}).get('code')}",
    )
    a3 = r["A3"]
    reasons = [s.get("reason") for s in a3.get("samples") or []]
    mc.check(
        "A3-pod-events-as-logs",
        a3.get("ok")
        and a3.get("log_source") == "k8s_events"
        and a3.get("coverage") == "partial"
        and "BackOff" in reasons
        and any(s.get("type") == "Warning" for s in a3.get("samples") or []),
        f"reasons={reasons[:6]}",
    )
    a4 = r["A4"]
    mc.check(
        "A4-tracing-capability-missing",
        (a4.get("error") or {}).get("code") == "capability_missing",
    )
    a4b = r["A4b"]
    mc.check(
        "A4b-topology-via-runner",
        a4b.get("ok") and a4b.get("cluster") == EDGE88,
        f"ok={a4b.get('ok')} {(a4b.get('error') or {}).get('message', '')[:100]}",
    )
    a8 = {c["name"]: c for c in r["A8"]["clusters"]}
    mc.check(
        "A8-list-clusters",
        len(a8) == 3
        and a8[EDGE88]["online"]
        and a8[EDGE89]["online"]
        and a8[EDGE88]["capabilities"]["logs"] == "k8s_events",
        " ".join(f"{n[:12]}={c['online']}" for n, c in a8.items()),
    )
    p11 = r["P1-1"]
    mc.check(
        "P1-1-label-values-scoped",
        "aiops-case-10" in p11 and "aiops-case-08" not in p11,
        p11[:160],
    )
    mc.check(
        "P1-1b-center-scoped",
        '"status":"success"' in r["P1-1b"].replace(" ", ""),
        r["P1-1b"][:120],
    )
    mc.check("P1-required", (r["P1-req"].get("error") or {}).get("code") == "cluster_required")

    # P1-2: our runner down (fault injection on our own component only).
    import subprocess
    import time

    kc = ["kubectl", "--kubeconfig", mc.kubeconfig("edge-88"), "-n", "aiops"]
    subprocess.run(
        [*kc, "scale", "deploy/aiops-edge-runner", "--replicas=0"], check=True, capture_output=True
    )
    subprocess.run(
        [*kc, "wait", "--for=delete", "pod", "-l", "app=aiops-edge-runner", "--timeout=60s"],
        capture_output=True,
    )
    try:
        started = time.monotonic()
        down = run_tools(
            [
                (
                    "k8s",
                    "k8s",
                    "kubectl_get_by_kind_in_namespace",
                    {"cluster": "edge-88", "kind": "pod", "namespace": "aiops-case-06"},
                ),
                (
                    "prom",
                    "prom",
                    "execute_prometheus_instant_query",
                    {"cluster": "edge-88", "query": "count(up)"},
                ),
            ]
        )
        elapsed = time.monotonic() - started
        mc.check(
            "P1-2-runner-down-k8s-unreachable",
            "cluster_unreachable" in down.get("k8s", ""),
            f"{down.get('k8s', '')[:120]} total={elapsed:.1f}s",
        )
        mc.check(
            "P1-2-metrics-still-available",
            '"status":"success"' in down.get("prom", "").replace(" ", ""),
        )
    finally:
        subprocess.run(
            [*kc, "scale", "deploy/aiops-edge-runner", "--replicas=1"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [*kc, "rollout", "status", "deploy/aiops-edge-runner", "--timeout=120s"],
            capture_output=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["p0", "p1"], required=True)
    args = parser.parse_args()
    {"p0": phase_p0, "p1": phase_p1}[args.phase]()
    mc.finish()


if __name__ == "__main__":
    main()
