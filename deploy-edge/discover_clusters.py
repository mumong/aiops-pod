"""Print cluster-config entries for the clusters xnet has joined (make mc-discover).

Input (stdin): ``kubectl get nodes -l node-role.kubernetes.io/xnet-agent -o json`` from
the center. Each joined cluster is an xnet virtual Node; its name is the cluster name
and the ``cluster`` label of the observability data. The center carries xnet's own
``node-role.kubernetes.io/self`` label. Only names, Ready, uuid, alias and the
panorama IP are read; the join-token annotation is never read or printed.

The output is the ``clusters:`` block of deploy-edge/clusters.mc.yaml; aliases are
suggestions (xnet alias, else ``edge-<last IP octet>``) to edit before use.
"""

import json
import sys


def _ip(annotations):
    try:
        return (
            json.loads(annotations.get("xnet-cloud.cluster/panorama") or "{}").get("internalIp")
            or ""
        )
    except ValueError:
        return ""


def entries(nodes):
    out = []
    for node in nodes.get("items") or []:
        meta = node.get("metadata") or {}
        labels, annotations = meta.get("labels") or {}, meta.get("annotations") or {}
        ready = next(
            (
                c.get("status")
                for c in (node.get("status") or {}).get("conditions") or []
                if c.get("type") == "Ready"
            ),
            "Unknown",
        )
        ip = _ip(annotations)
        center = "node-role.kubernetes.io/self" in labels
        alias = (annotations.get("xnet-cloud.agent/alias") or "").strip()
        aliases = (
            ["center", "中心集群", "中心"]
            if center
            else [alias]
            if alias
            else [f"edge-{ip.rsplit('.', 1)[-1]}"]
            if ip
            else []
        )
        out.append(
            {
                "name": meta.get("name"),
                "center": center,
                "ready": ready,
                "ip": ip,
                "aliases": aliases,
            }
        )
    return sorted(out, key=lambda e: (not e["center"], e["name"]))


def render(items):
    center = next((e["name"] for e in items if e["center"]), None)
    lines = [
        "# make mc-discover：xnet 已接入的集群。别名是建议值，可按习惯修改；",
        "# 把下面的 clusters 块替换进集群配置（默认 deploy-edge/clusters.mc.yaml），其余部分沿用。",
        "clusters:",
        "  default: null",
        f"  center: {center or 'null'}",
        "  items:",
    ]
    for e in items:
        role = "中心" if e["center"] else "边缘"
        lines += [
            f"    - name: {e['name']}   # {role}，IP {e['ip'] or '?'}，Ready={e['ready']}",
            f"      aliases: [{', '.join(e['aliases'])}]",
            f"      access: {'local' if e['center'] else 'xnet'}",
            "      observability: victoria",
        ]
    if not items:
        lines.append("    []   # 没有发现 xnet 虚拟 Node：xnet 未安装，或边缘尚未加入")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(entries(json.load(sys.stdin))))
