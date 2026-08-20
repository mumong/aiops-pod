"""并发证据采集节点（多异常扇出）。

设计（2026-08-05 用户拍板，2026-08-18 收敛）：
- layer 检出的每个异常 Pod 都走本节点；默认 N=1 也进入同一 lane 契约。
- 每个异常组一条独立流水线（全新 context + 完整 max_steps 预算）：
  EvidenceCollectorNode 采集后复用正式 RootCauseAnalyzerNode，结果落盘到
  每组独立归档 {run_id}-gN。
- 不做全局 RCA：每组 formal RCA 是该组唯一根因权威；本节点之后直达
  conclusion，由其确定性拼接已校验诊断与结构化真实数据。

N 阶梯实测依据：单 context evidence 在 N=5 降级、N=10 完全塌缩
（35 项计划 0 执行）；每组独立 context 是唯一不随 N 退化的路径。
"""

import copy
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Mapping, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.entity_evidence_snapshot import (
    build_entity_evidence_snapshot,
)
from app.core.workflow.lane_diagnosis_artifact import (
    LaneDiagnosisArtifactWriter,
)
from app.core.workflow.state import WorkflowState

logger = logging.getLogger(__name__)

# 单组摘要注入 conclusion 的字符上限（摘要必须紧凑，N 份合计才装得下）
_GROUP_SUMMARY_CHAR_LIMIT = 1600


class _ScopedParallelEventQueue:
    """Attach authoritative group scope to one collector's live events."""

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
            return (
                item[0],
                decorated,
            )
        return item

    def put_nowait(self, item: Any) -> None:
        self._target.put_nowait(self._decorate(item))

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        self._target.put(self._decorate(item), block=block, timeout=timeout)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _LaneExecutionFailure(RuntimeError):
    """Carry the failed lane stage across the worker future boundary."""

    def __init__(self, stage: str, cause: Exception):
        self.stage = stage
        self.message = str(cause) or cause.__class__.__name__
        super().__init__(self.message)


