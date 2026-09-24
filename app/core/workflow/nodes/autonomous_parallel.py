"""Bounded independent Pod lanes, without legacy diagnostic publication gates."""
import asyncio
import copy
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field

from app.core.aicall.client import StructuredContextBudgetError
from app.core.aicall.working_context import compact_working_material
from app.core.context.archive import ContextArchive
from app.core.prompts import (
    PARALLEL_TARGETS_PROMPT,
    PARALLEL_LANE_QUESTION_TEMPLATE,
    PARALLEL_FANIN_INSTRUCTION,
)
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.nodes.parallel_evidence import _ScopedParallelEventQueue
from app.core.workflow.nodes.query_answer import build_working_material


class PodTarget(BaseModel):
    namespace: str = Field(min_length=1)
    name: str = Field(min_length=1)
    question: str = Field(description="该对象需要调查的问题，不是已经确认的根因")


class PodTargets(BaseModel):
    targets: list[PodTarget] = Field(default_factory=list)


class LaneQueue(_ScopedParallelEventQueue):
    """Stream scoped tools, not interleaved fragments from different models."""
    @staticmethod
    def _is_text(item):
        return isinstance(item, tuple) and item[0] == "thinking" and item[1].get("type") in {"ai_token", "ai_message"}

    def put_nowait(self, item):
        if not self._is_text(item):
            super().put_nowait(item)

    def put(self, item, block=True, timeout=None):
        if not self._is_text(item):
            super().put(item, block=block, timeout=timeout)


def plan_groups(node, state):
    material = build_working_material(state)
    try:
        def classify(payload):
            return node.ai_call.call_structured(
                system_prompt=PARALLEL_TARGETS_PROMPT,
                question=json.dumps(payload, ensure_ascii=False, default=str), schema=PodTargets,
                node_id="diagnosis_targets", run_id=getattr(node, "current_run_id", ""), max_tokens=4000)
        try:
            plan, _ = classify(material)
        except StructuredContextBudgetError as exc:
            if "working_context_compaction_required" not in str(exc):
                raise
            model = node.ai_call._create_chat_model(node_id="context_compaction", disable_streaming=True).bind(max_tokens=3000)
            material = asyncio.run(compact_working_material(model, material,
                lambda **e: node.ai_call._push(node._event_queue, node.node_id, [], **e)))
            plan, _ = classify(material)
        plan = PodTargets.model_validate(plan)
        groups, seen = [], set()
        for target in plan.targets:
            key = (target.namespace, target.name)
            if key in seen:
                continue
            seen.add(key)
            groups.append({"group_id": f"g{len(groups)+1}", "question": target.question,
                           "entities": [{"kind": "Pod", "namespace": target.namespace, "name": target.name}]})
        if getattr(node, "current_run_id", ""):
            ContextArchive(run_id=node.current_run_id).write_json("parallel/plan.json", {"input": material, "groups": groups})
        return {"autonomous_groups": groups}
    except Exception as exc:
        # A formatting/provider failure must not erase the diagnosis or imply health.
        if hasattr(node.ai_call, "_push"):
            node.ai_call._push(node._event_queue, node.node_id, [], type="runtime_status", status="running",
                               content="分组暂不可用，保留当前证据并继续单路诊断。")
        return {"autonomous_groups": [], "warnings": [*(state.get("warnings") or []), f"parallel planning unavailable: {exc}"]}


