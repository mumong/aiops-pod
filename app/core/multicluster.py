"""Cluster scope of a run (specs/008-multi-cluster).

Without a multi-cluster config this module is inert: the router keeps its
original schema and prompt, tools are not wrapped, kubectl runs in-cluster.

In a multi-cluster deployment:
- the router must name the scope (one cluster, several, or the center); names
  are resolved here against the registry, never invented by the model;
- every MCP tool that accepts ``cluster`` is bound to the run's scope: a single
  cluster is forced, several clusters are checked (engineering guarantee, not a
  prompt request);
- kubectl run by AIOps itself targets a remote cluster through the shim.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, Iterable, List, Optional, Tuple

from aiops_edge.clusters import EdgeConfig, load_config

logger = logging.getLogger(__name__)

ALL = "*"
EDGES = "*edge"  # every cluster except the center
_lock = threading.Lock()
_config: Optional[EdgeConfig] = None


def config() -> EdgeConfig:
    global _config
    with _lock:
        if _config is None:
            _config = load_config()
        return _config


def reset() -> None:
    global _config
    with _lock:
        _config = None


def multi() -> bool:
    return config().multi


def _label(cluster) -> str:
    return f"{cluster.name}（{'、'.join(cluster.aliases)}）" if cluster.aliases else cluster.name


def scope_question() -> str:
    cfg = config()
    center = cfg.resolve(cfg.center) if cfg.center else None
    edges = [c for c in cfg.clusters.values() if center is None or c.name != center.name]
    edge_names = "、".join(c.aliases[0] if c.aliases else c.name for c in edges)
    return (
        "当前是多集群部署，请说明要查看的范围：中心集群"
        + (f"（{center.aliases[0] if center.aliases else center.name}）" if center else "")
        + f"、某个边缘集群（{edge_names}），还是全部集群？"
    )


def router_prompt() -> str:
    """Addendum to REQUEST_ROUTER_PROMPT; only used in multi-cluster deployments.

    The model decides the scope from its own reading of the user's intent (Boss
    2026-10-22: no special handling, no sample phrases to match); code only
    resolves names and asks when the scope is genuinely unspecified.
    """
    cfg = config()
    lines = [
        f"- {_label(c)}：{'中心集群' if c.name == cfg.center else '边缘集群（子集群）'}"
        for c in cfg.clusters.values()
    ]
    return (
        "\n\n# 集群范围（多集群部署）\n"
        "可用集群：\n" + "\n".join(lines) + "\n"
        "按你对用户意图的理解决定 cluster_mode 和 clusters：\n"
        "- none：回答不需要任何集群的数据。\n"
        "- inventory：问的是集群本身（有哪些、角色与在线情况），不是集群里的工作负载。\n"
        "- single / multiple / center：需要集群里的实际数据；分别是一个集群、多个集群、中心集群。\n"
        "- unspecified：需要集群数据，但问题和会话都没有说明范围；系统会向用户确认，不要替用户选择。\n"
        '- clusters：用户说的集群名或别名（原样）；全部集群填 ["*"]（含中心集群）；'
        '全部边缘集群填 ["*edge"]（不含中心集群）；center 可留空。\n'
        "- 会话中已经明确的范围，后续指代沿用；用户改了范围就按新的填写。\n"
    )


def virtual_node_note() -> str:
    """Nodes named after configured clusters are xnet virtual nodes, not machines."""
    names = "、".join(config().clusters)
    return (
        f"Node {names} 是 xnet 为接入的集群虚拟出的节点，只表示该集群已连接；"
        "它们不是真实计算节点，不按承载工作负载的节点评估资源、压力或健康。"
    )


def resolve_contract(
    contract: Dict[str, Any], evidence: Optional[str] = None
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Canonical clusters for a routed contract, or the clarification to ask instead.

    Engineering guarantees only: an unspecified scope is asked about, unknown
    cluster names are listed, repair stays on one cluster. Whether a question
    needs cluster data at all is the model's reading of the intent.
    """
    del evidence  # kept for callers; scope is no longer gated on wording
    cfg = config()
    mode = contract.get("cluster_mode") or "unspecified"
    names = [str(n).strip() for n in contract.get("clusters") or [] if str(n).strip()]
    if mode == "none":
        return dict(contract, clusters=[], cluster_mode="none"), None
    if mode == "inventory":
        return dict(contract, clusters=list(cfg.clusters), cluster_mode="inventory"), None
    if mode == "unspecified" or (not names and mode != "center"):
        return contract, scope_question()
    if mode == "center":
        names = names or [cfg.center or ""]
    if ALL in names:
        resolved = list(cfg.clusters)
    elif EDGES in names:
        center = cfg.resolve(cfg.center) if cfg.center else None
        resolved = [n for n in cfg.clusters if center is None or n != center.name]
    else:
        resolved, unknown = [], []
        for name in names:
            cluster = cfg.resolve(name)
            if cluster is None:
                unknown.append(name)
            elif cluster.name not in resolved:
                resolved.append(cluster.name)
        if unknown:
            available = "；".join(_label(c) for c in cfg.clusters.values())
            return (
                contract,
                f"没有找到集群：{'、'.join(unknown)}。可用集群：{available}。请重新指定。",
            )
    out = dict(contract, clusters=resolved, cluster_mode="single" if len(resolved) == 1 else mode)
    if len(resolved) > 1 and contract.get("route") == "remediation":
        return out, (
            f"修复每次只针对一个集群（本次涉及 {len(resolved)} 个）。"
            "请先选择其中一个集群；也可以先做跨集群诊断，再分别发起修复。"
        )
    return out, None


