"""Print cluster-config entries for the clusters xnet has joined (make mc-discover).

Input (stdin): ``kubectl get nodes -l node-role.kubernetes.io/xnet-agent -o json`` from
the center. Each joined cluster is an xnet virtual Node; its name is the cluster name
and the ``cluster`` label of the observability data. The center carries xnet's own
``node-role.kubernetes.io/self`` label. Only names, Ready, uuid, alias and the
panorama IP are read; the join-token annotation is never read or printed.

The output is the part of deploy-edge/clusters.mc.yaml between its ``### 替换开始`` and
``### 替换结束 ###`` markers, framed by the same markers; aliases are suggestions (xnet
alias, else ``edge-<last IP octet>``) to edit before use.
"""

import json
import sys

# The same marker lines frame the replaceable block in deploy-edge/clusters.mc.yaml.
BEGIN = "### 替换开始：在中心执行 make mc-discover，用输出中两行 ### 之间的内容整段替换这里 ###"
END = "### 替换结束 ###"


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
        "# make mc-discover：xnet 已接入的集群。把下面两行 ### 之间的内容（含这两行）整段替换到",
        "# deploy-edge/clusters.mc.yaml 中同样两行 ### 之间；别名是建议值，可按习惯修改。",
        f"  {BEGIN}",
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
    lines.append(f"  {END}")
    return "\n".join(lines)


def replace_block(template, rendered):
    """The template with its marked block swapped for the marked block of ``rendered``."""
    begin, end = "  " + BEGIN, "  " + END
    if begin not in template or end not in template:
        raise SystemExit("集群配置里找不到 ### 替换开始 / 替换结束 ### 标记，请手动替换")
    start, stop = template.index(begin), template.index(end) + len(end)
    return template[:start] + rendered[rendered.index(begin) :].rstrip("\n") + template[stop:]


if __name__ == "__main__":
    rendered = render(entries(json.load(sys.stdin)))
    if len(sys.argv) > 1:  # make mc-discover WRITE=1: update the cluster config in place
        path = sys.argv[1]
        with open(path, encoding="utf-8") as f:
            updated = replace_block(f.read(), rendered)
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"已写入 {path}（### 之间的集群列表）；别名可按习惯修改")
    else:
        print(rendered)
