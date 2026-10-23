#!/usr/bin/env python3
"""X3 / SC-006: the center runtime must not depend on edge kubeconfigs.

Scans the center cluster's ``aiops`` and ``mcp`` namespaces (ConfigMaps,
Secrets, workload env and volumes) for edge API server addresses and for any
kubeconfig whose server points at an edge cluster. Edge addresses come from the
ops kubeconfigs, so nothing is hard-coded here.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

RUNTIME_NAMESPACES = ("aiops", "mcp")


def edge_api_servers() -> list[str]:
    servers = []
    for name in mc.EDGE_KUBECONFIGS:
        text = Path(mc.kubeconfig(name)).read_text()
        match = re.search(r"server:\s*(\S+)", text)
        if match:
            servers.append(urlparse(match.group(1)).netloc)
    return servers


def texts(ns: str) -> list[tuple[str, str]]:
    found = []
    for item in mc.kubectl_json("center", "get", "configmaps", "-n", ns)["items"]:
        for key, value in (item.get("data") or {}).items():
            found.append((f"configmap/{item['metadata']['name']}/{key}", value))
    for item in mc.kubectl_json("center", "get", "secrets", "-n", ns)["items"]:
        for key, value in (item.get("data") or {}).items():
            try:
                decoded = base64.b64decode(value).decode("utf-8", "replace")
            except ValueError:
                continue
            found.append((f"secret/{item['metadata']['name']}/{key}", decoded))
    for kind in ("deployments", "statefulsets"):
        for item in mc.kubectl_json("center", "get", kind, "-n", ns)["items"]:
            found.append((f"{kind}/{item['metadata']['name']}/spec", json.dumps(item["spec"])))
    return found


def main() -> None:
    edges = edge_api_servers()
    hosts = {e.split(":")[0] for e in edges}
    print(f"edge API servers: {edges}")
    for ns in RUNTIME_NAMESPACES:
        try:
            entries = texts(ns)
        except RuntimeError as exc:
            mc.check(f"X3-{ns}-readable", False, str(exc))
            continue
        hits = []
        for where, text in entries:
            if any(e in text for e in edges):
                hits.append(f"{where}: edge API server address")
            if "clusters:" in text and "server:" in text:
                servers = re.findall(r"server:\s*(\S+)", text)
                if any(urlparse(s).hostname in hosts for s in servers):
                    hits.append(f"{where}: kubeconfig for an edge cluster")
        for hit in hits:
            print(f"  {hit}")
        mc.check(f"X3-{ns}-no-edge-kubeconfig", not hits, f"scanned={len(entries)}")
    mc.finish()


if __name__ == "__main__":
    main()
