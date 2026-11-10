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


# Each MCP server process gets its own env from the mounted mcp_config.yaml (e.g. the
# AIOPS_ES_* namespaces of aiops-observability-query); apply it before running a case.
SERVER_ENV = r"""
import os, yaml
for _srv in (yaml.safe_load(open(os.environ.get("MCP_CONFIG_PATH", "/app/config/mcp_config.yaml"))) or {}).get("basicmcp") or []:
    if _srv.get("name") == "aiops-observability-query":
        os.environ.update({k: str(v) for k, v in (_srv.get("env") or {}).items()})
"""


def pod_py(code: str, timeout: int = 60) -> dict:
    script = "cd /app/servers && python3 - <<'PYEOF'\n" + SERVER_ENV + code + "\nPYEOF"
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

    # Edge-89 runs a runner now; take it away for this case only (our component, restored after).
    with mc.runner_down("edge-89"):
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
        and a8[EDGE88]["data"]["logs"] == "k8s_events",  # key "data" since MCP 8.0.6
        " ".join(f"{n[:12]}={c['online']}" for n, c in a8.items()),
    )
    # Expected from the live placement (cases move between runs): a case namespace only on
    # edge-89 must be listed, one only on edge-88 must not.
    case_ns = {
        edge: {
            n["metadata"]["name"]
            for n in mc.kubectl_json(edge, "get", "namespaces")["items"]
            if n["metadata"]["name"].startswith("aiops-case-")
        }
        for edge in ("edge-88", "edge-89")
    }
    only89 = sorted(case_ns["edge-89"] - case_ns["edge-88"])
    only88 = sorted(case_ns["edge-88"] - case_ns["edge-89"])
    values = set(json.loads(r["P1-1"]).get("data") or [])
    mc.check(
        "P1-1-label-values-scoped",
        bool(only89) and bool(only88) and set(only89) <= values and not values & set(only88),
        f"edge-89 only={only89} edge-88 only={only88} returned={sorted(v for v in values if v.startswith('aiops-case-'))}",
    )
    mc.check(
        "P1-1b-center-scoped",
        '"status":"success"' in r["P1-1b"].replace(" ", ""),
        r["P1-1b"][:120],
    )
    mc.check("P1-required", (r["P1-req"].get("error") or {}).get("code") == "cluster_required")

    # P1-2: our runner down (fault injection on our own component only).
    import time

    with mc.runner_down("edge-88"):
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


