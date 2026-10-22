"""make mc-discover: cluster-config entries from xnet virtual Nodes, never the join token."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "discover", ROOT / "deploy-edge/discover_clusters.py"
)
discover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discover)


def node(name, center=False, alias="", ip="10.2.5.88", ready="True"):
    labels = {"node-role.kubernetes.io/xnet-agent": ""}
    if center:
        labels["node-role.kubernetes.io/self"] = ""
    return {
        "metadata": {
            "name": name,
            "labels": labels,
            "annotations": {
                "xnet-cloud.agent/alias": alias,
                "xnet-cloud.agent/token": "SECRET-JOIN-TOKEN",
                "xnet-cloud.cluster/panorama": json.dumps({"internalIp": ip}),
            },
        },
        "status": {"conditions": [{"type": "Ready", "status": ready}]},
    }


def test_center_first_edges_with_alias_or_ip_suggestion_and_no_token():
    out = discover.render(
        discover.entries(
            {
                "items": [
                    node("vc-b", ip="10.2.5.89", ready="False"),
                    node("vc-a", alias="beijing"),
                    node("vc-xnet-management", center=True, ip="10.2.5.85"),
                ]
            }
        )
    )
    assert "center: vc-xnet-management" in out
    assert out.index("vc-xnet-management") < out.index("vc-a") < out.index("vc-b")
    assert "aliases: [beijing]" in out and "aliases: [edge-89]" in out
    assert "Ready=False" in out and "access: local" in out and out.count("access: xnet") == 2
    assert "SECRET-JOIN-TOKEN" not in out


def test_no_virtual_nodes_says_why():
    assert "没有发现 xnet 虚拟 Node" in discover.render(discover.entries({"items": []}))