def extract_abnormal_groups(layer_handoff: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从 layer_handoff 提取异常组列表；无 issue_groups 时按 Pod 逐个成组。"""
    handoff = layer_handoff or {}
    groups = [
        g for g in (handoff.get("issue_groups") or handoff.get("abnormal_groups") or [])
        if isinstance(g, dict) and (g.get("entities") or g.get("status_keywords"))
    ]
    if groups:
        return groups
    # 回退：每个 abnormal_pod 单独一组
    fallback = []
    for i, pod in enumerate(handoff.get("abnormal_pods") or [], start=1):
        if not isinstance(pod, dict) or not pod.get("name"):
            continue
        fallback.append({
            "group_id": f"g{i}",
            "status_keywords": [pod.get("status")] if pod.get("status") else [],
            "pod_abnormal_type": "",
            "entities": [{
                "kind": "Pod",
                "namespace": pod.get("namespace", ""),
                "name": pod.get("name", ""),
            }],
            "possible_scenarios": [],
        })
    return fallback


def expand_groups_to_entity_lanes(
    groups: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Split coarse Layer groups into stable one-Pod diagnostic lanes."""
    lanes: List[Dict[str, Any]] = []
    for group_index, group in enumerate(groups):
        parent_id = str(group.get("group_id") or f"g{group_index + 1}")
        entities = [
            entity
            for entity in (group.get("entities") or [])
            if isinstance(entity, dict)
            and str(entity.get("name") or "").strip()
        ]
        if len(entities) <= 1:
            lane = copy.deepcopy(group)
            lane["group_id"] = parent_id
            lane["parent_group_id"] = parent_id
            lane["presentation_index"] = len(lanes)
            lanes.append(lane)
            continue
        for entity_index, entity in enumerate(entities, start=1):
            lane = copy.deepcopy(group)
            lane["group_id"] = f"{parent_id}-p{entity_index}"
            lane["parent_group_id"] = parent_id
            lane["presentation_index"] = len(lanes)
            lane["entities"] = [copy.deepcopy(entity)]
            lanes.append(lane)
    return lanes


class ParallelEvidenceNode(WorkflowNode):
    """多异常并发诊断：每组独立采集、正式 RCA、落盘和结构化交接。"""

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

    @property
    def node_id(self) -> str:
        return "parallel_evidence"

    @property
    def node_name(self) -> str:
        return "并发证据采集"

    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]

    # ------------------------------------------------------------------
    def _max_concurrency(self, lane_count: Optional[int] = None) -> int:
        """Return lane fan-out concurrency, independent from LLM capacity.

        Historically ``max_concurrency`` limited the whole lane pool to three,
        which serialized tool I/O together with model access.  A parallel lane
        now exists for every discovered Pod by default.  Deployments that need
        an explicit safety cap can set ``lane_concurrency``; model/provider
        throttling belongs to the model client rather than this fan-out.
        """
        wf = self._get_workflow_config()
        evidence = wf.get("evidence", {}) if isinstance(wf, dict) else {}
        parallel = evidence.get("parallel", {}) if isinstance(evidence, dict) else {}
        discovered = max(1, int(lane_count or 1))
        try:
            value = int(parallel.get("lane_concurrency"))
            if value <= 0:
                return discovered
            return max(1, min(value, discovered))
        except (TypeError, ValueError):
            return discovered

    def execute(self, state: WorkflowState) -> WorkflowState:
        new_state: WorkflowState = {"current_node": self.node_id}
        question = state.get("question", "")
        run_id = state.get("run_id", "") or getattr(self, "current_run_id", "")
        handoff = state.get("layer_handoff") or {}
        parent_groups = extract_abnormal_groups(handoff)
        groups = expand_groups_to_entity_lanes(parent_groups)
        lane_inventory = [
            {
                "group_id": str(group.get("group_id") or f"g{index + 1}"),
                "parent_group_id": str(
                    group.get("parent_group_id")
                    or group.get("group_id")
                    or f"g{index + 1}"
                ),
                "presentation_index": int(
                    group.get("presentation_index")
                    if group.get("presentation_index") is not None
                    else index
                ),
                "entities": copy.deepcopy(group.get("entities") or []),
            }
            for index, group in enumerate(groups)
        ]
        # Capture the expected lanes before any worker starts.  This inventory
        # is the authoritative left side of the total fan-in contract; the
        # executor compares it with terminal results instead of inferring N
        # from whatever futures happened to return.
        new_state["parallel_lane_inventory"] = lane_inventory

        logger.info(
            "🚀 [parallel_evidence] 多异常并发采集: %d 个 Layer 组 -> %d 个 Pod lane, 并发度=%d",
            len(parent_groups), len(groups), self._max_concurrency(len(groups)),
        )

        if not groups:
            new_state.setdefault("errors", []).append(
                "parallel_evidence: layer_handoff 无异常组，无法并发采集"
            )
            new_state["group_results"] = []
            self._save_thinking(state, new_state, [])
            return new_state

        results: List[Optional[Dict[str, Any]]] = [None] * len(groups)
        merged_thinking: List[Dict[str, Any]] = []

        def run_group(index: int, group: Dict[str, Any]) -> Dict[str, Any]:
            gid = str(group.get("group_id") or f"g{index + 1}")
            stage = "lane_setup"
            try:
                scoped_state = self._build_group_state(
                    question=question,
                    state=state,
                    handoff=handoff,
                    group=group,
                    gid=gid,
                )
                attempt_records: List[Dict[str, Any]] = []

                def execute_attempt(
                    attempt: int,
                    attempt_state: WorkflowState,
                ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
                    nonlocal stage
                    logger.info(
                        "📍 [parallel_evidence:%s] ReAct attempt %d 开始 | 实体=%s",
                        gid,
                        attempt,
                        self._group_entity_labels(group),
                    )
                    collector = self._build_group_collector(
                        gid,
                        run_id,
                        group,
                        attempt=attempt,
                    )
                    stage = (
                        "evidence_collection"
                        if attempt == 1
                        else "evidence_collection_retry"
                    )
                    attempt_group_state = collector.execute(attempt_state)
                    stage = (
                        "evidence_projection"
                        if attempt == 1
                        else "evidence_projection_retry"
                    )
                    attempt_result = self._build_group_result(
                        gid,
                        group,
                        attempt_group_state,
                        run_id,
                    )
                    stage = "rca" if attempt == 1 else "rca_retry"
                    rca = self._build_group_rca(
                        gid,
                        run_id,
                        group,
                        attempt=attempt,
                    )
                    rca_state: WorkflowState = {
                        **attempt_state,
                        **attempt_group_state,
                        "entity_evidence_snapshot": attempt_result[
                            "entity_evidence_snapshot"
                        ],
                    }
                    attempt_rca_update = rca.execute(rca_state)
                    gate = self._minimum_rca_gate(
                        attempt_result,
                        attempt_rca_update,
                    )
                    attempt_records.append({
                        "diagnosis_attempt": attempt,
                        "collector_archive_run_id": getattr(
                            collector,
                            "current_run_id",
                            "",
                        ),
                        "minimum_rca_gate": gate,
                        "rca_attempts": list(
                            attempt_rca_update.get("rca_attempts") or []
                        ),
                    })
                    return (
                        attempt_result,
                        attempt_rca_update,
                        attempt_group_state,
                        gate,
                    )

                result, rca_update, group_state, gate = execute_attempt(
                    1,
                    scoped_state,
                )
                if gate.get("verdict") == "retry":
                    retry_state = self._build_retry_group_state(
                        scoped_state=scoped_state,
                        group_state=group_state,
                        result=result,
                        rca_update=rca_update,
                        feedback=gate,
                    )
                    result, rca_update, group_state, gate = execute_attempt(
                        2,
                        retry_state,
                    )
                    if gate.get("verdict") != "pass":
                        rca_update = self._force_inconclusive_rca(
                            rca_update,
                            gate,
                        )

                rca_update["rca_attempts"] = attempt_records
                stage = "diagnosis_projection"
                self._attach_validated_diagnosis(result, group, rca_update)
                stage = "artifact_persistence"
                self._persist_lane_diagnosis_artifact(result, rca_update)
                return result
            except Exception as exc:  # noqa: BLE001
                raise _LaneExecutionFailure(stage, exc) from exc

        def record_error_lane(index: int, stage: str, message: str) -> None:
            group = groups[index]
            gid = str(group.get("group_id") or f"g{index + 1}")
            error_result = self._build_terminal_error_result(
                index=index,
                group=group,
                run_id=run_id,
                stage=stage,
                message=message,
            )
            new_state.setdefault("errors", []).append(
                f"parallel_evidence:{gid}:{stage}: {message}"
            )
            try:
                self._persist_lane_diagnosis_artifact(error_result, {})
            except Exception as persist_exc:  # noqa: BLE001
                persistence_message = str(persist_exc) or persist_exc.__class__.__name__
                error_result["artifact_persistence_error"] = persistence_message
                new_state.setdefault("errors", []).append(
                    f"parallel_evidence:{gid}:artifact_persistence: "
                    f"{persistence_message}"
                )
                logger.error(
                    "❌ [parallel_evidence:%s] 错误终态归档失败: %s",
                    gid,
                    persistence_message,
                )
            results[index] = error_result

        max_workers = self._max_concurrency(len(groups))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(run_group, i, g): i for i, g in enumerate(groups)
            }
            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                    logger.info(
                        "✅ [parallel_evidence:%s] 完成 | 摘要 %d 字符",
                        results[i]["group_id"], len(results[i].get("summary") or ""),
                    )
                except Exception as exc:  # noqa: BLE001
                    gid = str(groups[i].get("group_id") or f"g{i + 1}")
                    logger.error("❌ [parallel_evidence:%s] 组采集失败: %s", gid, exc)
                    stage = (
                        exc.stage
                        if isinstance(exc, _LaneExecutionFailure)
                        else "lane_execution"
                    )
                    message = (
                        exc.message
                        if isinstance(exc, _LaneExecutionFailure)
                        else (str(exc) or exc.__class__.__name__)
                    )
                    record_error_lane(i, stage, message)

        group_results: List[Dict[str, Any]] = []
        for i, result in enumerate(results):
            if result is None:
                record_error_lane(
                    i,
                    "future_result",
                    "lane future completed without a result",
                )
                result = results[i]
            if result is None:  # defensive: record_error_lane always assigns
                raise RuntimeError("failed to construct terminal lane result")
            group_results.append(result)
        # 各组 thinking 事件合并进主流（带组标记），保证归档与展示可追溯
        for r in group_results:
            for ev in r.get("thinking_events") or []:
                merged_thinking.append({**ev, "group_id": r["group_id"]})
            # thinking 事件已合并到主 state，组结果里只留必要字段
            r["thinking_events"] = [
                ev for ev in (r.get("thinking_events") or [])
                if ev.get("type") == "tool_result"
            ]

        new_state["group_results"] = group_results
        new_state["authoritative_lane_artifacts"] = [
            result["lane_diagnosis_artifact"]
            for result in group_results
            if isinstance(result.get("lane_diagnosis_artifact"), dict)
        ]
        # 兼容下游统计口径：合并各组 evidence 完整度的简单平均
        completeness = [
            r.get("completeness") for r in group_results
            if isinstance(r.get("completeness"), (int, float))
        ]
        if completeness:
            new_state["evidence_completeness"] = sum(completeness) / len(completeness)

        self._save_thinking(state, new_state, merged_thinking)
        logger.info(
            "🎉 [parallel_evidence] 全部完成: %d/%d 组成功",
            sum(1 for r in group_results if not r.get("error")), len(groups),
        )
        return new_state

    # ------------------------------------------------------------------
    def _build_group_collector(
        self,
        gid: str,
        run_id: str,
        group: Dict[str, Any],
        *,
        attempt: int = 1,
    ) -> EvidenceCollectorNode:
        """为一个组构建独立的 evidence 采集器（共享服务，隔离归档）。"""
        collector = EvidenceCollectorNode(
            self.holmes_service, self.metrics, self.runbook_catalog,
        )
        collector.ai_call = getattr(self, "ai_call", None)
        collector.tools = getattr(self, "tools", []) or []
        collector.workflow_config_override = getattr(self, "workflow_config_override", None)
        collector.cancel_event = getattr(self, "cancel_event", None)
        # One collector invocation owns exactly one full ReAct session.  The
        # agent may use all of its max_steps; code does not start fresh
        # contexts to refill that budget or stop it after a mandatory subset.
        collector.single_react_session = True
        collector.run_observability_baseline = attempt == 1
        # 每组独立归档目录 {run_id}-gN，避免并发工具序号冲突
        attempt_suffix = "" if attempt == 1 else f"-retry{attempt}"
        collector.current_run_id = (
            f"{run_id}-{gid}{attempt_suffix}" if run_id else ""
        )
        # 共享事件队列：通过 scoped wrapper 附加权威组身份。
        queue = getattr(self, "_event_queue", None)
        if queue is not None:
            collector.set_event_queue(_ScopedParallelEventQueue(
                queue,
                group_id=gid,
                entities=group.get("entities") or [],
            ))
        return collector

    def _build_group_rca(
        self,
        gid: str,
        run_id: str,
        group: Dict[str, Any],
        *,
        attempt: int = 1,
    ) -> RootCauseAnalyzerNode:
        """Build the same formal RCA node used by the single-anomaly path."""
        rca = RootCauseAnalyzerNode(
            self.holmes_service,
            self.metrics,
            self.runbook_catalog,
        )
        rca.ai_call = getattr(self, "ai_call", None)
        rca.tools = getattr(self, "tools", []) or []
        rca.workflow_config_override = getattr(self, "workflow_config_override", None)
        rca.cancel_event = getattr(self, "cancel_event", None)
        # A failed minimum gate is repaired by a fresh, tool-capable ReAct
        # attempt.  Do not spend another model-only RCA repair inside the same
        # attempt.
        rca.disable_internal_repair = True
        attempt_suffix = "" if attempt == 1 else f"-retry{attempt}"
        rca.current_run_id = f"{run_id}-{gid}{attempt_suffix}" if run_id else ""
        queue = getattr(self, "_event_queue", None)
        if queue is not None:
            rca.set_event_queue(_ScopedParallelEventQueue(
                queue,
                group_id=gid,
                entities=group.get("entities") or [],
            ))
        return rca

    @classmethod
    def _minimum_rca_gate(
        cls,
        result: Mapping[str, Any],
        rca_update: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Catch only common, high-impact small-model publication failures.

        This is intentionally not a semantic proof of root cause.  It checks
        that a diagnosed result owns at least one code-selected causal
        candidate and that an inconclusive result did not simply ignore the
        strongest available causal Facts.
        """
        rca = cls._parse_rca_analysis(rca_update.get("rca_analysis") or "{}")
        snapshot = (
            result.get("entity_evidence_snapshot")
            if isinstance(result.get("entity_evidence_snapshot"), Mapping)
            else {}
        )
        manifest = (
            snapshot.get("selection_manifest")
            if isinstance(snapshot.get("selection_manifest"), Mapping)
            else {}
        )
        eligible = [
            str(fact_id)
            for fact_id in (manifest.get("eligible_support_fact_ids") or [])
            if str(fact_id).strip()
        ]
        causal_candidates = [
            str(fact_id)
            for fact_id in (
                manifest.get("direct_causal_candidate_fact_ids") or []
            )
            if str(fact_id).strip()
        ]
        if "direct_causal_candidate_fact_ids" not in manifest:
            fact_index = (
                snapshot.get("fact_index")
                if isinstance(snapshot.get("fact_index"), Mapping)
                else {}
            )
            selected = set(manifest.get("rca_input_fact_ids") or eligible)
            causal_candidates = [
                fact_id
                for fact_id in eligible
                if fact_id in selected
                and isinstance(fact_index.get(fact_id), Mapping)
                and str(
                    fact_index[fact_id].get("evidence_role") or ""
                ) == "causal_candidate"
                and str(fact_index[fact_id].get("directness") or "")
                == "direct"
            ]
        claim = (
            rca.get("claim_validation")
            if isinstance(rca.get("claim_validation"), Mapping)
            else rca_update.get("claim_validation")
        )
        if not isinstance(claim, Mapping):
            claim = {}
        supporting = [
            str(fact_id)
            for fact_id in (
                claim.get("valid_supporting_fact_ids")
                or rca.get("supporting_fact_ids")
                or []
            )
            if str(fact_id).strip()
        ]
        contradicting = [
            str(fact_id)
            for fact_id in (
                claim.get("valid_contradicting_fact_ids")
                or rca.get("contradicting_fact_ids")
                or []
            )
            if str(fact_id).strip()
        ]
        accounted = set(supporting) | set(contradicting)
        for hypothesis in rca.get("hypotheses") or []:
            if not isinstance(hypothesis, Mapping):
                continue
            accounted.update(
                str(fact_id)
                for fact_id in [
                    *(hypothesis.get("supporting_fact_ids") or []),
                    *(hypothesis.get("contradicting_fact_ids") or []),
                ]
                if str(fact_id).strip()
            )

        failure_codes: List[str] = []
        reasons: List[str] = []
        diagnostic_status = str(
            rca.get("diagnostic_status") or "inconclusive"
        ).lower()
        causal_support = [
            fact_id
            for fact_id in supporting
            if fact_id in set(causal_candidates)
        ]
        if diagnostic_status == "diagnosed":
            if causal_candidates and not causal_support:
                failure_codes.append("PRIMARY_CAUSAL_SUPPORT_MISSING")
                reasons.append(
                    "diagnosed result has no supporting Fact selected as a "
                    "direct causal candidate"
                )
            diagnosis_supported = claim.get("diagnosis_supported")
            if diagnosis_supported is False or (
                diagnosis_supported is None and claim.get("valid") is False
            ):
                failure_codes.append("CLAIM_VALIDATION_FAILED")
                reasons.extend(str(item) for item in (claim.get("reasons") or []))
        else:
            ignored = [
                fact_id
                for fact_id in causal_candidates
                if fact_id not in accounted
            ]
            if ignored:
                failure_codes.append("UNACCOUNTED_CAUSAL_FACT")
                reasons.append(
                    "inconclusive result did not account for available direct "
                    "causal candidates"
                )

        focus_fact_ids = [
            fact_id
            for fact_id in causal_candidates
            if fact_id not in accounted or not causal_support
        ][:8]
        return {
            "contract_version": "aiops.minimum-rca-gate.v1",
            "verdict": "retry" if failure_codes else "pass",
            "failure_codes": list(dict.fromkeys(failure_codes)),
            "reasons": list(dict.fromkeys(reason for reason in reasons if reason)),
            "focus_fact_ids": focus_fact_ids,
            "valid_supporting_fact_ids": supporting,
            "valid_contradicting_fact_ids": contradicting,
        }

    @classmethod
    def _build_retry_group_state(
        cls,
        *,
        scoped_state: Mapping[str, Any],
        group_state: Mapping[str, Any],
        result: Mapping[str, Any],
        rca_update: Mapping[str, Any],
        feedback: Mapping[str, Any],
    ) -> WorkflowState:
        """Create a fresh ReAct context with structured prior-result handoff."""
        retry_state: WorkflowState = copy.deepcopy(dict(scoped_state))
        retry_handoff = copy.deepcopy(
            scoped_state.get("layer_handoff")
            if isinstance(scoped_state.get("layer_handoff"), Mapping)
            else {}
        )
        snapshot = (
            result.get("entity_evidence_snapshot")
            if isinstance(result.get("entity_evidence_snapshot"), Mapping)
            else {}
        )
        fact_index = (
            snapshot.get("fact_index")
            if isinstance(snapshot.get("fact_index"), Mapping)
            else {}
        )
        manifest = (
            snapshot.get("selection_manifest")
            if isinstance(snapshot.get("selection_manifest"), Mapping)
            else {}
        )
        selected_ids = [
            str(fact_id)
            for fact_id in (manifest.get("rca_input_fact_ids") or [])
            if str(fact_id) in fact_index
        ]
        retry_handoff["diagnosis_retry"] = {
            "contract_version": "aiops.react-diagnosis-retry.v1",
            "attempt": 2,
            "instruction": (
                "Start one fresh ReAct investigation focused on the failed "
                "gate. Keep valid facts, collect only missing evidence, and "
                "do not merely repair JSON."
            ),
            "validation_feedback": dict(feedback),
            "previous_rca": cls._parse_rca_analysis(
                rca_update.get("rca_analysis") or "{}"
            ),
            "selection_manifest": dict(manifest),
            "selected_facts": [
                dict(fact_index[fact_id]) for fact_id in selected_ids
                if isinstance(fact_index.get(fact_id), Mapping)
            ],
        }
        retry_state["layer_handoff"] = retry_handoff
        retry_state["layer_analysis"] = json.dumps(
            retry_handoff,
            ensure_ascii=False,
            default=str,
        )
        retry_state["question"] = (
            f"{scoped_state.get('question', '')}\n"
            "（第一次诊断未通过最小证据门禁；请用一次新的完整 ReAct 调查解决反馈中的缺口。）"
        )
        retry_state["thinking_events"] = [
            copy.deepcopy(event)
            for event in (group_state.get("thinking_events") or [])
            if isinstance(event, Mapping) and event.get("type") == "tool_result"
        ]
        retry_state["evidence_analysis"] = group_state.get(
            "evidence_analysis",
            "{}",
        )
        return retry_state

    @classmethod
    def _force_inconclusive_rca(
        cls,
        rca_update: Mapping[str, Any],
        feedback: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Fail closed after the second complete ReAct attempt."""
        update = copy.deepcopy(dict(rca_update))
        parsed = cls._parse_rca_analysis(update.get("rca_analysis") or "{}")
        reasons = [
            str(item) for item in (feedback.get("reasons") or [])
            if str(item).strip()
        ] or ["second ReAct attempt did not pass the minimum RCA gate"]
        parsed.update({
            "diagnostic_status": "inconclusive",
            "root_cause": "证据不足，第二次完整调查仍未形成可发布根因",
            "root_cause_summary": "证据不足，第二次完整调查仍未形成可发布根因",
            "confidence": min(float(parsed.get("confidence") or 0.0), 0.49),
        })
        parsed["unknowns"] = list(dict.fromkeys([
            *(parsed.get("unknowns") or []),
            *reasons,
        ]))
        claim = (
            parsed.get("claim_validation")
            if isinstance(parsed.get("claim_validation"), Mapping)
            else {}
        )
        parsed["claim_validation"] = {
            **dict(claim),
            "valid": False,
            "diagnostic_status": "inconclusive",
            "reasons": list(dict.fromkeys([
                *(claim.get("reasons") or []),
                *reasons,
            ])),
        }
        update["claim_validation"] = parsed["claim_validation"]
        update["rca_analysis"] = json.dumps(
            parsed,
            ensure_ascii=False,
            default=str,
        )
        return update

    @staticmethod
    def _group_entity_labels(group: Dict[str, Any]) -> str:
        labels = []
        for e in (group.get("entities") or [])[:4]:
            if isinstance(e, dict):
                labels.append(f"{e.get('namespace', '')}/{e.get('name', '')}")
        return ",".join(labels) or "?"

    def _build_group_state(
        self,
        *,
        question: str,
        state: WorkflowState,
        handoff: Dict[str, Any],
        group: Dict[str, Any],
        gid: str,
    ) -> WorkflowState:
        """构建单组 scoped 状态：handoff 只含该组，采集范围钉死在组实体上。"""
        entities = group.get("entities") or []
        primary = entities[0] if entities and isinstance(entities[0], dict) else {}
        status_keywords = [s for s in (group.get("status_keywords") or []) if s]
        scoped_handoff = {
            "diagnosis_scope": "single_group",
            "layer": handoff.get("layer", "ABNORMAL"),
            "confidence": handoff.get("confidence", 0.5),
            "primary_problem": (
                f"[{gid}] {primary.get('namespace', '')}/{primary.get('name', '')} "
                f"{'/'.join(status_keywords)} {group.get('pod_abnormal_type', '')}"
            ).strip(),
            "abnormal_pods": [
                {
                    "name": e.get("name", ""),
                    "namespace": e.get("namespace", ""),
                    "status": (status_keywords[0] if status_keywords else None),
                }
                for e in entities if isinstance(e, dict)
            ],
            "issue_groups": [group],
            "abnormal_groups": [group],
            "pod_status_keyword": (status_keywords[0] if status_keywords else ""),
            "pod_abnormal_type": group.get("pod_abnormal_type", ""),
            "possible_scenarios": group.get("possible_scenarios") or [],
            "matched_runbooks": handoff.get("matched_runbooks") or [],
            "must_verify": [
                f"只诊断本组实体 {self._group_entity_labels(group)}，"
                "不要采集其他 namespace/Pod 的证据",
            ],
            "current_abnormal_summary": {
                "source": "parallel_evidence_group_scope",
                "status_counts": {k: 1 for k in status_keywords} or {},
                "total_abnormal": len(entities),
                "selected_rows": [],
            },
        }
        scoped_question = (
            f"只调查 {self._group_entity_labels(group)}；初始状态为 "
            f"{'/'.join(status_keywords) or '未知'}。用真实工具事实判断其当前异常、"
            "已恢复或证据不足，不查询其他 Pod。"
        )
        return {
            "question": scoped_question,
            "run_id": state.get("run_id", ""),
            "layer": state.get("layer"),
            "layer_analysis": json.dumps(scoped_handoff, ensure_ascii=False),
            "layer_handoff": scoped_handoff,
            "possible_scenarios": group.get("possible_scenarios") or [],
            # key_entities 必须是 dict（evidence planner 对每项调 .get('type')/.get('value')）
            "key_entities": [
                {
                    "type": e.get("kind", "Pod"),
                    "value": f"{e.get('namespace', '')}/{e.get('name', '')}",
                }
                for e in entities if isinstance(e, dict)
            ],
            "context_archive_ref": state.get("context_archive_ref", ""),
            "layer_archive_ref": state.get("layer_archive_ref") or {},
            "thinking_events": [],
            "errors": [],
            "warnings": [],
        }

    @staticmethod
    def _build_group_result(
        gid: str,
        group: Dict[str, Any],
        group_state: Dict[str, Any],
        run_id: str,
    ) -> Dict[str, Any]:
        """从组的 evidence 执行结果提炼落盘引用 + 摘要。"""
        evidence_analysis = group_state.get("evidence_analysis") or "{}"
        summary = ""
        legacy_text_fallback = False
        collection_summary = ""
        completeness = None
        try:
            parsed = json.loads(evidence_analysis) if isinstance(evidence_analysis, str) else evidence_analysis
            if isinstance(parsed, dict):
                summary = str(parsed.get("llm_analysis") or "").strip()
                collection_summary = str(parsed.get("collection_summary") or "").strip()
                completeness = parsed.get("plan_completeness")
        except (ValueError, TypeError):
            pass
        if not summary:
            # 回退：用最后一条 ai_message 作为组分析
            for ev in reversed(group_state.get("thinking_events") or []):
                full = str(ev.get("full_content") or "").strip()
                preview = str(ev.get("content") or "").strip()
                if ev.get("type") == "ai_message" and (full or preview):
                    summary = full or preview
                    legacy_text_fallback = True
                    break
        summary = summary[:_GROUP_SUMMARY_CHAR_LIMIT]

        snapshot = build_entity_evidence_snapshot(
            entities=group.get("entities") or [],
            evidence_analysis=evidence_analysis,
            thinking_events=group_state.get("thinking_events") or [],
            status_keywords=group.get("status_keywords") or [],
        )
        snapshot_handoff = snapshot.to_handoff()

        return {
            "group_id": gid,
            "parent_group_id": group.get("parent_group_id") or gid,
            "presentation_index": group.get("presentation_index"),
            "pod_abnormal_type": group.get("pod_abnormal_type", ""),
            "status_keywords": group.get("status_keywords") or [],
            "entities": group.get("entities") or [],
            "summary": summary,
            "legacy_text_fallback": legacy_text_fallback,
            "entity_summaries": [],
            "dimension_evidence_by_entity": snapshot_handoff[
                "dimension_evidence_by_entity"
            ],
            "entity_evidence_snapshot": snapshot_handoff,
            "collection_summary": collection_summary,
            "completeness": completeness,
            "evidence_analysis": evidence_analysis,
            "thinking_events": group_state.get("thinking_events") or [],
            "archive_run_id": f"{run_id}-{gid}" if run_id else "",
            "error": None,
        }

    @staticmethod
    def _build_terminal_error_result(
        *,
        index: int,
        group: Mapping[str, Any],
        run_id: str,
        stage: str,
        message: str,
    ) -> Dict[str, Any]:
        gid = str(group.get("group_id") or f"g{index + 1}")
        terminal_error = {
            "stage": str(stage or "lane_execution"),
            "message": str(message or "lane execution failed"),
        }
        selection_manifest: Dict[str, Any] = {"rca_input_fact_ids": []}
        snapshot = {
            "contract_version": "aiops.entity-evidence-snapshot.v1",
            "entities": list(group.get("entities") or []),
            "fact_ledgers": [],
            "fact_index": {},
            "selection_manifest": selection_manifest,
        }
        return {
            "group_id": gid,
            "parent_group_id": group.get("parent_group_id") or gid,
            "presentation_index": max(
                0,
                int(group.get("presentation_index") or index),
            ),
            "pod_abnormal_type": group.get("pod_abnormal_type", ""),
            "entities": list(group.get("entities") or []),
            "status_keywords": list(group.get("status_keywords") or []),
            "error": terminal_error["message"],
            "terminal_status": "error",
            "terminal_error": terminal_error,
            "summary": f"该组诊断失败: {terminal_error['message']}",
            "diagnostic_status": "inconclusive",
            "rca_analysis": "{}",
            "entity_summaries": [],
            "dimension_evidence_by_entity": {},
            "entity_evidence_snapshot": snapshot,
            "evidence_analysis": "{}",
            "thinking_events": [],
            "archive_run_id": f"{run_id}-{gid}" if run_id else "",
        }

    @staticmethod
    def _deterministic_entity_summary(
        entity: Dict[str, Any],
        group: Dict[str, Any],
        dimensions: Dict[str, Any],
    ) -> Dict[str, Any]:
        facts = [
            fact
            for dimension in dimensions.values()
            for fact in (dimension.get("facts") or [])
            if isinstance(fact, dict)
        ]
        phenomenon = str(facts[0].get("value") or "") if facts else "未采集到可用于归因的真实事实"
        return {
            "namespace": str(entity.get("namespace") or ""),
            "name": str(entity.get("name") or ""),
            "status": "/".join(group.get("status_keywords") or []),
            "phenomenon": phenomenon,
            "root_cause": "证据不足",
            "diagnostic_status": "inconclusive",
            "causal_chain": [],
            "confidence": 0.0,
            "supporting_fact_ids": [],
            "contradicting_fact_ids": [],
            "unknowns": ["结构化单组分析不可用，请查看各维度真实事实和归档"],
            "claim_validation": {"valid": False},
        }

    @staticmethod
    def _authoritative_artifact_entities(
        result: Mapping[str, Any],
        rca_update: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        snapshot = (
            result.get("entity_evidence_snapshot")
            if isinstance(result.get("entity_evidence_snapshot"), Mapping)
            else {}
        )
        rca_input = (
            rca_update.get("rca_input_projection")
            if isinstance(rca_update.get("rca_input_projection"), Mapping)
            else {}
        )
        authoritative_ids = list(
            rca_input.get("authoritative_entity_ids") or []
        )
        if not authoritative_ids:
            authoritative_ids = list(dict.fromkeys(
                str(entity_id)
                for ledger in (snapshot.get("fact_ledgers") or [])
                if isinstance(ledger, Mapping)
                for entity_id in (ledger.get("scope_entity_ids") or [])
                if str(entity_id).lower().startswith("k8s.pod:")
            ))
        entities = [
            dict(entity)
            for entity in (result.get("entities") or [])
            if isinstance(entity, Mapping)
        ]
        by_key = {
            f"{entity.get('namespace', '')}/{entity.get('name', '')}": entity
            for entity in entities
        }
        projected: List[Dict[str, Any]] = []
        for entity_id in authoritative_ids:
            key = ParallelEvidenceNode._entity_key_from_canonical_id(entity_id)
            entity = dict(by_key.get(key) or {})
            entity["entity_id"] = entity_id
            uid_separator = str(entity_id).rfind(":")
            scoped_separator = str(entity_id).find(":")
            if uid_separator > scoped_separator:
                entity.setdefault("uid", str(entity_id)[uid_separator + 1:])
            projected.append(entity)
        return projected or entities

    @staticmethod
    def _persist_lane_diagnosis_artifact(
        result: Dict[str, Any],
        rca_update: Mapping[str, Any],
    ) -> None:
        archive_run_id = str(result.get("archive_run_id") or "").strip()
        if not archive_run_id:
            raise ValueError("lane artifact persistence requires archive_run_id")
        snapshot = (
            result.get("entity_evidence_snapshot")
            if isinstance(result.get("entity_evidence_snapshot"), Mapping)
            else {}
        )
        selected_rca = ParallelEvidenceNode._parse_rca_analysis(
            rca_update.get("rca_analysis") or result.get("rca_analysis") or "{}"
        )
        claim_validation = (
            selected_rca.get("claim_validation")
            if isinstance(selected_rca.get("claim_validation"), Mapping)
            else rca_update.get("claim_validation")
        )
        if not isinstance(claim_validation, Mapping):
            claim_validation = {"valid": False}
        rca_input = (
            rca_update.get("rca_input_projection")
            if isinstance(rca_update.get("rca_input_projection"), Mapping)
            else {
                "contract_version": "aiops.rca-input-projection.v1",
                "authoritative_entity_ids": [
                    item.get("entity_id")
                    for item in ParallelEvidenceNode._authoritative_artifact_entities(
                        result,
                        rca_update,
                    )
                    if item.get("entity_id")
                ],
                "selection_manifest": snapshot.get("selection_manifest") or {},
                "selected_facts": [
                    fact
                    for fact_id in (
                        (snapshot.get("selection_manifest") or {}).get(
                            "rca_input_fact_ids", []
                        )
                    )
                    if (
                        fact := (snapshot.get("fact_index") or {}).get(fact_id)
                    )
                ],
            }
        )
        final_projection = {
            "terminal_status": result.get("terminal_status") or result.get(
                "diagnostic_status", "inconclusive"
            ),
            "diagnostic_status": result.get(
                "diagnostic_status", "inconclusive"
            ),
            "entity_summaries": result.get("entity_summaries") or [],
        }
        terminal_status = str(
            result.get("terminal_status")
            or result.get("diagnostic_status")
            or "inconclusive"
        ).lower()
        if terminal_status not in {"diagnosed", "inconclusive", "error"}:
            terminal_status = "inconclusive"
        terminal_error = (
            result.get("terminal_error")
            if isinstance(result.get("terminal_error"), Mapping)
            else {}
        )
        artifact = LaneDiagnosisArtifactWriter(archive_run_id).persist(
            group_id=str(result.get("group_id") or "unknown"),
            parent_group_id=str(
                result.get("parent_group_id")
                or result.get("group_id")
                or "unknown"
            ),
            presentation_index=max(
                0,
                int(result.get("presentation_index") or 0),
            ),
            authoritative_entities=(
                ParallelEvidenceNode._authoritative_artifact_entities(
                    result,
                    rca_update,
                )
            ),
            snapshot=snapshot,
            selection_manifest=(
                snapshot.get("selection_manifest")
                if isinstance(snapshot.get("selection_manifest"), Mapping)
                else {}
            ),
            rca_input=rca_input,
            rca_attempts=list(rca_update.get("rca_attempts") or []),
            selected_rca=selected_rca,
            claim_validation=dict(claim_validation),
            final_projection=final_projection,
            terminal_error=dict(terminal_error),
            terminal_status=terminal_status,
        )
        result["terminal_status"] = terminal_status
        result["lane_diagnosis_artifact"] = artifact
        result["lane_diagnosis_artifact_ref"] = artifact["artifact_ref"]

    @staticmethod
    def _parse_rca_analysis(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return copy.deepcopy(value)
        try:
            parsed = json.loads(value) if value else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _causal_chain_steps(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if not isinstance(value, dict):
            return []
        preferred = ("trigger", "mechanism", "manifestation")
        values = [value.get(key) for key in preferred if value.get(key) not in (None, "")]
        values.extend(
            item for key, item in value.items()
            if key not in preferred and item not in (None, "", [], {})
        )
        return [
            json.dumps(item, ensure_ascii=False, default=str)
            if isinstance(item, (dict, list)) else str(item)
            for item in values
        ]

    @staticmethod
    def _entity_key_from_canonical_id(value: Any) -> str:
        text = str(value or "").strip()
        prefix = "k8s.pod:"
        if not text.lower().startswith(prefix):
            return ""
        scoped = text[len(prefix):]
        namespace, separator, remainder = scoped.partition("/")
        if not separator:
            return ""
        name = remainder.split(":", 1)[0]
        return f"{namespace}/{name}" if namespace and name else ""

    def _attach_validated_diagnosis(
        self,
        result: Dict[str, Any],
        group: Dict[str, Any],
        rca_update: Dict[str, Any],
    ) -> None:
        """Project one already-validated formal RCA into entity summaries."""
        entities = [item for item in (group.get("entities") or []) if isinstance(item, dict)]
        dimensions_by_entity = result.get("dimension_evidence_by_entity") or {}
        allowed_entities = {
            f"{item.get('namespace', '')}/{item.get('name', '')}": item
            for item in entities
        }
        fact_owner: Dict[str, str] = {}
        for key in allowed_entities:
            for dimension in (dimensions_by_entity.get(key) or {}).values():
                for fact in dimension.get("facts") or []:
                    if isinstance(fact, dict) and fact.get("fact_id"):
                        fact_owner[str(fact["fact_id"])] = key

        rca_analysis_raw = rca_update.get("rca_analysis") or "{}"
        rca = self._parse_rca_analysis(rca_analysis_raw)
        diagnostic_status = str(rca.get("diagnostic_status") or "inconclusive")
        claim_validation = (
            copy.deepcopy(rca.get("claim_validation"))
            if isinstance(rca.get("claim_validation"), dict)
            else {"valid": False}
        )
        hypotheses_by_key: Dict[str, Dict[str, Any]] = {}
        for hypothesis in rca.get("hypotheses") or []:
            if not isinstance(hypothesis, dict):
                continue
            refs = [
                str(item) for item in [
                    *(hypothesis.get("supporting_fact_ids") or []),
                    *(hypothesis.get("contradicting_fact_ids") or []),
                ] if str(item).strip()
            ]
            candidate_keys = {
                fact_owner[fact_id] for fact_id in refs if fact_id in fact_owner
            }
            entity_key = self._entity_key_from_canonical_id(hypothesis.get("entity_id"))
            if entity_key:
                candidate_keys.add(entity_key)
            candidate_keys &= set(allowed_entities)
            if len(candidate_keys) == 1:
                candidate_key = next(iter(candidate_keys))
                current = hypotheses_by_key.get(candidate_key)
                if current is None or float(hypothesis.get("confidence") or 0.0) > float(
                    current.get("confidence") or 0.0
                ):
                    hypotheses_by_key[candidate_key] = hypothesis

        by_key: Dict[str, Dict[str, Any]] = {}
        for key, entity in allowed_entities.items():
            hypothesis = hypotheses_by_key.get(key)
            # The validated top-level RCA is the selected conclusion for a
            # single-entity group. Hypotheses may include alternatives.
            source = rca if len(allowed_entities) == 1 else (hypothesis or {})
            supporting = [
                str(fact_id) for fact_id in source.get("supporting_fact_ids") or []
                if fact_owner.get(str(fact_id)) == key
            ]
            contradicting = [
                str(fact_id) for fact_id in source.get("contradicting_fact_ids") or []
                if fact_owner.get(str(fact_id)) == key
            ]
            entity_diagnosed = diagnostic_status == "diagnosed" and bool(supporting)
            if not source or not entity_diagnosed:
                fallback = self._deterministic_entity_summary(
                    entity,
                    group,
                    dimensions_by_entity.get(key) or {},
                )
                fallback["unknowns"] = list(dict.fromkeys([
                    *(source.get("unknowns") or []),
                    *(rca.get("unknowns") or []),
                    "正式 RCA 未返回当前实体的有效 supporting_fact_ids",
                ]))
                fallback["claim_validation"] = claim_validation
                by_key[key] = fallback
                continue

            root_cause = str(
                source.get("summary")
                or source.get("root_cause_summary")
                or source.get("root_cause")
                or "证据不足"
            )
            by_key[key] = {
                "namespace": str(entity.get("namespace") or ""),
                "name": str(entity.get("name") or ""),
                "status": "/".join(group.get("status_keywords") or []),
                "phenomenon": str(rca.get("phenomenon") or root_cause),
                "root_cause": root_cause,
                "diagnostic_status": "diagnosed",
                "causal_chain": self._causal_chain_steps(rca.get("causal_chain")),
                "confidence": float(source.get("confidence") or rca.get("confidence") or 0.0),
                "supporting_fact_ids": supporting,
                "contradicting_fact_ids": contradicting,
                "unknowns": list(source.get("unknowns") or []),
                "claim_validation": claim_validation,
            }

        for key, entity in allowed_entities.items():
            if key not in by_key:
                by_key[key] = self._deterministic_entity_summary(
                    entity,
                    group,
                    dimensions_by_entity.get(key) or {},
                )
        result["entity_summaries"] = [by_key[key] for key in allowed_entities]
        result["diagnostic_status"] = diagnostic_status
        result["rca_analysis"] = (
            rca_analysis_raw
            if isinstance(rca_analysis_raw, str)
            else json.dumps(rca_analysis_raw, ensure_ascii=False, default=str)
        )
        if rca and diagnostic_status == "diagnosed":
            result["summary"] = str(
                rca.get("root_cause_summary")
                or rca.get("root_cause")
                or result.get("summary")
                or ""
            )