def aiops_py(code: str, timeout: int = 300) -> dict:
    """Run Python inside the center's AIOps Pod (it has the full aiops_edge client and config)."""
    import subprocess

    out = subprocess.run(
        [
            "kubectl",
            "--kubeconfig",
            mc.kubeconfig("center"),
            "-n",
            "aiops",
            "exec",
            "-i",
            "deploy/aiops-copilot",
            "-c",
            "aiops-copilot",
            "--",
            "python",
            "-",
        ],
        input=code,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    try:
        return json.loads(out.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"rc": out.returncode, "stdout": out.stdout[-300:], "stderr": out.stderr[-400:]}


P3_GATES = r"""
import json, uuid
from aiops_edge.clusters import load_config
from aiops_edge.tunnel import TunnelClient, EdgeError
cfg = load_config(); edge = cfg.resolve("edge-88"); t = TunnelClient.from_access(cfg.xnet)
POD, NS = "__POD__", "aiops-case-09"
def call(path, payload):
    try:
        return {"ok": True, **t.request(edge, path, payload)}
    except EdgeError as e:
        return {"ok": False, "code": e.code, "rule": e.detail.get("rule")}
out = {}
out["A10b"] = call("/v1/kubectl", {"argv": ["kubectl", "exec", POD, "-n", NS, "--", "reboot"], "mode": "exec"})
out["touch"] = call("/v1/kubectl", {"argv": ["kubectl", "exec", POD, "-n", NS, "--", "touch", "/dev/shm/aiops-mc-a10c"], "mode": "exec"})
out["A10c-file-before"] = call("/v1/kubectl", {"argv": ["kubectl", "exec", POD, "-n", NS, "--", "ls", "/dev/shm"], "mode": "exec"})
rm = ["kubectl", "exec", POD, "-n", NS, "--", "rm", "-f", "/dev/shm/aiops-mc-a10c"]
out["A10c-no-approval"] = call("/v1/kubectl", {"argv": rm, "mode": "exec"})
out["A10c-with-approval"] = call("/v1/kubectl", {"argv": rm, "mode": "exec", "approval_id": "acceptance-a10c"})
out["A10c-file-after"] = call("/v1/kubectl", {"argv": ["kubectl", "exec", POD, "-n", NS, "--", "ls", "/dev/shm"], "mode": "exec"})
key = "acceptance-a11c-" + uuid.uuid4().hex[:8]
job = {"idempotency_key": key, "argv": ["kubectl", "annotate", "pod", POD, "-n", NS, "aiops-mc-a11c=" + key[-8:], "--overwrite"]}
out["A11c-1"] = call("/v1/jobs", job)
out["A11c-2"] = call("/v1/jobs", job)
out["A11c-key"] = key
print(json.dumps(out, ensure_ascii=False))
"""

P3_LOST = r"""
import json, uuid
from aiops_edge.clusters import load_config
from aiops_edge.jobs_client import RemoteJobs, RemoteResultUnknown
from aiops_edge.tunnel import TunnelClient
cfg = load_config(); edge = cfg.resolve("edge-88")
jobs = RemoteJobs(TunnelClient.from_access(cfg.xnet), poll_seconds=2)
try:
    jobs.run(edge, ["kubectl", "exec", "__POD__", "-n", "aiops-case-09", "--", "sleep", "45"],
             key="acceptance-a12d-" + uuid.uuid4().hex[:8], timeout_s=60, deadline_s=240)
    print(json.dumps({"result": "finished"}))
except RemoteResultUnknown as e:
    print(json.dumps({"result": "unknown", "message": str(e)}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"result": "error", "message": str(e)}, ensure_ascii=False))
"""


def phase_p3() -> None:
    import subprocess
    import threading
    import time

    driver = next(
        p["metadata"]["name"]
        for p in mc.kubectl_json("edge-88", "get", "pods", "-n", "aiops-case-09")["items"]
        if p["metadata"]["name"].startswith("traffic-driver")
    )
    r = aiops_py(P3_GATES.replace("__POD__", driver))
    if "A10b" not in r:
        mc.check("P3-tools-ran", False, str(r)[:400])
        return
    mc.check(
        "A10b-runner-refuses-reboot",
        r["A10b"].get("code") == "policy_denied" and r["A10b"].get("rule") == "denied_executables",
        str(r["A10b"]),
    )
    mc.check(
        "A10c-rm-needs-approval",
        r["A10c-no-approval"].get("rule") == "approval_required",
        str(r["A10c-no-approval"]),
    )
    mc.check(
        "A10c-rm-with-approval-runs",
        r["touch"].get("exit_code") == 0
        and "aiops-mc-a10c" in r["A10c-file-before"].get("stdout", "")
        and r["A10c-with-approval"].get("exit_code") == 0
        and "aiops-mc-a10c" not in r["A10c-file-after"].get("stdout", ""),
        f"touch={r['touch'].get('exit_code')} rm={r['A10c-with-approval'].get('exit_code')}",
    )
    same = r["A11c-1"].get("job_id") and r["A11c-1"].get("job_id") == r["A11c-2"].get("job_id")
    time.sleep(5)
    logs = subprocess.run(
        [
            "kubectl",
            "--kubeconfig",
            mc.kubeconfig("edge-88"),
            "-n",
            "aiops",
            "logs",
            "-l",
            "app=aiops-edge-runner",
            "--tail=-1",
        ],
        capture_output=True,
        text=True,
    ).stdout
    # unique key: all runner Pods, no time window (Pods get replaced; node clocks skew)
    executed = sum(
        1 for line in logs.splitlines() if r["A11c-key"] in line and "exit_code" in line
    )
    mc.check(
        "A11c-idempotent-job",
        same and executed == 1,
        f"job={r['A11c-1'].get('job_id')} executions={executed}",
    )

    # A12d + P3-1: delete the runner Pod while a job runs (our component only).
    result = {}
    worker = threading.Thread(
        target=lambda: result.update(aiops_py(P3_LOST.replace("__POD__", driver), 400))
    )
    worker.start()
    time.sleep(12)
    kc = ["kubectl", "--kubeconfig", mc.kubeconfig("edge-88"), "-n", "aiops"]
    subprocess.run(
        [*kc, "delete", "pod", "-l", "app=aiops-edge-runner", "--wait=false"], capture_output=True
    )
    worker.join(420)
    mc.check(
        "A12d-lost-job-is-unknown",
        result.get("result") == "unknown" and "不会自动重新提交" in result.get("message", ""),
        str(result)[:200],
    )
    subprocess.run(
        [*kc, "rollout", "status", "deploy/aiops-edge-runner", "--timeout=180s"],
        capture_output=True,
    )
    rc, out, err = pod_sh(f"AIOPS_CLUSTER={EDGE88} kubectl get pods -n aiops-case-09")
    mc.check("P3-1-runner-recovers", rc == 0 and "traffic-driver" in out, err.strip()[:120])


# efk profile: center Prometheus / Elasticsearch / DeepFlow hold every cluster's data.
# Each check asks one cluster and verifies, from the data itself, that nothing of
# another cluster comes back. Clusters and target Pods are read from the running
# config and the clusters themselves, not hard-coded.
EFK_RAW = r"""
import json
import cluster_scope
from aiops_observability.query import logs as L, tracing as T
from aiops_observability.collectors import deepflow as D
cfg = cluster_scope.config()
out = {}
for name in cfg.clusters:
    with cluster_scope.activate({"cluster": name}) as scope:
        c = scope.cluster.name
        # ES: every hit of a namespace-wide search belongs to the active cluster.
        body = {"size": 200, "_source": ["cluster"], "query": {"range": {"@timestamp": {"gte": "now-30m"}}}}
        hits = L._hits(L._query_elasticsearch(body))
        es = sorted({(h.get("_source") or {}).get("cluster") for h in hits})
        # DeepFlow: flows whose Pod side is in this cluster carry only this cluster's name.
        sql = ("SELECT dictGetOrDefault('flow_tag.pod_cluster_map','name',toUInt64(pod_cluster_id_1),'') AS c, count() AS n "
               "FROM flow_log.l7_flow_log WHERE time > now() - INTERVAL 30 MINUTE AND "
               + "1 = 1" + D.cluster_condition(1) + " GROUP BY c FORMAT JSON")
        df = T._query_deepflow(sql)
        out[c] = {"es_hits": len(hits), "es_clusters": es,
                  "df": {r["c"]: int(r["n"]) for r in df.get("data", [])}, "df_error": df.get("error")}
# Control: the same queries with no active cluster see several clusters, so the
# per-cluster results above are the filter's doing, not a single-cluster backend.
body = {"size": 0, "query": {"range": {"@timestamp": {"gte": "now-30m"}}},
        "aggs": {"c": {"terms": {"field": "cluster", "size": 100}}}}
es = L._query_elasticsearch(body)
df = T._query_deepflow("SELECT dictGetOrDefault('flow_tag.pod_cluster_map','name',toUInt64(pod_cluster_id_1),'') AS c, "
                       "count() AS n FROM flow_log.l7_flow_log WHERE time > now() - INTERVAL 30 MINUTE AND c != '' "
                       "GROUP BY c FORMAT JSON")
out["_unscoped"] = {"es": sorted(b["key"] for b in es.get("aggregations", {}).get("c", {}).get("buckets", [])),
                    "df": sorted(r["c"] for r in df.get("data", []))}
print(json.dumps(out))
"""


def _cluster_pods() -> dict:
    """{cluster name: (kubeconfig name, namespace, pod)} from list_clusters and each cluster's Pods."""
    listed = run_tools([("L", "clusters", "", {})])["L"]
    pods = {}
    for entry in listed["clusters"]:
        # ops kubeconfigs are named after a cluster alias (center, edge-88, ...)
        alias = next(
            (a for a in ["center", *entry["aliases"]] if (mc.KUBE_DIR / a).is_file()), None
        )
        if entry["role"] != "center" and alias == "center":
            alias = next((a for a in entry["aliases"] if (mc.KUBE_DIR / a).is_file()), None)
        if alias is None:
            continue
        items = mc.kubectl_json(alias, "get", "pods", "-A")["items"]
        running = [p for p in items if p["status"].get("phase") == "Running"]

        def rank(p, _ns=("aiops-case-", "aiops")):
            ns = p["metadata"]["namespace"]
            return (
                0 if ns.startswith(_ns[0]) else 1 if ns == _ns[1] else 2,
                ns,
                p["metadata"]["name"],
            )

        for p in sorted(running, key=rank)[:20]:
            ns, pod = p["metadata"]["namespace"], p["metadata"]["name"]
            try:
                lines = mc.kubectl(
                    alias, "logs", "-n", ns, pod, "--all-containers", "--since=30m", timeout=30
                )
            except RuntimeError:
                continue
            if lines.strip():
                pods[entry["name"]] = (alias, ns, pod)
                break
    return {"listed": listed, "pods": pods}


def phase_efk() -> None:
    found = _cluster_pods()
    listed, pods = found["listed"], found["pods"]
    clusters = [c["name"] for c in listed["clusters"]]
    for c in listed["clusters"]:
        mc.check(
            f"EFK-0-{c['name']}-listed",
            c["online"]
            and c["data"] == {"metrics": True, "logs": "container_logs", "traces": True},
            json.dumps(c["data"]),
        )
    cases = []
    for name in clusters:
        others = [o for o in clusters if o != name]
        cases += [
            (
                f"up:{name}",
                "prom",
                "execute_prometheus_instant_query",
                {"cluster": name, "query": "up"},
            ),
            (
                f"cross:{name}",
                "prom",
                "execute_prometheus_instant_query",
                {"cluster": name, "query": 'up{cluster="%s"}' % others[0]},
            ),
            (
                f"agg:{name}",
                "prom",
                "execute_prometheus_instant_query",
                {"cluster": name, "query": "count by (cluster) (kube_pod_info)"},
            ),
            (f"lv:{name}", "prom", "get_label_values", {"cluster": name, "label_name": "cluster"}),
        ]
        if name in pods:
            _, ns, pod = pods[name]
            base = {"cluster": name, "namespace": ns, "pod": pod, "window_minutes": 60}
            cases += [
                (
                    f"logs:{name}",
                    "obs",
                    "query_pod_logs",
                    {**base, "purpose": "recent container logs"},
                ),
                (
                    f"trace:{name}",
                    "obs",
                    "query_pod_tracing",
                    {**base, "purpose": "requests to this pod"},
                ),
                (
                    f"promql:{name}",
                    "obs",
                    "execute_pod_promql",
                    {
                        **base,
                        "purpose": "memory",
                        "promql": 'container_memory_working_set_bytes{namespace="%s",pod="%s"}'
                        % (ns, pod),
                        "query_type": "instant",
                    },
                ),
            ]
    r = run_tools(cases)
    for name in clusters:
        up = json.loads(r[f"up:{name}"]).get("data", {}).get("result", [])
        seen = {s["metric"].get("cluster") for s in up}
        mc.check(
            f"EFK-1-{name}-promql-only-own",
            up and seen == {name},
            f"series={len(up)} clusters={seen}",
        )
        cross = json.loads(r[f"cross:{name}"]).get("data", {}).get("result", [])
        mc.check(f"EFK-2-{name}-cross-cluster-empty", cross == [], f"series={len(cross)}")
        agg = json.loads(r[f"agg:{name}"]).get("data", {}).get("result", [])
        mc.check(
            f"EFK-3-{name}-aggregation-scoped",
            [s["metric"].get("cluster") for s in agg] == [name],
            str([(s["metric"], s["value"][1]) for s in agg]),
        )
        values = json.loads(r[f"lv:{name}"]).get("data")
        mc.check(
            f"EFK-4-{name}-label-values-scoped", values == [name], f"cluster label values={values}"
        )
        if name not in pods:
            mc.check(f"EFK-5-{name}-has-case-pod", False, "no running aiops-case workload Pod")
            continue
        logs = r[f"logs:{name}"]
        mc.check(
            f"EFK-5-{name}-container-logs",
            logs.get("ok")
            and logs.get("cluster") == name
            and logs.get("backend") == "elasticsearch"
            and logs.get("coverage") in ("present", "partial")
            and logs.get("samples"),
            f"ok={logs.get('ok')} coverage={logs.get('coverage')} backend={logs.get('backend')} "
            f"samples={len(logs.get('samples') or [])} error={(logs.get('error') or {}).get('code')}",
        )
        trace = r[f"trace:{name}"]
        mc.check(
            f"EFK-6-{name}-tracing-runs",
            trace.get("ok")
            and trace.get("cluster") == name
            and trace.get("backend") == "deepflow",
            f"ok={trace.get('ok')} coverage={trace.get('coverage')} flows={len(trace.get('samples') or [])} "
            f"error={(trace.get('error') or {}).get('code')}",
        )
        pq = r[f"promql:{name}"]
        mc.check(
            f"EFK-7-{name}-pod-promql",
            pq.get("ok") and pq.get("cluster") == name and pq.get("coverage") == "present",
            f"ok={pq.get('ok')} coverage={pq.get('coverage')} error={(pq.get('error') or {}).get('code')}",
        )
    raw = pod_py(EFK_RAW, timeout=180)
    control = raw.get("_unscoped") or {}
    mc.check(
        "EFK-C-unscoped-backends-hold-several-clusters",
        set(control.get("es") or []) >= set(clusters) and len(control.get("df") or []) > 1,
        json.dumps(control),
    )
    for name in clusters:
        got = raw.get(name) or {}
        mc.check(
            f"EFK-8-{name}-es-hits-only-own",
            got.get("es_hits", 0) > 0 and got.get("es_clusters") == [name],
            f"hits={got.get('es_hits')} clusters={got.get('es_clusters')}",
        )
        df = got.get("df") or {}
        mc.check(
            f"EFK-9-{name}-deepflow-only-own",
            not got.get("df_error") and set(df) == {name} and df[name] > 0,
            f"by cluster={df} error={str(got.get('df_error'))[:120]}",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["p0", "p1", "p3", "efk"], required=True)
    args = parser.parse_args()
    {"p0": phase_p0, "p1": phase_p1, "p3": phase_p3, "efk": phase_efk}[args.phase]()
    mc.finish()


if __name__ == "__main__":
    main()
