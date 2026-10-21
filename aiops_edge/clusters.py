"""Cluster configuration shared by AIOps, MCP and the kubectl shim.

Without a config file the deployment is single-cluster: one ``local`` cluster,
exactly as before this feature (spec FR-003). In multi-cluster mode there is no
implicit default cluster; the caller must name one (spec FR-005).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_ENV = "AIOPS_CLUSTERS_CONFIG"
DEFAULT_CONFIG_PATH = "/etc/aiops-clusters/clusters.yaml"
LOCAL = "local"
XNET_PREFIX = "vc-"
XNET_MANAGEMENT_UUID = "xnet-management"
_BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def uuid_to_node_name(uuid: str) -> str:
    """xnet's rule: ``vc-`` + base36 of the 16 UUID bytes, left-padded to 22."""
    if uuid == XNET_MANAGEMENT_UUID:
        return XNET_PREFIX + uuid
    num = int(uuid.replace("-", ""), 16)
    out = ""
    while num:
        num, rem = divmod(num, 36)
        out = _BASE36[rem] + out
    return XNET_PREFIX + out.rjust(22, "0")


def node_name_to_uuid(name: str) -> str:
    if name == XNET_PREFIX + XNET_MANAGEMENT_UUID:
        return XNET_MANAGEMENT_UUID
    body = name[len(XNET_PREFIX) :] if name.startswith(XNET_PREFIX) else ""
    if not body or any(c not in _BASE36 for c in body):
        raise ValueError(f"not an xnet cluster node name: {name!r}")
    num = 0
    for c in body:
        num = num * 36 + _BASE36.index(c)
    if num >= 1 << 128:
        raise ValueError(f"not an xnet cluster node name: {name!r}")
    h = f"{num:032x}"
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


@dataclass(frozen=True)
class Cluster:
    name: str
    access: str = LOCAL  # local | xnet
    aliases: tuple = ()
    observability: str = "legacy"
    uuid: str = ""

    @property
    def remote(self) -> bool:
        return self.access == "xnet"


@dataclass(frozen=True)
class XnetAccess:
    proxy_url: str
    runner_url: str
    cert_file: str = ""
    key_file: str = ""
    ca_file: str = ""
    signing_key_file: str = ""
    per_cluster_concurrency: int = 4
    call_timeout_seconds: int = 15


@dataclass
class EdgeConfig:
    clusters: Dict[str, Cluster] = field(default_factory=dict)
    center: Optional[str] = None
    default: Optional[str] = None
    xnet: Optional[XnetAccess] = None
    profiles: Dict[str, dict] = field(default_factory=dict)
    multi: bool = False

    def resolve(self, name: Optional[str]) -> Optional[Cluster]:
        """Canonical cluster for a name or alias; None when unknown or unspecified."""
        key = (name or "").strip().lower()
        if not key:
            key = (self.default or "").lower() if self.default else ""
            if not key:
                return None
        if key == LOCAL:
            if not self.multi:
                return self.clusters[LOCAL]
            key = (self.center or "").lower()
        for cluster in self.clusters.values():
            if key == cluster.name.lower() or key in (a.lower() for a in cluster.aliases):
                return cluster
        return None

    def names(self) -> List[str]:
        return [
            f"{c.name}" + (f" ({', '.join(c.aliases)})" if c.aliases else "")
            for c in self.clusters.values()
        ]


def _read(path: Path) -> dict:
    text = path.read_text()
    try:
        import yaml  # available in the AIOps and MCP images

        return yaml.safe_load(text) or {}
    except ImportError:
        return json.loads(text)


def load_config(path: Optional[str] = None) -> EdgeConfig:
    path = path or os.environ.get(CONFIG_ENV) or DEFAULT_CONFIG_PATH
    p = Path(path)
    if not p.is_file():
        return EdgeConfig(clusters={LOCAL: Cluster(name=LOCAL)}, default=LOCAL)
    raw = _read(p).get("clusters") or {}
    xnet_raw = (raw.get("access") or {}).get("xnet")
    xnet = XnetAccess(**xnet_raw) if xnet_raw else None
    clusters: Dict[str, Cluster] = {}
    for item in raw.get("items") or []:
        access = item.get("access", LOCAL)
        if access == "xnet" and xnet is None:
            raise ValueError(
                f"cluster {item['name']} uses xnet but clusters.access.xnet is missing"
            )
        uuid = item.get("uuid") or (node_name_to_uuid(item["name"]) if access == "xnet" else "")
        clusters[item["name"]] = Cluster(
            name=item["name"],
            access=access,
            aliases=tuple(item.get("aliases") or ()),
            observability=item.get("observability", "legacy"),
            uuid=uuid,
        )
    if not clusters:
        clusters = {LOCAL: Cluster(name=LOCAL)}
    multi = len(clusters) > 1 or any(c.remote for c in clusters.values())
    return EdgeConfig(
        clusters=clusters,
        center=raw.get("center"),
        default=raw.get("default") if not multi else raw.get("default") or None,
        xnet=xnet,
        profiles=_read(p).get("observability_profiles") or {},
        multi=multi,
    )
