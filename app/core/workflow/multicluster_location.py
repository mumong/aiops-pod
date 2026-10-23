"""Location over several clusters in one deep diagnosis (docs/specs/008-multi-cluster US6).

The existing location (layer) node runs once per cluster, in parallel, with its
tools bound to that cluster. Results are merged without changing any contract:

- target ids are prefixed with the cluster label (``edge-88/t1``), so equal
  namespace/name on two clusters never collide and ``scoped_handoff`` still
  selects by id;
- groups carry ``cluster`` / ``cluster_label``; lanes bind their tools to the
  group's cluster (``multicluster.run_clusters``);
- a cluster whose location failed is reported as incomplete, the others go on;
- a single remaining group narrows the run to its cluster, because the serial
  evidence path has no lane group.

Each cluster's events stay on the location node and carry ``cluster_lane`` so
the UI can show one card per cluster; they must not be re-attributed to the
evidence stage, or the stream would close the location stage early.
"""

from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core import multicluster
from app.core.aicall.errors import ModelStreamInterrupted

_ASSESSMENT_ORDER = {"abnormal": 0, "inconclusive": 1, "healthy": 2}


class ClusterLaneQueue:
    """Tag a cluster's thinking events with its label; the node stays the location node."""

    def __init__(self, target: Any, *, label: str):
        self._target = target
        self._label = label

    def _decorate(self, item: Any) -> Any:
        if isinstance(item, tuple) and len(item) == 2 and item[0] == "thinking":
            if isinstance(item[1], dict):
                return (item[0], {**item[1], "cluster_lane": self._label})
        return item

    def put_nowait(self, item: Any) -> None:
        self._target.put_nowait(self._decorate(item))

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        self._target.put(self._decorate(item), block=block, timeout=timeout)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


def _lane_status(node: Any, label: str, status: str, content: str) -> None:
    target = getattr(node, "_event_queue", None)
    if target is None:
        return
    from app.core.aicall.streaming import push_event

    push_event(
        ClusterLaneQueue(target, label=label),
        "runtime_status",
        getattr(node, "node_id", "layer"),
        type="runtime_status",
        status=status,
        content=content,
    )


def _outcome_note(out: Dict[str, Any]) -> str:
    handoff = out.get("diagnosis_handoff") or {}
    targets = [t for t in handoff.get("targets") or [] if t.get("status") == "investigate"]
    excluded = len(out.get("expected_exclusions") or [])
    tail = f"，{excluded} 个按运维声明排除" if excluded else ""
    if targets:
        return f"定位完成：{len(targets)} 个待排查目标{tail}"
    if excluded:
        return f"定位完成：未发现异常{tail}"
    status = (handoff.get("pod_assessment") or {}).get("status")
    return "定位完成：未发现异常" if status == "healthy" else "定位完成"


def _run_one(node: Any, state: Dict[str, Any], cluster: str) -> Dict[str, Any]:
    """Execute a fresh location node of the same class, bound to one cluster."""
    label = multicluster.labels([cluster])[0]
    sub = type(node)(node.holmes_service, node.metrics, node.runbook_catalog)
    for attr in (
        "ai_call",
        "cancel_event",
        "workflow_config_override",
        "autonomous_parallel_enabled",
    ):
        if hasattr(node, attr):
            setattr(sub, attr, getattr(node, attr))
    sub.current_run_id = f"{getattr(node, 'current_run_id', '')}-{label}"
    tools = getattr(node, "_unscoped_tools", None) or getattr(node, "tools", []) or []
    sub.tools = multicluster.scoped_tools(list(tools), state)
    if getattr(node, "_event_queue", None) is not None:
        sub.set_event_queue(ClusterLaneQueue(node._event_queue, label=label))
    return sub.execute(state)


def _cluster_state(
    state: Dict[str, Any], cluster: str, *, annotate: bool = False
) -> Dict[str, Any]:
    contract = dict(state.get("request_contract") or {})
    label = multicluster.labels([cluster])[0]
    contract.update(clusters=[cluster], cluster_mode="single", cluster_labels=[label])
    out = {**state, "request_contract": contract}
    if annotate:
        # The tools are bound anyway; telling the model avoids it reaching for the other cluster.
        out["question"] = f"{state.get('question') or ''}（本次只定位集群 {label} 的问题）"
    return out


def _probe(cluster: str) -> Tuple[bool, str]:
    """Remote clusters must answer through the tunnel before we locate them."""
    resolved = multicluster.config().resolve(cluster)
    if resolved is None or not resolved.remote:
        return True, ""
    try:
        from aiops_edge.jobs_client import RemoteJobs

        jobs = RemoteJobs.from_config()
        return (True, "") if jobs.reachable(resolved) else (False, "cluster_unreachable")
    except Exception as exc:  # misconfiguration counts as unreachable, with its reason
        return False, str(exc)[:120]