class AutonomousParallelNode(WorkflowNode):
    def __init__(self, holmes_service=None, metrics=None, runbook_catalog=None):
        self.holmes_service, self.metrics, self.runbook_catalog = holmes_service, metrics, runbook_catalog

    @property
    def node_id(self):
        return "parallel_evidence"

    @property
    def node_name(self):
        return "分组并发诊断"

    def _run_lane(self, group, state):
        from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode, DiagnosisRootCauseNode
        started_at = time.time()
        # Never share the mutable AICall memory/compaction policy between workers.
        client = self.holmes_service._build_request_scoped_ai_call()
        if client is None:
            raise RuntimeError("无法创建独立诊断客户端")
        local = copy.deepcopy(state)
        local["diagnosis_target"] = group
        entity = group["entities"][0]
        local["original_question"] = state.get("original_question") or state["question"]
        local["question"] = PARALLEL_LANE_QUESTION_TEMPLATE.format(
            namespace=entity["namespace"], name=entity["name"], question=group["question"],
        )
        local["original_request_contract"] = copy.deepcopy(state.get("request_contract"))
        local["request_contract"] = {**(state.get("request_contract") or {}), "scope": "pod",
                                     "namespaces": [entity["namespace"]], "pod_names": [entity["name"]]}
        local["shared_location_notes"] = state.get("query_draft", "")
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
                node.set_event_queue(LaneQueue(self._event_queue,
                    group_id=group["group_id"], entities=group["entities"]))
            try:
                if node._event_queue is not None:
                    client._push(node._event_queue, node.node_id, [], type="runtime_status", status="running",
                                 content=f"{group['group_id']}：正在{'采集证据' if node.collect else '分析根因'}")
                local.update(node.execute(local))
            except Exception as exc:
                failure = f"{node.node_id}: {exc}"
                local["thinking_events"] = [*(local.get("thinking_events") or []),
                    {"type": "execution_incomplete", "reason": failure}]
                # Keep evidence on an RCA failure; no semantic retry or forced verdict.
                break
        material = build_working_material(local)
        own_events = (local.get("thinking_events") or [])[inherited:]
        own_incomplete = any(e.get("type") == "execution_incomplete" for e in own_events)
        return {"group_id": group["group_id"], "target": group, "run_id": lane_run,
                "started_at": started_at,
                "status": "partial" if failure or own_incomplete else "completed",
                "error": failure, "material": material}, own_events

    def execute(self, state):
        groups = state.get("autonomous_groups") or []
        workers = max(1, min(8, int(os.getenv("AIOPS_AUTONOMOUS_PARALLEL_WORKERS", "3"))))
        results, events = {}, list(state.get("thinking_events") or [])
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._run_lane, group, state): group for group in groups}
            for future in as_completed(futures):
                group = futures[future]
                gid = group["group_id"]
                try:
                    result, lane_events = future.result()
                except Exception as exc:
                    result = {"group_id": gid, "target": group, "status": "partial", "error": str(exc)}
                    lane_events = [{"type": "execution_incomplete", "reason": f"{gid}: {exc}"}]
                results[gid] = result
                result["completed_at"] = time.time()
                events.extend({**e, "lane_id": gid} for e in lane_events)
                if result["status"] == "partial" and not any(e.get("type") == "execution_incomplete" for e in lane_events):
                    events.append({"type": "execution_incomplete", "lane_id": gid, "reason": f"{gid}: {result.get('error') or 'partial'}"})
                if getattr(self, "ai_call", None):
                    lane_queue = LaneQueue(self._event_queue, group_id=gid, entities=group['entities']) if self._event_queue is not None else None
                    self.ai_call._push(lane_queue, self.node_id, [], type="runtime_status", status="complete",
                        content=f"{gid}：{'部分完成' if result['status'] == 'partial' else '分支已结束'}")
                    self.ai_call._push(self._event_queue, self.node_id, [], type="runtime_status", status="running",
                        content=f"分组诊断已结束 {len(results)}/{len(groups)}；{gid}：{'部分完成' if result['status'] == 'partial' else '已结束'}")
        ordered = [results[g["group_id"]] for g in groups]
        warnings = list(state.get("warnings") or [])
        if getattr(self, "current_run_id", ""):
            try:
                ContextArchive(run_id=self.current_run_id).write_json("parallel/results.json", ordered)
            except Exception as exc:
                warnings.append(f"parallel archive failed: {exc}")
        return {"autonomous_group_results": ordered, "thinking_events": events,
                "warnings": warnings,
                "query_draft": PARALLEL_FANIN_INSTRUCTION}