def labels(names: Iterable[str]) -> List[str]:
    """Short display names (first alias) for canonical cluster names."""
    cfg = config()
    out = []
    for name in names:
        cluster = cfg.resolve(name)
        out.append(cluster.aliases[0] if cluster and cluster.aliases else name)
    return out


def run_clusters(state: Dict[str, Any]) -> List[str]:
    """Clusters a node may touch: its lane's group cluster, else the routed scope."""
    # Parallel lanes carry their group as ``diagnosis_target`` (stage_material.branch_state).
    for key in ("group", "diagnosis_target"):
        group = state.get(key) or {}
        if isinstance(group, dict) and group.get("cluster"):
            return [group["cluster"]]
    contract = state.get("request_contract") or {}
    return list(contract.get("clusters") or [])


def _accepts_cluster(tool: Any) -> bool:
    schema = getattr(tool, "args_schema", None)
    if isinstance(schema, dict):
        return "cluster" in (schema.get("properties") or {})
    fields = getattr(schema, "model_fields", None) or {}
    return "cluster" in fields


def _bind(
    arguments: Dict[str, Any], clusters: List[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    args = dict(arguments or {})
    requested = str(args.get("cluster") or "").strip()
    if len(clusters) == 1:
        if requested and requested != clusters[0]:
            resolved = config().resolve(requested)
            if resolved is None or resolved.name != clusters[0]:
                logger.info(
                    "[multicluster] cluster %r replaced by run scope %s", requested, clusters[0]
                )
        args["cluster"] = clusters[0]
        return args, None
    if not clusters:
        return None, "aiops: cluster_required: 本次运行没有确定集群范围"
    if not requested:
        return (
            None,
            f"aiops: cluster_required: 本次涉及多个集群，请在 cluster 参数中指定其一：{', '.join(clusters)}",
        )
    resolved = config().resolve(requested)
    if resolved is None or resolved.name not in clusters:
        return (
            None,
            f"aiops: cluster_out_of_scope: {requested} 不在本次范围内（{', '.join(clusters)}）",
        )
    args["cluster"] = resolved.name
    return args, None


def _scoped(tool: Any, clusters: List[str]) -> Any:
    from langchain_core.tools import StructuredTool

    async def _acoroutine(**kwargs: Any) -> Any:
        args, error = _bind(kwargs, clusters)
        return error if error else await tool.ainvoke(args)

    def _func(**kwargs: Any) -> Any:
        args, error = _bind(kwargs, clusters)
        return error if error else tool.invoke(args)

    wrapped = StructuredTool.from_function(
        func=_func,
        coroutine=_acoroutine,
        name=tool.name,
        description=getattr(tool, "description", "") or "",
        args_schema=getattr(tool, "args_schema", None),
        return_direct=getattr(tool, "return_direct", False),
        response_format="content",
    )
    wrapped.metadata = dict(getattr(tool, "metadata", None) or {})
    return wrapped


def scoped_tools(tools: Iterable[Any], state: Dict[str, Any]) -> Any:
    """Bind cluster-aware tools to the run's scope; unchanged in single-cluster mode."""
    if not multi():
        return tools
    clusters = run_clusters(state)
    return [_scoped(t, clusters) if _accepts_cluster(t) else t for t in tools]


def kubectl_env(cluster: Optional[str]) -> Optional[Dict[str, str]]:
    """Environment for kubectl run by AIOps itself: None keeps in-cluster behaviour."""
    if not cluster or not multi():
        return None
    resolved = config().resolve(cluster)
    if resolved is None or not resolved.remote:
        return None
    return {**os.environ, "AIOPS_CLUSTER": resolved.name}


def job_cluster(contract: Optional[Dict[str, Any]]):
    """The remote cluster a repair job targets, or None (local / single-cluster)."""
    if not multi() or not contract:
        return None
    clusters = contract.get("clusters") or []
    if len(clusters) != 1:
        return None
    cluster = config().resolve(clusters[0])
    return cluster if cluster is not None and cluster.remote else None


def job_label(contract: Optional[Dict[str, Any]]) -> str:
    """Display label of a job's cluster in multi-cluster mode ('' otherwise)."""
    if not multi() or not contract or len(contract.get("clusters") or []) != 1:
        return ""
    return labels(contract["clusters"])[0]
