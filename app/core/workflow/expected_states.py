"""Operator-declared expected states (Boss 2026-10-22).

Some platforms run replicas that look abnormal by design, e.g. leader election
where only one replica is Ready and the standbys stay ``0/1 Running``. The model
cannot know that, so the operator declares it in the clusters config::

    expected_states:
      - cluster: center                      # optional; name or alias
        namespace: xnet
        workload: Deployment/xnet-management
        reason: 主备选举，同一时间只有 1 个副本 Ready
        healthy_when: {ready_replicas_min: 1}

After location, code checks each target against the declarations on live data:
the Pod must belong to the declared workload, be Running with every container
running (only readiness failing), and the workload must meet ``healthy_when``.
Only then the target becomes ``excluded`` with the declaration as its reason;
otherwise it stays a normal investigation (a declared standby that crashes, or a
workload with no Ready replica, is still abnormal). Excluded objects are always
named in the report.
"""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core import multicluster

logger = logging.getLogger(__name__)

Runner = Callable[[List[str]], str]


def declarations() -> List[Dict[str, Any]]:
    path = os.environ.get("AIOPS_CLUSTERS_CONFIG") or ""
    if not path or not Path(path).is_file():
        return []
    try:
        import yaml

        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except Exception as exc:  # a broken declaration must not break diagnosis
        logger.warning("expected_states: config unreadable: %s", exc)
        return []
    items = raw.get("expected_states") or []
    return [item for item in items if isinstance(item, dict) and item.get("workload")]


def _applies(item: Dict[str, Any], cluster: Optional[str], namespace: str) -> bool:
    if str(item.get("namespace") or "") != namespace:
        return False
    if not item.get("cluster"):
        return True
    declared = multicluster.config().resolve(str(item["cluster"]))
    return declared is not None and declared.name == cluster


def _owner(pod: Dict[str, Any], namespace: str, run: Runner) -> str:
    """``Kind/name`` of the controller workload; a ReplicaSet resolves to its Deployment."""
    refs = [r for r in pod.get("metadata", {}).get("ownerReferences") or [] if r.get("controller")]
    if not refs:
        return ""
    kind, name = refs[0].get("kind", ""), refs[0].get("name", "")
    if kind == "ReplicaSet":
        rs = json.loads(run(["get", "replicaset", name, "-n", namespace, "-o", "json"]))
        up = [
            r for r in rs.get("metadata", {}).get("ownerReferences") or [] if r.get("controller")
        ]
        if up:
            kind, name = up[0].get("kind", ""), up[0].get("name", "")
    return f"{kind}/{name}"


def _only_unready(pod: Dict[str, Any]) -> bool:
    status = pod.get("status") or {}
    containers = status.get("containerStatuses") or []
    return (
        status.get("phase") == "Running"
        and bool(containers)
        and all("running" in (c.get("state") or {}) for c in containers)
    )


def _ready_replicas(workload: str, namespace: str, run: Runner) -> Tuple[int, int]:
    kind, name = workload.split("/", 1)
    obj = json.loads(run(["get", kind.lower(), name, "-n", namespace, "-o", "json"]))
    status = obj.get("status") or {}
    return int(status.get("readyReplicas") or 0), int(
        (obj.get("spec") or {}).get("replicas") or status.get("replicas") or 0
    )


def apply_expected_states(
    handoff: Dict[str, Any],
    state: Dict[str, Any],
    run: Optional[Runner] = None,
    items: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Mark targets that match a satisfied declaration as ``excluded``; name them."""
    items = declarations() if items is None else items
    targets = handoff.get("targets") or []
    if not items or not targets:
        return handoff, []
    clusters = multicluster.run_clusters(state)
    cluster = clusters[0] if len(clusters) == 1 else None
    label = multicluster.labels([cluster])[0] if cluster and multicluster.multi() else ""
    if run is None:
        from app.core.remediation.pod_executor import run_argv

        def run(argv: List[str]) -> str:
            return run_argv(argv, cluster=cluster)

    out = copy.deepcopy(handoff)
    excluded: List[str] = []
    for target in out.get("targets") or []:
        entity = target.get("entity") or {}
        namespace, name = entity.get("namespace") or "", entity.get("name") or ""
        if target.get("status", "investigate") != "investigate" or entity.get("kind") != "Pod":
            continue
        rules = [item for item in items if _applies(item, cluster, namespace)]
        if not rules:
            continue
        try:
            pod = json.loads(run(["get", "pod", name, "-n", namespace, "-o", "json"]))
            owner = _owner(pod, namespace, run)
            rule = next((r for r in rules if str(r["workload"]) == owner), None)
            if rule is None or not _only_unready(pod):
                continue
            ready, desired = _ready_replicas(owner, namespace, run)
        except Exception as exc:  # unverifiable: keep investigating, never exclude blindly
            logger.warning("expected_states: cannot verify %s/%s: %s", namespace, name, exc)
            continue
        minimum = int((rule.get("healthy_when") or {}).get("ready_replicas_min") or 1)
        if ready < minimum:
            continue
        reason = str(rule.get("reason") or "运维声明的预期状态")
        target["status"] = "excluded"
        target["status_reason"] = (
            f"运维声明：{reason}（{owner} 当前 {ready}/{desired} Ready，满足至少 {minimum} 个）"
        )[:240]
        excluded.append(
            f"{label + ' ' if label else ''}{namespace}/{name}（{reason}；{owner} {ready}/{desired} Ready）"
        )
    if excluded and not any(
        t.get("status", "investigate") == "investigate" for t in out.get("targets") or []
    ):
        assessment = dict(out.get("pod_assessment") or {})
        if assessment.get("status") == "abnormal":
            # Every abnormal object is declared and verified: nothing left to diagnose.
            assessment["status"] = "healthy"
            assessment["reason"] = (
                "定位发现的对象均符合运维声明的预期状态：" + "；".join(excluded)
            )[:600]
            out["pod_assessment"] = assessment
    return out, excluded
