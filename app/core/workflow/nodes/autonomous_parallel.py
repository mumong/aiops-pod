"""Bounded independent Pod lanes, without legacy diagnostic publication gates."""

import copy
import threading
import time
from typing import Any, Dict, List, Optional

from app.core.aicall.errors import ModelStreamInterrupted, raise_on_model_disconnect
from app.core.context.archive import ContextArchive
from app.core.log_context import log_context
from app.core.prompts import (
    PARALLEL_FANIN_INSTRUCTION,
    PARALLEL_LANE_QUESTION_TEMPLATE,
)
from app.core.workflow.diagnosis_contract import DiagnosisHandoff, LocationHandoff, scoped_handoff
from app.core.workflow.group_runner import iter_group_results, resolve_lane_workers
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.nodes.query_answer import build_working_material
from app.core.workflow.pod_identity import complete_pod_namespaces
from app.core.workflow.stage_material import branch_state


class LaneQueue:
    """Keep text and tools scoped to their group; never mix sibling streams.

    Thinking events from a lane are re-attributed to ``parallel_evidence`` and
    carry the authoritative group scope; everything else passes through.
    """

    def __init__(self, target: Any, *, group_id: str, entities: List[Dict[str, Any]]):
        self._target = target
        self._parallel_context = {
            "group_id": group_id,
            "entities": copy.deepcopy(entities),
        }

    def _decorate(self, item: Any) -> Any:
        if (
            isinstance(item, tuple)
            and len(item) == 2
            and item[0] == "thinking"
            and isinstance(item[1], dict)
        ):
            lane_stage = item[1].get("lane_stage") or item[1].get("node")
            decorated = {
                **item[1],
                "node": "parallel_evidence",
                "parallel_context": copy.deepcopy(self._parallel_context),
            }
            if lane_stage:
                decorated["lane_stage"] = lane_stage
            return (item[0], decorated)
        return item

    def put_nowait(self, item: Any) -> None:
        self._target.put_nowait(self._decorate(item))

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        self._target.put(self._decorate(item), block=block, timeout=timeout)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


def plan_groups(node, state):
    material = build_working_material(state)
    try:
        handoff = state.get("diagnosis_handoff")
        if handoff is None:
            return {"autonomous_groups": []}  # historical input stays serial; no re-extraction
        schema = (
            LocationHandoff
            if handoff.get("contract_version") == "location-handoff.v1"
            else DiagnosisHandoff
        )
        handoff = copy.deepcopy(handoff)
        completed = complete_pod_namespaces(
            target.get("entity")
            for target in handoff.get("targets") or []
            if isinstance(target, dict)
        )
        plan = schema.model_validate(handoff)
        targets = [t for t in plan.targets if t.status == "investigate"]
        # Existing lane runtime scopes Pod queries. Other resource kinds retain
        # the entire contract in the serial workflow rather than being dropped.
        groups = []
        if all(t.entity.kind == "Pod" and t.entity.namespace for t in targets):
            for target in targets:
                groups.append(
                    {
                        "group_id": f"g{len(groups) + 1}",
                        "target_id": target.target_id,
                        "question": "；".join(getattr(target, "next_questions", []))
                        or target.issue,
                        "entities": [target.entity.model_dump()],
                    }
                )
        if getattr(node, "current_run_id", ""):
            ContextArchive(run_id=node.current_run_id).write_json(
                "parallel/plan.json", {"input": material, "groups": groups}
            )
        result = {"autonomous_groups": groups}
        if completed:
            result["diagnosis_handoff"] = handoff  # identities completed from the API server
        return result
    except Exception as exc:
        # A formatting/provider failure must not erase the diagnosis or imply health.
        if hasattr(node.ai_call, "_push"):
            node.ai_call._push(
                node._event_queue,
                node.node_id,
                [],
                type="runtime_status",
                status="running",
                content="分组暂不可用，保留当前证据并继续单路诊断。",
            )
        return {
            "autonomous_groups": [],
            "warnings": [*(state.get("warnings") or []), f"parallel planning unavailable: {exc}"],
        }


