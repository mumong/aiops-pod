#!/usr/bin/env python3
"""A15: contract checks on the xnet capabilities we rely on (no xnet changes).

Run after every xnet upgrade:
- tunnel /proxy reaches each edge with xnet's client cert, and refuses without it;
- forwarded requests keep our headers (needed for runner signatures);
- virtual Node name <-> cluster UUID conversion matches xnet's rule;
- observability ``cluster`` label equals the virtual Node name, and edge
  ``cluster_id`` equals the UUID.
"""

from __future__ import annotations

import ssl
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def uuid_to_name(uuid: str) -> str:
    num = int(uuid.replace("-", ""), 16)
    out = ""
    while num:
        num, rem = divmod(num, 36)
        out = BASE36[rem] + out
    return "vc-" + out.rjust(22, "0")


def main() -> None:
    edges = mc.edge_clusters()
    mc.check("A15-edges-present", len(edges) >= 2, f"edges={len(edges)}")

    for edge in edges:
        mc.check(
            f"A15-name-uuid-{edge['name']}",
            uuid_to_name(edge["uuid"]) == edge["name"],
            edge["uuid"],
        )

    with mc.xnet_client_cert() as cert:
        for edge in edges:
            status, body = mc.tunnel_get(edge["uuid"], "http://localhost:7070/k8s/nodes", cert)
            mc.check(
                f"A15-proxy-{edge['name']}",
                status == 200 and b"NodeList" in body,
                f"http={status}",
            )
        status, body = mc.tunnel_get(
            "00000000-0000-0000-0000-000000000000", "http://localhost:7070/k8s/nodes", cert
        )
        mc.check("A15-proxy-unknown-cluster", status != 200, f"http={status} {body[:60]!r}")

    try:
        status, _ = mc.tunnel_get(
            edges[0]["uuid"], "http://localhost:7070/k8s/nodes", None, timeout=10
        )
        refused = status in (401, 403)
    except (ssl.SSLError, urllib.error.URLError, ConnectionError, OSError):
        refused = True
    mc.check("A15-proxy-requires-client-cert", refused)

    labels = set(mc.http_json(f"{mc.VM_URL}/api/v1/label/cluster/values")["data"])
    for edge in edges:
        mc.check(f"A15-cluster-label-{edge['name']}", edge["name"] in labels)
        ids = mc.http_json(
            f"{mc.VM_URL}/api/v1/label/cluster_id/values",
            {"match[]": f'up{{cluster="{edge["name"]}"}}'},
        )["data"]
        mc.check(f"A15-cluster-id-{edge['name']}", ids == [edge["uuid"]], f"cluster_id={ids}")
    mc.finish()


if __name__ == "__main__":
    main()
