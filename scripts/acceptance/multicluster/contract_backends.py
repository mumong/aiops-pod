#!/usr/bin/env python3
"""Backend contract checks for the two observability profiles (tasks T036).

- VictoriaMetrics: ``extra_label`` pins every selector to one cluster, even when
  the query names another cluster.
- VictoriaLogs: Kubernetes events can be selected per cluster and parsed.
- Metric parity: the metric names our tools and runbooks rely on exist in the
  new backend for every cluster, and in the legacy Prometheus (10.2.0.48, read
  through the API server's service proxy with the default kubeconfig).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

# kube-state-metrics emits these only while some container is waiting / has terminated,
# so they are required only on clusters running fault cases (the edges).
STATE_METRICS = (
    "kube_pod_container_status_waiting_reason",
    "kube_pod_container_status_last_terminated_reason",
)
COMMON_METRICS = (
    "kube_pod_status_phase",
    "kube_pod_container_status_restarts_total",
    "kube_pod_info",
    "kube_pod_owner",
    "container_cpu_usage_seconds_total",
    "container_memory_working_set_bytes",
    "container_oom_events_total",
    "node_memory_MemAvailable_bytes",
)
LEGACY_PROXY = "/api/v1/namespaces/monitor/services/observability-prometheus:9090/proxy"
EVENT = re.compile(
    r"^event name: .*,involvedObject_name: [^,]*,reasoni?: [^,]*,type: (Normal|Warning),message: "
)


def vm_query(query: str, cluster: str) -> list:
    return mc.http_json(
        f"{mc.VM_URL}/api/v1/query", {"query": query, "extra_label": f"cluster={cluster}"}
    )["data"]["result"]


def main() -> None:
    edges = mc.edge_clusters()
    clusters = [e["name"] for e in edges] + ["vc-xnet-management"]
    a, b = edges[0]["name"], edges[1]["name"]

    only_a = {r["metric"].get("cluster") for r in vm_query("up", a)}
    mc.check("CB-extra-label-pins-cluster", only_a == {a}, f"clusters={only_a}")
    crossed = vm_query(f'up{{cluster="{b}"}}', a)
    mc.check("CB-extra-label-beats-explicit-matcher", crossed == [], f"series={len(crossed)}")

    for cluster in clusters:
        names = set(
            mc.http_json(
                f"{mc.VM_URL}/api/v1/label/__name__/values",
                {"extra_label": f"cluster={cluster}", "start": "1h"},
            )["data"]
        )
        required = COMMON_METRICS + (STATE_METRICS if cluster != "vc-xnet-management" else ())
        missing = [m for m in required if m not in names]
        mc.check(f"CB-metrics-{cluster[:14]}", not missing, f"missing={missing}")

    lines = mc.http_lines(
        f"{mc.VLOGS_URL}/select/logsql/query",
        {"query": f'cluster:="{a}" "involvedObject_name:" | limit 20', "start": "24h"},
    )
    parsed = [line for line in lines if EVENT.match(line.get("_msg", ""))]
    mc.check(
        "CB-vlogs-events-per-cluster",
        parsed and all(line.get("cluster") == a for line in lines),
        f"lines={len(lines)} parsed={len(parsed)}",
    )

    try:
        raw = subprocess.run(
            ["kubectl", "get", "--raw", f"{LEGACY_PROXY}/api/v1/label/__name__/values"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout
        legacy = set(json.loads(raw)["data"])
        missing = [m for m in COMMON_METRICS + STATE_METRICS if m not in legacy]
        mc.check("CB-metrics-legacy-prometheus", not missing, f"missing={missing}")
    except (subprocess.SubprocessError, ValueError, KeyError) as exc:
        mc.check("CB-metrics-legacy-prometheus", False, f"legacy Prometheus unreachable: {exc}")
    mc.finish()


if __name__ == "__main__":
    main()