class AutonomousParallelNode(WorkflowNode):
    # workflow.evidence.parallel.max_workers (config) > AIOPS_AUTONOMOUS_PARALLEL_WORKERS
    # (env) > 3. The model service's admission control remains the real capacity limit;
    # this bounds how many lanes one request pushes at it at once.
    autonomous_parallel_workers = None

    def lane_workers(self) -> int:
        return resolve_lane_workers(self.autonomous_parallel_workers)

    def __init__(self, holmes_service=None, metrics=None, runbook_catalog=None):
        self.holmes_service, self.metrics, self.runbook_catalog = (
            holmes_service,
            metrics,
            runbook_catalog,
        )

    @property
    def node_id(self):
        return "parallel_evidence"

    @property
    def node_name(self):
        return "分组并发诊断"

    def _run_lane(self, group, state):
        with log_context(lane=group["group_id"]):
            return self._run_lane_in_context(group, state)

    def _run_lane_in_context(self, group, state):
        from app.core.workflow.nodes.autonomous_diagnosis import (
            DiagnosisEvidenceNode,
            DiagnosisRootCauseNode,
        )

        started_at = time.time()
        # Never share the mutable AICall memory/compaction policy between workers.
        client = self.holmes_service._build_request_scoped_ai_call()
        if client is None:
            raise RuntimeError("无法创建独立诊断客户端")
        local = branch_state(state, group)
        entity = group["entities"][0]
        local["original_question"] = state.get("original_question") or state["question"]
        local["question"] = PARALLEL_LANE_QUESTION_TEMPLATE.format(
            namespace=entity["namespace"],
            name=entity["name"],
            question=group["question"],
        )
        local["original_request_contract"] = copy.deepcopy(state.get("request_contract"))
        local["request_contract"] = {
            **(state.get("request_contract") or {}),
            "scope": "pod",
            "namespaces": [entity["namespace"]],
            "pod_names": [entity["name"]],
        }
        local["shared_location_notes"] = ""
        local["shared_runbooks"] = [
            {
                "runbook_id": (e.get("tool_args") or {}).get("runbook_id"),
                "raw_ref": e["raw_ref"],
                "status": e.get("status"),
                "scope": "shared",
            }
            for e in state.get("thinking_events") or []
            if e.get("type") == "tool_result"
            and e.get("tool_name") == "fetch_runbook"
            and e.get("raw_ref")
            and e.get("status") == "success"
            and e.get("semantic_success") is not False
        ]
        local["query_draft"] = ""
        local["autonomous_groups"] = []
        local["autonomous_group_results"] = []
        inherited = len(local.get("thinking_events") or [])
        lane_run = f"{self.current_run_id}-{group['group_id']}"
        failure = None
        for cls in (DiagnosisEvidenceNode, DiagnosisRootCauseNode):
            if self.cancel_event is not None and self.cancel_event.is_set():
                failure = "cancelled"
                break
            node = cls(self.holmes_service, self.metrics, self.runbook_catalog)
            node.ai_call = client
            node.tools = list(getattr(self, "tools", []) or [])
            node.current_run_id = lane_run
            node.cancel_event = self.cancel_event
            node.workflow_config_override = getattr(self, "workflow_config_override", None)
            if self._event_queue is not None:
                node.set_event_queue(
                    LaneQueue(
                        self._event_queue, group_id=group["group_id"], entities=group["entities"]
                    )
                )
            try:
                if node._event_queue is not None:
                    client._push(
                        node._event_queue,
                        node.node_id,
                        [],
                        type="runtime_status",
                        status="running",
                        content=f"{group['group_id']}：正在{'采集证据' if node.collect else '分析根因'}",
                    )
                local.update(node.execute(local))
            except Exception as exc:
                try:
                    raise_on_model_disconnect(exc)
                except ModelStreamInterrupted:
                    self.cancel_event.set()
                    raise
                failure = f"{node.node_id}: {exc}"
                local["thinking_events"] = [
                    *(local.get("thinking_events") or []),
                    {"type": "execution_incomplete", "reason": failure},
                ]
                # Keep evidence on an RCA failure; no semantic retry or forced verdict.
                break
        material = build_working_material(local)
        material_ref = ContextArchive(run_id=lane_run).write_json(
            "cases/work-context.json", material
        )
        own_events = (local.get("thinking_events") or [])[inherited:]
        own_incomplete = any(e.get("type") == "execution_incomplete" for e in own_events)
        return {
            "group_id": group["group_id"],
            "target": group,
            "run_id": lane_run,
            "started_at": started_at,
            "status": "partial" if failure or own_incomplete else "completed",
            "error": failure,
            "material_ref": material_ref,
            "case_result": local.get("diagnosis_case_result"),
        }, own_events

    def execute(self, state):
        # Local stop signal must not mark the parent run as user-cancelled;
        # the fatal exception must reach the executor's error event instead.
        parent_cancel = self.cancel_event

        class BranchStop(threading.Event):
            def is_set(self):
                return super().is_set() or bool(parent_cancel and parent_cancel.is_set())

        self.cancel_event = BranchStop()
        groups = state.get("autonomous_groups") or []
        workers = self.lane_workers()
        results, events = {}, list(state.get("thinking_events") or [])
        for group, value, error in iter_group_results(
            groups,
            lambda g: self._run_lane(g, state),
            max_workers=workers,
            cancel=self.cancel_event,
        ):
            gid = group["group_id"]
            if isinstance(error, ModelStreamInterrupted):
                self.cancel_event.set()
                raise error
            if error is None:
                result, lane_events = value
            else:
                result = {
                    "group_id": gid,
                    "target": group,
                    "status": "partial",
                    "error": str(error),
                }
                lane_events = [{"type": "execution_incomplete", "reason": f"{gid}: {error}"}]
                if state.get("diagnosis_handoff") and group.get("target_id"):
                    retained = scoped_handoff(state["diagnosis_handoff"], group["target_id"])
                    result["material"] = {
                        "protected_handoff": {"diagnosis_handoff": retained},
                        "execution_incomplete": [str(error)],
                    }
            results[gid] = result
            result["completed_at"] = time.time()
            events.extend({**e, "lane_id": gid} for e in lane_events)
            if result["status"] == "partial" and not any(
                e.get("type") == "execution_incomplete" for e in lane_events
            ):
                events.append(
                    {
                        "type": "execution_incomplete",
                        "lane_id": gid,
                        "reason": f"{gid}: {result.get('error') or 'partial'}",
                    }
                )
            if getattr(self, "ai_call", None):
                lane_queue = (
                    LaneQueue(self._event_queue, group_id=gid, entities=group["entities"])
                    if self._event_queue is not None
                    else None
                )
                self.ai_call._push(
                    lane_queue,
                    self.node_id,
                    [],
                    type="runtime_status",
                    status="complete",
                    content=f"{gid}：{'部分完成' if result['status'] == 'partial' else '分支已结束'}",
                )
                self.ai_call._push(
                    self._event_queue,
                    self.node_id,
                    [],
                    type="runtime_status",
                    status="running",
                    content=f"分组诊断已结束 {len(results)}/{len(groups)}；{gid}：{'部分完成' if result['status'] == 'partial' else '已结束'}",
                )
        ordered = [results[g["group_id"]] for g in groups]
        warnings = list(state.get("warnings") or [])
        if getattr(self, "current_run_id", ""):
            try:
                ContextArchive(run_id=self.current_run_id).write_json(
                    "parallel/results.json", ordered
                )
            except Exception as exc:
                warnings.append(f"parallel archive failed: {exc}")
        return {
            "autonomous_group_results": ordered,
            "thinking_events": events,
            "warnings": warnings,
            "query_draft": PARALLEL_FANIN_INSTRUCTION,
        }
