"""Location must account for every Pod the inventory shows outside the nominal state.

The model reads the Pod inventory and decides what to investigate. Run 51d58579
showed two ways an abnormal Pod vanished: the inventory was read in the projected
records form (which ``lifecycle_core`` does not parse, so nothing checked coverage)
and the model skipped a Pod that its own tool output listed as ``ready: false``.

After location, code reads the scope's Pods once and compares mechanically, using
the same nominal criteria as ``lifecycle_core.NOMINAL_CRITERIA``. Every non-nominal
Pod that no target names is added as an ``investigate`` target whose issue lists the
raw status facts; one the model set ``assessed`` goes back to ``investigate`` (each
abnormal Pod gets evidence and a formal RCA). Code decides only "not yet
investigated", never what the fault is;
operator declarations (``expected_states``) still apply afterwards. If the read
fails, the handoff is left unchanged (logged), never guessed.
"""

from __future__ import annotations

import copy
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core import multicluster

logger = logging.getLogger(__name__)

WINDOW_MINUTES = 10  # POD_DETECTION_GUIDANCE: current state plus the last 10 minutes
Runner = Callable[[List[str]], str]


def _parse_time(value: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def status_facts(pod: Dict[str, Any], now: datetime) -> List[str]:
    """Raw facts that put a Pod outside the nominal state; empty when nominal."""
    meta, status = pod.get("metadata") or {}, pod.get("status") or {}
    phase = status.get("phase") or "Unknown"
    if phase == "Succeeded" and not meta.get("deletionTimestamp"):
        return []
    facts = []
    if meta.get("deletionTimestamp"):
        facts.append(f"删除中（deletionTimestamp={meta['deletionTimestamp']}）")
    if phase != "Running":
        facts.append(
            f"phase={phase}" + (f"（{status['reason']}）" if status.get("reason") else "")
        )
    ready = next(
        (c.get("status") for c in status.get("conditions") or [] if c.get("type") == "Ready"),
        None,
    )
    if phase == "Running" and ready != "True":
        facts.append(f"Ready={ready or '未知'}")
    since = now - timedelta(minutes=WINDOW_MINUTES)
    for container in status.get("containerStatuses") or []:
        name, state = container.get("name", "?"), container.get("state") or {}
        if "running" not in state:
            kind = next(iter(state), "unknown")
            reason = (state.get(kind) or {}).get("reason")
            facts.append(f"容器 {name} {kind}" + (f"（{reason}）" if reason else ""))
        elif container.get("ready") is not True and phase == "Running":
            facts.append(f"容器 {name} 运行但未就绪")
        last = (container.get("lastState") or {}).get("terminated") or {}
        finished = _parse_time(last.get("finishedAt"))
        if finished and finished >= since:
            facts.append(
                f"容器 {name} {WINDOW_MINUTES} 分钟内终止过（{last.get('reason') or '-'}，"
                f"exit {last.get('exitCode')}，累计重启 {container.get('restartCount', 0)}）"
            )
    return facts


def _readable(cluster: Optional[str]) -> bool:
    """Only this Pod's ServiceAccount or a remote cluster's runner; never ambient kubeconfig."""
    import os
    from pathlib import Path

    if multicluster.kubectl_env(cluster) is not None:
        return True
    return (
        bool(os.environ.get("KUBERNETES_SERVICE_HOST"))
        and Path("/var/run/secrets/kubernetes.io/serviceaccount/token").is_file()
    )


def _scope_argv(state: Dict[str, Any]) -> List[List[str]]:
    namespaces = (state.get("request_contract") or {}).get("namespaces") or []
    base = ["get", "pods", "-o", "json"]
    return [[*base, "-n", ns] for ns in namespaces] if namespaces else [[*base, "-A"]]


def reconcile_inventory(
    handoff: Dict[str, Any],
    state: Dict[str, Any],
    run: Optional[Runner] = None,
    now: Optional[datetime] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Every non-nominal Pod is investigated: add unaccounted ones, reopen "assessed" ones."""
    contract = state.get("request_contract") or {}
    if contract.get("pod_names") or not isinstance(handoff.get("targets"), list):
        return handoff, []  # a named Pod is the whole scope; nothing else to account for
    clusters = multicluster.run_clusters(state)
    cluster = clusters[0] if len(clusters) == 1 else None
    if run is None:
        if not _readable(cluster):
            return handoff, []
        from app.core.remediation.pod_executor import run_argv

        def run(argv: List[str]) -> str:
            return run_argv(["kubectl", *argv], cluster=cluster)

    now = now or datetime.now(timezone.utc)
    try:
        pods = [
            pod for argv in _scope_argv(state) for pod in json.loads(run(argv)).get("items") or []
        ]
    except Exception as exc:  # unverifiable: leave the model's handoff as it is
        logger.warning("inventory_reconcile: Pod list unavailable: %s", exc)
        return handoff, []
    named = {
        ((t.get("entity") or {}).get("namespace") or "", (t.get("entity") or {}).get("name"))
        for t in handoff["targets"]
    }
    # Pods bound to a Node named after a configured cluster sit on an xnet virtual node:
    # they stand for workloads placed in that cluster, not Pods running here
    # (same rule as multicluster.virtual_node_note, derived from config).
    virtual = set(multicluster.config().clusters) if multicluster.multi() else set()
    out = copy.deepcopy(handoff)
    by_key = {
        ((t.get("entity") or {}).get("namespace") or "", (t.get("entity") or {}).get("name")): t
        for t in out["targets"]
    }
    added = []
    for pod in pods:
        meta = pod.get("metadata") or {}
        key = (meta.get("namespace") or "", meta.get("name"))
        if (pod.get("spec") or {}).get("nodeName") in virtual:
            continue
        facts = status_facts(pod, now)
        if facts and by_key.get(key, {}).get("status") == "assessed":
            # Every currently non-nominal Pod gets its own evidence and formal RCA; the
            # location stage cannot close it alone (run 73f4a1f5: edge-88 OOM and
            # liveness Pods were "assessed" and got no diagnosis). deferred/excluded
            # keep their explicit, reasoned dispositions.
            by_key[key]["status"], by_key[key]["status_reason"] = "investigate", ""
            added.append(f"{key[0]}/{key[1]}")
            continue
        if not facts or key in named:
            continue
        out["targets"].append(
            {
                "target_id": f"inventory-{key[0]}-{key[1]}"[:120],
                "entity": {
                    "kind": "Pod",
                    "namespace": key[0],
                    "name": key[1],
                    "uid": meta.get("uid") or "",
                },
                "issue": ("清单核对补充（定位未列出）：" + "；".join(facts))[:320],
                "status": "investigate",
                "status_reason": "",
                "evidence_refs": [],
            }
        )
        added.append(f"{key[0]}/{key[1]}")
    if added:
        assessment = out.get("pod_assessment")
        if isinstance(assessment, dict):
            assessment["status"] = "abnormal"
            assessment["reason"] = (
                f"{assessment.get('reason') or ''}（代码核对 Pod 清单：{len(added)} 个"
                f"非正常状态 Pod 需要取证：{'、'.join(added)}）"
            )[:600]
        logger.info("inventory_reconcile: added %s", added)
    return out, added