def per_cluster_location(
    node: Any,
    state: Dict[str, Any],
    run_one: Optional[Callable[[Any, Dict[str, Any], str], Dict[str, Any]]] = None,
    probe: Optional[Callable[[str], Tuple[bool, str]]] = None,
) -> Dict[str, Any]:
    run_one = run_one or _run_one
    probe = probe or _probe
    clusters = multicluster.run_clusters(state)
    inherited = list(state.get("thinking_events") or [])

    def task(cluster: str) -> Tuple[str, Optional[Dict[str, Any]], str]:
        label = multicluster.labels([cluster])[0]
        _lane_status(node, label, "running", "正在检查集群连通性")
        # An unreachable cluster would "locate" nothing and look healthy; say it was not checked.
        reachable, reason = probe(cluster)
        if not reachable:
            note = f"集群当前不可达（{reason}），未能检查"
            _lane_status(node, label, "failed", note)
            return cluster, None, note
        _lane_status(node, label, "running", "正在定位")
        located, note = None, ""
        for attempt in range(2):
            try:
                located = run_one(node, _cluster_state(state, cluster, annotate=True), cluster)
                break
            except ModelStreamInterrupted:
                # Run e43e8298: one cluster lost its model stream and went unchecked.
                # A transport drop is transient; one fresh attempt, unless the user stopped.
                cancel = getattr(node, "cancel_event", None)
                note = "定位失败（模型连接中断" + ("，已重试 1 次）" if attempt else "）")
                if attempt or (cancel is not None and cancel.is_set()):
                    break
                _lane_status(node, label, "running", "模型连接中断，正在重新定位")
            except Exception as exc:  # one cluster must not take the others down
                note = f"定位失败（{str(exc)[:240]}）"
                break
        if located is None:
            _lane_status(node, label, "failed", note)
            return cluster, None, note
        _lane_status(node, label, "complete", _outcome_note(located))
        return cluster, located, ""

    with ThreadPoolExecutor(max_workers=max(1, len(clusters))) as pool:
        results = list(pool.map(task, clusters))

    targets: List[Dict[str, Any]] = []
    groups: List[Dict[str, Any]] = []
    analyses: List[str] = []
    events: List[Dict[str, Any]] = list(inherited)
    failures: List[str] = []
    excluded: List[str] = []
    assessments: List[Dict[str, Any]] = []
    for cluster, out, error in results:
        label = multicluster.labels([cluster])[0]
        if out is None:
            failures.append(f"{label}：{error}")
            analyses.append(f"### 集群 {label}\n\n{error}，本次结果不完整。")
            continue
        handoff = out.get("diagnosis_handoff") or {}
        for item in handoff.get("targets") or []:
            item = copy.deepcopy(item)
            item["target_id"] = f"{label}/{item['target_id']}"
            targets.append(item)
        excluded.extend(out.get("expected_exclusions") or [])
        if handoff.get("pod_assessment"):
            assessments.append(handoff["pod_assessment"])
        for group in out.get("autonomous_groups") or []:
            groups.append(
                {
                    **group,
                    "target_id": f"{label}/{group['target_id']}",
                    "cluster": cluster,
                    "cluster_label": label,
                }
            )
        analyses.append(
            f"### 集群 {label}\n\n{out.get('layer_analysis') or out.get('query_draft') or ''}"
        )
        events.extend((out.get("thinking_events") or [])[len(inherited) :])
    for index, group in enumerate(groups, 1):
        group["group_id"] = f"g{index}"

    assessment = None
    if assessments:
        assessment = min(assessments, key=lambda a: _ASSESSMENT_ORDER.get(a.get("status"), 1))
    analysis = "\n\n".join(analyses)
    output: Dict[str, Any] = {
        "diagnosis_handoff": {
            "contract_version": "location-handoff.v1",
            "targets": targets,
            "coverage": "partial" if failures else "complete",
            "coverage_note": ("未完成定位的集群：" + "；".join(failures))[:320]
            if failures
            else "",
            "pod_assessment": assessment,
        },
        "autonomous_groups": groups,
        "layer_analysis": analysis,
        "query_draft": analysis,
        "thinking_events": events,
        "diagnosis_events_start": len(events),
    }
    if excluded:
        output["expected_exclusions"] = excluded
    if failures and assessment and assessment.get("status") == "healthy":
        # A cluster that was not checked cannot be reported as "no Pod anomalies".
        assessment = {
            **assessment,
            "status": "inconclusive",
            "reason": ("未完成检查的集群：" + "；".join(failures))[:600],
        }
        output["diagnosis_handoff"]["pod_assessment"] = assessment
    if failures:
        output["cluster_failures"] = failures
        output["warnings"] = [
            *(state.get("warnings") or []),
            *(f"cluster location failed: {f}" for f in failures),
        ]
    if len(groups) == 1:
        output["request_contract"] = _cluster_state(state, groups[0]["cluster"])[
            "request_contract"
        ]
    return output
