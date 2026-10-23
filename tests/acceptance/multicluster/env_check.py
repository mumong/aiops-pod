#!/usr/bin/env python3
"""Environment baseline for the three-cluster test env (acceptance doc §3).

Checks clusters, xnet tunnel and both observability stores, lists known
collection noise, and (with --snapshot FILE) writes the xnet/monitor object
snapshot used by snapshot_diff.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

SNAPSHOT_KINDS = ("deployments", "statefulsets", "daemonsets", "services", "configmaps", "secrets")


def snapshot(path: str) -> None:
    data = {}
    for name in ("center", *mc.EDGE_KUBECONFIGS):
        for ns in mc.SNAPSHOT_NAMESPACES:
            for kind in SNAPSHOT_KINDS:
                try:
                    items = mc.kubectl_json(name, "get", kind, "-n", ns)["items"]
                except RuntimeError:
                    continue
                for item in items:
                    body = {
                        k: item.get(k)
                        for k in ("spec", "data", "stringData")
                        if item.get(k) is not None
                    }
                    labels = item["metadata"].get("labels") or {}
                    digest = hashlib.sha256(
                        json.dumps([body, labels], sort_keys=True).encode()
                    ).hexdigest()
                    data[f"{name}/{ns}/{kind}/{item['metadata']['name']}"] = digest
        crds = mc.kubectl(name, "get", "crd", "-o", "name").split()
        data[f"{name}/crds"] = hashlib.sha256("\n".join(sorted(crds)).encode()).hexdigest()
    Path(path).write_text(json.dumps(data, indent=1, sort_keys=True))
    print(f"snapshot: {len(data)} objects -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", help="write xnet/monitor snapshot to this file")
    args = parser.parse_args()

    for name in ("center", *mc.EDGE_KUBECONFIGS):
        nodes = mc.kubectl_json(name, "get", "nodes")["items"]
        real = [n for n in nodes if not n["metadata"]["name"].startswith("vc-")]
        ready = all(
            any(c["type"] == "Ready" and c["status"] == "True" for c in n["status"]["conditions"])
            for n in real
        )
        mc.check(f"ENV-nodes-{name}", ready and bool(real), f"nodes={len(real)}")

    edges = mc.edge_clusters()
    mc.check(
        "ENV-xnet-edges",
        len(edges) == 2 and all(e["ready"] == "True" for e in edges),
        " ".join(f"{e['name']}={e['ready']}" for e in edges),
    )

    with mc.xnet_client_cert() as cert:
        for edge in edges:
            status, body = mc.tunnel_get(edge["uuid"], "http://localhost:7070/k8s/nodes", cert)
            mc.check(
                f"ENV-tunnel-{edge['name']}",
                status == 200 and b"NodeList" in body,
                f"http={status}",
            )

    labels = set(mc.http_json(f"{mc.VM_URL}/api/v1/label/cluster/values")["data"])
    expected = {e["name"] for e in edges} | {"vc-xnet-management"}
    mc.check("ENV-vm-clusters", expected <= labels, f"labels={sorted(labels)}")

    hits = mc.http_json(
        f"{mc.VLOGS_URL}/select/logsql/field_values",
        {"query": "*", "field": "cluster", "start": "7d"},
    )["values"]
    log_clusters = {v["value"] for v in hits}
    mc.check("ENV-vlogs-clusters", expected <= log_clusters, f"clusters={sorted(log_clusters)}")

    noise = mc.http_json(f"{mc.VM_URL}/api/v1/query", {"query": "up == 0"})["data"]["result"]
    print("known noise (up==0):")
    for series in noise:
        m = series["metric"]
        print(f"  {m.get('cluster')} {m.get('job')} {m.get('instance')}")

    if args.snapshot:
        snapshot(args.snapshot)
    mc.finish()


if __name__ == "__main__":
    main()
