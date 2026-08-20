"""
节点2：证据链采集

职责：
- 调用 LLM 规划需要采集的证据
- 调用工具实际采集证据
- 记录 LLM 调用和工具调用统计
- 详细的输出，详细的给证据具有逻辑性
- 输出：evidence_items, evidence_analysis, evidence_completeness, tool_results

设计：
- 有自己的专用 prompt
- 调用 LLM 进行证据规划（使用和 HolmesService 相同的方式）
- 支持使用 runbooks 和 tools
- 统计 LLM 调用和工具调用次数
"""

import json
import logging
import os
import re
import shlex
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from app.core.context.archive import ContextArchive
from app.core.workflow.diagnosis_state import (
    DiagnosisSubmission,
    EvidenceSlotDiagnosisSubmission,
    bind_evidence_slots,
    submission_to_rca,
)
from app.core.workflow.entity_evidence_snapshot import (
    EntityEvidenceSnapshot,
    build_entity_evidence_snapshot,
)
from app.core.workflow.fact_contract import (
    build_kubernetes_lifecycle_fact_ledger,
    build_observability_query_fact_ledger,
    compact_aiops_legacy_context_json,
    compact_fact_ledgers_json,
    is_observability_event_semantic_success,
    normalize_topology_query_fact_value,
    normalize_case_fact_ledger,
    normalize_fact_ledger,
    project_final_observability_events,
    validate_rca_claims,
)
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import EvidenceCollectionOutput, EvidencePlanOutput, QueryResult
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer, EvidenceItem, EvidenceLevel
from app.core.prompts import (
    AUTONOMOUS_DIAGNOSIS_AGENT_PROMPT,
    EVIDENCE_PLAN_PROTOCOL_DYNAMIC,
    EVIDENCE_PLAN_PROTOCOL_EXISTING,
    EVIDENCE_PLAN_PROTOCOL_PREPLANNED,
    EVIDENCE_USER_MESSAGE_TEMPLATE,
    get_workflow_prompt,
    get_query_evidence_normalization_prompt,
)

logger = logging.getLogger(__name__)


class EvidenceCollectorNode(WorkflowNode):
    """
    证据链采集节点

    每次执行都会：
    1. 调用 LLM 规划需要采集的证据
    2. 调用工具实际采集证据
    3. 统计 LLM 调用和工具调用次数
    4. 计算证据完整度
    """

    _AIOPS_DETAIL_TOOLS = {
        "get_aiops_case_evidence",
        "query_aiops_k8s_snapshot",
        "query_aiops_metrics",
        "query_aiops_logs",
        "query_aiops_deepflow_flows",
        "build_aiops_topology",
    }
    _OBSERVABILITY_QUERY_ORDER = (
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
        "query_pod_topology",
    )
    # Code-owned pre-ReAct baseline covers Kubernetes lifecycle plus the three
    # observability signals. Layer only establishes identity and coarse status;
    # describe is the generic source of container state, events and config.
    # Topology remains an optional follow-up rather than a baseline dimension.
    _PRE_REACT_BASELINE_TOOLS = (
        "kubectl_describe",
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
    )
    _OBSERVABILITY_QUERY_TOOLS = set(_OBSERVABILITY_QUERY_ORDER)
    _QUERY_ONLY_PROMETHEUS_TOOLS = {
        "list_prometheus_rules",
        "get_metric_names",
        "get_label_values",
        "get_all_labels",
        "get_series",
        "get_metric_metadata",
        "execute_prometheus_instant_query",
        "execute_prometheus_range_query",
    }
    _KUBERNETES_LIFECYCLE_AUTHORITY_TOOLS = {
        "kubectl_describe",
        "kubectl_get_yaml",
    }
    _AUTONOMOUS_DIAGNOSIS_TOOLS = {
        "fetch_runbook",
        "get_aiops_case_evidence",
        "query_aiops_k8s_snapshot",
        "query_aiops_metrics",
        "query_aiops_logs",
        "query_aiops_deepflow_flows",
        "build_aiops_topology",
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
        "query_pod_topology",
        "kubectl_describe",
        "kubectl_events",
        "kubectl_get",
        "kubectl_get_pod",
        "kubectl_get_yaml",
        "kubectl_get_by_name",
        "kubectl_get_by_kind_in_namespace",
        "kubectl_get_by_kind_in_cluster",
        "kubectl_find_resource",
        "kubectl_container_logs",
        "kubectl_container_previous_logs",
        "kubectl_logs",
        "kubectl_previous_logs",
        "kubectl_logs_all_containers",
        "kubectl_previous_logs_all_containers",
        "kubectl_logs_grep",
        "kubectl_logs_all_containers_grep",
        "kubectl_top_pods",
        "kubectl_top_nodes",
        "kubectl_lineage_parents",
        "kubectl_lineage_children",
        "kubectl_verify",
    }
    _DNS1123_LABEL_RE = re.compile(
        r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
    )
    _SYSTEM_FORCED_PLAN_SOURCES = {
        "mandatory_live_observability",
        "observability_first_round_gate",
        "structured_plan_fallback",
    }
    _STRUCTURED_PLAN_TERMINAL_REASON = (
        "结构化证据计划为空且没有已确认的 Pod 目标，未执行工具"
    )

    def __init__(
        self,
        holmes_service: Any = None,
        metrics: Any = None,
        runbook_catalog: Any = None,
    ):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 和工具调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog
        self._logged_evidence_user_prompt = False
        self._early_stop_state = {
            "triggered": False,
            "reason": "",
            "required_levels": ["critical", "important"],
        }

    @property
    def node_id(self) -> str:
        return "evidence"

    @property
    def node_name(self) -> str:
        return "证据链采集"


    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]

    def _is_autonomous_observability_enabled(self) -> bool:
        workflow = self._get_workflow_config()
        evidence = workflow.get("evidence", {}) if isinstance(workflow, dict) else {}
        mode = evidence.get("observability_mode") if isinstance(evidence, dict) else None
        return str(mode or "").strip().lower() == "autonomous"

    def _is_observability_first_round_gate_enabled(self) -> bool:
        if not self._is_autonomous_observability_enabled():
            return False
        workflow = self._get_workflow_config()
        evidence = workflow.get("evidence", {}) if isinstance(workflow, dict) else {}
        gate = (
            evidence.get("observability_first_round_gate", {})
            if isinstance(evidence, dict)
            else {}
        )
        if isinstance(gate, dict) and "enabled" in gate:
            return self._parse_bool_config(gate.get("enabled"), True)
        return True

    @staticmethod
    def _has_semantic_tool_success(thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and ev.get("semantic_success", True) is not False
            for ev in (thinking_events or [])
        )

    @classmethod
    def _has_effective_tool_evidence(cls, thinking_events: List[Dict[str, Any]]) -> bool:
        """A tool result is effective when it is positive evidence or a diagnostic failure.

        Some probes intentionally fail when the cluster dependency is broken,
        e.g. `curl registry-1.docker.io` timing out. Those must count as
        collected evidence instead of triggering a retry.
        """
        return cls._has_semantic_tool_success(thinking_events) or cls._has_diagnostic_negative_tool_result(thinking_events)

    @classmethod
    def _has_diagnostic_negative_tool_result(cls, thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and cls._is_diagnostic_negative_tool_result(
                ev.get("tool_name", ""),
                ev.get("result", ev.get("result_preview", "")),
                ev.get("structured") or {},
            )
            for ev in (thinking_events or [])
        )

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行证据采集逻辑

        流程：
        1. 调用 LLM 规划需要采集的证据
        2. 根据规划调用工具采集证据
        3. 解析工具输出，标记哪些证据已采集
        4. 计算证据完整度
        5. 记录 LLM 调用和工具调用次数到 metrics
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }
        self._diagnosis_submission = None

        try:
            question = state.get("question", "")
            layer = state.get("layer")
            layer_analysis = state.get("layer_analysis", "{}")
            layer_handoff = state.get("layer_handoff") or self._parse_layer_handoff(layer_analysis)
            possible_scenarios = state.get("possible_scenarios", [])
            key_entities = state.get("key_entities", [])

            logger.info(f"📋 证据采集: 层级={layer}, 可能场景={possible_scenarios}")
            logger.debug(f"📋 [DEBUG] 证据采集输入: question={question[:100]}, "
                        f"layer_handoff长度={len(json.dumps(layer_handoff, ensure_ascii=False, default=str))}, "
                        f"key_entities={key_entities}")
            self._early_stop_state = {
                "triggered": False,
                "reason": "",
                "required_levels": ["critical", "important"],
            }
            self._logged_evidence_user_prompt = False
            self._structured_plan_terminal_empty = False
            self._structured_plan_failure_reason = ""

            # 1. 调用 LLM 规划证据采集计划
            evidence_plan, thinking_events, llm_result_text = self._plan_evidence_with_llm(
                question=question,
                layer=layer,
                possible_scenarios=possible_scenarios,
                key_entities=key_entities,
                layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
                context_archive_ref=state.get("context_archive_ref", ""),
                layer_archive_ref=state.get("layer_archive_ref") or {},
            )
            retry_reason = self._get_plan_protocol_failure_reason(
                evidence_plan=evidence_plan,
                thinking_events=thinking_events,
            )
            if (
                retry_reason
                and not self._structured_plan_terminal_empty
                and not bool(getattr(self, "single_react_session", False))
            ):
                retry_existing_plan = (
                    evidence_plan
                    if self._plan_exists_without_tool_results(retry_reason)
                    else None
                )
                logger.warning("⚠️ [evidence] 首轮结果违反采证协议：%s；发起一次重试", retry_reason)
                evidence_plan, thinking_events, llm_result_text = self._plan_evidence_with_llm(
                    question=question,
                    layer=layer,
                    possible_scenarios=possible_scenarios,
                    key_entities=key_entities,
                    layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
                    context_archive_ref=state.get("context_archive_ref", ""),
                    layer_archive_ref=state.get("layer_archive_ref") or {},
                    strict_mode=retry_existing_plan is None,
                    failure_reason=(
                        "上一轮 evidence_plan 已有效，本轮不要重新输出 evidence_plan；"
                        "请直接按既有计划调用至少一个 critical 或 important 级真实工具。"
                        if retry_existing_plan
                        else retry_reason
                    ),
                    existing_plan=retry_existing_plan,
                )

            # 2. 构建证据项列表（基于 thinking_events 中 AICall 真实工具调用）
            tool_results = []
            evidence_items = self._build_evidence_items_from_thinking(
                evidence_plan=evidence_plan,
                thinking_events=thinking_events,
            )
            upstream_evidence_items = self._build_upstream_evidence_items(
                evidence_plan=evidence_plan,
                thinking_events=state.get("thinking_events", []),
            )
            if not self._early_stop_state.get("triggered"):
                self._early_stop_state = self._derive_early_stop_state(
                    evidence_plan,
                    evidence_items,
                    thinking_events=thinking_events,
                )

            # 2.1 回退：evidence 节点没采集到证据时，从 layer 阶段的 thinking_events 统计
            if not evidence_items and not upstream_evidence_items:
                layer_thinking = state.get("thinking_events", [])
                layer_tool_events = [
                    ev
                    for ev in self._project_final_evidence_events(
                        layer_thinking
                    )
                    if ev.get("type") == "tool_result"
                    and ev.get("status") == "success"
                    and ev.get("node") == "layer"
                    and ev.get("tool_name", "").lower() not in self._NON_EVIDENCE_TOOLS
                ]
                if layer_tool_events:
                    logger.info("📊 [evidence] evidence 节点未采集新证据，"
                                "回退到 layer 阶段的 %d 个工具调用", len(layer_tool_events))
                    for ti, ev in enumerate(layer_tool_events):
                        evidence_items.append(EvidenceItem(
                            id=f"layer_{ti}",
                            description=f"上游采集: {ev.get('tool_name', '')}",
                            level=EvidenceLevel.IMPORTANT,
                            weight=0.2,
                            collected=True,
                            value=(ev.get("result", "") or ev.get("result_preview", ""))[:500],
                            source="layer_fallback",
                        ))

            # 3. 计算完整度
            skipped_plan_ids = self._classify_sufficient_evidence_skips(
                evidence_plan=evidence_plan,
                evidence_items=evidence_items,
                early_stop=self._early_stop_state,
            )
            combined_evidence_items = self._merge_evidence_items(evidence_items, upstream_evidence_items)
            # Layer observations remain visible in the inventory, but evidence
            # completeness only measures the evidence node's deduplicated plan.
            completeness = self._calculate_completeness(evidence_items)

            # 4. 更新 metrics（记录 LLM 调用和工具调用次数）
            self._update_metrics(evidence_plan, tool_results)

            # 5. 从 thinking_events 提取 MCP 工具的真实输出数据
            tool_data_from_llm = self._extract_tool_data_from_thinking(thinking_events)
            evidence_tool_stats = self._calculate_evidence_tool_stats(
                evidence_plan=evidence_plan,
                thinking_events=thinking_events,
                evidence_items=evidence_items,
                upstream_evidence_items=upstream_evidence_items,
            )
            observability_target_stats = self._calculate_observability_target_coverage(
                evidence_plan=evidence_plan,
                thinking_events=thinking_events,
            )
            diagnostic_evidence_stats = self._calculate_diagnostic_evidence_coverage(
                thinking_events
            )
            source_coverage = self._calculate_source_coverage(thinking_events)
            detail_retrieval = self._calculate_detail_retrieval(thinking_events)
            unresolved_questions = self._build_unresolved_questions(
                thinking_events,
                diagnostic_evidence_stats,
            )

            # 6. 构建证据清单（真实数据，供 conclusion LLM 引用）
            # plan_total 保持与模型输出的 evidence_plan 对齐；environment_total
            # 只统计真实环境证据。报告同时展示两个口径，避免用户看到
            # evidence_plan=4 项但“证据完整度 3/3”这种不直观结果。
            measurable_items = self._measurable_evidence_items(evidence_items)
            plan_stats = self._calculate_plan_completeness(evidence_items, upstream_evidence_items)
            plan_collected = plan_stats["plan_collected"]
            plan_total = plan_stats["plan_total"]
            collected = sum(1 for e in measurable_items if e.collected)
            total = len(measurable_items)
            not_collected = [e for e in measurable_items if not e.collected]
            plan_completeness = plan_stats["plan_completeness"]
            evidence_facts = self._build_evidence_facts(combined_evidence_items)
            evidence_conflicts = self._build_evidence_conflicts(tool_data_from_llm, layer_handoff)
            missing_evidence = [
                {"id": e.id, "description": e.description, "level": e.level.value if hasattr(e.level, "value") else str(e.level)}
                for e in not_collected
            ]

            plan_by_id = self._index_evidence_plan_by_id(evidence_plan)
            evidence_inventory = []
            for e in combined_evidence_items:
                plan_item = plan_by_id.get(str(e.id), {})
                evidence_inventory.append({
                    "id": e.id,
                    "description": e.description,
                    "level": e.level.value if hasattr(e.level, 'value') else str(e.level),
                    "tool": plan_item.get("tool", ""),
                    "command": plan_item.get("command", ""),
                    "purpose": plan_item.get("purpose", ""),
                    "collected": e.collected,
                    "source": getattr(e, 'source', ''),
                    "outcome": getattr(e, 'outcome', 'unknown'),
                })

            # 未采集原因说明
            missing_reasons = []
            for e in not_collected:
                source = getattr(e, 'source', '')
                if source == "planned":
                    missing_reasons.append(f"{e.id}({e.description}): 已规划但工具执行失败或无匹配结果")
                else:
                    missing_reasons.append(f"{e.id}({e.description}): 未采集")
            if self._structured_plan_terminal_empty:
                missing_reasons.append(
                    self._structured_plan_failure_reason
                    or self._STRUCTURED_PLAN_TERMINAL_REASON
                )

            collection_output = self._build_evidence_collection_output(
                evidence_plan=evidence_plan,
                tool_results=tool_results,
                tool_data=tool_data_from_llm,
                llm_result_text=llm_result_text,
                plan_total=plan_total,
                plan_collected=plan_collected,
                plan_completeness=plan_completeness,
                environment_total=total,
                environment_collected=collected,
                environment_completeness=completeness,
                evidence_inventory=evidence_inventory,
                missing_reasons=missing_reasons,
                early_stop=dict(self._early_stop_state),
                executed_tool_count=evidence_tool_stats["executed_tool_count"],
                matched_tool_count=evidence_tool_stats["matched_tool_count"],
                unplanned_tool_count=evidence_tool_stats["unplanned_tool_count"],
                case_tool_count=evidence_tool_stats["case_tool_count"],
                supplemental_tool_count=evidence_tool_stats["supplemental_tool_count"],
                skipped_plan_count=len(skipped_plan_ids),
                observability_target_total=observability_target_stats["observability_target_total"],
                observability_target_collected=observability_target_stats["observability_target_collected"],
                observability_target_completeness=observability_target_stats[
                    "observability_target_completeness"
                ],
                diagnostic_evidence_total=diagnostic_evidence_stats[
                    "diagnostic_evidence_total"
                ],
                diagnostic_evidence_collected=diagnostic_evidence_stats[
                    "diagnostic_evidence_collected"
                ],
                diagnostic_evidence_completeness=diagnostic_evidence_stats[
                    "diagnostic_evidence_completeness"
                ],
                diagnostic_evidence_missing=diagnostic_evidence_stats[
                    "diagnostic_evidence_missing"
                ],
                dimension_coverage_total=diagnostic_evidence_stats[
                    "dimension_coverage_total"
                ],
                dimension_coverage_collected=diagnostic_evidence_stats[
                    "dimension_coverage_collected"
                ],
                dimension_coverage=diagnostic_evidence_stats[
                    "dimension_coverage"
                ],
                diagnostic_sufficiency=diagnostic_evidence_stats[
                    "diagnostic_sufficiency"
                ],
                diagnostic_sufficiency_label=diagnostic_evidence_stats[
                    "diagnostic_sufficiency_label"
                ],
                source_coverage=source_coverage,
                detail_retrieval=detail_retrieval,
                unresolved_questions=unresolved_questions,
                plan_status=(
                    "terminal_empty"
                    if self._structured_plan_terminal_empty
                    else "ready"
                ),
                plan_failure_reason=self._structured_plan_failure_reason,
            )

            new_state.update({
                "evidence_items": combined_evidence_items,
                "evidence_analysis": self._publish_evidence_analysis(
                    collection_output
                ),
                "evidence_completeness": (
                    diagnostic_evidence_stats["diagnostic_sufficiency"]
                    if diagnostic_evidence_stats["diagnostic_evidence_total"]
                    else completeness
                ),
                "tool_results": tool_results,
                "evidence_facts": evidence_facts,
                "evidence_conflicts": evidence_conflicts,
                "missing_evidence": missing_evidence,
                "diagnosis_submission": deepcopy(
                    getattr(self, "_diagnosis_submission", None)
                ),
                "query_result": self._build_query_result(
                    question=question,
                    layer=layer,
                    evidence_plan=evidence_plan,
                    evidence_inventory=evidence_inventory,
                    tool_data=tool_data_from_llm,
                    collection_summary=collection_output.collection_summary,
                    missing_reasons=missing_reasons,
                ) if layer == Layer.QUERY else None,
            })

            logger.info(f"✅ 证据采集完成: {collected}/{total} 项, 完整度 {completeness:.0%}")
            if self._early_stop_state.get("triggered"):
                logger.info("🛑 [evidence] 动态提前停止: %s",
                            self._early_stop_state.get("reason", "critical 和 important 级证据均已满足"))
            if missing_reasons:
                logger.info(f"   未采集证据 ({len(missing_reasons)} 项):")
                for reason in missing_reasons:
                    logger.info(f"     - {reason}")
            logger.info(f"   LLM 调用: 1 次, 工具调用: {len(tool_results)} 次")

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

        except Exception as e:
            logger.error(f"证据采集失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "evidence_items": [],
                "evidence_analysis": "{}",
                "evidence_completeness": 0.0,
                "tool_results": [],
                "diagnosis_submission": None,
            })
            self._save_thinking(state, new_state, [])

        return new_state

    @staticmethod
    def _parse_layer_handoff(layer_analysis: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(layer_analysis) if layer_analysis else {}
            if isinstance(parsed, dict):
                handoff = {
                    "layer": parsed.get("layer"),
                    "confidence": parsed.get("confidence"),
                    "primary_problem": parsed.get("reasoning", ""),
                    "active_entities": (
                        parsed.get("active_entities")
                        or parsed.get("key_entities", [])
                    ),
                    "possible_scenarios": parsed.get("possible_scenarios", []),
                    "must_verify": ["基于真实 tool_result 重新验证上游定位"],
                }
                for field in (
                    "primary_pod",
                    "primary_entities",
                    "abnormal_pods",
                    "issue_groups",
                    "abnormal_groups",
                ):
                    if field in parsed:
                        handoff[field] = parsed.get(field)
                return handoff
        except (json.JSONDecodeError, TypeError):
            pass
        return {}

    @staticmethod
    def _build_evidence_facts(evidence_items: List[EvidenceItem]) -> List[Dict[str, Any]]:
        facts = []
        for item in evidence_items:
            if not item.collected:
                continue
            facts.append({
                "id": item.id,
                "description": item.description,
                "level": item.level.value if hasattr(item.level, "value") else str(item.level),
                "value": (item.value or "")[:500],
                "source": getattr(item, "source", ""),
            })
        return facts

    @staticmethod
    def _build_evidence_collection_output(
        evidence_plan: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        tool_data: List[Dict[str, Any]],
        llm_result_text: str,
        plan_total: int,
        plan_collected: int,
        plan_completeness: float,
        environment_total: int,
        environment_collected: int,
        environment_completeness: float,
        evidence_inventory: List[Dict[str, Any]],
        missing_reasons: List[str],
        early_stop: Dict[str, Any],
        executed_tool_count: int = 0,
        matched_tool_count: int = 0,
        unplanned_tool_count: int = 0,
        case_tool_count: int = 0,
        supplemental_tool_count: int = 0,
        skipped_plan_count: int = 0,
        observability_target_total: int = 0,
        observability_target_collected: int = 0,
        observability_target_completeness: float = 0.0,
        diagnostic_evidence_total: int = 0,
        diagnostic_evidence_collected: int = 0,
        diagnostic_evidence_completeness: float = 0.0,
        diagnostic_evidence_missing: Optional[List[str]] = None,
        dimension_coverage_total: int = 0,
        dimension_coverage_collected: int = 0,
        dimension_coverage: float = 0.0,
        diagnostic_sufficiency: float = 0.0,
        diagnostic_sufficiency_label: str = "",
        source_coverage: Optional[Dict[str, Any]] = None,
        detail_retrieval: Optional[Dict[str, Any]] = None,
        unresolved_questions: Optional[List[str]] = None,
        plan_status: str = "ready",
        plan_failure_reason: str = "",
    ) -> EvidenceCollectionOutput:
        is_first_round_gate = any(
            isinstance(item, dict)
            and item.get("source") == "observability_first_round_gate"
            for item in (evidence_plan or [])
        )
        observability_summary = (
            (
                "首轮可观测查询执行 "
                if is_first_round_gate
                else "Pod 可观测性覆盖 "
            )
            + f"{observability_target_collected}/"
            f"{observability_target_total}，完整度 {observability_target_completeness:.0%}"
            if observability_target_total
            else "Pod 可观测性覆盖不适用"
        )
        return EvidenceCollectionOutput.model_validate({
            "evidence_plan": evidence_plan,
            "tool_results": [r.get("summary", "") for r in tool_results],
            "tool_data": tool_data,
            "llm_analysis": llm_result_text[:3000] if llm_result_text else "",
            "plan_status": plan_status,
            "plan_failure_reason": plan_failure_reason,
            "collection_summary": (
                f"{observability_summary}；"
                f"去重后证据计划 {plan_total} 项，实际采集 {plan_collected} 项，"
                f"未采集 {plan_total - plan_collected} 项，完整度 {plan_completeness:.0%}；"
                f"evidence 节点真实环境证据 {environment_collected}/{environment_total} 项，"
                f"完整度 {environment_completeness:.0%}；"
                f"决定性多维证据 {diagnostic_evidence_collected}/"
                f"{diagnostic_evidence_total} 项，维度覆盖 "
                f"{dimension_coverage:.0%}，诊断充分度 "
                f"{diagnostic_sufficiency:.0%}"
                f"（{diagnostic_sufficiency_label or '未评估'}）；"
                + (
                    f"补充计划 {skipped_plan_count} 项因实时 case 已完整而跳过；"
                    if skipped_plan_count
                    else ""
                )
                +
                f"evidence 节点实际执行工具 {executed_tool_count} 个，"
                f"其中核心 case {case_tool_count} 个、补充证据 {supplemental_tool_count} 个；"
                f"已满足计划项 {matched_tool_count} 个，计划外补证 {unplanned_tool_count} 个"
            ),
            "plan_total": plan_total,
            "plan_collected": plan_collected,
            "plan_completeness": plan_completeness,
            "environment_evidence_total": environment_total,
            "environment_evidence_collected": environment_collected,
            "environment_evidence_completeness": environment_completeness,
            "executed_tool_count": executed_tool_count,
            "matched_tool_count": matched_tool_count,
            "unplanned_tool_count": unplanned_tool_count,
            "case_tool_count": case_tool_count,
            "supplemental_tool_count": supplemental_tool_count,
            "skipped_plan_count": skipped_plan_count,
            "observability_target_total": observability_target_total,
            "observability_target_collected": observability_target_collected,
            "observability_target_completeness": observability_target_completeness,
            "diagnostic_evidence_total": diagnostic_evidence_total,
            "diagnostic_evidence_collected": diagnostic_evidence_collected,
            "diagnostic_evidence_completeness": diagnostic_evidence_completeness,
            "diagnostic_evidence_missing": diagnostic_evidence_missing or [],
            "dimension_coverage_total": dimension_coverage_total,
            "dimension_coverage_collected": dimension_coverage_collected,
            "dimension_coverage": dimension_coverage,
            "diagnostic_sufficiency": diagnostic_sufficiency,
            "diagnostic_sufficiency_label": diagnostic_sufficiency_label,
            "source_coverage": source_coverage or {},
            "case_target_coverage": {
                "mode": (
                    "observability_first_round_gate"
                    if is_first_round_gate
                    else "case_target"
                ),
                "total": observability_target_total,
                "collected": observability_target_collected,
                "rate": observability_target_completeness,
            },
            "detail_retrieval": detail_retrieval or {},
            "diagnostic_sufficiency_summary": {
                "score": diagnostic_sufficiency,
                "label": diagnostic_sufficiency_label or "未评估",
            },
            "unresolved_questions": unresolved_questions or [],
            "evidence_inventory": evidence_inventory,
            "missing_reasons": missing_reasons,
            "early_stop": early_stop,
        })

    def _publish_evidence_analysis(
        self,
        output: EvidenceCollectionOutput,
    ) -> str:
        full_payload = output.model_dump(mode="json")
        run_id = str(getattr(self, "current_run_id", "") or "").strip()
        if run_id:
            try:
                ContextArchive(run_id=run_id).write_json(
                    "node_outputs/evidence.full.json",
                    full_payload,
                )
            except Exception as exc:
                logger.warning(
                    "⚠️ [evidence] 写入完整 Evidence 审计归档失败: %s",
                    exc,
                )

        handoff_payload = dict(full_payload)
        handoff_payload.pop("llm_analysis", None)
        return json.dumps(
            handoff_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _build_evidence_conflicts(
        tool_data: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        conflicts = []
        abnormal_pods = (layer_handoff or {}).get("abnormal_pods") or []
        abnormal_pod_keys = {
            (str(pod.get("namespace") or ""), str(pod.get("name") or ""))
            for pod in abnormal_pods
            if isinstance(pod, dict) and pod.get("name")
        }
        for item in tool_data:
            data = item.get("data", "") or ""
            if re.search(r"no events found|no resources found|notfound|not found|command failed|error from server", data, re.IGNORECASE):
                missing_pod = EvidenceCollectorNode._extract_missing_abnormal_pod(data, abnormal_pod_keys)
                object_missing = bool(missing_pod)
                conflict = {
                    "tool": item.get("tool", "unknown"),
                    "reason": data[:300],
                    "severity": "critical" if object_missing else "warning",
                    "object_missing": object_missing,
                }
                if object_missing:
                    conflict["object"] = {
                        "kind": "Pod",
                        "name": missing_pod[1],
                        "namespace": missing_pod[0],
                    }
                    conflict["message"] = (
                        "异常 Pod 当前不存在；历史事件或归档摘要不能继续作为该 Pod 当前异常的正向证据"
                    )
                conflicts.append(conflict)
        return conflicts

    @staticmethod
    def _extract_missing_abnormal_pod(
        data: str,
        abnormal_pod_keys: set[tuple[str, str]],
    ) -> Optional[tuple[str, str]]:
        if not data or not abnormal_pod_keys:
            return None
        for namespace, pod_name in abnormal_pod_keys:
            name = re.escape(pod_name)
            patterns = (
                rf"(?:^|:\s*)pods?\s+[\"']{name}[\"']\s+(?:not\s*found|notfound)\b",
                rf"\bpods?/{name}\s+(?:not\s*found|notfound)\b",
            )
            if any(re.search(pattern, data or "", re.IGNORECASE) for pattern in patterns):
                return namespace, pod_name
        return None

    def _build_query_result(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_plan: List[Dict[str, Any]],
        evidence_inventory: List[Dict[str, Any]],
        tool_data: List[Dict[str, Any]],
        collection_summary: str,
        missing_reasons: List[str],
    ) -> Dict[str, Any]:
        """QUERY 模式下将真实工具结果归一化为 Pydantic QueryResult，供 conclusion 纯渲染。"""
        if layer != Layer.QUERY:
            return {}

        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)
        if not hasattr(ai_call, "call_structured"):
            logger.warning("⚠️ [evidence] ai_call 不支持 call_structured，使用 QUERY 通用回退")
            return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)

        prompt = get_query_evidence_normalization_prompt(self._get_prompt_language())
        payload = {
            "question": question,
            "collection_summary": collection_summary,
            "evidence_plan": evidence_plan,
            "evidence_inventory": evidence_inventory,
            "tool_data": tool_data,
            "missing_reasons": missing_reasons,
        }

        try:
            normalized, _ = ai_call.call_structured(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False),
                schema=QueryResult,
                node_id="query_result_normalize",
                run_id=getattr(self, "current_run_id", ""),
            )
            if normalized:
                result = normalized.model_dump()
                result.setdefault("query_target", question)
                result.setdefault("collection_summary", collection_summary)
                return QueryResult.model_validate(result).model_dump()
        except Exception as exc:
            logger.warning("⚠️ [evidence] QUERY 结果归一化失败，使用通用回退: %s", exc)

        return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)

    @staticmethod
    def _build_query_result_fallback(
        question: str,
        tool_data: List[Dict[str, Any]],
        collection_summary: str,
        missing_reasons: List[str],
    ) -> Dict[str, Any]:
        rows = []
        for item in tool_data[:10]:
            rows.append({
                "tool": item.get("tool", "unknown"),
                "result": item.get("data", "")[:200] or "未获取到",
            })

        notes = list(missing_reasons[:5])
        if not rows:
            notes.append("未能从工具结果中归一化出更细粒度的数据表。")

        return QueryResult.model_validate({
            "query_target": question,
            "collection_summary": collection_summary,
            "columns": [
                {"key": "tool", "label": "工具"},
                {"key": "result", "label": "结果摘要"},
            ],
            "rows": rows,
            "notes": notes,
            "missing": [{"field": "result", "reason": reason} for reason in missing_reasons[:5]],
            "sources": [],
        }).model_dump()

    def _plan_evidence_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict],
        layer_analysis: str = "",
        context_archive_ref: str = "",
        layer_archive_ref: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
        failure_reason: str = "",
        existing_plan: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple:
        """
        调用 LLM 规划证据采集

        Returns:
            (evidence_plan_list, intermediate_events_list, llm_result_text)
            llm_result_text: LLM 的完整输出文本（包含工具调用结果和分析）
        """
        if getattr(self, 'ai_call', None) is None:
            logger.warning("⚠️ [evidence] ai_call 未设置，无法生成 Pydantic evidence_plan")
            return [], [], ""
        try:
            layer_str = layer.value if layer else "L2"
            if bool(getattr(self, "require_diagnosis_submission", False)):
                # A Pod lane already has authoritative identity from Layer.
                # Code schedules the generic lifecycle + three-signal starting
                # point; the single Diagnosis Agent remains free to select any
                # existing read-only diagnostic tool after seeing the results.
                # No separate planning model is needed in this path.
                handoff_for_plan = self._parse_handoff_json(layer_analysis)
                evidence_plan = self._build_structured_plan_fallback(
                    handoff_for_plan
                )
                if self._is_observability_first_round_gate_enabled():
                    evidence_plan = self._ensure_autonomous_observability_gate_plan(
                        evidence_plan,
                        handoff_for_plan,
                    )
                    evidence_plan = [
                        item
                        for item in evidence_plan
                        if self._normalize_plan_text(item.get("tool"))
                        in {
                            "kubectl_describe",
                            *self._PRE_REACT_BASELINE_TOOLS,
                        }
                    ]
                if not evidence_plan:
                    self._structured_plan_terminal_empty = True
                    self._structured_plan_failure_reason = (
                        self._STRUCTURED_PLAN_TERMINAL_REASON
                    )
                    return [], [], ""
                return self._execute_existing_evidence_plan(
                    question=question,
                    layer=layer,
                    possible_scenarios=possible_scenarios,
                    key_entities=key_entities,
                    layer_analysis=layer_analysis,
                    context_archive_ref=context_archive_ref,
                    layer_archive_ref=layer_archive_ref,
                    evidence_plan=evidence_plan,
                    failure_reason=(
                        "代码已根据权威 Pod 身份建立通用 lifecycle 与三维 baseline；"
                        "请自主调查并提交诊断"
                    ),
                )
            # possible_scenarios 可能是 str 列表或 dict 列表（含 scenario/probability 字段）
            if possible_scenarios:
                parts = []
                for s in possible_scenarios:
                    if isinstance(s, dict):
                        parts.append(s.get("scenario", str(s)))
                    else:
                        parts.append(str(s))
                scenarios_str = ", ".join(parts)
            else:
                scenarios_str = "未知"

            # 构建 entities 信息用于 prompt
            entities_str = ""
            if key_entities:
                entities_str = "\n".join([
                    f"  - {e.get('type', '')}: {e.get('value', '')}"
                    for e in key_entities[:10]
                ])

            # 构建完整的 system prompt
            system_prompt = get_workflow_prompt(
                "evidence",
                prompt_language=self._get_prompt_language(),
            ).format(
                layer=layer_str,
                possible_scenarios=scenarios_str
            )

            # 添加 entities 信息到 prompt
            if entities_str:
                system_prompt += f"\n\n# 已提取的关键实体\n{entities_str}\n"

            if strict_mode:
                system_prompt += (
                    "\n\n# 本轮最低要求\n"
                    f"- 失败原因：{failure_reason or '上一轮只返回计划，没有执行工具'}\n"
                    "- 至少执行一条 critical/important 只读工具；没有真实 tool_result 时不得声称采集完成。\n"
                )

            user_message = self._build_evidence_user_message(
                question=question,
                layer=layer_str,
                layer_handoff=layer_analysis,
                context_archive_ref=context_archive_ref,
                layer_archive_ref=layer_archive_ref or {},
                strict_mode=strict_mode,
                failure_reason=failure_reason,
                existing_plan=existing_plan,
                plan_mode="dynamic_collection",
                observability_mode=(
                    "autonomous"
                    if self._is_autonomous_observability_enabled()
                    else "legacy"
                ),
            )
            if not getattr(self, "_logged_evidence_user_prompt", False):
                logger.info(
                    "📨 [evidence] LLM user prompt | chars=%d strict=%s\n%s",
                    len(user_message),
                    strict_mode,
                    user_message,
                )
                self._logged_evidence_user_prompt = True
            self._archive_node_input(
                {
                    "node": self.node_id,
                    "strict_mode": strict_mode,
                    "question": question,
                    "user_message": user_message,
                    "layer": layer_str,
                    "layer_handoff": layer_analysis,
                    "system_prompt_chars": len(system_prompt),
                    "user_message_chars": len(user_message),
                }
            )

            if existing_plan is not None:
                handoff_for_existing = self._parse_handoff_json(layer_analysis)
                evidence_plan = self._prepare_evidence_plan(
                    existing_plan,
                    handoff_for_existing,
                )
                if not evidence_plan:
                    logger.warning("⚠️ [evidence] 既有 evidence_plan 为空，拒绝执行自由文本采证")
                    return [], [], ""
                return self._execute_existing_evidence_plan(
                    question=question,
                    layer=layer,
                    possible_scenarios=possible_scenarios,
                    key_entities=key_entities,
                    layer_analysis=layer_analysis,
                    context_archive_ref=context_archive_ref,
                    layer_archive_ref=layer_archive_ref,
                    evidence_plan=evidence_plan,
                    failure_reason=failure_reason or "沿用既有 Pydantic evidence_plan 执行采证",
                )

            evidence_plan, plan_raw = self._generate_structured_evidence_plan(
                system_prompt=system_prompt,
                user_message=user_message,
                layer_str=layer_str,
            )
            handoff_for_plan = self._parse_handoff_json(layer_analysis)
            evidence_plan = self._prepare_evidence_plan(
                evidence_plan,
                handoff_for_plan,
            )
            if (
                not evidence_plan
                and self._is_autonomous_observability_enabled()
            ):
                evidence_plan = self._build_structured_plan_fallback(
                    handoff_for_plan
                )
            if not evidence_plan:
                if not self._collect_confirmed_handoff_pod_targets(
                    handoff_for_plan
                ):
                    self._structured_plan_terminal_empty = True
                    self._structured_plan_failure_reason = (
                        self._STRUCTURED_PLAN_TERMINAL_REASON
                    )
                logger.warning("LLM 未返回有效 evidence_plan Pydantic 结构，拒绝进入工具执行")
                return [], [], plan_raw

            return self._execute_existing_evidence_plan(
                question=question,
                layer=layer,
                possible_scenarios=possible_scenarios,
                key_entities=key_entities,
                layer_analysis=layer_analysis,
                context_archive_ref=context_archive_ref,
                layer_archive_ref=layer_archive_ref,
                evidence_plan=evidence_plan,
                failure_reason="Pydantic evidence_plan 已生成，本轮只执行既有计划",
            )

        except Exception as e:
            logger.warning(f"LLM Pydantic evidence_plan 生成或执行失败: {e}")
            return [], [], ""

    def _generate_structured_evidence_plan(
        self,
        system_prompt: str,
        user_message: str,
        layer_str: str,
    ) -> tuple[List[Dict[str, Any]], str]:
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None or not hasattr(ai_call, "call_structured"):
            logger.warning("⚠️ [evidence] ai_call 不支持 call_structured，无法生成 Pydantic evidence_plan")
            return [], ""

        plan_prompt = (
            system_prompt.rstrip()
            + "\n\n# 结构化计划生成模式\n"
            + "只生成最小 `EvidencePlanOutput`，不调用工具、不总结结论。每个计划项只表达一个待验证问题。\n"
        )
        llm_start = time.time()
        try:
            try:
                structured, raw = ai_call.call_structured(
                    system_prompt=plan_prompt,
                    question=user_message,
                    schema=EvidencePlanOutput,
                    node_id="evidence_plan",
                    run_id=getattr(self, "current_run_id", ""),
                    max_tokens=2048,
                )
            except Exception as exc:
                logger.warning(
                    "⚠️ [evidence] Pydantic evidence_plan 生成失败，使用统一回退: %s",
                    exc,
                )
                return [], json.dumps({
                    "error": type(exc).__name__,
                    "message": str(exc),
                }, ensure_ascii=False)
        finally:
            if self.metrics:
                self.metrics.record_llm_call(
                    self.node_id,
                    (time.time() - llm_start) * 1000,
                )
        if structured is None:
            return [], raw
        output = structured.model_dump()
        output.setdefault("layer", layer_str)
        return [item.model_dump() for item in structured.evidence_plan], raw

    @classmethod
    def _build_structured_plan_fallback(
        cls,
        layer_handoff: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        targets = cls._collect_confirmed_handoff_pod_targets(
            layer_handoff or {}
        )
        if not targets:
            return []

        fallback_plan = []
        for index, (namespace, pod) in enumerate(targets, start=1):
            fallback_plan.append({
                "id": f"structured-plan-fallback-{index}",
                "description": "确认目标 Pod 当前生命周期状态和事件",
                "level": "critical",
                "tool": "kubectl_describe",
                "command": (
                    f"kubectl describe pod {shlex.quote(pod)} "
                    f"-n {shlex.quote(namespace)}"
                ),
                "tool_args": {
                    "kind": "pod",
                    "namespace": namespace,
                    "name": pod,
                },
                "purpose": "确认目标 Pod 的当前状态、容器终态和近期事件",
                "evidence_type": "pod_lifecycle",
                "target_scope": f"{namespace}/{pod}",
                "acceptable_tools": ["kubectl_describe"],
                "source": "structured_plan_fallback",
            })
        return cls._normalize_evidence_plan(
            fallback_plan,
            layer_handoff=layer_handoff,
        )

    def _execute_existing_evidence_plan(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict],
        layer_analysis: str,
        context_archive_ref: str,
        layer_archive_ref: Optional[Dict[str, Any]],
        evidence_plan: List[Dict[str, Any]],
        failure_reason: str,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        layer_str = layer.value if layer else "L2"
        parsed_layer_handoff = self._parse_handoff_json(layer_analysis)
        if (
            self._is_observability_first_round_gate_enabled()
            and not bool(getattr(self, "require_diagnosis_submission", False))
        ):
            evidence_plan = self._ensure_autonomous_observability_gate_plan(
                evidence_plan,
                parsed_layer_handoff,
            )
        if possible_scenarios:
            parts = []
            for s in possible_scenarios:
                if isinstance(s, dict):
                    parts.append(s.get("scenario", str(s)))
                else:
                    parts.append(str(s))
            scenarios_str = ", ".join(parts)
        else:
            scenarios_str = "未知"

        diagnosis_agent = bool(
            getattr(self, "require_diagnosis_submission", False)
        )
        if diagnosis_agent:
            system_prompt = AUTONOMOUS_DIAGNOSIS_AGENT_PROMPT
        else:
            system_prompt = get_workflow_prompt(
                "evidence",
                prompt_language=self._get_prompt_language(),
            ).format(
                layer=layer_str,
                possible_scenarios=scenarios_str,
            )
        if key_entities:
            entities_str = "\n".join([
                f"  - {e.get('type', '')}: {e.get('value', e.get('name', ''))}"
                for e in key_entities[:10]
            ])
            system_prompt += f"\n\n# 已提取的关键实体\n{entities_str}\n"

        user_message = self._build_evidence_user_message(
            question=question,
            layer=layer_str,
            layer_handoff=layer_analysis,
            context_archive_ref=context_archive_ref,
            layer_archive_ref=layer_archive_ref or {},
            strict_mode=False,
            failure_reason=failure_reason,
            existing_plan=evidence_plan,
            plan_mode="preplanned_execution",
            observability_mode=(
                "autonomous"
                if self._is_autonomous_observability_enabled()
                else "legacy"
            ),
        )
        if diagnosis_agent:
            user_message = (
                f"{user_message.rstrip()}\n\n"
                "# 本轮完成条件\n"
                "在自主调查结束时必须通过 DiagnosisSubmission 结构化合同提交"
                "现象、根因、最短因果链和真实 Fact ID；不要只返回自然语言摘要。\n"
            )

        legacy_early_stop_enabled = self._is_early_stop_enabled(default=True)
        autonomous_mode = self._is_autonomous_observability_enabled()
        first_round_gate = self._is_observability_first_round_gate_enabled()
        has_mandatory_targets = bool(self._mandatory_case_targets(evidence_plan))
        logger.info(
            "🧭 [evidence] autonomous_mode=%s first_round_gate=%s "
            "legacy_early_stop=%s mandatory_targets=%s",
            autonomous_mode,
            first_round_gate,
            legacy_early_stop_enabled,
            has_mandatory_targets,
        )
        all_thinking_events: List[Dict[str, Any]] = []
        llm_text_parts: List[str] = []
        remaining_plan = list(evidence_plan)
        stalled_rounds = 0
        tool_result_sequence_start = 0
        blocked_tool_names = self._blocked_tools_for_preplanned_execution(
            evidence_plan
        )
        self._active_evidence_plan = evidence_plan
        try:
            if bool(getattr(self, "single_react_session", False)):
                # Parallel diagnosis owns at most two complete ReAct agents.
                # Each agent receives one uninterrupted AICall max_steps
                # budget: no mandatory-gate stop checker, outer retry, fresh
                # context refill, refinement, or reconciliation is started by
                # this collector invocation.
                baseline_events = self._run_pre_react_observability_baseline(
                    evidence_plan
                )
                all_thinking_events.extend(baseline_events)
                if diagnosis_agent and baseline_events:
                    fast_submission = self._try_compact_fact_diagnosis(
                        events=baseline_events,
                        phase="baseline",
                        max_attempts=2,
                    )
                    if fast_submission is not None:
                        self._diagnosis_submission = (
                            fast_submission.model_dump(mode="json")
                        )
                        logger.info(
                            "⚡ [evidence] 四维 baseline 已形成可发布诊断，"
                            "跳过工具型 ReAct"
                        )
                        return evidence_plan, all_thinking_events, (
                            fast_submission.model_dump_json()
                        )
                if baseline_events:
                    user_message = self._append_baseline_handoff(
                        user_message,
                        baseline_events,
                    )
                baseline_result_count = sum(
                    1
                    for event in baseline_events
                    if event.get("type") == "tool_result"
                )
                if diagnosis_agent:
                    structured, response, round_events = self._call_structured_agent(
                        question=user_message,
                        system_prompt=system_prompt,
                        schema=DiagnosisSubmission,
                        use_tools=True,
                        stop_checker=None,
                        tool_result_sequence_start=baseline_result_count,
                        blocked_tool_names=blocked_tool_names,
                        skip_remediation_policy=True,
                    )
                    if structured is None and response is not None:
                        extractor = getattr(
                            getattr(self, "ai_call", None),
                            "extract_json_payload",
                            None,
                        )
                        parsed = (
                            extractor(response.result or "")
                            if callable(extractor)
                            else None
                        )
                        try:
                            structured = (
                                DiagnosisSubmission.model_validate(parsed)
                                if isinstance(parsed, dict)
                                else None
                            )
                        except Exception:
                            structured = None
                else:
                    response, round_events = self._call_llm(
                        user_message,
                        system_prompt,
                        stop_checker=None,
                        tool_result_sequence_start=baseline_result_count,
                        blocked_tool_names=blocked_tool_names,
                        skip_remediation_policy=True,
                    )
                all_thinking_events.extend(round_events or [])
                if response and response.result:
                    llm_text_parts.append(response.result)
                if diagnosis_agent:
                    selected_submission = (
                        structured
                        if isinstance(structured, DiagnosisSubmission)
                        else None
                    )
                    if not self._diagnosis_submission_is_acceptable(
                        selected_submission,
                        all_thinking_events,
                    ):
                        semantic_hint: Dict[str, Any] = {}
                        if selected_submission is not None:
                            semantic_hint = selected_submission.model_dump(
                                mode="json"
                            )
                        elif response is not None and response.result:
                            semantic_hint = {
                                "agent_output": str(response.result)[:2000]
                            }
                        repaired = self._try_compact_fact_diagnosis(
                            events=all_thinking_events,
                            phase="post_react_binding",
                            semantic_hint=semantic_hint,
                        )
                        if repaired is not None:
                            selected_submission = repaired
                            logger.info(
                                "🔗 [evidence] 代码已将紧凑证据槽位绑定为权威 Fact ID"
                            )
                    self._diagnosis_submission = (
                        selected_submission.model_dump(mode="json")
                        if selected_submission is not None
                        else None
                    )
                llm_text = "\n".join(llm_text_parts)
                if self._has_effective_tool_evidence(all_thinking_events):
                    logger.info(
                        "📋 [evidence] 单次完整 ReAct session 完成: plan=%d, tool_events=%d",
                        len(evidence_plan),
                        sum(
                            1 for event in all_thinking_events
                            if event.get("type") == "tool_result"
                        ),
                    )
                    return evidence_plan, all_thinking_events, llm_text
                logger.warning(
                    "⚠️ [evidence] 单次完整 ReAct session 未产生有效工具结果"
                )
                return evidence_plan, all_thinking_events, llm_text

            while True:
                prior_attempted = (
                    self._attempted_autonomous_observability_gate_items(
                        all_thinking_events
                    )
                    if first_round_gate
                    else (
                        self._attempted_autonomous_observability_targets(
                            all_thinking_events
                        )
                        if autonomous_mode
                        else self._attempted_mandatory_case_targets(
                            all_thinking_events
                        )
                    )
                )

                def stop_checker(round_events: List[Dict[str, Any]]) -> bool:
                    return self._should_stop_collection_early(
                        [*all_thinking_events, *round_events]
                    )

                response, round_events = self._call_llm(
                    user_message,
                    system_prompt,
                    stop_checker=(
                        self._should_stop_autonomous_collection
                        if autonomous_mode
                        else (
                            stop_checker
                            if has_mandatory_targets
                            else (
                                self._should_stop_collection_early
                                if legacy_early_stop_enabled
                                else None
                            )
                        )
                    ),
                    tool_result_sequence_start=tool_result_sequence_start,
                    blocked_tool_names=blocked_tool_names,
                    skip_remediation_policy=True,
                )
                all_thinking_events.extend(round_events)
                if response and response.result:
                    llm_text_parts.append(response.result)
                tool_result_sequence_start = sum(
                    1
                    for event in all_thinking_events
                    if event.get("type") == "tool_result"
                )

                remaining_plan = (
                    self._remaining_unattempted_autonomous_items(
                        evidence_plan,
                        all_thinking_events,
                    )
                    if autonomous_mode
                    else self._remaining_unattempted_mandatory_items(
                        evidence_plan,
                        all_thinking_events,
                    )
                )
                if self._early_stop_state.get("reason") == "context_budget_stop":
                    if not (first_round_gate and remaining_plan):
                        break
                    logger.info(
                        "🔄 [evidence] 当前 ReAct round 达到上下文预算，"
                        "使用全新 context 继续 %d 个未尝试首轮门控项",
                        len(remaining_plan),
                    )
                    self._early_stop_state = {
                        "triggered": False,
                        "reason": "",
                        "required_levels": ["critical", "important"],
                    }
                if not remaining_plan:
                    # 注意（架构决策 2026-08-04）：不在代码层做“反馈补采”控制。
                    # 补证由 agent 在 ReAct 循环内根据真实工具结果自主决定
                    # （见 EVIDENCE_COLLECTOR_PROMPT“补证由上一轮真实结果驱动”），
                    # 唯一硬约束是 max_steps 与上下文预算；plan 只作参考与统计口径。
                    if has_mandatory_targets and not autonomous_mode:
                        refinement_response, refinement_events = (
                            self._run_post_case_evidence_refinement(
                                question=question,
                                thinking_events=all_thinking_events,
                                tool_result_sequence_start=tool_result_sequence_start,
                            )
                        )
                        all_thinking_events.extend(refinement_events)
                        if refinement_response and refinement_response.result:
                            llm_text_parts.append(refinement_response.result)
                        tool_result_sequence_start = sum(
                            1
                            for event in all_thinking_events
                            if event.get("type") == "tool_result"
                        )
                        if self._max_context_usage_ratio(all_thinking_events) >= 0.8:
                            self._early_stop_state = {
                                "triggered": True,
                                "reason": "context_budget_stop",
                                "required_levels": ["mandatory_live_observability"],
                                "context_usage_ratio": self._max_context_usage_ratio(
                                    all_thinking_events
                                ),
                                "uncollected_targets": [],
                                "detail_retrieval": self._calculate_detail_retrieval(
                                    all_thinking_events
                                ),
                            }
                            break

                        reconciliation_response, reconciliation_events = (
                            self._run_post_case_runbook_reconciliation(
                                question=question,
                                layer_analysis=layer_analysis,
                                thinking_events=all_thinking_events,
                                tool_result_sequence_start=tool_result_sequence_start,
                            )
                        )
                        all_thinking_events.extend(reconciliation_events)
                        if reconciliation_response and reconciliation_response.result:
                            llm_text_parts.append(reconciliation_response.result)
                        self._early_stop_state = {
                            "triggered": True,
                            "reason": "post_case_reconciliation_complete",
                            "required_levels": ["mandatory_live_observability"],
                            "uncollected_targets": [],
                            "post_case_reconciliation": True,
                            "runbook_reconciliation": {
                                "evaluated": True,
                                "fetched_runbooks": self._fetched_runbook_ids(
                                    reconciliation_events
                                ),
                            },
                            "detail_retrieval": self._calculate_detail_retrieval(
                                all_thinking_events
                            ),
                        }
                    break

                current_attempted = (
                    self._attempted_autonomous_observability_gate_items(
                        all_thinking_events
                    )
                    if first_round_gate
                    else (
                        self._attempted_autonomous_observability_targets(
                            all_thinking_events
                        )
                        if autonomous_mode
                        else self._attempted_mandatory_case_targets(
                            all_thinking_events
                        )
                    )
                )
                if len(current_attempted) > len(prior_attempted):
                    stalled_rounds = 0
                else:
                    stalled_rounds += 1
                if stalled_rounds >= 2:
                    self._early_stop_state = {
                        "triggered": True,
                        "reason": "collection_stalled",
                        "required_levels": ["mandatory_live_observability"],
                        "uncollected_targets": [
                            (
                                f"{namespace}/{pod}:{tool}"
                                if tool
                                else f"{namespace}/{pod}"
                            )
                            for namespace, pod, tool in (
                                self._autonomous_observability_gate_items(
                                    remaining_plan
                                )
                                if first_round_gate
                                else [
                                    (namespace, pod, "")
                                    for namespace, pod in (
                                        self._autonomous_observability_targets(
                                            remaining_plan
                                        )
                                        if autonomous_mode
                                        else self._mandatory_case_targets(
                                            remaining_plan
                                        )
                                    )
                                ]
                            )
                        ],
                    }
                    break

                user_message = self._build_evidence_user_message(
                    question=question,
                    layer=layer_str,
                    layer_handoff=layer_analysis,
                    context_archive_ref=context_archive_ref,
                    layer_archive_ref=layer_archive_ref or {},
                    strict_mode=False,
                    failure_reason=(
                        "继续执行尚未尝试的首轮 Metrics、Logging、Tracing、Topology 门控项"
                        if first_round_gate
                        else "继续执行尚未尝试的 mandatory 实时可观测性采集项"
                    ),
                    existing_plan=remaining_plan,
                    plan_mode="preplanned_execution",
                    observability_mode=(
                        "autonomous"
                        if autonomous_mode
                        else "legacy"
                    ),
                )
                completed_summary = (
                    self._format_completed_autonomous_gate_summary(
                        all_thinking_events
                    )
                    if first_round_gate
                    else self._format_completed_mandatory_summary(
                        all_thinking_events
                    )
                )
                if completed_summary:
                    user_message = (
                        f"{user_message.rstrip()}\n\n"
                        "# 已完成首轮采集摘要（不要用相同参数重复调用）\n"
                        f"{completed_summary}\n"
                    )
                blocked_tool_names = self._blocked_tools_for_preplanned_execution(
                    remaining_plan
                )
        finally:
            self._active_evidence_plan = None

        llm_text = "\n".join(llm_text_parts)
        if self._has_effective_tool_evidence(all_thinking_events):
            logger.info("📋 [evidence] 使用 Pydantic evidence_plan 执行采证: %d 项", len(evidence_plan))
            return evidence_plan, all_thinking_events, llm_text
        logger.warning("⚠️ [evidence] Pydantic evidence_plan 已生成，但执行阶段未产生有效工具结果")
        return evidence_plan, all_thinking_events, llm_text


    def _run_post_case_evidence_refinement(
        self,
        *,
        question: str,
        thinking_events: List[Dict[str, Any]],
        tool_result_sequence_start: int,
    ) -> tuple[Any, List[Dict[str, Any]]]:
        """Give Qwen one bounded, generic chance to expand decisive evidence."""
        context_ratio = self._max_context_usage_ratio(thinking_events)
        if context_ratio >= 0.8:
            self._early_stop_state = {
                "triggered": True,
                "reason": "context_budget_stop",
                "required_levels": ["mandatory_live_observability"],
                "context_usage_ratio": context_ratio,
                "uncollected_targets": [],
                "detail_retrieval": {
                    "evaluated": False,
                    "skipped": True,
                    "reason": "context_budget_stop",
                    "requested": 0,
                    "collected": 0,
                    "refs": [],
                },
            }
            return None, []

        payload = self._build_post_case_refinement_payload(thinking_events)
        eligible_cases = [
            case
            for case in (payload.get("cases") or [])
            if str(case.get("case_id") or "").strip()
        ]
        if not eligible_cases:
            return None, []
        payload = {"cases": eligible_cases}

        enabled_detail_tools = {
            str(getattr(tool, "name", "") or "").strip().lower()
            for tool in (getattr(self, "tools", []) or [])
            if str(getattr(tool, "name", "") or "").strip().lower()
            in self._AIOPS_DETAIL_TOOLS
        }
        has_ref_reader_work = (
            "get_aiops_case_evidence" in enabled_detail_tools
            and any(
                case.get("case_id") and case.get("recommended_refs_by_dimension")
                for case in payload["cases"]
            )
        )
        has_live_fine_tools = bool(
            enabled_detail_tools - {"get_aiops_case_evidence"}
        )
        if not has_ref_reader_work and not has_live_fine_tools:
            self._early_stop_state["detail_retrieval"] = {
                "evaluated": False,
                "skipped": True,
                "reason": "no_eligible_detail_tool_or_ref",
                "requested": 0,
                "collected": 0,
                "refs": [],
            }
            return None, []

        user_message = (
            "action=post_case_evidence_refinement\n\n"
            f"# 用户问题\n{question}\n\n"
            "# 实时 Case 首屏事实与未回答问题\n"
            f"{json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
            "# 任务\n"
            "- 只判断当前首屏事实是否足以回答用户问题；coverage=present 仅表示数据源存在，"
            "不等于诊断证据充分。\n"
            "- 如关键判断缺少原文、时间序列、可关联 Trace 或责任边，调用一个或少量允许的"
            "细粒度 AIOps 工具补证。\n"
            "- `get_aiops_case_evidence` 只能使用上面真实给出的 case_id 与 "
            "recommended_refs_by_dimension，不得猜测 ref。\n"
            "- 当前证据已经决定性、没有冲突时允许零工具调用，并回答 "
            "`detail_retrieval: current_case_sufficient`。\n"
            "- 最多执行这一轮；禁止重新调用 collect_aiops_case、kubectl、Runbook 或修复工具。"
        )
        system_prompt = (
            "你负责在实时 AIOps Case 之后做一次窄范围证据补全。"
            "你只选择是否展开真实 evidence ref 或调用已启用的 AIOps 细粒度查询；"
            "不得按故障类型套规则，不得生成根因或修复结论。"
        )
        response, events = self._call_llm(
            user_message,
            system_prompt,
            tool_result_sequence_start=tool_result_sequence_start,
            blocked_tool_names=self._blocked_tools_for_post_case_refinement(),
            skip_remediation_policy=True,
        )
        self._early_stop_state["detail_retrieval"] = {
            "evaluated": True,
            "skipped": False,
            **self._calculate_detail_retrieval(events),
        }
        return response, events


    def _blocked_tools_for_post_case_refinement(self) -> set[str]:
        return {
            str(getattr(tool, "name", "") or "")
            for tool in (getattr(self, "tools", []) or [])
            if str(getattr(tool, "name", "") or "").strip()
            and str(getattr(tool, "name", "") or "").strip().lower()
            not in self._AIOPS_DETAIL_TOOLS
        }


    @classmethod
    def _build_post_case_refinement_payload(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        cases: List[Dict[str, Any]] = []
        acquired_refs = {
            str(args.get("evidence_ref") or "").strip()
            for event in (thinking_events or [])
            if event.get("type") == "tool_result"
            and str(event.get("tool_name") or "").lower()
            == "get_aiops_case_evidence"
            if isinstance((args := event.get("tool_args")), dict)
            and str(args.get("evidence_ref") or "").strip()
        }
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or event.get("status") != "success"
                or str(event.get("tool_name") or "").lower()
                != "collect_aiops_case"
            ):
                continue
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            if structured.get("status") != "case_collected":
                continue
            primary = (
                structured.get("primary_entity")
                if isinstance(structured.get("primary_entity"), dict)
                else {}
            )
            target = (
                f"{primary.get('namespace') or 'unknown'}/"
                f"{primary.get('name') or 'unknown'}"
            )
            recommended = (
                structured.get("recommended_refs_by_dimension")
                if isinstance(
                    structured.get("recommended_refs_by_dimension"),
                    dict,
                )
                else {}
            )
            recommended = {
                str(dimension): [
                    str(ref)
                    for ref in refs[:3]
                    if str(ref).strip() and str(ref) not in acquired_refs
                ]
                for dimension, refs in recommended.items()
                if isinstance(refs, list)
            }
            recommended = {
                dimension: refs
                for dimension, refs in recommended.items()
                if refs
            }
            assessment = cls._calculate_diagnostic_evidence_coverage([event])
            unresolved = list(assessment.get("diagnostic_evidence_missing") or [])
            if (
                assessment.get("diagnostic_evidence_total")
                and float(assessment.get("diagnostic_sufficiency") or 0.0) < 0.85
            ):
                unresolved.append(
                    f"{target}: first-screen diagnostic evidence is "
                    f"{assessment.get('diagnostic_sufficiency_label') or 'insufficient'} "
                    f"({float(assessment.get('diagnostic_sufficiency') or 0.0):.0%})"
                )
            conflicts = structured.get("conflicts")
            if isinstance(conflicts, list):
                unresolved.extend(
                    str(item) for item in conflicts[:5] if str(item).strip()
                )

            details = (
                structured.get("dimension_details")
                if isinstance(structured.get("dimension_details"), dict)
                else {}
            )
            cases.append({
                "case_id": str(structured.get("case_id") or ""),
                "target": target,
                "source_coverage": dict(
                    structured.get("coverage")
                    if isinstance(structured.get("coverage"), dict)
                    else {}
                ),
                "signals_summary": [
                    item
                    for item in (structured.get("signals_summary") or [])[:8]
                    if isinstance(item, dict)
                ],
                "dimension_details": cls._compact_post_case_dimension_details(
                    details
                ),
                "recommended_refs_by_dimension": recommended,
                "already_acquired_refs": sorted(acquired_refs),
                "diagnostic_sufficiency": {
                    "score": assessment.get("diagnostic_sufficiency", 0.0),
                    "label": assessment.get(
                        "diagnostic_sufficiency_label",
                        "未评估",
                    ),
                },
                "unresolved_questions": list(dict.fromkeys(unresolved)),
            })
        return {"cases": cases}


    @staticmethod
    def _compact_post_case_dimension_details(
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        def select(section: str, fields: Dict[str, int]) -> Dict[str, Any]:
            source = details.get(section)
            if not isinstance(source, dict):
                return {}
            result = {
                key: source.get(key)
                for key in (
                    "coverage",
                    "deepflow_coverage",
                    "tempo_coverage",
                )
                if key in source
            }
            for key, limit in fields.items():
                value = source.get(key)
                if isinstance(value, list):
                    result[key] = [
                        item for item in value[:limit] if isinstance(item, dict)
                    ]
            return result

        return {
            "metrics": select("metrics", {"highlights": 3}),
            "logs": select("logs", {"samples": 3}),
            "tracing": select("tracing", {"flows": 3, "spans": 3}),
            "topology": select("topology", {"edges": 6}),
        }


    @staticmethod
    def _max_context_usage_ratio(
        thinking_events: List[Dict[str, Any]],
    ) -> float:
        return max(
            (
                float(event.get("context_usage_ratio"))
                for event in (thinking_events or [])
                if isinstance(event.get("context_usage_ratio"), (int, float))
            ),
            default=0.0,
        )


    def _run_post_case_runbook_reconciliation(
        self,
        *,
        question: str,
        layer_analysis: str,
        thinking_events: List[Dict[str, Any]],
        tool_result_sequence_start: int,
    ) -> tuple[Any, List[Dict[str, Any]]]:
        """Give Qwen one bounded chance to refine references after live evidence."""
        case_summary = self._format_completed_mandatory_summary(thinking_events)
        if not case_summary:
            return None, []
        detail_summary = self._format_post_case_detail_summary(thinking_events)

        handoff = self._parse_handoff_json(layer_analysis)
        matched = handoff.get("matched_runbooks") if isinstance(handoff, dict) else []
        if isinstance(matched, str):
            matched = [matched]
        existing_runbooks = [
            safe_id
            for item in (matched or [])
            if (safe_id := self._safe_runbook_id(str(item or "")))
        ]
        existing_text = (
            "\n".join(f"- {item}" for item in dict.fromkeys(existing_runbooks))
            or "- 无"
        )
        user_message = f"""action=post_case_runbook_reconciliation

# 用户问题
{question}

# 上游已经实际获取的 Runbook
{existing_text}

# 实时 collect_aiops_case 决定性摘要
{case_summary}

{detail_summary}

# 任务
- 这是 evidence_plan 完成后的 Runbook 重新裁决，不得重写 evidence_plan，也不得采集新的环境证据。
- 由你根据每个异常 Pod 的 Kubernetes 终态、决定性日志、Trace 和错误码，自主判断现有 Runbook 是否仍准确。
- 如果实时证据把通用候选收敛成更具体异常，只调用 `fetch_runbook` 获取缺失且明显匹配的 Runbook。
- 已在“上游已经实际获取”列表中的 Runbook 禁止重复调用；同一新 Runbook 本轮最多调用一次。
- 不要求每个 Pod 都新增 Runbook。现有 Runbook 足够或没有可靠匹配时，不调用工具并明确回答 `runbook_reconciliation: keep_existing_or_none`。
- Runbook 是参考知识，不是真实环境证据；不得把名称、标签或 Runbook 内容写成已证实根因。
"""
        system_prompt = """你负责根据实时可观测性证据重新裁决诊断 Runbook。
只允许调用 fetch_runbook；不得调用 Kubernetes、日志、指标、Trace、case 或修复工具。
Runbook 的选择由你完成，宿主不会按故障类型做硬编码映射。"""
        return self._call_llm(
            user_message,
            system_prompt,
            tool_result_sequence_start=tool_result_sequence_start,
            blocked_tool_names=self._blocked_tools_for_runbook_reconciliation(),
            skip_remediation_policy=True,
        )


    @staticmethod
    def _format_post_case_detail_summary(
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        lines = []
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or event.get("status") != "success"
                or str(event.get("tool_name") or "").lower()
                not in EvidenceCollectorNode._AIOPS_DETAIL_TOOLS
            ):
                continue
            args = (
                event.get("tool_args")
                if isinstance(event.get("tool_args"), dict)
                else {}
            )
            result = " ".join(
                str(
                    event.get("result")
                    or event.get("result_preview")
                    or ""
                ).split()
            )[:800]
            lines.append(
                f"- tool={event.get('tool_name')} "
                f"case_id={args.get('case_id') or '-'} "
                f"evidence_ref={args.get('evidence_ref') or '-'} "
                f"result={result}"
            )
        if not lines:
            return "# 按需细粒度补证\n- 本轮未展开额外 evidence ref。"
        return "# 按需细粒度补证\n" + "\n".join(lines)


    def _blocked_tools_for_runbook_reconciliation(self) -> set[str]:
        return {
            str(getattr(tool, "name", "") or "")
            for tool in (getattr(self, "tools", []) or [])
            if str(getattr(tool, "name", "") or "").strip()
            and str(getattr(tool, "name", "") or "").strip().lower()
            != "fetch_runbook"
        }


    def _diagnosis_snapshot_from_events(
        self,
        events: List[Dict[str, Any]],
    ) -> Optional[EntityEvidenceSnapshot]:
        """Build one bounded authoritative snapshot from collected events."""
        entities: List[Dict[str, str]] = []
        seen_entities: set[tuple[str, str]] = set()
        for event in events or []:
            if event.get("type") != "tool_result":
                continue
            target = self._extract_tool_event_pod_target(
                event,
                require_consistent=False,
            )
            if not target or target in seen_entities:
                continue
            seen_entities.add(target)
            entities.append({
                "kind": "Pod",
                "namespace": target[0],
                "name": target[1],
            })
        if not entities:
            return None
        tool_data = self._extract_tool_data_from_thinking(events)
        if not tool_data:
            return None
        try:
            return build_entity_evidence_snapshot(
                entities=entities,
                evidence_analysis={"tool_data": tool_data},
                thinking_events=events,
            )
        except Exception as exc:
            logger.warning(
                "⚠️ [evidence] 无法从当前工具事实建立紧凑诊断快照: %s",
                exc,
            )
            return None


    @staticmethod
    def _compact_diagnosis_catalog(
        snapshot: EntityEvidenceSnapshot,
        *,
        limit: int = 20,
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        """Project deterministic 1-based slots for a small-model contract."""
        manifest = snapshot.selection_manifest.to_dict()
        ordered_ids = list(dict.fromkeys([
            *(manifest.get("direct_causal_candidate_fact_ids") or []),
            *(manifest.get("required_context_fact_ids") or []),
            *(manifest.get("eligible_support_fact_ids") or []),
            *(manifest.get("rca_input_fact_ids") or []),
        ]))
        slot_fact_ids: List[str] = []
        catalogue: List[Dict[str, Any]] = []
        for fact_id in ordered_ids:
            fact = snapshot.fact_index.get(str(fact_id))
            if not isinstance(fact, Mapping):
                continue
            slot_fact_ids.append(str(fact_id))
            display = str(
                fact.get("display_value")
                or f"{fact.get('attribute')}={fact.get('value')}"
            )
            catalogue.append({
                "slot": len(slot_fact_ids),
                "dimension": fact.get("dimension"),
                "evidence_role": fact.get("evidence_role"),
                "attribute": fact.get("attribute"),
                "value": display[:600],
                "directness": fact.get("directness"),
                "confidence": fact.get("confidence"),
            })
            if len(slot_fact_ids) >= max(1, int(limit)):
                break
        return slot_fact_ids, catalogue


    @staticmethod
    def _authoritative_snapshot_entity_ids(
        snapshot: EntityEvidenceSnapshot,
    ) -> List[str]:
        return list(dict.fromkeys(
            str(entity_id)
            for ledger in snapshot.fact_ledgers
            for entity_id in ledger.scope_entity_ids
            if str(entity_id).strip()
        ))


    def _diagnosis_submission_is_acceptable(
        self,
        submission: Optional[DiagnosisSubmission],
        events: List[Dict[str, Any]],
    ) -> bool:
        """Check references and the minimum generic causal-support boundary."""
        accepted, _reasons = self._diagnosis_submission_acceptance(
            submission,
            events,
        )
        return accepted


    def _diagnosis_submission_acceptance(
        self,
        submission: Optional[DiagnosisSubmission],
        events: List[Dict[str, Any]],
    ) -> tuple[bool, List[str]]:
        """Return the generic publishability verdict and bounded feedback.

        The feedback describes contract failures only.  It never chooses a
        root cause, metric, Case, or evidence Fact for the model.
        """
        if submission is None:
            return False, ["未返回可解析的结构化诊断"]
        snapshot = self._diagnosis_snapshot_from_events(events)
        if snapshot is None or not snapshot.fact_ledgers:
            return False, ["当前没有可校验的权威事实账本"]
        causal_ids = set(
            snapshot.selection_manifest.direct_causal_candidate_fact_ids
        )
        if submission.diagnostic_status == "inconclusive":
            if causal_ids:
                return False, [
                    "事实目录含有直接因果候选，不能在未引用它们时提交 inconclusive"
                ]
            return True, []
        try:
            validated = validate_rca_claims(
                submission_to_rca(
                    submission,
                    authoritative_entity_ids=(
                        self._authoritative_snapshot_entity_ids(snapshot)
                    ),
                ),
                snapshot.fact_ledgers,
                authoritative_entity_ids=(
                    self._authoritative_snapshot_entity_ids(snapshot)
                ),
            )
        except Exception as exc:
            return False, [f"结构化诊断校验失败: {type(exc).__name__}"]
        claim = (
            validated.get("claim_validation")
            if isinstance(validated.get("claim_validation"), Mapping)
            else {}
        )
        valid_support = set(claim.get("valid_supporting_fact_ids") or [])
        accepted = bool(
            claim.get("diagnosis_publishable") is True
            and valid_support
            and (not causal_ids or valid_support & causal_ids)
        )
        if accepted:
            return True, []
        reasons = [
            str(reason).strip()
            for reason in (claim.get("reasons") or [])
            if str(reason).strip()
        ]
        if not valid_support:
            reasons.append("至少选择一个可校验的支撑证据槽位")
        if causal_ids and not valid_support & causal_ids:
            reasons.append("支撑证据必须包含至少一个 causal_candidate 槽位")
        if claim.get("diagnosis_publishable") is not True:
            reasons.append("当前提交尚未达到可发布诊断合同")
        return False, list(dict.fromkeys(reasons))[:6]


    def _try_compact_fact_diagnosis(
        self,
        *,
        events: List[Dict[str, Any]],
        phase: str,
        semantic_hint: Optional[Mapping[str, Any]] = None,
        max_attempts: int = 1,
    ) -> Optional[DiagnosisSubmission]:
        """Use a compact no-tool call, then bind slots to Fact IDs in code.

        This path only runs when code already sees direct causal candidates.
        It never chooses a Case, metric name or root cause in Python.
        """
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None or not hasattr(ai_call, "call_structured"):
            return None
        snapshot = self._diagnosis_snapshot_from_events(events)
        if snapshot is None or not snapshot.fact_ledgers:
            return None
        if not snapshot.selection_manifest.direct_causal_candidate_fact_ids:
            return None
        slot_fact_ids, catalogue = self._compact_diagnosis_catalog(snapshot)
        if not slot_fact_ids:
            return None
        entities = [
            {
                "namespace": entity.get("namespace"),
                "name": entity.get("name"),
            }
            for entity in snapshot.entities
        ]
        system_prompt = """
# 唯一职责：从给定事实形成紧凑诊断并选择证据槽位
输入只包含当前 Pod 的真实结构化事实。不得调用工具，也不得使用输入外信息。
判断最上游、可行动且被事实支持的原因，并输出最短的 原因→机制→现象 因果链。
supporting_evidence_slots 与 contradicting_evidence_slots 只能填写 facts 中存在的
正整数 slot；不要输出、编造或改写 Fact ID。diagnosed 必须至少选择一个
causal_candidate，并同时选择支撑根因关键条件的 configuration/context（若存在）。
如果事实只能描述现象而不能支持原因，提交 inconclusive 并写明缺口。
phenomenon、root_cause、causal_chain、unknowns、confidence_reason 等所有面向用户的
文字字段必须使用简体中文；Pod 名、命名空间、指标名、状态名和原始错误可保留原文。
""".strip()
        previous_diagnosis = dict(semantic_hint or {})
        validation_feedback: List[str] = []
        attempts = max(1, int(max_attempts))
        for attempt in range(1, attempts + 1):
            question = json.dumps({
                "contract_version": "aiops.compact-diagnosis-input.v1",
                "entities": entities,
                "facts": catalogue,
                "previous_semantic_diagnosis": previous_diagnosis,
                "validation_feedback": validation_feedback,
                "attempt": attempt,
                "max_attempts": attempts,
            }, ensure_ascii=False, separators=(",", ":"), default=str)
            start = time.time()
            structured: Optional[EvidenceSlotDiagnosisSubmission] = None
            try:
                candidate, _raw = ai_call.call_structured(
                    system_prompt=system_prompt,
                    question=question,
                    schema=EvidenceSlotDiagnosisSubmission,
                    node_id=(
                        f"evidence_{phase}"
                        if attempt == 1
                        else f"evidence_{phase}_retry"
                    ),
                    run_id=getattr(self, "current_run_id", ""),
                    max_tokens=1800,
                )
                if isinstance(candidate, EvidenceSlotDiagnosisSubmission):
                    structured = candidate
            except Exception as exc:
                validation_feedback = [
                    f"上次调用未返回有效结构: {type(exc).__name__}"
                ]
                logger.warning(
                    "⚠️ [evidence] 紧凑诊断阶段 %s 第 %d/%d 次未返回有效结构: %s",
                    phase,
                    attempt,
                    attempts,
                    exc,
                )
            finally:
                if self.metrics:
                    self.metrics.record_llm_call(
                        self.node_id,
                        (time.time() - start) * 1000,
                    )
            if structured is None:
                if not validation_feedback:
                    validation_feedback = ["上次响应无法解析为结构化诊断合同"]
            else:
                previous_diagnosis = structured.model_dump(mode="json")
                try:
                    bound = bind_evidence_slots(
                        structured,
                        slot_fact_ids=slot_fact_ids,
                    )
                except ValueError as exc:
                    validation_feedback = [str(exc)]
                    logger.warning(
                        "⚠️ [evidence] 紧凑诊断阶段 %s 第 %d/%d 次槽位非法: %s",
                        phase,
                        attempt,
                        attempts,
                        exc,
                    )
                else:
                    accepted, validation_feedback = (
                        self._diagnosis_submission_acceptance(bound, events)
                    )
                    if accepted:
                        return bound
                    logger.warning(
                        "⚠️ [evidence] 紧凑诊断阶段 %s 第 %d/%d 次未通过: %s",
                        phase,
                        attempt,
                        attempts,
                        "；".join(validation_feedback) or "未知合同错误",
                    )
            if attempt < attempts:
                logger.info(
                    "🔁 [evidence] baseline 事实已足够，使用代码校验反馈进行第 %d 次紧凑诊断",
                    attempt + 1,
                )
        return None


    @staticmethod
    def _fetched_runbook_ids(
        thinking_events: List[Dict[str, Any]],
    ) -> List[str]:
        fetched: List[str] = []
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or event.get("status") != "success"
                or str(event.get("tool_name") or "").casefold() != "fetch_runbook"
            ):
                continue
            args = event.get("tool_args") if isinstance(event.get("tool_args"), dict) else {}
            runbook_id = str(args.get("runbook_id") or "").strip()
            if runbook_id and runbook_id not in fetched:
                fetched.append(runbook_id)
        return fetched


    def _run_pre_react_observability_baseline(
        self,
        evidence_plan: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Run one source-backed lifecycle + three-signal baseline before ReAct.

        The structured plan still owns query parameters.  Code only schedules
        one scoped call per Pod and dimension concurrently, so this introduces
        no Case/status/metric-name branching.  A retry collector receives the
        first attempt's facts and can investigate freely without mechanically
        repeating the baseline.
        """
        if not bool(getattr(self, "run_observability_baseline", True)):
            return []
        if not self._is_observability_first_round_gate_enabled():
            return []
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None or not hasattr(ai_call, "execute_tool_batch"):
            logger.warning(
                "⚠️ [evidence] 无可用 execute_tool_batch，跳过代码级首轮三维 baseline"
            )
            return []

        requests: List[Dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for item in evidence_plan or []:
            if not isinstance(item, dict):
                continue
            tool_name = self._normalize_plan_text(item.get("tool"))
            if tool_name not in self._PRE_REACT_BASELINE_TOOLS:
                continue
            target = self._extract_plan_pod_target(item)
            if not target:
                continue
            key = (target[0], target[1], tool_name)
            if key in seen:
                continue
            seen.add(key)
            requests.append({
                "tool_name": tool_name,
                "tool_args": dict(item.get("tool_args") or {}),
                "plan_item_id": str(item.get("id") or ""),
                "purpose": str(item.get("purpose") or ""),
            })
        if not requests:
            return []

        logger.info(
            "🚦 [evidence] ReAct 前并行执行四维 baseline: calls=%d targets=%d",
            len(requests),
            len({
                (request["tool_args"].get("namespace"), request["tool_args"].get("pod"))
                for request in requests
            }),
        )
        return ai_call.execute_tool_batch(
            tool_requests=requests,
            tools=getattr(self, "tools", []) or [],
            stream_queue=getattr(self, "_event_queue", None),
            node_id=self.node_id,
            run_id=getattr(self, "current_run_id", ""),
            cancel_event=getattr(self, "cancel_event", None),
            max_workers=len(requests),
        )

    def _append_baseline_handoff(
        self,
        user_message: str,
        baseline_events: List[Dict[str, Any]],
    ) -> str:
        """Give ReAct a compact baseline without replaying raw tool payloads."""
        observations = []
        for event in baseline_events:
            if event.get("type") != "tool_result":
                continue
            observations.append({
                "tool_name": event.get("tool_name"),
                "status": event.get("status"),
                "semantic_success": event.get("semantic_success"),
                "summary": str(event.get("result") or "")[:600],
                "raw_ref": event.get("raw_ref"),
                "structured_ref": event.get("structured_ref"),
                "summary_ref": event.get("summary_ref"),
            })
        compact_facts: List[Dict[str, Any]] = []
        snapshot = self._diagnosis_snapshot_from_events(baseline_events)
        if snapshot is not None:
            slot_fact_ids, catalogue = self._compact_diagnosis_catalog(
                snapshot
            )
            compact_facts = [
                {**fact, "fact_id": slot_fact_ids[index]}
                for index, fact in enumerate(catalogue)
            ]
        payload = json.dumps(
            {
                "contract_version": "aiops.pre-react-baseline.v2",
                "observations": observations,
                "facts": compact_facts,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        return (
            f"{user_message.rstrip()}\n\n"
            "# 代码预采集的 Kubernetes 与三维可观测性 baseline\n"
            "以下是 ReAct 启动前已真实并行执行的生命周期、Metrics、Logging、"
            "Tracing 紧凑事实，不是根因结论。"
            "再自主决定需要调用哪些只读工具继续调查；不要机械重复完全相同的查询。\n"
            f"{payload}\n"
        )

    def _blocked_tools_for_preplanned_execution(
        self,
        evidence_plan: List[Dict[str, Any]],
    ) -> set[str]:
        """Limit execution to tools declared by the structured evidence plan."""
        allowed_tools = {"fetch_runbook"}
        if bool(getattr(self, "require_diagnosis_submission", False)):
            # The lane's core Agent must be able to choose among the existing
            # read-only diagnostic tools after seeing baseline results.  Write
            # tools and arbitrary shell execution remain unavailable unless a
            # separate workflow explicitly plans them.
            allowed_tools.update(self._AUTONOMOUS_DIAGNOSIS_TOOLS)
        if self._is_autonomous_observability_enabled():
            allowed_tools.update(self._OBSERVABILITY_QUERY_TOOLS)
        if any(
            isinstance(item, dict)
            and (
                item.get("source") == "mandatory_live_observability"
                or self._normalize_plan_text(item.get("tool")) == "collect_aiops_case"
            )
            for item in (evidence_plan or [])
        ):
            allowed_tools.add("get_aiops_case_evidence")
        for item in evidence_plan or []:
            if not isinstance(item, dict):
                continue
            tool_name = str(item.get("tool") or "").strip().lower()
            if tool_name:
                allowed_tools.add(tool_name)
            allowed_tools.update(
                str(name or "").strip().lower()
                for name in (item.get("acceptable_tools") or [])
                if str(name or "").strip()
            )

        # The general Prometheus MCP is intentionally reserved for /query.
        # Pod diagnosis must use execute_pod_promql so every selector remains
        # bound to the exact namespace/pod evidence scope.  A model-generated
        # plan cannot override this workflow boundary.
        allowed_tools.difference_update(self._QUERY_ONLY_PROMETHEUS_TOOLS)

        return {
            str(getattr(tool, "name", "") or "")
            for tool in (getattr(self, "tools", []) or [])
            if str(getattr(tool, "name", "") or "").strip()
            and str(getattr(tool, "name", "") or "").strip().lower()
            not in allowed_tools
        }

    def _ensure_autonomous_observability_gate_plan(
        self,
        evidence_plan: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        plan = [
            dict(item)
            for item in (evidence_plan or [])
            if isinstance(item, dict)
        ]
        targets = [
            (namespace.lower(), pod.lower())
            for namespace, pod in self._collect_confirmed_handoff_pod_targets(
                layer_handoff or {}
            )
        ]
        targets = list(dict.fromkeys(targets))
        if not targets:
            return plan

        selected_indexes: set[int] = set()
        gate_items: List[Dict[str, Any]] = []
        for target_index, (namespace, pod) in enumerate(targets, start=1):
            for tool_name in self._OBSERVABILITY_QUERY_ORDER:
                existing_index = next(
                    (
                        index
                        for index, item in enumerate(plan)
                        if index not in selected_indexes
                        and self._normalize_plan_text(item.get("tool")) == tool_name
                        and self._extract_plan_pod_target(item)
                        == (namespace, pod)
                    ),
                    None,
                )
                if existing_index is not None:
                    item = dict(plan[existing_index])
                    selected_indexes.add(existing_index)
                else:
                    item = self._build_autonomous_observability_gate_item(
                        namespace=namespace,
                        pod=pod,
                        tool_name=tool_name,
                        target_index=target_index,
                    )
                    logger.info(
                        "🧭 [evidence] 补入首轮可观测门控项: %s/%s:%s",
                        namespace,
                        pod,
                        tool_name,
                    )

                args = dict(item.get("tool_args") or {})
                args.setdefault("namespace", namespace)
                args.setdefault("pod", pod)
                args.setdefault(
                    "purpose",
                    self._default_observability_gate_purpose(tool_name),
                )
                item["tool_args"] = args
                item["purpose"] = str(
                    item.get("purpose")
                    or args.get("purpose")
                    or self._default_observability_gate_purpose(tool_name)
                )
                item["level"] = "critical"
                item["source"] = "observability_first_round_gate"
                acceptable = [
                    str(value).strip()
                    for value in (item.get("acceptable_tools") or [])
                    if str(value).strip()
                ]
                if tool_name not in acceptable:
                    acceptable.append(tool_name)
                item["acceptable_tools"] = acceptable
                gate_items.append(item)

        remaining = [
            item
            for index, item in enumerate(plan)
            if index not in selected_indexes
        ]
        return self._normalize_evidence_plan(
            [*remaining, *gate_items],
            layer_handoff=layer_handoff,
        )

    @classmethod
    def _build_autonomous_observability_gate_item(
        cls,
        *,
        namespace: str,
        pod: str,
        tool_name: str,
        target_index: int,
    ) -> Dict[str, Any]:
        purpose = cls._default_observability_gate_purpose(tool_name)
        common = {
            "id": (
                f"observability-gate-{target_index}-"
                f"{cls._observability_tool_dimension(tool_name)}"
            ),
            "description": (
                f"首轮查询异常 Pod {namespace}/{pod} 的"
                f"{cls._observability_tool_dimension(tool_name)} 真实数据"
            ),
            "level": "critical",
            "tool": tool_name,
            "purpose": purpose,
            "acceptable_tools": [tool_name],
            "source": "observability_first_round_gate",
        }
        if tool_name == "execute_pod_promql":
            namespace_selector = json.dumps(namespace)
            pod_selector = json.dumps(pod)
            promql = " or ".join([
                (
                    "kube_pod_status_phase"
                    f"{{namespace={namespace_selector},pod={pod_selector}}}"
                ),
                (
                    "kube_pod_container_status_waiting_reason"
                    f"{{namespace={namespace_selector},pod={pod_selector}}}"
                ),
                (
                    "kube_pod_container_status_last_terminated_reason"
                    f"{{namespace={namespace_selector},pod={pod_selector}}}"
                ),
                (
                    "kube_pod_container_status_restarts_total"
                    f"{{namespace={namespace_selector},pod={pod_selector}}}"
                ),
            ])
            common.update({
                "command": "execute generic Pod lifecycle PromQL",
                "tool_args": {
                    "namespace": namespace,
                    "pod": pod,
                    "purpose": purpose,
                    "promql": promql,
                    "query_type": "instant",
                },
            })
            return common
        if tool_name == "query_pod_logs":
            common.update({
                "command": "query recent real Pod logs without preset fault keywords",
                "tool_args": {
                    "namespace": namespace,
                    "pod": pod,
                    "purpose": purpose,
                    "window_minutes": 30,
                    "max_records": 20,
                    "allow_name_fallback": True,
                },
            })
            return common
        if tool_name == "query_pod_topology":
            common.update({
                "command": "query source-backed Pod topology relationships",
                "tool_args": {
                    "namespace": namespace,
                    "pod": pod,
                    "purpose": purpose,
                },
            })
            return common
        common.update({
            "command": "query recent real Pod flows and application spans",
            "tool_args": {
                "namespace": namespace,
                "pod": pod,
                "purpose": purpose,
                "window_minutes": 30,
                "direction": "any",
                "include_tempo": True,
                "max_records": 20,
            },
        })
        return common

    @staticmethod
    def _observability_tool_dimension(tool_name: str) -> str:
        return {
            "execute_pod_promql": "metrics",
            "query_pod_logs": "logging",
            "query_pod_tracing": "tracing",
            "query_pod_topology": "topology",
        }.get(str(tool_name or "").strip().lower(), "observability")

    @classmethod
    def _default_observability_gate_purpose(cls, tool_name: str) -> str:
        return {
            "execute_pod_promql": (
                "首轮获取目标 Pod 的真实生命周期、等待原因、终止原因和重启指标，"
                "为后续选择更具体的 PromQL 提供基线"
            ),
            "query_pod_logs": (
                "首轮获取目标 Pod 最近时间窗的真实 ES/Filebeat 日志，"
                "识别可用于后续精确查询的错误原文、字段、路径或 trace ID"
            ),
            "query_pod_tracing": (
                "首轮获取目标 Pod 最近时间窗的真实 DeepFlow 流量和 Tempo Span，"
                "确认调用数据是否存在并发现可继续追踪的请求或 trace ID"
            ),
            "query_pod_topology": (
                "首轮获取目标 Pod 的真实 Kubernetes 控制器、Service、节点和容器关系，"
                "为后续因果链提供来源可核验的拓扑边"
            ),
        }.get(str(tool_name or "").strip().lower(), "首轮获取目标 Pod 的真实可观测性数据")


    @staticmethod
    def _build_evidence_user_message(
        question: str,
        layer: str,
        layer_handoff: str,
        context_archive_ref: str = "",
        layer_archive_ref: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
        failure_reason: str = "",
        existing_plan: Optional[List[Dict[str, Any]]] = None,
        plan_mode: str = "dynamic_collection",
        observability_mode: str = "legacy",
    ) -> str:
        strict_section = ""
        if existing_plan:
            plan_lines = []
            for item in existing_plan:
                if not isinstance(item, dict):
                    continue
                plan_lines.append(
                    "- {id}: level={level}, tool={tool}, command={command}, tool_args={tool_args}, purpose={purpose}".format(
                        id=item.get("id", ""),
                        level=item.get("level", ""),
                        tool=item.get("tool", ""),
                        command=item.get("command", ""),
                        tool_args=json.dumps(item.get("tool_args") or {}, ensure_ascii=False, default=str),
                        purpose=item.get("purpose", ""),
                    )
                )
            strict_section = f"""

# 既有 evidence_plan
直接执行以下计划，不重新规划：
{chr(10).join(plan_lines)}
- {failure_reason or '请直接按既有计划执行工具'}
"""
        elif strict_mode:
            strict_section = f"""

# 上一轮结果被系统拒绝
- 失败原因：{failure_reason or '上一轮只返回计划，没有执行工具'}
- 至少执行一个 critical/important 只读工具；没有 tool_result 时不得声称采集完成。
"""
        archive_refs = layer_archive_ref or {}
        archive_lines = []
        context_root = (context_archive_ref or "").strip()
        if context_root:
            archive_lines.extend([
                "# context archive",
                "- context archive 已落盘，仅供人工排障；evidence 默认不要读取归档。",
                "- 归档不是当前环境证据，不要把读取归档写入 evidence_plan。",
            ])
        if archive_refs.get("handoff_ref"):
            archive_lines.append("- layer handoff 已由上方 layer_handoff 注入；不要重复读取归档。")
        archive_section = "\n".join(archive_lines).strip() if archive_lines else "无"
        if existing_plan:
            plan_protocol = EVIDENCE_PLAN_PROTOCOL_EXISTING
        elif plan_mode == "preplanned_execution":
            plan_protocol = EVIDENCE_PLAN_PROTOCOL_PREPLANNED
        else:
            plan_protocol = EVIDENCE_PLAN_PROTOCOL_DYNAMIC
        handoff_obj = EvidenceCollectorNode._parse_handoff_json(layer_handoff)
        compact_handoff = EvidenceCollectorNode._compact_layer_handoff_for_prompt(handoff_obj, layer_handoff)
        abnormal_summary_section = EvidenceCollectorNode._format_current_abnormal_summary_for_prompt(handoff_obj)
        matched_runbook_context = EvidenceCollectorNode._build_matched_runbook_context_for_prompt(handoff_obj)
        message = EVIDENCE_USER_MESSAGE_TEMPLATE.format(
            question=question,
            compact_handoff=compact_handoff,
            abnormal_summary_section=abnormal_summary_section,
            matched_runbook_context=matched_runbook_context,
            archive_section=archive_section,
            plan_protocol=plan_protocol,
            strict_section=strict_section,
            output_instruction=(
                "直接执行既有 Pydantic evidence_plan 中的必要工具，最后输出简短证据结论。"
                if existing_plan
                else "调用必要真实工具后输出简短证据结论；不要手写 EvidenceCollectionOutput。"
            ),
        )
        if not existing_plan or observability_mode == "autonomous":
            case_guidance = EvidenceCollectorNode._build_live_observability_plan_guidance(
                question,
                handoff_obj,
                observability_mode=observability_mode,
            )
            if case_guidance:
                message = f"{message.rstrip()}\n\n{case_guidance}\n"
        retry_context = handoff_obj.get("diagnosis_retry")
        if isinstance(retry_context, dict):
            retry_payload = json.dumps(
                retry_context,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )
            message = (
                f"{message.rstrip()}\n\n"
                "# 第二次完整 ReAct 诊断上下文\n"
                "根据门禁反馈重新调查未解决的问题。保留已有有效事实，必要时用只读工具补证；"
                "可以放弃第一次判断，不要只修 JSON，也不要重复完全相同的查询。\n"
                f"{retry_payload[:18000]}\n"
            )
        return message

    @classmethod
    def _build_live_observability_plan_guidance(
        cls,
        question: str,
        handoff: Dict[str, Any],
        observability_mode: str = "legacy",
    ) -> str:
        del question
        autonomous_mode = (
            str(observability_mode or "").strip().lower() == "autonomous"
        )
        targets = cls._collect_confirmed_handoff_pod_targets(handoff)
        if not targets:
            return ""
        rendered_targets = ", ".join(
            f"{namespace}/{pod}"
            for namespace, pod in targets[:8]
        )
        if len(targets) > 8:
            rendered_targets += f" 等 {len(targets)} 个 Pod"
        if autonomous_mode:
            return (
                "# 自主可观测性组合查询\n"
                f"- 上游已确认的异常 Pod 候选：{rendered_targets}。\n"
                "- 代码已安排 Kubernetes 与 Metrics、Logging、Tracing、Topology 首轮查询；真实执行并保持精确实体范围。\n"
                "- 首轮结果可能是 present、empty、absent、weak 或 error；先判断它们是否回答各自 purpose。\n"
                "- 仍有关键歧义或冲突时，用新的 purpose 自主选择少量补证；没有诊断增益时停止，不追求维度齐全。\n"
                "- 只在完整 trace_id 一致时关联日志、Flow 和 Span；上下文使用率达到 80% 时停止新增采集。"
            )
        return (
            "# 实时可观测性证据优先\n"
            f"- 上游已确认的异常 Pod 候选：{rendered_targets}。\n"
            "- 诊断应优先依赖当前环境工具返回的真实证据，而不是 Runbook、名称、标签或模型经验推断。\n"
            "- 每个已确认异常 Pod 都必须优先执行其 mandatory `collect_aiops_case` 计划项；"
            "这是 Pod 级高信息密度入口，可一次返回 Kubernetes、Metrics、Logging、Tracing 和 Topology。\n"
            "- coarse 结果足够时避免重复采集；coverage 缺失、冲突、error、absent 或工具不可用时，"
            "kubectl/Prometheus 等细粒度工具才作为补证和降级路径。\n"
            "- Agent 负责真实执行、理解 coverage 和选择必要补证，但不能跳过 mandatory coarse 项后直接推论。\n"
            "- 上下文使用率达到 80% 后停止新增采集，明确列出未采集 Pod，不得把它们写成已验证结论。"
        )

    @classmethod
    def _validated_pod_target(
        cls,
        namespace: Any,
        pod: Any,
    ) -> Optional[tuple[str, str]]:
        namespace_text = str(namespace or "")
        pod_text = str(pod or "")
        if (
            not namespace_text
            or len(namespace_text) > 63
            or not cls._DNS1123_LABEL_RE.fullmatch(namespace_text)
            or not pod_text
            or len(pod_text) > 253
        ):
            return None
        segments = pod_text.split(".")
        if not segments or any(
            len(segment) > 63
            or not cls._DNS1123_LABEL_RE.fullmatch(segment)
            for segment in segments
        ):
            return None
        return namespace_text, pod_text

    @classmethod
    def _collect_confirmed_handoff_pod_targets(
        cls,
        handoff: Dict[str, Any],
    ) -> List[tuple[str, str]]:
        confirmed_targets: List[tuple[str, str]] = []

        def add_target(entity: Dict[str, Any]) -> None:
            target = cls._validated_pod_target(
                entity.get("namespace"),
                entity.get("name") or entity.get("value"),
            )
            if target:
                confirmed_targets.append(target)

        primary_pod = handoff.get("primary_pod")
        if isinstance(primary_pod, dict):
            add_target(primary_pod)
        for entity in handoff.get("primary_entities") or []:
            if not isinstance(entity, dict):
                continue
            kind = entity.get("kind") or entity.get("type")
            if str(kind or "").strip().lower() == "pod":
                add_target(entity)
        for group_key in ("issue_groups", "abnormal_groups"):
            for group in handoff.get(group_key) or []:
                if not isinstance(group, dict):
                    continue
                for entity in (
                    group.get("entities")
                    or group.get("primary_entities")
                    or []
                ):
                    if not isinstance(entity, dict):
                        continue
                    kind = entity.get("kind") or entity.get("type")
                    if str(kind or "").strip().lower() == "pod":
                        add_target(entity)
        for entity in handoff.get("abnormal_pods") or []:
            if not isinstance(entity, dict):
                continue
            kind = entity.get("kind") or entity.get("type") or "pod"
            if str(kind).strip().lower() == "pod":
                add_target(entity)
        return list(dict.fromkeys(confirmed_targets))

    @classmethod
    def _collect_handoff_pod_targets(
        cls,
        handoff: Dict[str, Any],
    ) -> List[tuple[str, str]]:
        confirmed_targets = cls._collect_confirmed_handoff_pod_targets(
            handoff
        )
        fallback_targets: List[tuple[str, str]] = []

        def add_target(entity: Dict[str, Any], destination: List[tuple[str, str]]) -> None:
            target = cls._validated_pod_target(
                entity.get("namespace"),
                entity.get("name") or entity.get("value"),
            )
            if target:
                destination.append(target)

        for entity in handoff.get("active_entities") or []:
            if not isinstance(entity, dict):
                continue
            if str(entity.get("type") or "").strip().lower() != "pod":
                continue
            add_target(entity, fallback_targets)
        if confirmed_targets:
            confirmed_set = set(confirmed_targets)
            targets = [
                target for target in fallback_targets
                if target in confirmed_set
            ] + confirmed_targets
        else:
            targets = fallback_targets
        return list(dict.fromkeys(targets))

    @classmethod
    def _bind_handoff_pod_target(
        cls,
        item: Dict[str, Any],
        handoff_targets: List[tuple[str, str]],
    ) -> Dict[str, Any]:
        bound = dict(item)
        if (
            cls._normalize_plan_text(bound.get("tool")) != "collect_aiops_case"
            or cls._extract_plan_pod_target(bound)
            or not handoff_targets
        ):
            return bound

        text = " ".join(
            str(value).strip().lower()
            for value in (
                bound.get("command"),
                bound.get("description"),
                bound.get("purpose"),
                bound.get("target_scope"),
            )
            if isinstance(value, str) and value.strip()
        )
        text = " ".join(text.split())
        if not text:
            return bound

        def contains_identifier(value: str) -> bool:
            return bool(re.search(
                rf"(?<![A-Za-z0-9_.-]){re.escape(value.lower())}"
                r"(?![A-Za-z0-9_.-])",
                text,
            ))

        pod_matches = [
            (namespace.lower(), pod.lower())
            for namespace, pod in handoff_targets
            if contains_identifier(pod)
        ]
        if len(pod_matches) > 1:
            pod_matches = [
                target
                for target in pod_matches
                if contains_identifier(target[0])
            ]
        if len(pod_matches) != 1:
            return bound

        namespace, pod = pod_matches[0]
        args = dict(bound.get("tool_args") or {})
        args.setdefault("namespace", namespace)
        args.setdefault("pod", pod)
        bound["tool_args"] = args
        logger.info(
            "🧭 [evidence] 依据已确认异常 Pod 绑定自然语言计划: id=%s target=%s/%s",
            bound.get("id", ""),
            namespace,
            pod,
        )
        return bound

    def _ensure_mandatory_aiops_case_plan(
        self,
        evidence_plan: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        plan = [dict(item) for item in (evidence_plan or []) if isinstance(item, dict)]
        tool_names = {
            str(getattr(tool, "name", "") or "")
            for tool in (getattr(self, "tools", []) or [])
        }
        if "collect_aiops_case" not in tool_names:
            return plan

        targets = self._collect_confirmed_handoff_pod_targets(
            layer_handoff or {}
        )
        if not targets:
            return plan
        normalized_targets = {
            (namespace.lower(), pod.lower())
            for namespace, pod in targets
        }

        existing_by_target: Dict[tuple[str, str], Dict[str, Any]] = {}
        remaining: List[Dict[str, Any]] = []
        preserved_extra_targets: set[tuple[str, str]] = set()
        for item in plan:
            if self._normalize_plan_text(item.get("tool")) != "collect_aiops_case":
                remaining.append(item)
                continue
            target = self._extract_plan_pod_target(item)
            if not target:
                remaining.append(item)
                continue
            if target not in normalized_targets:
                if target in preserved_extra_targets:
                    logger.info(
                        "♻️ [evidence] 跳过额外目标的重复 collect_aiops_case 计划: id=%s target=%s/%s",
                        item.get("id", ""),
                        target[0],
                        target[1],
                    )
                    continue
                preserved_extra_targets.add(target)
                remaining.append(item)
                continue
            if target in existing_by_target:
                logger.info(
                    "♻️ [evidence] 跳过同目标重复 collect_aiops_case 计划: id=%s target=%s/%s",
                    item.get("id", ""),
                    target[0],
                    target[1],
                )
                continue
            item["level"] = "critical"
            item["source"] = "mandatory_live_observability"
            args = dict(item.get("tool_args") or {})
            args.setdefault("namespace", target[0])
            args.setdefault("pod", target[1])
            args.setdefault("scenario", "auto")
            item["tool_args"] = args
            existing_by_target[target] = item

        mandatory: List[Dict[str, Any]] = []
        for index, (namespace, pod) in enumerate(targets, start=1):
            normalized_target = (namespace.lower(), pod.lower())
            existing = existing_by_target.get(normalized_target)
            if existing is not None:
                mandatory.append(existing)
                continue
            mandatory.append({
                "id": f"aiops-case-{index}",
                "description": f"实时采集异常 Pod {namespace}/{pod} 的多维可观测性 case",
                "level": "critical",
                "tool": "collect_aiops_case",
                "command": f"collect_aiops_case namespace={namespace} pod={pod}",
                "tool_args": {
                    "namespace": namespace,
                    "pod": pod,
                    "scenario": "auto",
                },
                "purpose": "采集 Kubernetes、Metrics、Logging、Tracing 和 Topology 真实证据",
                "acceptable_tools": ["collect_aiops_case"],
                "source": "mandatory_live_observability",
            })
            logger.info(
                "🧭 [evidence] 补入 mandatory collect_aiops_case: %s/%s",
                namespace,
                pod,
            )

        return mandatory + remaining

    def _prepare_evidence_plan(
        self,
        evidence_plan: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        normalized = self._normalize_evidence_plan(
            evidence_plan,
            layer_handoff=layer_handoff,
        )
        if self._is_autonomous_observability_enabled():
            return normalized
        with_mandatory = self._ensure_mandatory_aiops_case_plan(
            normalized,
            layer_handoff,
        )
        return self._normalize_evidence_plan(
            with_mandatory,
            layer_handoff=layer_handoff,
        )

    @staticmethod
    def _parse_handoff_json(layer_handoff: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(layer_handoff) if layer_handoff else {}
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _compact_layer_handoff_for_prompt(handoff: Dict[str, Any], raw_handoff: str) -> str:
        if not handoff:
            return raw_handoff or "{}"

        keep_keys = {
            "layer",
            "derived_layer",
            "confidence",
            "primary_problem",
            "reasoning",
            "abnormal_pods",
            "abnormal_groups",
            "pod_status_keyword",
            "pod_abnormal_type",
            "status_category",
            "active_entities",
            "active_signals",
            "possible_scenarios",
            "must_verify",
            "issue_groups",
            "current_abnormal_summary",
            "matched_runbooks",
            "diagnosis_retry",
        }
        compact = {
            key: EvidenceCollectorNode._strip_archive_refs(handoff[key])
            for key in keep_keys
            if key in handoff
        }
        summary = compact.get("current_abnormal_summary")
        if isinstance(summary, dict):
            compact["current_abnormal_summary"] = {
                key: summary[key]
                for key in ("source", "status_counts", "total_abnormal", "selected_rows")
                if key in summary
            }
        return json.dumps(compact, ensure_ascii=False, default=str)

    @staticmethod
    def _strip_archive_refs(value: Any) -> Any:
        archive_keys = {
            "archive_ref",
            "context_archive_ref",
            "raw_ref",
            "summary_ref",
            "structured_ref",
            "handoff_ref",
            "input_ref",
            "output_ref",
            "full_analysis_ref",
        }
        if isinstance(value, dict):
            return {
                key: EvidenceCollectorNode._strip_archive_refs(item)
                for key, item in value.items()
                if key not in archive_keys
            }
        if isinstance(value, list):
            return [EvidenceCollectorNode._strip_archive_refs(item) for item in value]
        return value

    @classmethod
    def _build_matched_runbook_context_for_prompt(cls, handoff: Dict[str, Any]) -> str:
        matched = handoff.get("matched_runbooks") if isinstance(handoff, dict) else []
        if isinstance(matched, str):
            matched = [matched]
        if not isinstance(matched, list) or not matched:
            return ""

        sections = []
        seen = set()
        for runbook_id in matched[:5]:
            safe_id = cls._safe_runbook_id(str(runbook_id or ""))
            if not safe_id or safe_id in seen:
                continue
            seen.add(safe_id)
            content = cls._read_runbook_content(safe_id)
            if not content:
                logger.info("📚 [evidence] layer matched runbook 未找到，跳过注入: %s", safe_id)
                continue
            summary = cls._extract_runbook_plan_context(content)
            if summary:
                sections.append(f"## {safe_id}\n{summary}")

        if not sections:
            return ""
        return "# Layer 已确认 Runbook 上下文\n" + "\n\n".join(sections)

    @staticmethod
    def _safe_runbook_id(runbook_id: str) -> str:
        text = os.path.basename((runbook_id or "").strip())
        if not text:
            return ""
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", text):
            return ""
        return text if text.endswith(".md") else f"{text}.md"

    @classmethod
    def _read_runbook_content(cls, runbook_id: str) -> str:
        for directory in cls._candidate_runbook_dirs():
            path = directory / runbook_id
            try:
                if path.is_file():
                    return path.read_text(encoding="utf-8")
            except OSError:
                continue
        return cls._read_runbook_from_configmap(runbook_id)

    @staticmethod
    def _candidate_runbook_dirs() -> List[Path]:
        dirs = []
        env_dirs = os.getenv("AIOPS_RUNBOOK_DIRS", "")
        for item in env_dirs.split(":"):
            item = item.strip()
            if item:
                dirs.append(Path(item))
        dirs.extend([
            Path("/app/knowledge_base/runbooks"),
            Path("knowledge_base/runbooks"),
            Path("/etc/aiops/runbooks"),
        ])
        return dirs

    @staticmethod
    def _read_runbook_from_configmap(runbook_id: str) -> str:
        for path in (Path("deploy/configmap/runbooks.yaml"), Path("deploy/configmap/runbooks.bak.yaml")):
            try:
                if not path.is_file():
                    continue
                import yaml

                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                content = ((data.get("data") or {}).get(runbook_id) or "")
                if content:
                    return str(content)
            except Exception:
                logger.debug("📚 [evidence] 读取 runbook configmap 失败: %s", path, exc_info=True)
        return ""

    @staticmethod
    def _extract_runbook_plan_context(content: str, max_chars: int = 2500) -> str:
        lines = (content or "").splitlines()
        if not lines:
            return ""

        title = next((line for line in lines if line.startswith("# ")), "").strip()
        wanted_headings = (
            "Evidence 节点推荐计划",
            "必查项",
            "判定规则",
            "状态识别",
            "典型原因",
        )
        sections = [title] if title else []
        i = 0
        while i < len(lines):
            line = lines[i]
            heading = line.strip().lstrip("#").strip()
            if any(key in heading for key in wanted_headings):
                block = [line.rstrip()]
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.startswith("# "):
                        break
                    block.append(nxt.rstrip())
                    i += 1
                sections.append("\n".join(block).strip())
                continue
            i += 1

        if len(sections) <= (1 if title else 0):
            sections.append("\n".join(lines[:80]).strip())
        text = "\n\n".join(part for part in sections if part).strip()
        return text[:max_chars]

    @staticmethod
    def _format_current_abnormal_summary_for_prompt(handoff: Dict[str, Any]) -> str:
        summary = handoff.get("current_abnormal_summary") if isinstance(handoff, dict) else {}
        issue_groups = handoff.get("issue_groups") if isinstance(handoff, dict) else []
        lines = ["# 当前异常结构化摘要（必须优先审查）"]

        status_counts = summary.get("status_counts") if isinstance(summary, dict) else {}
        if isinstance(status_counts, dict) and status_counts:
            lines.append("status_counts:")
            for status, count in status_counts.items():
                lines.append(f"- {status}: {count}")
        else:
            lines.append("status_counts: 未提供；从 issue_groups/abnormal_pods 进行最小覆盖。")

        selected_rows = summary.get("selected_rows") if isinstance(summary, dict) else []
        if isinstance(selected_rows, list) and selected_rows:
            lines.append("selected_rows:")
            for row in selected_rows[:10]:
                lines.append(f"- {row}")

        if isinstance(issue_groups, list) and issue_groups:
            lines.append("issue_groups:")
            for idx, group in enumerate(issue_groups[:8], start=1):
                if not isinstance(group, dict):
                    continue
                group_id = group.get("group_id") or f"g{idx}"
                statuses = ", ".join(str(s) for s in group.get("status_keywords", []) if s)
                abnormal_type = group.get("pod_abnormal_type", "")
                layers = ", ".join(str(l) for l in group.get("compatible_layers", []) if l)
                entities = group.get("entities") or group.get("primary_entities") or []
                entity_texts = []
                if isinstance(entities, list):
                    for entity in entities[:5]:
                        if not isinstance(entity, dict):
                            continue
                        namespace = entity.get("namespace", "")
                        name = entity.get("name", "")
                        kind = entity.get("kind", "Pod")
                        entity_texts.append(f"{kind}/{namespace}/{name}" if namespace else f"{kind}/{name}")
                lines.append(
                    f"- {group_id}: statuses={statuses or 'unknown'}, "
                    f"type={abnormal_type or 'unknown'}, layers={layers or 'unknown'}, "
                    f"entities={', '.join(entity_texts) or 'unknown'}"
                )

        lines.append(
            "要求：非 Running/Completed/Succeeded/Ready/Bound/Active 的状态都需要至少最小验证；"
            "主异常组做完整验证，非主异常组验证当前状态 + 一个最关键事件/配置/依赖信号。"
        )
        return "\n".join(lines)

    def _get_plan_protocol_failure_reason(
        self,
        evidence_plan: List[Dict],
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        """检查 evidence 是否遵守了先 plan 后执行的协议。"""
        if evidence_plan:
            if not self._has_effective_tool_evidence(thinking_events):
                return "上一轮只返回 evidence_plan，没有任何有效工具证据，系统已拒绝该结果"
            return ""

        return "上一轮没有可用的 Pydantic evidence_plan，系统已拒绝该结果"

    @staticmethod
    def _plan_exists_without_tool_results(reason: str) -> bool:
        return "只返回 evidence_plan" in (reason or "")

    @classmethod
    def _normalize_evidence_plan(
        cls,
        evidence_plan: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Bound and deduplicate LLM-generated evidence plans.

        This keeps dynamic planning but removes repeated variants for the same
        evidence dimension, e.g. curl/telnet/nc against the same registry.
        """
        handoff_targets = cls._collect_confirmed_handoff_pod_targets(
            layer_handoff or {}
        )
        prepared = [
            cls._bind_handoff_pod_target(
                cls._normalize_plan_tool_args(item),
                handoff_targets,
            )
            for item in (evidence_plan or [])
            if isinstance(item, dict)
        ]
        coarse_targets = {
            target
            for item in prepared
            if cls._normalize_plan_text(item.get("tool")) == "collect_aiops_case"
            if (target := cls._extract_plan_pod_target(item))
        }
        has_coarse_case = bool(coarse_targets)

        normalized: List[Dict[str, Any]] = []
        seen_signatures: set[tuple[str, str, str]] = set()
        max_items = 10
        regular_items = 0

        for item in prepared:
            is_system_forced = (
                item.get("source") in cls._SYSTEM_FORCED_PLAN_SOURCES
            )
            if not is_system_forced and cls._is_redundant_with_coarse_case(
                item,
                coarse_targets=coarse_targets,
                has_coarse_case=has_coarse_case,
            ):
                logger.info(
                    "♻️ [evidence] coarse case 已覆盖同目标细粒度计划: id=%s tool=%s command=%s",
                    item.get("id", ""),
                    item.get("tool", ""),
                    item.get("command", ""),
                )
                continue
            signature = cls._evidence_plan_signature(item)
            if signature in seen_signatures:
                logger.info(
                    "♻️ [evidence] 跳过重复采证计划: id=%s tool=%s command=%s",
                    item.get("id", ""),
                    item.get("tool", ""),
                    item.get("command", ""),
                )
                continue
            seen_signatures.add(signature)
            if not is_system_forced:
                if regular_items >= max_items:
                    logger.info("✂️ [evidence] evidence_plan 超过 %d 项，已截断", max_items)
                    continue
                regular_items += 1
            normalized.append(item)

        if layer_handoff:
            logger.info(
                "📋 [evidence] 不再自动补全 evidence_plan；异常组覆盖只通过 LLM Pydantic plan 与后续统计呈现"
            )
        return normalized

    @classmethod
    def _is_redundant_with_coarse_case(
        cls,
        item: Dict[str, Any],
        *,
        coarse_targets: set[tuple[str, str]],
        has_coarse_case: bool,
    ) -> bool:
        tool = cls._normalize_plan_text(item.get("tool"))
        if tool == "collect_aiops_case" or not has_coarse_case:
            return False
        if tool in {"fetch_runbook", "read_context_archive"}:
            return False
        if tool in {"get_aiops_case", "get_aiops_case_evidence"}:
            # The case id does not exist until collect_aiops_case returns, so
            # these cannot be useful in the same initial plan.
            return True

        redundant_tools = {
            "kubectl_describe",
            "kubectl_get_by_name",
            "kubectl_get_yaml",
            "kubectl_events",
            "kubectl_logs",
            "kubectl_previous_logs",
            "kubectl_logs_all_containers",
            "kubectl_previous_logs_all_containers",
            "kubectl_container_logs",
            "kubectl_container_previous_logs",
            "kubectl_logs_grep",
            "kubectl_logs_all_containers_grep",
            "execute_prometheus_instant_query",
            "execute_prometheus_range_query",
            "query_aiops_k8s_snapshot",
            "query_aiops_metrics",
            "query_aiops_logs",
            "query_aiops_deepflow_flows",
            "build_aiops_topology",
        }
        if tool not in redundant_tools:
            return False
        target = cls._extract_plan_pod_target(item)
        return bool(target and target in coarse_targets)

    @classmethod
    def _extract_plan_pod_target(cls, item: Dict[str, Any]) -> Optional[tuple[str, str]]:
        tool = cls._normalize_plan_text(item.get("tool"))
        command = str(item.get("command") or "")
        target_scope = str(item.get("target_scope") or "").strip()
        args = item.get("tool_args") if isinstance(item.get("tool_args"), dict) else {}

        namespace = str(
            args.get("namespace")
            or args.get("target_namespace")
            or ""
        ).strip("'\"").lower()
        kind = cls._normalize_resource_kind(
            args.get("kind")
            or args.get("resource_kind")
            or args.get("resource_type")
            or args.get("entity_type")
        )
        pod_name = str(
            args.get("pod")
            or args.get("pod_name")
            or args.get("target_pod")
            or args.get("target_pod_name")
            or ""
        ).strip("'\"").lower()
        if not pod_name and kind in {"", "pod"}:
            pod_name = str(
                args.get("entity_name")
                or args.get("entity")
                or args.get("name")
                or args.get("resource_name")
                or ""
            ).strip("'\"").lower()
        if not pod_name and tool in {
            "kubectl_logs",
            "kubectl_previous_logs",
            "kubectl_logs_all_containers",
            "kubectl_previous_logs_all_containers",
            "kubectl_container_logs",
            "kubectl_container_previous_logs",
            "kubectl_logs_grep",
            "kubectl_logs_all_containers_grep",
        }:
            pod_name = str(args.get("name") or args.get("resource_name") or "").strip("'\"").lower()

        if target_scope:
            scope = target_scope.strip("'\" /")
            if scope.lower().startswith("pod:"):
                scope = scope[4:].strip()
            scope_parts = [part.strip().lower() for part in scope.split("/") if part.strip()]
            if len(scope_parts) == 2:
                namespace = namespace or scope_parts[0]
                pod_name = pod_name or scope_parts[1]
            elif len(scope_parts) == 3 and scope_parts[0] == "pod":
                namespace = namespace or scope_parts[1]
                pod_name = pod_name or scope_parts[2]

        if tool == "collect_aiops_case":
            entity_path_match = re.search(
                r"\b(?:[A-Za-z_][A-Za-z0-9_]*_)?entity\s*[:=]\s*"
                r"[\"']?pod/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)"
                r"(?=[\"'\s,;)]|$)",
                command,
                re.IGNORECASE,
            )
            if entity_path_match:
                namespace = namespace or entity_path_match.group(1).lower()
                pod_name = pod_name or entity_path_match.group(2).lower()
            bare_target_match = re.fullmatch(
                r"\s*([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\s*",
                command,
            )
            if bare_target_match:
                namespace = namespace or bare_target_match.group(1).lower()
                pod_name = pod_name or bare_target_match.group(2).lower()
            prefixed_target_match = re.search(
                r"\bfor\s+([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?=\s|$|[,;)])",
                command,
                re.IGNORECASE,
            )
            if prefixed_target_match:
                namespace = namespace or prefixed_target_match.group(1).lower()
                pod_name = pod_name or prefixed_target_match.group(2).lower()
            colon_target_match = re.fullmatch(
                r"\s*pod:([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+)\s*",
                command,
                re.IGNORECASE,
            )
            if colon_target_match:
                pod_name = pod_name or colon_target_match.group(1).lower()
                namespace = namespace or colon_target_match.group(2).lower()

        namespace_match = re.search(
            r"(?:^|\s)-n\s+([^\s]+)|(?:^|\s)--namespace(?:=|\s+)([^\s]+)",
            command,
            re.IGNORECASE,
        )
        if not namespace and namespace_match:
            namespace = (namespace_match.group(1) or namespace_match.group(2) or "").strip("'\"").lower()

        coarse_match = re.search(
            r"\bpod(?:\s+|/)([A-Za-z0-9_.-]+)\s+"
            r"in\s+namespace\s+([A-Za-z0-9_.-]+)",
            command,
            re.IGNORECASE,
        )
        if coarse_match:
            pod_name = pod_name or coarse_match.group(1).lower()
            namespace = namespace or coarse_match.group(2).lower()

        pod_command_match = re.search(
            r"(?:^|\s)pod\s+([A-Za-z0-9_.-]+)(?=\s|$)",
            command,
            re.IGNORECASE,
        )
        if pod_command_match and not pod_command_match.group(1).startswith("-"):
            pod_name = pod_name or pod_command_match.group(1).lower()

        event_match = re.search(r"involvedObject\.name=([^,\s]+)", command, re.IGNORECASE)
        if event_match and tool == "kubectl_events":
            pod_name = pod_name or event_match.group(1).strip("'\"").lower()

        logs_match = re.search(r"\bkubectl\s+logs\s+([A-Za-z0-9_.-]+)", command, re.IGNORECASE)
        if logs_match:
            pod_name = pod_name or logs_match.group(1).lower()

        resource_target = cls._extract_plan_resource_target(command)
        if resource_target.get("kind") == "pod":
            namespace = namespace or resource_target.get("namespace", "")
            pod_name = pod_name or resource_target.get("name", "")

        if not pod_name:
            pod_filter = re.search(
                r"\b(?:target_)?pod(?:_name)?\s*(?:=|=~)\s*[\"']?([A-Za-z0-9_.-]+)",
                command,
                re.IGNORECASE,
            )
            if pod_filter:
                pod_name = pod_filter.group(1).lower()
        if (
            not pod_name
            and tool == "collect_aiops_case"
            and re.search(r"\b(?:get\s+)?pod\b", command, re.IGNORECASE)
        ):
            name_filter = re.search(
                r"\b(?:target_)?(?:pod_)?name\s*(?:=|=~)\s*[\"']?([A-Za-z0-9_.-]+)",
                command,
                re.IGNORECASE,
            )
            if name_filter:
                pod_name = name_filter.group(1).lower()
        if (
            not pod_name
            and tool == "collect_aiops_case"
            and re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\(", command)
        ):
            name_filter = re.search(
                r"\b(?:target_)?(?:pod_)?name\s*=\s*[\"']?"
                r"([A-Za-z0-9_.-]+)",
                command,
                re.IGNORECASE,
            )
            if name_filter:
                pod_name = name_filter.group(1).lower()
        if not namespace:
            namespace_filter = re.search(
                r"\b(?:target_)?namespace\s*(?:=|=~)\s*[\"']?([A-Za-z0-9_.-]+)",
                command,
                re.IGNORECASE,
            )
            if namespace_filter:
                namespace = namespace_filter.group(1).lower()

        if tool == "collect_aiops_case" and (not namespace or not pod_name):
            labelled_values = {
                key.lower(): value.lower()
                for key, value in re.findall(
                    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*"
                    r"[\"']?([A-Za-z0-9_.-]+)",
                    command,
                )
            }
            for key, value in labelled_values.items():
                if not key.endswith("_name") or "pod" not in key:
                    continue
                prefix = key[:-len("_name")]
                paired_namespace = labelled_values.get(f"{prefix}_namespace")
                if not paired_namespace:
                    continue
                pod_name = pod_name or value
                namespace = namespace or paired_namespace
                break

        if namespace and pod_name:
            return namespace, pod_name
        return None

    @classmethod
    def _normalize_plan_tool_args(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(item)
        tool = cls._normalize_plan_text(normalized.get("tool"))
        command = str(normalized.get("command") or "")

        if cls._plan_requires_yaml(normalized):
            if tool != "kubectl_get_yaml":
                logger.info(
                    "🧭 [evidence] 将 YAML 采证计划工具规范化为 kubectl_get_yaml: id=%s old_tool=%s command=%s",
                    normalized.get("id", ""),
                    normalized.get("tool", ""),
                    command,
                )
            normalized["tool"] = "kubectl_get_yaml"
            acceptable_tools = [
                str(item).strip()
                for item in (normalized.get("acceptable_tools") or [])
                if str(item).strip()
            ]
            if "kubectl_get_yaml" not in acceptable_tools:
                acceptable_tools.insert(0, "kubectl_get_yaml")
            if "run_bash_command" not in acceptable_tools:
                acceptable_tools.append("run_bash_command")
            normalized["acceptable_tools"] = acceptable_tools
            tool_args = normalized.get("tool_args")
            if isinstance(tool_args, dict):
                # `output_format=yaml` is a kubectl_get_by_name convention in
                # some MCPs. Keeping it on kubectl_get_yaml can make the model
                # copy an incompatible argument shape. The command remains the
                # source of truth for the YAML target.
                cleaned_args = dict(tool_args)
                cleaned_args.pop("output_format", None)
                normalized["tool_args"] = cleaned_args

        tool = cls._normalize_plan_text(normalized.get("tool"))
        if tool in {"kubectl_get_yaml", "kubectl_describe", "kubectl_get_by_name"}:
            derived_args = cls._derive_kubectl_named_resource_tool_args(command)
            if derived_args:
                current_args = normalized.get("tool_args") if isinstance(normalized.get("tool_args"), dict) else {}
                merged_args = dict(derived_args)
                merged_args.update({k: v for k, v in dict(current_args).items() if v not in (None, "")})
                normalized["tool_args"] = merged_args

        if isinstance(normalized.get("tool_args"), dict) and normalized["tool_args"]:
            return normalized

        if tool == "kubectl_events":
            tool_args = cls._derive_kubectl_events_tool_args(command)
            if tool_args:
                normalized["tool_args"] = tool_args
        return normalized

    @classmethod
    def _plan_requires_yaml(cls, item: Dict[str, Any]) -> bool:
        command = str(item.get("command") or "")
        evidence_type = cls._normalize_plan_text(item.get("evidence_type"), item.get("purpose"), item.get("description"))
        tool_args = item.get("tool_args") if isinstance(item.get("tool_args"), dict) else {}
        output_format = str((tool_args or {}).get("output_format") or "").strip().lower()
        return (
            output_format in {"yaml", "yml"}
            or bool(re.search(r"(?:^|\s)(?:-o|--output)(?:=|\s+)(?:yaml|yml)\b", command, re.IGNORECASE))
            or "pod_yaml" in evidence_type
            or " yaml" in f" {evidence_type}"
            or "yaml " in f"{evidence_type} "
        )

    @staticmethod
    def _derive_kubectl_events_tool_args(command: str) -> Dict[str, str]:
        text = command or ""
        namespace = ""
        namespace_match = re.search(r"(?:^|\s)-n\s+([^\s]+)|(?:^|\s)--namespace(?:=|\s+)([^\s]+)", text)
        if namespace_match:
            namespace = namespace_match.group(1) or namespace_match.group(2) or ""

        resource_name = ""
        name_match = re.search(r"involvedObject\.name=([^,\s]+)", text)
        if name_match:
            resource_name = name_match.group(1)
        if not resource_name:
            object_match = re.search(r"\b(?:pod|pods)/([A-Za-z0-9_.-]+)", text, re.IGNORECASE)
            if object_match:
                resource_name = object_match.group(1)

        args: Dict[str, str] = {}
        if resource_name:
            args["resource_type"] = "pod"
            args["resource_name"] = resource_name
        if namespace:
            args["namespace"] = namespace
        return args

    @staticmethod
    def _derive_kubectl_named_resource_tool_args(command: str) -> Dict[str, str]:
        text = command or ""
        if not text.strip():
            return {}

        namespace = ""
        namespace_match = re.search(r"(?:^|\s)-n\s+([^\s]+)|(?:^|\s)--namespace(?:=|\s+)([^\s]+)", text)
        if namespace_match:
            namespace = namespace_match.group(1) or namespace_match.group(2) or ""

        # Supports common forms:
        #   kubectl get pod my-pod -n ns -o yaml
        #   kubectl get -o yaml pod my-pod -n ns
        #   kubectl describe node node1
        tokens = re.findall(r"(?:'[^']*'|\"[^\"]*\"|\S+)", text)
        tokens = [token.strip("'\"") for token in tokens]
        if not tokens:
            return {}

        resource_kinds = {
            "pod": "pod",
            "pods": "pod",
            "node": "node",
            "nodes": "node",
            "deployment": "deployment",
            "deployments": "deployment",
            "statefulset": "statefulset",
            "statefulsets": "statefulset",
            "daemonset": "daemonset",
            "daemonsets": "daemonset",
            "replicaset": "replicaset",
            "replicasets": "replicaset",
            "service": "service",
            "services": "service",
            "svc": "service",
            "pvc": "pvc",
            "pv": "pv",
            "configmap": "configmap",
            "configmaps": "configmap",
            "secret": "secret",
            "secrets": "secret",
            "storageclass": "storageclass",
            "storageclasses": "storageclass",
        }
        flag_with_value = {"-n", "--namespace", "-o", "--output", "-l", "--selector", "--field-selector"}

        for idx, token in enumerate(tokens):
            kind = resource_kinds.get(token.lower())
            if not kind:
                continue
            name = ""
            cursor = idx + 1
            while cursor < len(tokens):
                candidate = tokens[cursor]
                if candidate in flag_with_value:
                    cursor += 2
                    continue
                if any(candidate.startswith(prefix) for prefix in ("-n=", "--namespace=", "-o=", "--output=")):
                    cursor += 1
                    continue
                if candidate.startswith("-"):
                    cursor += 1
                    continue
                name = candidate
                break
            if not name:
                continue
            args = {"kind": kind, "name": name}
            if namespace:
                args["namespace"] = namespace
            return args
        return {}

    @classmethod
    def _evidence_plan_signature(cls, item: Dict[str, Any]) -> tuple[str, str, str]:
        tool = cls._normalize_plan_text(item.get("tool"))
        command = cls._normalize_plan_text(item.get("command"))
        purpose = cls._normalize_plan_text(item.get("purpose"), item.get("description"))
        if tool in cls._OBSERVABILITY_QUERY_TOOLS:
            pod_target = cls._extract_plan_pod_target(item)
            if pod_target:
                return (
                    tool,
                    f"{pod_target[0]}/{pod_target[1]}",
                    purpose[:120] or command[:160],
                )
        target = cls._extract_plan_target(command)
        intent = cls._classify_plan_intent(command, purpose)

        if intent in {"registry_connectivity", "dns_connectivity"} and target:
            return ("connectivity", intent, target)
        if intent == "runtime_info":
            return (tool, intent, target or "runtime")
        if intent and target:
            return (tool, intent, target)
        return (tool, intent or purpose[:80], command[:160])

    @staticmethod
    def _normalize_plan_text(*values: Any) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return " ".join(value.lower().split())
        return ""

    @staticmethod
    def _extract_plan_target(command: str) -> str:
        text = command or ""
        resource_target = EvidenceCollectorNode._extract_plan_resource_target(text)
        if resource_target:
            kind = resource_target.get("kind", "")
            namespace = resource_target.get("namespace", "")
            name = resource_target.get("name", "")
            if namespace:
                return f"{kind}/{namespace}/{name}"
            return f"{kind}/{name}"

        url_match = re.search(r"https?://([^/\s:]+)", text, re.IGNORECASE)
        if url_match:
            return url_match.group(1).lower()

        host_match = re.search(
            r"\b([a-z0-9][a-z0-9.-]*\.(?:io|com|net|org|cn|local))\b",
            text,
            re.IGNORECASE,
        )
        if host_match:
            return host_match.group(1).lower()

        node_match = re.search(r"\bnode\s+([a-z0-9]([-a-z0-9]*[a-z0-9])?)\b", text, re.IGNORECASE)
        if node_match:
            return f"node/{node_match.group(1)}"

        return ""

    @staticmethod
    def _extract_plan_resource_target(command: str) -> Dict[str, str]:
        """Extract a concrete kubectl resource target from common command forms.

        Supported examples:
        - kubectl describe pod name -n ns
        - kubectl describe pod -n ns name
        - kubectl get pod/name -n ns -o yaml
        - kubectl get pod -n ns name -o yaml
        """
        text = command or ""
        if "kubectl" not in text and not re.search(r"\b(get|describe)\s+", text, re.IGNORECASE):
            return {}

        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
        if not tokens:
            return {}

        namespace = ""
        cleaned: List[str] = []
        skip_next = False
        for idx, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue
            lower = token.lower()
            if lower in {"-n", "--namespace"}:
                if idx + 1 < len(tokens):
                    namespace = tokens[idx + 1].strip("'\"")
                    skip_next = True
                continue
            if lower.startswith("--namespace="):
                namespace = token.split("=", 1)[1].strip("'\"")
                continue
            cleaned.append(token)

        verbs = {"get", "describe", "logs", "events"}
        kind_aliases = {
            "pod": "pod",
            "pods": "pod",
            "po": "pod",
            "node": "node",
            "nodes": "node",
            "no": "node",
            "secret": "secret",
            "secrets": "secret",
            "configmap": "configmap",
            "configmaps": "configmap",
            "cm": "configmap",
            "pvc": "pvc",
            "pvcs": "pvc",
            "persistentvolumeclaim": "pvc",
            "persistentvolumeclaims": "pvc",
            "service": "service",
            "services": "service",
            "svc": "service",
            "deployment": "deployment",
            "deployments": "deployment",
            "replicaset": "replicaset",
            "replicasets": "replicaset",
            "rs": "replicaset",
            "daemonset": "daemonset",
            "daemonsets": "daemonset",
            "ds": "daemonset",
            "statefulset": "statefulset",
            "statefulsets": "statefulset",
            "sts": "statefulset",
            "event": "event",
            "events": "event",
            "networkpolicy": "networkpolicy",
            "networkpolicies": "networkpolicy",
        }
        value_flags = {
            "-o",
            "--output",
            "-l",
            "--selector",
            "--field-selector",
            "--sort-by",
            "--container",
            "-c",
            "--since",
            "--tail",
        }
        boolean_flags = {
            "-A",
            "--all-namespaces",
            "--show-labels",
            "--previous",
            "--watch",
            "-w",
            "--ignore-not-found",
        }

        verb_index = next((i for i, token in enumerate(cleaned) if token.lower() in verbs), -1)
        if verb_index < 0:
            return {}

        i = verb_index + 1
        while i < len(cleaned):
            token = cleaned[i]
            lower = token.lower()
            if lower in boolean_flags:
                i += 1
                continue
            if lower in value_flags:
                i += 2
                continue
            if lower.startswith("-"):
                i += 1
                continue
            if "/" in lower:
                kind_part, name_part = lower.split("/", 1)
                kind = kind_aliases.get(kind_part)
                if kind and name_part:
                    return {"kind": kind, "namespace": namespace.lower(), "name": name_part.strip("'\"").lower()}
            kind = kind_aliases.get(lower)
            if kind:
                j = i + 1
                while j < len(cleaned):
                    candidate = cleaned[j]
                    candidate_lower = candidate.lower()
                    if candidate_lower in boolean_flags:
                        j += 1
                        continue
                    if candidate_lower in value_flags:
                        j += 2
                        continue
                    if candidate_lower.startswith("-"):
                        j += 1
                        continue
                    if candidate_lower in kind_aliases:
                        return {"kind": kind, "namespace": namespace.lower(), "name": ""}
                    if re.match(r"^[a-z0-9]([-a-z0-9.]*[a-z0-9])?$", candidate_lower):
                        return {"kind": kind, "namespace": namespace.lower(), "name": candidate_lower.strip("'\"")}
                    break
                return {"kind": kind, "namespace": namespace.lower(), "name": ""}
            i += 1

        return {}

    @staticmethod
    def _classify_plan_intent(command: str, purpose: str) -> str:
        text = f"{command}\n{purpose}"
        if re.search(r"\b(curl|wget|telnet|nc|ping)\b|连通|可达|访问|registry|docker\.io|镜像仓库", text, re.IGNORECASE):
            if re.search(r"dns|nslookup|dig|解析", text, re.IGNORECASE):
                return "dns_connectivity"
            return "registry_connectivity"
        if re.search(r"\bdescribe\s+(pod|po)\b|events?|事件", text, re.IGNORECASE):
            return "pod_events"
        if re.search(r"\b(docker|containerd|crictl|runtime)\b.*\b(info|version|status)\b|容器运行时|docker 守护进程", text, re.IGNORECASE):
            return "runtime_info"
        if re.search(r"\bget\s+(pod|po)\b.*-o\s+yaml|yaml|imagepullsecrets?|镜像|配置", text, re.IGNORECASE):
            return "pod_config"
        if re.search(r"\b(secret|imagepullsecret|dockerconfigjson)\b", text, re.IGNORECASE):
            return "secret_config"
        if re.search(r"\b(logs?)\b|日志", text, re.IGNORECASE):
            return "pod_logs"
        if re.search(r"\bdescribe\s+node\b|kubelet|节点", text, re.IGNORECASE):
            return "node_state"
        return ""

    def _should_stop_collection_early(self, thinking_events: list) -> bool:
        """
        动态采证提前停止条件：
        - 已解析到 evidence_plan
        - 至少已有一次成功工具调用
        - 所有 critical + important 级计划证据都已被当前工具结果满足
        或者
        - 没有 critical/important 项时，全部计划项都已满足
        """
        evidence_plan = getattr(self, "_active_evidence_plan", None)
        if not evidence_plan:
            return False

        successful_tools = [
            ev
            for ev in self._project_final_evidence_events(
                thinking_events
            )
            if ev.get("type") == "tool_result"
            and ev.get("deduplicated") is not True
            and ev.get("status") == "success"
            and (
                ev.get("semantic_success", True) is not False
                or self._is_diagnostic_negative_tool_result(
                    ev.get("tool_name", ""),
                    ev.get("result", ev.get("result_preview", "")),
                    ev.get("structured") or {},
                )
            )
        ]
        if not successful_tools:
            return False

        mandatory_targets = self._mandatory_case_targets(evidence_plan)
        if mandatory_targets:
            attempted_targets = self._attempted_mandatory_case_targets(thinking_events)
            uncollected_targets = [
                f"{namespace}/{pod}"
                for namespace, pod in mandatory_targets
                if (namespace, pod) not in attempted_targets
            ]
            max_context_ratio = max(
                (
                    float(ev.get("context_usage_ratio"))
                    for ev in thinking_events
                    if isinstance(ev.get("context_usage_ratio"), (int, float))
                ),
                default=0.0,
            )
            if max_context_ratio >= 0.8:
                self._early_stop_state = {
                    "triggered": True,
                    "reason": "context_budget_stop",
                    "required_levels": ["mandatory_live_observability"],
                    "context_usage_ratio": max_context_ratio,
                    "uncollected_targets": uncollected_targets,
                }
                return True

            successful_targets = self._successful_mandatory_case_targets(thinking_events)
            if all(target in successful_targets for target in mandatory_targets):
                self._early_stop_state = {
                    "triggered": False,
                    "reason": "mandatory_live_observability_ready_for_reconciliation",
                    "required_levels": ["mandatory_live_observability"],
                    "uncollected_targets": [],
                    "post_case_reconciliation": False,
                }
                return False
            return False

        if self._coarse_case_has_missing_dimensions(evidence_plan, thinking_events):
            self._early_stop_state = {
                "triggered": False,
                "reason": "collect_aiops_case 存在缺失维度，继续按 coverage 补证",
                "required_levels": ["critical", "important"],
            }
            return False

        evidence_items = self._build_evidence_items_from_thinking(evidence_plan, thinking_events)
        planned_items = [
            e for e in evidence_items
            if getattr(e, "source", "") in ("thinking_match", "thinking_negative_match", "planned")
        ]
        required_items = [
            e for e in planned_items
            if e.level in (EvidenceLevel.CRITICAL, EvidenceLevel.IMPORTANT)
        ]

        if required_items:
            missing_required = [e.description for e in required_items if not e.collected]
            if missing_required:
                return False

            self._early_stop_state = {
                "triggered": True,
                "reason": "critical 和 important 级证据均已满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }
            return True

        all_collected = bool(planned_items) and all(e.collected for e in planned_items)
        if all_collected:
            self._early_stop_state = {
                "triggered": True,
                "reason": "计划中的证据已全部满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }
        return all_collected

    @classmethod
    def _mandatory_case_targets(
        cls,
        evidence_plan: List[Dict[str, Any]],
    ) -> List[tuple[str, str]]:
        targets = [
            target
            for item in (evidence_plan or [])
            if isinstance(item, dict)
            and item.get("source") == "mandatory_live_observability"
            if (target := cls._extract_plan_pod_target(item))
        ]
        return list(dict.fromkeys(targets))

    @classmethod
    def _extract_tool_event_pod_target(
        cls,
        event: Dict[str, Any],
        *,
        require_consistent: bool = False,
    ) -> Optional[tuple[str, str]]:
        args = event.get("tool_args") if isinstance(event.get("tool_args"), dict) else {}
        requested = cls._extract_plan_pod_target({
            "tool": event.get("tool_name") or "collect_aiops_case",
            "command": event.get("command") or "",
            "target_scope": event.get("target_scope") or "",
            "tool_args": args,
        })
        structured = event.get("structured") if isinstance(event.get("structured"), dict) else {}
        primary = (
            structured.get("primary_entity")
            if isinstance(structured.get("primary_entity"), dict)
            else {}
        )
        observed_namespace = str(primary.get("namespace") or "").strip().lower()
        observed_pod = str(primary.get("name") or "").strip().lower()
        observed = (
            (observed_namespace, observed_pod)
            if observed_namespace and observed_pod
            else None
        )
        entity = (
            structured.get("entity")
            if isinstance(structured.get("entity"), dict)
            else {}
        )
        entity_namespace = str(entity.get("namespace") or "").strip().lower()
        entity_pod = str(
            entity.get("pod") or entity.get("name") or ""
        ).strip().lower()
        if entity_namespace and entity_pod:
            observed = (entity_namespace, entity_pod)
        if require_consistent and requested and observed and requested != observed:
            logger.warning(
                "⚠️ [evidence] collect_aiops_case 请求目标与返回实体不一致: requested=%s/%s observed=%s/%s",
                requested[0],
                requested[1],
                observed[0],
                observed[1],
            )
            return None
        return observed or requested

    @classmethod
    def _trusted_pod_uid_index(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[tuple[str, str], str]:
        candidates: Dict[tuple[str, str], set[str]] = {}
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or event.get("status") != "success"
                or event.get("semantic_success") is not True
            ):
                continue
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            tool_name = str(
                event.get("tool_name") or ""
            ).strip().lower()
            if (
                tool_name
                not in cls._KUBERNETES_LIFECYCLE_AUTHORITY_TOOLS
            ):
                continue
            requested_scope = cls._exact_pod_identity_request(event)
            if not requested_scope:
                continue
            scope = cls._extract_tool_event_pod_target(
                event,
                require_consistent=True,
            )
            if not scope or scope != requested_scope:
                continue
            observed_uids: set[str] = set()
            for candidate, name_keys in (
                (structured.get("primary_entity"), ("name", "pod")),
                (structured.get("entity"), ("pod", "name")),
                (structured, ("name", "pod")),
            ):
                if not isinstance(candidate, dict):
                    continue
                kind = str(candidate.get("kind") or "Pod").strip().lower()
                namespace = str(
                    candidate.get("namespace") or ""
                ).strip().lower()
                name = next(
                    (
                        str(candidate.get(key) or "").strip().lower()
                        for key in name_keys
                        if str(candidate.get(key) or "").strip()
                    ),
                    "",
                )
                uid = str(
                    candidate.get("uid")
                    or candidate.get("pod_uid")
                    or ""
                ).strip()
                if (
                    kind in {"pod", "pods"}
                    and namespace
                    and name
                    and (namespace, name) == scope
                    and uid
                ):
                    observed_uids.add(uid)
            if observed_uids:
                candidates.setdefault(scope, set()).update(observed_uids)
        return {
            scope: next(iter(uids))
            for scope, uids in candidates.items()
            if len(uids) == 1
        }

    @classmethod
    def _exact_pod_identity_request(
        cls,
        event: Dict[str, Any],
    ) -> Optional[tuple[str, str]]:
        args = (
            event.get("tool_args")
            if isinstance(event.get("tool_args"), dict)
            else {}
        )
        kind = cls._normalize_resource_kind(
            args.get("kind")
            or args.get("resource_kind")
            or args.get("resource_type")
            or args.get("entity_type")
        )
        if kind != "pod":
            return None
        return cls._extract_plan_pod_target({
            "tool": event.get("tool_name") or "",
            "tool_args": args,
        })

    @classmethod
    def _with_trusted_pod_uid(
        cls,
        event: Dict[str, Any],
        structured: Dict[str, Any],
        trusted_uid_index: Dict[tuple[str, str], str],
    ) -> Dict[str, Any]:
        scope = cls._extract_tool_event_pod_target(
            event,
            require_consistent=True,
        )
        uid = trusted_uid_index.get(scope) if scope else None
        if not uid:
            return dict(structured)

        enriched = dict(structured)
        for key, name_keys, uid_key in (
            ("primary_entity", ("name", "pod"), "uid"),
            ("entity", ("pod", "name"), "pod_uid"),
        ):
            candidate = enriched.get(key)
            if not isinstance(candidate, dict):
                continue
            candidate_scope = (
                str(candidate.get("namespace") or "").strip().lower(),
                next(
                    (
                        str(candidate.get(name_key) or "").strip().lower()
                        for name_key in name_keys
                        if str(candidate.get(name_key) or "").strip()
                    ),
                    "",
                ),
            )
            if (
                key == "entity"
                and candidate_scope == ("", "")
                and str(candidate.get("kind") or "Pod").strip().lower()
                in {"pod", "pods"}
            ):
                candidate = dict(candidate)
                candidate["namespace"] = scope[0]
                candidate["pod"] = scope[1]
                candidate[uid_key] = uid
                enriched[key] = candidate
                continue
            if (
                candidate_scope == scope
                and not str(
                    candidate.get("uid")
                    or candidate.get("pod_uid")
                    or ""
                ).strip()
            ):
                candidate = dict(candidate)
                candidate[uid_key] = uid
                enriched[key] = candidate

        top_level_scope = (
            str(enriched.get("namespace") or "").strip().lower(),
            str(
                enriched.get("name")
                or enriched.get("pod")
                or ""
            ).strip().lower(),
        )
        if (
            top_level_scope == scope
            and not str(
                enriched.get("uid")
                or enriched.get("pod_uid")
                or ""
            ).strip()
        ):
            enriched["uid"] = uid
        return enriched

    @classmethod
    def _final_observability_query_events(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Return the shared final semantic projection for query attempts."""
        return [
            event
            for event in project_final_observability_events(
                thinking_events
            )
            if isinstance(event, dict)
        ]

    @classmethod
    def _project_final_evidence_events(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Keep raw non-query evidence and only final semantic query events."""
        final_query_event_ids = {
            id(event)
            for event in cls._final_observability_query_events(
                thinking_events
            )
        }
        return [
            event
            for event in (thinking_events or [])
            if isinstance(event, dict)
            and (
                str(event.get("tool_name") or "").strip().lower()
                not in cls._OBSERVABILITY_QUERY_TOOLS
                or id(event) in final_query_event_ids
            )
        ]

    @classmethod
    def _autonomous_observability_targets(
        cls,
        evidence_plan: List[Dict[str, Any]],
    ) -> List[tuple[str, str]]:
        targets = [
            (namespace, pod)
            for namespace, pod, _ in cls._autonomous_observability_gate_items(
                evidence_plan
            )
        ]
        return list(dict.fromkeys(targets))

    @classmethod
    def _autonomous_observability_gate_items(
        cls,
        evidence_plan: List[Dict[str, Any]],
    ) -> List[tuple[str, str, str]]:
        items = [
            (target[0], target[1], tool_name)
            for item in (evidence_plan or [])
            if isinstance(item, dict)
            and (
                tool_name := str(item.get("tool") or "").strip().lower()
            )
            in cls._OBSERVABILITY_QUERY_TOOLS
            if (target := cls._extract_plan_pod_target(item))
        ]
        return list(dict.fromkeys(items))

    @classmethod
    def _attempted_autonomous_observability_gate_items(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> set[tuple[str, str, str]]:
        attempted: set[tuple[str, str, str]] = set()
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
            ):
                continue
            tool_name = str(event.get("tool_name") or "").strip().lower()
            if tool_name not in cls._OBSERVABILITY_QUERY_TOOLS:
                continue
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            args = (
                event.get("tool_args")
                if isinstance(event.get("tool_args"), dict)
                else {}
            )
            purpose = str(
                structured.get("purpose") or args.get("purpose") or ""
            ).strip()
            if not purpose:
                continue
            target = cls._extract_tool_event_pod_target(
                event,
                require_consistent=True,
            )
            if target:
                attempted.add((target[0], target[1], tool_name))
        return attempted

    @classmethod
    def _attempted_autonomous_observability_targets(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> set[tuple[str, str]]:
        return {
            (namespace, pod)
            for namespace, pod, _ in (
                cls._attempted_autonomous_observability_gate_items(
                    thinking_events
                )
            )
        }

    @classmethod
    def _present_autonomous_observability_gate_items(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> set[tuple[str, str, str]]:
        present: set[tuple[str, str, str]] = set()
        for event in cls._final_observability_query_events(
            thinking_events
        ):
            tool_name = str(
                event.get("tool_name") or ""
            ).strip().lower()
            if tool_name not in cls._OBSERVABILITY_QUERY_TOOLS:
                continue
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            if (
                structured.get("status") != "query_succeeded"
                or str(
                    structured.get("coverage") or ""
                ).strip().lower() != "present"
            ):
                continue
            target = cls._extract_tool_event_pod_target(
                event,
                require_consistent=True,
            )
            if target:
                present.add((target[0], target[1], tool_name))
        return present

    @classmethod
    def _attempted_mandatory_case_targets(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> set[tuple[str, str]]:
        return {
            target
            for event in (thinking_events or [])
            if event.get("type") == "tool_result"
            and event.get("deduplicated") is not True
            and str(event.get("tool_name") or "").lower() == "collect_aiops_case"
            if (target := cls._extract_tool_event_pod_target(event))
        }

    @classmethod
    def _successful_mandatory_case_targets(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> set[tuple[str, str]]:
        return {
            target
            for event in (thinking_events or [])
            if event.get("type") == "tool_result"
            and event.get("deduplicated") is not True
            and event.get("status") == "success"
            and str(event.get("tool_name") or "").lower() == "collect_aiops_case"
            and isinstance(event.get("structured"), dict)
            and event["structured"].get("status") == "case_collected"
            if (target := cls._extract_tool_event_pod_target(
                event,
                require_consistent=True,
            ))
        }

    @classmethod
    def _calculate_observability_target_coverage(
        cls,
        evidence_plan: List[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        has_first_round_gate = any(
            isinstance(item, dict)
            and item.get("source") == "observability_first_round_gate"
            for item in (evidence_plan or [])
        )
        if has_first_round_gate:
            planned_gate_items = set(
                cls._autonomous_observability_gate_items(evidence_plan)
            )
            present_gate_items = (
                cls._present_autonomous_observability_gate_items(
                    thinking_events
                )
            )
            collected_gate_items = (
                planned_gate_items & present_gate_items
            )
            total = len(planned_gate_items)
            collected = len(collected_gate_items)
            return {
                "observability_target_total": total,
                "observability_target_collected": collected,
                "observability_target_completeness": (
                    collected / total if total else 0.0
                ),
            }

        mandatory_targets = set(cls._mandatory_case_targets(evidence_plan))
        if mandatory_targets:
            successful_targets = cls._successful_mandatory_case_targets(thinking_events)
            collected_targets = mandatory_targets & successful_targets
            total = len(mandatory_targets)
            collected = len(collected_targets)
            return {
                "observability_target_total": total,
                "observability_target_collected": collected,
                "observability_target_completeness": collected / total if total else 0.0,
            }

        planned_targets = {
            target
            for item in (evidence_plan or [])
            if isinstance(item, dict)
            and str(item.get("tool") or "").strip().lower()
            in cls._OBSERVABILITY_QUERY_TOOLS
            if (target := cls._extract_plan_pod_target(item))
        }
        successful_targets = {
            target
            for event in (thinking_events or [])
            if str(
                (
                    event.get("structured")
                    if isinstance(event.get("structured"), dict)
                    else {}
                ).get("purpose")
                or (
                    event.get("tool_args")
                    if isinstance(event.get("tool_args"), dict)
                    else {}
                ).get("purpose")
                or ""
            ).strip()
            if is_observability_event_semantic_success(event)
            if (target := cls._extract_tool_event_pod_target(event))
        }
        collected_targets = planned_targets & successful_targets
        total = len(planned_targets)
        collected = len(collected_targets)
        return {
            "observability_target_total": total,
            "observability_target_collected": collected,
            "observability_target_completeness": collected / total if total else 0.0,
        }

    @classmethod
    def _calculate_source_coverage(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        cases: List[Dict[str, Any]] = []
        queries: List[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for event in cls._final_observability_query_events(thinking_events):
            tool_name = str(event.get("tool_name") or "").lower()
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            target = cls._extract_tool_event_pod_target(event)
            dimension = str(structured.get("dimension") or "").strip().lower()
            purpose = str(structured.get("purpose") or "").strip()
            queries.append({
                "target": (
                    f"{target[0]}/{target[1]}"
                    if target
                    else "unknown/unknown"
                ),
                "tool": tool_name,
                "source_system": str(structured.get("source_system") or ""),
                "dimension": dimension,
                "purpose": purpose,
                "coverage": str(structured.get("coverage") or ""),
                "directness": str(structured.get("directness") or ""),
                "evidence_refs": list(
                    structured.get("evidence_refs") or []
                )[:20],
            })

        for event in thinking_events or []:
            tool_name = str(event.get("tool_name") or "").lower()
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or event.get("status") != "success"
                or tool_name != "collect_aiops_case"
            ):
                continue
            if structured.get("status") != "case_collected":
                continue
            target = cls._extract_tool_event_pod_target(event)
            if not target or target in seen:
                continue
            seen.add(target)
            cases.append({
                "target": f"{target[0]}/{target[1]}",
                "case_id": str(structured.get("case_id") or ""),
                "dimensions": dict(
                    structured.get("coverage")
                    if isinstance(structured.get("coverage"), dict)
                    else {}
                ),
            })
        return {"cases": cases, "queries": queries}

    @classmethod
    def _calculate_detail_retrieval(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        requested = 0
        collected = 0
        refs: List[str] = []
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or str(event.get("tool_name") or "").lower()
                not in cls._AIOPS_DETAIL_TOOLS
            ):
                continue
            requested += 1
            if event.get("status") == "success":
                collected += 1
            args = (
                event.get("tool_args")
                if isinstance(event.get("tool_args"), dict)
                else {}
            )
            evidence_ref = str(args.get("evidence_ref") or "").strip()
            if evidence_ref and evidence_ref not in refs:
                refs.append(evidence_ref)
        return {
            "evaluated": requested > 0,
            "requested": requested,
            "collected": collected,
            "refs": refs,
        }

    @classmethod
    def _build_unresolved_questions(
        cls,
        thinking_events: List[Dict[str, Any]],
        diagnostic_stats: Dict[str, Any],
    ) -> List[str]:
        questions = list(
            diagnostic_stats.get("diagnostic_evidence_missing") or []
        )
        for case in cls._build_post_case_refinement_payload(
            thinking_events
        ).get("cases", []):
            questions.extend(case.get("unresolved_questions") or [])
        return list(dict.fromkeys(str(item) for item in questions if str(item).strip()))

    @classmethod
    def _calculate_diagnostic_evidence_coverage(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Separate dimension presence from evidence quality and sufficiency."""
        dimension_results: Dict[
            tuple[str, str],
            tuple[bool, float, str],
        ] = {}

        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or event.get("status") != "success"
                or str(event.get("tool_name") or "").lower() != "collect_aiops_case"
            ):
                continue
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            if structured.get("status") != "case_collected":
                continue

            primary = (
                structured.get("primary_entity")
                if isinstance(structured.get("primary_entity"), dict)
                else {}
            )
            target = (
                f"{primary.get('namespace') or 'unknown'}/"
                f"{primary.get('name') or 'unknown'}"
            )
            details = (
                structured.get("dimension_details")
                if isinstance(structured.get("dimension_details"), dict)
                else {}
            )
            signals = (
                structured.get("signals_summary")
                if isinstance(structured.get("signals_summary"), list)
                else []
            )
            metrics = details.get("metrics") if isinstance(details.get("metrics"), dict) else {}
            logs = details.get("logs") if isinstance(details.get("logs"), dict) else {}
            tracing = details.get("tracing") if isinstance(details.get("tracing"), dict) else {}
            topology = details.get("topology") if isinstance(details.get("topology"), dict) else {}

            checks = {
                "k8s": any(
                    isinstance(signal, dict)
                    and str(signal.get("dimension") or "").lower() == "k8s"
                    and bool(str(signal.get("observed") or "").strip())
                    for signal in signals
                ),
                "metrics": bool(metrics.get("highlights")),
                "logs": bool(logs.get("samples")),
                "tracing": bool(tracing.get("flows") or tracing.get("spans")),
                "topology": bool(topology.get("edges")),
            }
            k8s_score = 0.0
            k8s_candidates = [
                signal
                for signal in signals
                if isinstance(signal, dict)
                and str(signal.get("dimension") or "").lower() == "k8s"
                and bool(str(signal.get("observed") or "").strip())
            ]
            if k8s_candidates:
                k8s_score = (
                    1.0
                    if any(
                        str(signal.get("strength") or "").lower() == "strong"
                        for signal in k8s_candidates
                    )
                    else 0.5
                )

            metric_score = 0.0
            metric_highlights = [
                item
                for item in (metrics.get("highlights") or [])
                if isinstance(item, dict)
            ]
            if metric_highlights:
                metric_score = 0.5
                if any(
                    len(item.get("samples") or []) >= 2
                    or any(
                        item.get(key) is True
                        for key in (
                            "anomaly",
                            "is_anomalous",
                            "breached",
                            "threshold_breached",
                        )
                    )
                    or bool(re.search(
                        r"anomal|breach|critical|warning|exceed",
                        " ".join(
                            str(item.get(key) or "")
                            for key in ("status", "severity", "assessment")
                        ),
                        re.IGNORECASE,
                    ))
                    for item in metric_highlights
                ):
                    metric_score = 1.0

            log_score = 0.0
            log_samples = [
                item
                for item in (logs.get("samples") or [])
                if isinstance(item, dict)
            ]
            if log_samples:
                log_score = 0.5
                decisive_log_pattern = re.compile(
                    r"error|fatal|exception|oom|config_missing|required config|"
                    r"missing|failed|denied|timeout|exit[_ ]?code",
                    re.IGNORECASE,
                )
                if any(
                    decisive_log_pattern.search(
                        " ".join(
                            str(value)
                            for value in (
                                item.get("message"),
                                item.get("event"),
                                item.get("level"),
                                item.get("error_code"),
                            )
                            if value not in (None, "")
                        )
                    )
                    for item in log_samples
                ):
                    log_score = 1.0

            trace_score = 0.0
            flows = [
                item
                for item in (tracing.get("flows") or [])
                if isinstance(item, dict)
            ]
            spans = [
                item
                for item in (tracing.get("spans") or [])
                if isinstance(item, dict)
            ]
            if flows or spans:
                trace_score = 0.5
                flow_ids = {
                    str(item.get("trace_id"))
                    for item in flows
                    if item.get("trace_id")
                }
                span_ids = {
                    str(item.get("trace_id"))
                    for item in spans
                    if item.get("trace_id")
                }
                has_error_semantics = any(
                    str(item.get("response_code") or "").startswith(("4", "5"))
                    for item in flows
                ) or any(
                    any(
                        key in (item.get("attributes") or {})
                        for key in (
                            "error.type",
                            "http.response.status_code",
                            "aiops.allocated_mib.before",
                            "aiops.allocated_mib.after",
                        )
                    )
                    for item in spans
                    if isinstance(item.get("attributes"), dict)
                )
                if (
                    flows
                    and spans
                    and ((flow_ids and span_ids and flow_ids & span_ids) or has_error_semantics)
                ):
                    trace_score = 1.0

            topology_score = 0.0
            topology_edges = [
                item
                for item in (topology.get("edges") or [])
                if isinstance(item, dict)
            ]
            if topology_edges:
                topology_score = 0.5
                relationships = {
                    str(item.get("relationship") or "").lower()
                    for item in topology_edges
                }
                has_traffic = any(
                    "calls" in relationship or "selects" in relationship
                    for relationship in relationships
                )
                has_ownership = any(
                    "owned_by" in relationship for relationship in relationships
                )
                if has_traffic and has_ownership:
                    topology_score = 1.0

            scores = {
                "k8s": k8s_score,
                "metrics": metric_score,
                "logs": log_score,
                "tracing": trace_score,
                "topology": topology_score,
            }
            for dimension, present in checks.items():
                dimension_results[(target, dimension)] = (
                    present,
                    scores[dimension],
                    f"{target}:{dimension}",
                )

        for event in cls._final_observability_query_events(thinking_events):
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            dimension = str(
                structured.get("dimension") or ""
            ).strip().lower()
            if not dimension:
                continue
            target_tuple = cls._extract_tool_event_pod_target(event)
            target = (
                f"{target_tuple[0]}/{target_tuple[1]}"
                if target_tuple
                else "unknown/unknown"
            )
            key = (target, dimension)
            coverage = str(
                structured.get("coverage") or ""
            ).strip().lower()
            evidence_rows = [
                item
                for field in (
                    "facts",
                    "samples",
                    "flows",
                    "spans",
                    "edges",
                )
                for item in (
                    structured.get(field)
                    if isinstance(structured.get(field), list)
                    else []
                )
                if isinstance(item, dict)
            ]
            query_has_evidence = (
                is_observability_event_semantic_success(event)
                and coverage in {"present", "weak", "partial"}
                and bool(evidence_rows)
            )
            query_present = (
                query_has_evidence
                and structured.get("status") == "query_succeeded"
                and coverage == "present"
            )
            query_score = 0.0
            if query_has_evidence:
                directness_values = {
                    str(item.get("directness") or "").strip().lower()
                    for item in evidence_rows
                    if item.get("directness")
                }
                query_score = (
                    0.25
                    if (
                        directness_values
                        and directness_values <= {
                            "related_context",
                            "weak",
                        }
                    )
                    else 1.0
                )
                if coverage in {"weak", "partial"}:
                    query_score = min(query_score, 0.5)
                if dimension == "metrics" and not any(
                    item.get("trend_evaluable") is True
                    and int(item.get("sample_count") or 0) >= 2
                    for item in evidence_rows
                ):
                    query_score = min(query_score, 0.4)

            current = dimension_results.get(key)
            if query_has_evidence and (
                current is None
                or (query_present and not current[0])
                or (
                    query_present == current[0]
                    and query_score > current[1]
                )
            ):
                dimension_results[key] = (
                    query_present,
                    query_score,
                    f"{target}:{dimension}",
                )
            elif current is None:
                dimension_results[key] = (
                    False,
                    0.0,
                    f"{target}:{dimension}({coverage or 'unknown'})",
                )

        total = len(dimension_results)
        collected = sum(
            1 for present, _, _ in dimension_results.values() if present
        )
        sufficiency_points = sum(
            score for _, score, _ in dimension_results.values()
        )
        missing = [
            label
            for present, _, label in dimension_results.values()
            if not present
        ]

        coverage = collected / total if total else 0.0
        sufficiency = sufficiency_points / total if total else 0.0
        if sufficiency >= 0.85:
            sufficiency_label = "充分"
        elif sufficiency >= 0.5:
            sufficiency_label = "部分充分"
        else:
            sufficiency_label = "不足"
        return {
            "diagnostic_evidence_total": total,
            "diagnostic_evidence_collected": collected,
            "diagnostic_evidence_completeness": coverage,
            "diagnostic_evidence_missing": missing,
            "dimension_coverage_total": total,
            "dimension_coverage_collected": collected,
            "dimension_coverage": coverage,
            "diagnostic_sufficiency": sufficiency,
            "diagnostic_sufficiency_label": sufficiency_label,
        }

    @classmethod
    def _remaining_unattempted_mandatory_items(
        cls,
        evidence_plan: List[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        attempted = cls._attempted_mandatory_case_targets(thinking_events)
        return [
            dict(item)
            for item in (evidence_plan or [])
            if isinstance(item, dict)
            and item.get("source") == "mandatory_live_observability"
            and (target := cls._extract_plan_pod_target(item))
            and target not in attempted
        ]

    @classmethod
    def _remaining_unattempted_autonomous_items(
        cls,
        evidence_plan: List[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        attempted = cls._attempted_autonomous_observability_gate_items(
            thinking_events
        )
        remaining_gate_items = (
            set(cls._autonomous_observability_gate_items(evidence_plan))
            - attempted
        )
        selected: List[Dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for item in evidence_plan or []:
            if not isinstance(item, dict):
                continue
            tool_name = str(item.get("tool") or "").strip().lower()
            if tool_name not in cls._OBSERVABILITY_QUERY_TOOLS:
                continue
            target = cls._extract_plan_pod_target(item)
            gate_item = (
                (target[0], target[1], tool_name)
                if target
                else None
            )
            if (
                not gate_item
                or gate_item not in remaining_gate_items
                or gate_item in seen
            ):
                continue
            selected.append(dict(item))
            seen.add(gate_item)
        return selected

    @classmethod
    def _format_completed_autonomous_gate_summary(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        lines: List[str] = []
        for event in cls._final_observability_query_events(thinking_events):
            tool_name = str(event.get("tool_name") or "").strip().lower()
            target = cls._extract_tool_event_pod_target(event)
            if not target:
                continue
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            coverage = str(
                structured.get("coverage")
                or ("error" if event.get("status") != "success" else "unknown")
            ).strip()
            purpose = str(
                structured.get("purpose")
                or (
                    event.get("tool_args", {}).get("purpose")
                    if isinstance(event.get("tool_args"), dict)
                    else ""
                )
                or ""
            ).strip()
            result = str(
                event.get("agent_facts")
                or cls._build_aiops_agent_facts(
                    tool_name=tool_name,
                    structured=structured,
                )
                or event.get("result")
                or event.get("result_preview")
                or ""
            )
            compact_result = " ".join(result.split())[:800]
            lines.append(
                f"- {target[0]}/{target[1]}:{tool_name} "
                f"status={event.get('status') or 'unknown'} "
                f"coverage={coverage or 'unknown'} purpose={purpose or '-'}"
            )
            if compact_result:
                lines.append(f"  真实返回摘要: {compact_result}")
        return "\n".join(lines)

    @classmethod
    def _format_completed_mandatory_summary(
        cls,
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        lines: List[str] = []
        seen: set[tuple[str, str]] = set()
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("deduplicated") is True
                or str(event.get("tool_name") or "").lower() != "collect_aiops_case"
            ):
                continue
            target = cls._extract_tool_event_pod_target(event)
            if not target or target in seen:
                continue
            seen.add(target)
            structured = (
                event.get("structured")
                if isinstance(event.get("structured"), dict)
                else {}
            )
            status = str(structured.get("status") or event.get("status") or "unknown")
            result = str(event.get("result") or event.get("result_preview") or "")
            compact_result = " ".join(result.split())[:1000]
            lines.append(
                f"- {target[0]}/{target[1]}: status={status}; {compact_result}"
            )
        return "\n".join(lines)

    def _derive_early_stop_state(
        self,
        evidence_plan: List[Dict],
        evidence_items: List[EvidenceItem],
        thinking_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """根据计划和采集结果后验推导提前停止状态，保证输出字段稳定。"""
        if self._coarse_case_has_missing_dimensions(evidence_plan, thinking_events or []):
            return {
                "triggered": False,
                "reason": "collect_aiops_case 存在缺失维度，未触发提前停止",
                "required_levels": ["critical", "important"],
            }

        planned_items = [
            e for e in evidence_items
            if getattr(e, "source", "") in ("thinking_match", "thinking_negative_match", "planned")
        ]
        required_items = [
            e for e in planned_items
            if e.level in (EvidenceLevel.CRITICAL, EvidenceLevel.IMPORTANT)
        ]

        if required_items and all(e.collected for e in required_items):
            return {
                "triggered": True,
                "reason": "critical 和 important 级证据均已满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }

        if planned_items and all(e.collected for e in planned_items):
            return {
                "triggered": True,
                "reason": "计划中的证据已全部满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }

        return {
            "triggered": False,
            "reason": "",
            "required_levels": ["critical", "important"],
        }

    @classmethod
    def _coarse_case_has_missing_dimensions(
        cls,
        evidence_plan: List[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> bool:
        if not any(
            cls._normalize_plan_text(item.get("tool")) == "collect_aiops_case"
            for item in (evidence_plan or [])
            if isinstance(item, dict)
        ):
            return False

        coarse_results = [
            ev
            for ev in (thinking_events or [])
            if ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and str(ev.get("tool_name") or "").lower() == "collect_aiops_case"
            and isinstance(ev.get("structured"), dict)
            and ev["structured"].get("status") == "case_collected"
        ]
        if not coarse_results:
            return False
        return not cls._aiops_case_coverage_complete(
            coarse_results[-1]["structured"].get("coverage")
        )

    # 非证据类工具（LLM 自用的辅助工具），不计入证据统计
    _NON_EVIDENCE_TOOLS = {
        "todowrite",
        "todo_write",
        "todo",
        # Archive reads are auxiliary context lookups. They can point the model
        # to raw files, but they are not fresh cluster observations and must not
        # become positive evidence by themselves.
        "read_context_archive",
        "fetch_runbook",
    }

    def _build_evidence_items_from_thinking(
        self,
        evidence_plan: List[Dict],
        thinking_events: list,
    ) -> List[EvidenceItem]:
        """
        从 thinking_events（AICall agent loop 真实工具调用）构建证据项列表。

        匹配逻辑：
        1. 有 plan 时：plan item 与工具调用匹配，未匹配的工具作为额外采集
        2. 无 plan 但有工具调用时：从工具调用反向构建证据项（过滤非证据工具）
        3. 无 plan 且无工具调用时：返回空列表（completeness 由 _calculate_completeness 处理）
        """
        evidence_items = []

        # 从 thinking_events 提取可用于证据匹配的工具调用。部分只读探测
        # 命令的失败结果本身就是诊断证据，例如 curl registry 超时。
        successful_tools = []
        for ev in self._project_final_evidence_events(
            thinking_events
        ):
            if (
                ev.get("type") == "tool_result"
                and ev.get("status") == "success"
                and ev.get("deduplicated") is not True
            ):
                result = ev.get("result", ev.get("result_preview", ""))
                structured = ev.get("structured") or {}
                semantic_success = ev.get("semantic_success", True) is not False
                diagnostic_negative = (
                    not semantic_success
                    and self._is_diagnostic_negative_tool_result(
                        ev.get("tool_name", ""),
                        result,
                        structured,
                    )
                )
                if not semantic_success and not diagnostic_negative:
                    continue
                structured_for_matching = dict(structured)
                structured_for_matching["_diagnostic_negative"] = diagnostic_negative
                successful_tools.append({
                    "tool_name": ev.get("tool_name", ""),
                    "result": result,
                    "tool_args": ev.get("tool_args") or {},
                    "structured": structured_for_matching,
                    "raw_ref": ev.get("raw_ref"),
                    "summary_ref": ev.get("summary_ref"),
                    "diagnostic_negative": diagnostic_negative,
                })

        # ── 无 plan 时：从工具调用反向构建证据项 ──
        if not evidence_plan and successful_tools:
            real_tools = [
                t for t in successful_tools
                if t["tool_name"].lower() not in self._NON_EVIDENCE_TOOLS
            ]
            skipped = len(successful_tools) - len(real_tools)
            if skipped:
                logger.debug("📊 [evidence] 过滤 %d 个非证据工具 (TodoWrite 等)", skipped)

            for ti, tool in enumerate(real_tools):
                evidence_items.append(EvidenceItem(
                    id=f"auto_{ti}",
                    description=f"工具采集: {tool['tool_name']}",
                    level=EvidenceLevel.IMPORTANT,
                    weight=0.2,
                    collected=True,
                    value=tool["result"][:500] if tool["result"] else None,
                    source="thinking_auto",
                ))

            logger.info("📊 [evidence] 证据统计(无plan模式): "
                        "thinking_tools=%d 个成功调用, 有效证据=%d, 过滤=%d",
                        len(successful_tools), len(real_tools), skipped)
            return evidence_items

        # ── 有 plan 时：正常匹配流程 ──
        matched_tool_indices = set()

        for plan_item in evidence_plan:
            plan_tool = (plan_item.get("tool") or "").lower()
            plan_cmd = (plan_item.get("command") or "").lower()
            plan_desc = (plan_item.get("description") or "").lower()
            plan_intent = str(plan_item.get("evidence_type") or "").lower()
            plan_tool_args = (
                plan_item.get("tool_args")
                if isinstance(plan_item.get("tool_args"), dict)
                else {}
            )
            plan_target_scope = str(plan_item.get("target_scope") or "")
            acceptable_tools = [
                str(tool or "").lower()
                for tool in (plan_item.get("acceptable_tools") or [])
            ]
            item_id = plan_item.get("id", f"ev_{len(evidence_items)}")

            level_str = plan_item.get("level", "important")
            level = EvidenceLevel.IMPORTANT
            if level_str == "critical":
                level = EvidenceLevel.CRITICAL
            elif level_str in {"optional", "reference"}:
                level = EvidenceLevel.OPTIONAL

            matched = False
            matched_result = None
            matched_tool = None
            for ti, tool in enumerate(successful_tools):
                if ti in matched_tool_indices:
                    continue
                tn = tool["tool_name"].lower()
                if self._tool_result_matches_plan(
                    plan_tool=plan_tool,
                    plan_cmd=plan_cmd,
                    plan_desc=plan_desc,
                    tool_name=tn,
                    result=tool.get("result", ""),
                    structured=tool.get("structured") or {},
                    tool_args=tool.get("tool_args") or {},
                    plan_intent=plan_intent,
                    plan_tool_args=plan_tool_args,
                    plan_target_scope=plan_target_scope,
                    acceptable_tools=acceptable_tools,
                ):
                    matched = True
                    matched_tool = tool
                    matched_result = tool["result"]
                    matched_tool_indices.add(ti)
                    break

            outcome = "positive"
            source = "thinking_match" if matched else "planned"
            if matched_tool and matched_tool.get("diagnostic_negative"):
                outcome = "negative"
                source = "thinking_negative_match"
            elif not matched:
                outcome = "unknown"

            evidence_items.append(EvidenceItem(
                id=item_id,
                description=plan_item.get("description", "未知证据"),
                level=level,
                weight=0.2,
                collected=matched,
                value=matched_result,
                source=source,
                outcome=outcome,
            ))

        # 有 plan 时，最终 evidence_items 必须与 plan 对齐。
        # 未规划但实际执行的工具结果保留在 tool_data/thinking_events 中，不能混入
        # evidence_items，否则前端展示的 plan 与最终完整度口径会漂移。
        unplanned_tool_count = sum(
            1 for ti, tool in enumerate(successful_tools)
            if ti not in matched_tool_indices
            and tool["tool_name"].lower() not in self._NON_EVIDENCE_TOOLS
        )
        logger.info("📊 [evidence] 证据统计: plan=%d 项, "
                    "thinking_tools=%d 个成功调用, "
                    "matched=%d, unplanned=%d",
                    len(evidence_plan), len(successful_tools),
                    len(matched_tool_indices),
                    unplanned_tool_count)

        return evidence_items

    def _calculate_evidence_tool_stats(
        self,
        evidence_plan: List[Dict],
        thinking_events: list,
        evidence_items: List[EvidenceItem],
        upstream_evidence_items: List[EvidenceItem],
    ) -> Dict[str, int]:
        """Calculate transparent tool/evidence counts from structured objects.

        Completeness is plan-item based. Tool counts are diagnostic metadata:
        executed tools can be greater than matched plan items when the agent
        performs extra probes, and matched can be lower than planned when some
        Pydantic plan intents were not satisfied.
        """
        planned_ids = {
            str(item.get("id", ""))
            for item in evidence_plan or []
            if isinstance(item, dict) and item.get("id")
        }
        del upstream_evidence_items
        matched_ids = {
            str(item.id)
            for item in (evidence_items or [])
            if item.collected
            and str(item.id) in planned_ids
            and str(getattr(item, "source", "") or "") in {
                "thinking_match",
                "thinking_negative_match",
            }
        }

        evidence_tool_events = self._extract_evidence_tool_events(thinking_events)
        executed_tool_count = len(evidence_tool_events)
        matched_tool_count = len(matched_ids)
        unplanned_tool_count = max(0, executed_tool_count - matched_tool_count)
        case_tool_count = sum(
            1
            for event in evidence_tool_events
            if str(event.get("tool_name") or "").strip().lower()
            == "collect_aiops_case"
        )
        supplemental_tool_count = max(0, executed_tool_count - case_tool_count)

        return {
            "executed_tool_count": executed_tool_count,
            "matched_tool_count": matched_tool_count,
            "unplanned_tool_count": unplanned_tool_count,
            "case_tool_count": case_tool_count,
            "supplemental_tool_count": supplemental_tool_count,
        }

    def _extract_evidence_tool_events(self, thinking_events: list) -> List[Dict[str, Any]]:
        """Return successful/diagnostic tool observations that count as evidence attempts."""
        evidence_events: List[Dict[str, Any]] = []
        for ev in self._project_final_evidence_events(
            thinking_events
        ):
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            if ev.get("deduplicated") is True:
                continue
            tool_name = str(ev.get("tool_name", "") or "").lower()
            if tool_name in self._NON_EVIDENCE_TOOLS:
                continue

            result = ev.get("result", ev.get("result_preview", "")) or ""
            structured = ev.get("structured") or {}
            semantic_success = ev.get("semantic_success", True) is not False
            diagnostic_negative = self._is_diagnostic_negative_tool_result(tool_name, result, structured)
            if not semantic_success and not diagnostic_negative:
                continue
            evidence_events.append(ev)
        return evidence_events

    def _build_upstream_evidence_items(
        self,
        evidence_plan: List[Dict],
        thinking_events: list,
    ) -> List[EvidenceItem]:
        """Convert upstream layer tool results into collected evidence items.

        Layer observations are real environment evidence when they are scoped to
        current abnormal objects. They should be visible and countable, but kept
        separate from evidence-plan execution with source=layer_verified.
        """
        layer_events = [
            ev
            for ev in self._project_final_evidence_events(
                thinking_events
            )
            if ev.get("type") == "tool_result"
            and ev.get("node") == "layer"
            and ev.get("status") == "success"
            and ev.get("deduplicated") is not True
            and str(ev.get("tool_name", "")).lower() not in self._NON_EVIDENCE_TOOLS
            and str(ev.get("tool_name", "")).lower() not in {"fetch_runbook", "read_context_archive"}
        ]
        if not layer_events:
            return []

        items: List[EvidenceItem] = []
        matched_plan_items = self._build_evidence_items_from_thinking(evidence_plan, layer_events) if evidence_plan else []
        for item in matched_plan_items:
            if item.collected:
                item.source = "layer_verified"
                items.append(item)

        matched_count = len(items)
        for index, ev in enumerate(layer_events, start=1):
            result = ev.get("result", "") or ev.get("result_preview", "")
            if not result:
                continue
            items.append(EvidenceItem(
                id=f"layer_{index}",
                description=f"上游已验证工具结果: {ev.get('tool_name', '')}",
                level=EvidenceLevel.IMPORTANT,
                weight=0.2,
                collected=True,
                value=result[:500],
                source="layer_verified",
                outcome="negative" if self._is_diagnostic_negative_tool_result(
                    ev.get("tool_name", ""),
                    result,
                    ev.get("structured") or {},
                ) else "positive",
            ))

        logger.info(
            "📊 [evidence] 纳入上游 layer 证据: layer_tools=%d plan_matched=%d total_added=%d",
            len(layer_events),
            matched_count,
            len(items),
        )
        return items

    @staticmethod
    def _merge_evidence_items(
        evidence_items: List[EvidenceItem],
        upstream_items: List[EvidenceItem],
    ) -> List[EvidenceItem]:
        if not upstream_items:
            return evidence_items

        merged: List[EvidenceItem] = [replace(item) for item in (evidence_items or [])]
        by_id = {str(item.id): idx for idx, item in enumerate(merged)}
        for item in upstream_items:
            item_id = str(item.id)
            if item_id in by_id:
                existing = merged[by_id[item_id]]
                if not existing.collected and item.collected:
                    existing.collected = True
                    existing.value = item.value
                    existing.source = item.source
                    existing.outcome = getattr(item, "outcome", getattr(existing, "outcome", "positive"))
                continue
            merged.append(replace(item))
            by_id[item_id] = len(merged) - 1
        return merged

    def _calculate_plan_completeness(
        self,
        evidence_items: List[EvidenceItem],
        upstream_items: List[EvidenceItem],
    ) -> Dict[str, Any]:
        """Calculate completeness from countable planned items only.

        Extra layer_verified observations remain visible in inventory, but they
        must not inflate plan completeness unless they satisfy a planned item by
        id.
        """
        planned_items = self._measurable_evidence_items([
            item for item in evidence_items or []
            if str(getattr(item, "source", "") or "") in {
                "thinking_match",
                "thinking_negative_match",
                "planned",
                "layer_verified",
            }
            and not str(item.id).startswith("layer_")
        ])
        if not planned_items:
            return {"plan_total": 0, "plan_collected": 0, "plan_completeness": 0.0}

        del upstream_items

        total = len(planned_items)
        collected = sum(1 for item in planned_items if item.collected)
        return {
            "plan_total": total,
            "plan_collected": collected,
            "plan_completeness": collected / total if total else 0.0,
        }

    @classmethod
    def _classify_sufficient_evidence_skips(
        cls,
        *,
        evidence_plan: List[Dict[str, Any]],
        evidence_items: List[EvidenceItem],
        early_stop: Dict[str, Any],
    ) -> List[str]:
        """Classify optional follow-ups skipped after mandatory cases are complete."""
        if (
            not early_stop.get("triggered")
            or early_stop.get("reason") not in {
                "mandatory_live_observability_complete",
                "post_case_reconciliation_complete",
            }
        ):
            return []

        plan_by_id = cls._index_evidence_plan_by_id(evidence_plan)
        skipped: List[str] = []
        for item in evidence_items or []:
            if item.collected or str(getattr(item, "source", "") or "") != "planned":
                continue
            plan_item = plan_by_id.get(str(item.id), {})
            item_level = item.level.value if hasattr(item.level, "value") else item.level
            if plan_item.get("source") == "mandatory_live_observability":
                continue
            is_critical = (
                cls._normalize_plan_text(item_level) == "critical"
                or cls._normalize_plan_text(plan_item.get("level")) == "critical"
            )
            if is_critical:
                continue
            item.source = "skipped_sufficient_evidence"
            item.outcome = "skipped"
            skipped.append(str(item.id))
        return skipped

    @classmethod
    def _index_evidence_plan_by_id(
        cls,
        evidence_plan: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Index plan items without letting lower-priority duplicates win."""
        level_rank = {
            "critical": 3,
            "important": 2,
            "optional": 1,
            "reference": 0,
        }
        indexed: Dict[str, Dict[str, Any]] = {}
        for item in evidence_plan or []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id", ""))
            if not item_id:
                continue
            current = indexed.get(item_id)
            if current is None:
                indexed[item_id] = item
                continue
            current_rank = level_rank.get(
                cls._normalize_plan_text(current.get("level")),
                -1,
            )
            candidate_rank = level_rank.get(
                cls._normalize_plan_text(item.get("level")),
                -1,
            )
            if candidate_rank > current_rank:
                indexed[item_id] = item
        return indexed

    @staticmethod
    def _tool_result_matches_plan(
        plan_tool: str,
        plan_cmd: str,
        plan_desc: str,
        tool_name: str,
        result: str,
        structured: Dict[str, Any],
        tool_args: Optional[Dict[str, Any]] = None,
        plan_intent: str = "",
        plan_tool_args: Optional[Dict[str, Any]] = None,
        plan_target_scope: str = "",
        acceptable_tools: Optional[List[str]] = None,
    ) -> bool:
        if not result or not result.strip():
            return False
        if "_diagnostic_negative" in (structured or {}):
            diagnostic_negative = bool((structured or {}).get("_diagnostic_negative"))
        else:
            diagnostic_negative = EvidenceCollectorNode._is_diagnostic_negative_tool_result(tool_name, result, structured or {})
        if (structured or {}).get("status") in {"invalid_tool", "command_failed", "extract_failed"} and not diagnostic_negative:
            return False
        if not plan_intent and not EvidenceCollectorNode._namespace_scope_matches(plan_cmd, result):
            return False

        combined = f"{plan_cmd}\n{plan_desc}"
        has_structured_intent = bool(plan_intent)
        intent = plan_intent or EvidenceCollectorNode._classify_plan_intent(plan_cmd, plan_desc)
        requires_yaml = EvidenceCollectorNode._plan_requires_yaml({
            "command": plan_cmd,
            "evidence_type": plan_intent,
            "description": plan_desc,
        })
        tool_match = EvidenceCollectorNode._tool_is_compatible_with_plan(
            plan_tool=plan_tool,
            plan_cmd=plan_cmd,
            intent=intent,
            tool_name=tool_name,
            acceptable_tools=acceptable_tools,
        )
        if not tool_match:
            return False

        expected_pod_target = EvidenceCollectorNode._extract_plan_pod_target({
            "tool": plan_tool,
            "command": plan_cmd,
            "target_scope": plan_target_scope,
            "tool_args": plan_tool_args or {},
        })
        observed_pod_target = EvidenceCollectorNode._extract_result_pod_target(
            result=result,
            structured=structured or {},
            tool_args=tool_args or {},
        )
        if (
            expected_pod_target
            and observed_pod_target
            and expected_pod_target != observed_pod_target
        ):
            return False

        if plan_tool in {"collect_aiops_case", "get_aiops_case"}:
            expected_status = "case_collected" if plan_tool == "collect_aiops_case" else "case_loaded"
            if tool_name != plan_tool or structured.get("status") != expected_status:
                return False
            target = EvidenceCollectorNode._extract_plan_pod_target({
                "tool": plan_tool,
                "command": plan_cmd,
                "target_scope": plan_target_scope,
                "tool_args": plan_tool_args or {},
            })
            primary = structured.get("primary_entity") if isinstance(structured.get("primary_entity"), dict) else {}
            if target and primary:
                return target == (
                    str(primary.get("namespace") or "").lower(),
                    str(primary.get("name") or "").lower(),
                )
            return True

        if requires_yaml and not EvidenceCollectorNode._result_is_yaml_evidence(tool_name, result, structured or {}):
            return False
        if requires_yaml:
            diagnostic_negative = False

        lower_result = result.lower()
        if plan_tool == "kubectl_events" and tool_name == "kubectl_events":
            expected_args = EvidenceCollectorNode._derive_kubectl_events_tool_args(plan_cmd)
            result_target = EvidenceCollectorNode._extract_result_resource_target(
                result=result,
                structured=structured or {},
                tool_args=tool_args or {},
            )
            expected_namespace = str(expected_args.get("namespace") or "").lower()
            expected_name = str(expected_args.get("resource_name") or "").lower()
            if expected_namespace and result_target.get("namespace") and expected_namespace != result_target["namespace"]:
                return False
            if expected_name and result_target.get("name") and expected_name != result_target["name"]:
                return False
            return structured.get("status") == "events_found" or bool(result.strip())

        plan_target = EvidenceCollectorNode._extract_plan_resource_target(plan_cmd)
        if plan_target and not plan_intent and intent not in {"registry_connectivity", "dns_connectivity"}:
            result_target = EvidenceCollectorNode._extract_result_resource_target(
                result=result,
                structured=structured or {},
                tool_args=tool_args or {},
            )
            if not EvidenceCollectorNode._resource_target_matches(plan_target, result_target):
                return False

        if (structured or {}).get("diagnostic_negative") or diagnostic_negative:
            return (
                intent in {"registry_connectivity", "dns_connectivity"}
                or EvidenceCollectorNode._negative_result_answers_plan(combined, lower_result)
            )

        if has_structured_intent:
            if intent in {"pod_status", "pod_events"}:
                return EvidenceCollectorNode._result_answers_pod_status(result, structured or {})
            if intent in {"pod_spec", "pod_config", "pod_lifecycle"}:
                return EvidenceCollectorNode._result_answers_pod_spec_or_lifecycle(result, structured or {}, intent)
            if intent in {"secret_config"}:
                return structured.get("resource_kind") == "Secret" or structured.get("kind") == "Secret" or "secret" in lower_result
        if "run_bash_command" in tool_name and intent in {"registry_connectivity", "dns_connectivity"}:
            probe_markers = (
                "curl",
                "wget",
                "telnet",
                "nc ",
                "ping",
                "registry",
                "docker.io",
                "resolve",
                "nslookup",
                "dig ",
                "connected",
                "connection",
                "timeout",
                "timed out",
            )
            return any(marker in lower_result for marker in probe_markers)
        if "run_bash_command" in tool_name and intent == "node_state":
            node_name = plan_target.get("name", "") if plan_target.get("kind") == "node" else ""
            return bool(node_name and node_name in lower_result and re.search(r"\bready\b|kubelet|containerd|runtime", lower_result))

        if "events" in combined or "事件" in combined:
            return (
                "kubectl_events" in tool_name
                or ("kubectl_describe" in tool_name and re.search(r"\b(status|reason|events?)\b|状态|事件", lower_result))
                or structured.get("status") == "events_found"
                or "last seen" in lower_result
                or "reason" in lower_result and "object" in lower_result
                or "failed to pull image" in lower_result
                or "back-off pulling image" in lower_result
            )

        if "logs" in combined or "日志" in combined:
            return (
                EvidenceCollectorNode._is_kubectl_log_tool(tool_name)
                or "run_bash_command" in tool_name
                or not (structured.get("kind") == "Pod" and "kubectl_get_yaml" in tool_name)
            )

        if "configmap" in combined:
            return structured.get("kind") == "ConfigMap" or "configmap" in lower_result

        if "secret" in combined or "imagepullsecret" in combined:
            return (
                structured.get("resource_kind") == "Secret"
                or structured.get("kind") == "Secret"
                or "secret" in lower_result
                or "dockerconfigjson" in lower_result
            )

        if "describe" in combined:
            return "kubectl_describe" in tool_name

        if "get pod" in plan_cmd or "describe pod" in plan_cmd:
            return structured.get("kind") == "Pod" or "pod" in lower_result

        return True

    @staticmethod
    def _tool_is_compatible_with_plan(
        plan_tool: str,
        plan_cmd: str,
        intent: str,
        tool_name: str,
        acceptable_tools: Optional[List[str]] = None,
    ) -> bool:
        """Treat LLM generated `tool` as a weak hint and command intent as truth.

        Smaller models often put a broad kubectl wrapper in the plan while the
        agent executes a more specific helper, e.g. plan says
        kubectl_get_by_kind_in_cluster but command is `kubectl describe pod`
        and the real tool is kubectl_describe. Hard-failing that case makes
        real evidence show as 0/N.
        """
        plan_tool = (plan_tool or "").lower()
        tool_name = (tool_name or "").lower()
        plan_cmd = (plan_cmd or "").lower()
        acceptable = {
            str(tool or "").lower()
            for tool in (acceptable_tools or [])
            if str(tool or "").strip()
        }

        if plan_tool in {"collect_aiops_case", "get_aiops_case", "get_aiops_case_evidence"}:
            return tool_name == plan_tool

        if acceptable:
            return any(
                tool_name == tool
                or tool_name in tool
                or tool in tool_name
                or tool_name.replace("_", "") == tool.replace("_", "")
                for tool in acceptable
            )

        if (
            (plan_tool and plan_tool == tool_name)
            or (plan_tool and plan_tool in tool_name)
            or (plan_tool and tool_name in plan_tool)
            or (plan_tool and plan_tool.replace("_", "") == tool_name.replace("_", ""))
        ):
            return True

        if (
            EvidenceCollectorNode._is_kubectl_log_tool(plan_tool)
            and EvidenceCollectorNode._is_kubectl_log_tool(tool_name)
        ):
            return True

        if "kubectl" in plan_cmd:
            if re.search(r"\bdescribe\s+", plan_cmd):
                return "kubectl_describe" in tool_name or "run_bash_command" in tool_name
            if re.search(r"\bget\s+", plan_cmd):
                return (
                    "kubectl_get" in tool_name
                    or "kubectl_describe" in tool_name
                    or "run_bash_command" in tool_name
                )
            if re.search(r"\blogs\s+", plan_cmd):
                return "run_bash_command" in tool_name or "kubectl_logs" in tool_name
            if re.search(r"\b(exec|curl|wget|nc|telnet|ping)\b", plan_cmd):
                return "run_bash_command" in tool_name

        if intent in {"registry_connectivity", "dns_connectivity", "pod_logs", "runtime_info"}:
            return "run_bash_command" in tool_name or "kubectl_run_image" in tool_name
        if intent in {"pod_status", "pod_events", "pod_config", "pod_spec", "pod_lifecycle", "secret_config", "node_state"}:
            return (
                tool_name.startswith("kubectl_")
                or "run_bash_command" in tool_name
            )

        return False

    def _should_stop_autonomous_collection(self, thinking_events: list) -> bool:
        """Let Qwen stop naturally, but enforce the hard 80% context boundary."""
        context_ratio = self._max_context_usage_ratio(thinking_events)
        if context_ratio < 0.8:
            return False

        active_plan = getattr(self, "_active_evidence_plan", None) or []
        planned_targets = {
            target
            for item in active_plan
            if isinstance(item, dict)
            if (target := self._extract_plan_pod_target(item))
        }
        planned_gate_items = {
            (namespace, pod, tool_name)
            for namespace, pod in planned_targets
            for tool_name in self._OBSERVABILITY_QUERY_ORDER
        }
        attempted_gate_items = (
            self._attempted_autonomous_observability_gate_items(
                thinking_events
            )
        )

        self._early_stop_state = {
            "triggered": True,
            "reason": "context_budget_stop",
            "required_levels": ["critical", "important"],
            "context_usage_ratio": context_ratio,
            "uncollected_targets": [
                f"{namespace}/{pod}:{tool_name}"
                for namespace, pod, tool_name in sorted(
                    planned_gate_items - attempted_gate_items
                )
            ],
        }
        return True

    @staticmethod
    def _is_kubectl_log_tool(tool_name: str) -> bool:
        return (tool_name or "").lower() in {
            "kubectl_logs",
            "kubectl_previous_logs",
            "kubectl_logs_all_containers",
            "kubectl_previous_logs_all_containers",
            "kubectl_container_logs",
            "kubectl_container_previous_logs",
            "kubectl_logs_grep",
            "kubectl_logs_all_containers_grep",
        }

    @staticmethod
    def _result_answers_pod_status(result: str, structured: Dict[str, Any]) -> bool:
        text = (result or "").lower()
        if structured.get("kind") == "Pod" or structured.get("resource_kind") == "Pod":
            return True
        if structured.get("status") in {"describe_summarized", "events_found", "kept_small_output"}:
            return True
        return any(
            marker in text
            for marker in (
                "imagepullbackoff",
                "errimagepull",
                "crashloopbackoff",
                "terminating",
                "oomkilled",
                "failed",
                "reason:",
                "status",
                "ready",
            )
        )

    @staticmethod
    def _result_answers_pod_spec_or_lifecycle(
        result: str,
        structured: Dict[str, Any],
        intent: str,
    ) -> bool:
        text = (result or "").lower()
        if structured.get("kind") == "Pod" or structured.get("resource_kind") == "Pod":
            return True
        if intent == "pod_lifecycle":
            return any(marker in text for marker in ("deletiontimestamp", "finalizers", "terminating"))
        return any(marker in text for marker in ("kind: pod", "image:", "imagepullsecrets", "containers:"))

    @staticmethod
    def _result_is_yaml_evidence(
        tool_name: str,
        result: str,
        structured: Dict[str, Any],
    ) -> bool:
        tool = (tool_name or "").lower()
        text = (result or "").lower()
        if structured.get("kind") or structured.get("resource_kind"):
            return True
        if "kubectl_get_yaml" in tool:
            return True
        if "run_bash_command" in tool and re.search(r"(?im)^\s*kind:\s+\w+", result or ""):
            return True
        return bool(
            "kubectl_get_yaml 关键字段摘要" in result
            or re.search(r"(?im)^\s*apiVersion:\s+", result or "")
            or re.search(r"(?im)^\s*kind:\s+pod\s*$", result or "")
            or ("deletiontimestamp:" in text and "finalizers:" in text)
        )

    @staticmethod
    def _extract_result_resource_target(
        result: str,
        structured: Dict[str, Any],
        tool_args: Dict[str, Any],
    ) -> Dict[str, str]:
        kind = EvidenceCollectorNode._normalize_resource_kind(
            structured.get("kind")
            or structured.get("resource_kind")
            or structured.get("resource_type")
            or tool_args.get("kind")
            or tool_args.get("resource_kind")
            or tool_args.get("resource_type")
        )
        name = str(
            structured.get("name")
            or structured.get("resource_name")
            or tool_args.get("name")
            or tool_args.get("resource_name")
            or ""
        ).strip("'\"").lower()
        namespace = str(
            structured.get("namespace")
            or tool_args.get("namespace")
            or ""
        ).strip("'\"").lower()

        text = result or ""
        if not name:
            match = re.search(r"(?im)^\s*name:\s*([^\s]+)\s*$", text)
            if match:
                name = match.group(1).strip("'\"").lower()
        if not namespace:
            match = re.search(r"(?im)^\s*namespace:\s*([^\s]+)\s*$", text)
            if match:
                namespace = match.group(1).strip("'\"").lower()
        if not kind:
            match = re.search(r"(?im)^\s*kind:\s*([^\s]+)\s*$", text)
            if match:
                kind = EvidenceCollectorNode._normalize_resource_kind(match.group(1))
        if not kind and re.search(r"\bpod/", text, re.IGNORECASE):
            kind = "pod"

        return {"kind": kind, "namespace": namespace, "name": name}

    @staticmethod
    def _extract_result_pod_target(
        result: str,
        structured: Dict[str, Any],
        tool_args: Dict[str, Any],
    ) -> Optional[tuple[str, str]]:
        for candidate in (
            structured.get("entity"),
            structured.get("primary_entity"),
        ):
            if not isinstance(candidate, dict):
                continue
            kind = EvidenceCollectorNode._normalize_resource_kind(
                candidate.get("kind") or candidate.get("type") or "pod"
            )
            namespace = str(candidate.get("namespace") or "").strip().lower()
            pod = str(
                candidate.get("pod")
                or candidate.get("name")
                or ""
            ).strip().lower()
            if kind in {"", "pod"} and namespace and pod:
                return namespace, pod

        resource_target = EvidenceCollectorNode._extract_result_resource_target(
            result=result,
            structured=structured,
            tool_args=tool_args,
        )
        if (
            resource_target.get("kind") in {"", "pod"}
            and resource_target.get("namespace")
            and resource_target.get("name")
        ):
            return (
                resource_target["namespace"],
                resource_target["name"],
            )

        namespace = str(tool_args.get("namespace") or "").strip().lower()
        pod = str(
            tool_args.get("pod")
            or tool_args.get("pod_name")
            or ""
        ).strip().lower()
        if namespace and pod:
            return namespace, pod
        return None

    @staticmethod
    def _normalize_resource_kind(value: Any) -> str:
        text = str(value or "").strip().lower()
        aliases = {
            "pods": "pod",
            "po": "pod",
            "nodes": "node",
            "no": "node",
            "secrets": "secret",
            "configmaps": "configmap",
            "cm": "configmap",
            "persistentvolumeclaim": "pvc",
            "persistentvolumeclaims": "pvc",
            "pvcs": "pvc",
            "services": "service",
            "svc": "service",
            "deployments": "deployment",
            "replicasets": "replicaset",
            "rs": "replicaset",
            "daemonsets": "daemonset",
            "ds": "daemonset",
            "statefulsets": "statefulset",
            "sts": "statefulset",
            "events": "event",
            "networkpolicies": "networkpolicy",
        }
        return aliases.get(text, text)

    @staticmethod
    def _resource_target_matches(plan_target: Dict[str, str], result_target: Dict[str, str]) -> bool:
        plan_kind = (plan_target or {}).get("kind", "")
        plan_name = (plan_target or {}).get("name", "")
        plan_namespace = (plan_target or {}).get("namespace", "")
        result_kind = (result_target or {}).get("kind", "")
        result_name = (result_target or {}).get("name", "")
        result_namespace = (result_target or {}).get("namespace", "")

        if not result_kind and not result_name and not result_namespace:
            return True

        if plan_kind and result_kind and plan_kind != result_kind:
            return False
        if plan_name:
            if result_name and plan_name != result_name:
                return False
        if plan_namespace:
            if result_namespace and plan_namespace != result_namespace:
                return False
        return True

    @staticmethod
    def _is_diagnostic_negative_tool_result(
        tool_name: str,
        result: str,
        structured: Dict[str, Any],
    ) -> bool:
        """Return True when a failed probe is itself useful diagnostic evidence."""
        tool = (tool_name or "").lower()
        text = " ".join([
            str(result or ""),
            str((structured or {}).get("stderr_preview") or ""),
            str((structured or {}).get("stdout_preview") or ""),
            str((structured or {}).get("stderr") or ""),
            str((structured or {}).get("stdout") or ""),
            " ".join(str(signal) for signal in ((structured or {}).get("signals") or [])),
        ]).lower()

        if any(name in tool for name in ("kubectl_", "kubernetes_")) and "kubectl_run_image" not in tool:
            k8s_negative_markers = (
                "error from server (notfound)",
                " not found",
                "failedmount",
                "failedattachvolume",
                "mountvolume.setup failed",
                "unable to attach or mount volumes",
                "failedscheduling",
                "0/ nodes are available",
                "0 nodes are available",
                "imagepullbackoff",
                "errimagepull",
                "failed to pull image",
                "back-off pulling image",
                "failedcreatepodsandbox",
                "readiness probe failed",
                "liveness probe failed",
                "oomkilled",
                "evicted",
                "deletiontimestamp",
                "finalizers:",
            )
            return any(marker in text for marker in k8s_negative_markers)

        if not any(name in tool for name in ("run_bash_command", "kubectl_run_image")):
            return False

        negative_markers = (
            "connection reset",
            "connection refused",
            "i/o timeout",
            "timed out",
            "timeout",
            "命令执行超时",
            "执行超时",
            "could not resolve host",
            "no route to host",
            "network is unreachable",
            "recv failure",
            "curl:",
            "wget:",
            "tls handshake timeout",
        )
        return any(marker in text for marker in negative_markers)

    @staticmethod
    def _negative_result_answers_plan(combined_plan_text: str, lower_result: str) -> bool:
        plan = (combined_plan_text or "").lower()
        intent_markers = (
            "连通",
            "网络",
            "访问",
            "可达",
            "docker.io",
            "registry",
            "镜像仓库",
            "仓库",
            "curl",
            "wget",
            "dns",
            "tls",
            "timeout",
            "event",
            "events",
            "事件",
            "describe",
            "状态",
            "reason",
            "原因",
            "mount",
            "volume",
            "卷",
            "挂载",
            "configmap",
            "secret",
            "pvc",
            "persistentvolumeclaim",
            "storageclass",
            "scheduling",
            "调度",
            "image",
            "镜像",
            "probe",
            "探针",
            "oom",
            "evicted",
            "驱逐",
        )
        result_markers = (
            "connection reset",
            "connection refused",
            "i/o timeout",
            "timed out",
            "timeout",
            "命令执行超时",
            "执行超时",
            "could not resolve host",
            "no route to host",
            "network is unreachable",
            "recv failure",
            "curl:",
            "wget:",
            "tls handshake timeout",
            "error from server (notfound)",
            " not found",
            "failedmount",
            "failedattachvolume",
            "mountvolume.setup failed",
            "unable to attach or mount volumes",
            "failedscheduling",
            "0 nodes are available",
            "imagepullbackoff",
            "errimagepull",
            "failed to pull image",
            "back-off pulling image",
            "failedcreatepodsandbox",
            "readiness probe failed",
            "liveness probe failed",
            "oomkilled",
            "evicted",
            "deletiontimestamp",
            "finalizers:",
        )
        return (
            any(marker in plan for marker in intent_markers)
            and any(marker in lower_result for marker in result_markers)
        )

    @staticmethod
    def _namespace_scope_matches(plan_cmd: str, result: str) -> bool:
        """Reject obvious namespace drift for tabular outputs."""
        match = re.search(r"(?:^|\s)(?:-n|--namespace(?:=|\s+))\s*([^\s]+)", plan_cmd or "")
        if not match:
            return True

        expected_namespace = match.group(1).strip("'\"").lower()
        if not expected_namespace:
            return True

        lower_result = (result or "").lower()
        if f"namespace: {expected_namespace}" in lower_result or f"namespace={expected_namespace}" in lower_result:
            return True

        lines = [line.strip() for line in (result or "").splitlines() if line.strip()]
        header_index = next(
            (
                idx for idx, line in enumerate(lines[:5])
                if "namespace" in line.lower().split()
            ),
            None,
        )
        if header_index is None:
            return True

        columns = lines[header_index].lower().split()
        try:
            namespace_index = columns.index("namespace")
        except ValueError:
            return True

        rows = lines[header_index + 1:]
        if not rows:
            return True

        namespaces = {
            parts[namespace_index].strip("'\"").lower()
            for row in rows
            if (parts := row.split()) and len(parts) > namespace_index
        }
        return not namespaces or expected_namespace in namespaces

    def _calculate_completeness(self, evidence_items: List[EvidenceItem]) -> float:
        """计算真实环境证据采集率，reference/runbook 不计入分母。"""
        measurable_items = self._measurable_evidence_items(evidence_items)
        if not measurable_items:
            return 0.0

        total = len(measurable_items)
        collected = sum(1 for e in measurable_items if e.collected)

        return collected / total

    def _measurable_evidence_items(self, evidence_items: List[EvidenceItem]) -> List[EvidenceItem]:
        """Return evidence items that should count toward collection completeness."""
        measurable: List[EvidenceItem] = []
        for item in evidence_items or []:
            level_value = item.level.value if hasattr(item.level, "value") else str(item.level)
            if str(level_value).lower() in {"optional", "reference"}:
                continue
            desc = (item.description or "").lower()
            source = str(getattr(item, "source", "") or "").lower()
            if source in {"reference", "archive", "skipped_sufficient_evidence"}:
                continue
            if "fetch_runbook" in desc or "read_context_archive" in desc:
                continue
            measurable.append(item)
        return measurable

    def _update_metrics(
        self,
        evidence_plan: List[Dict],
        tool_results: List[Dict]
    ):
        """更新 metrics 统计"""
        if not self.metrics:
            return

        # LLM 调用已经在 _plan_evidence_with_llm 中记录了
        # 这里只补充统计（如果有额外调用）

        # 记录工具调用统计
        for tool_result in tool_results:
            duration_ms = tool_result.get("duration_ms", 0)
            success = tool_result.get("success", True)
            self.metrics.record_tool_call(
                tool_name=tool_result.get("tool", "kubectl"),
                duration_ms=duration_ms,
                success=success
            )

    def _extract_tool_data_from_thinking(self, thinking_events: list) -> List[Dict]:
        """
        从 thinking_events 中提取 MCP 工具的真实输出数据

        这些数据来自 LLM agentic loop 中的工具调用（kubectl, prometheus 等），
        是下游节点（rca, conclusion）生成准确报告的关键数据源。
        """
        case_tool_data = []
        supplementary_tool_data = []
        trusted_uid_index = self._trusted_pod_uid_index(thinking_events)
        final_query_event_ids = {
            id(event)
            for event in self._final_observability_query_events(
                thinking_events
            )
        }
        for ev in thinking_events:
            if ev.get("type") == "tool_result" and ev.get("deduplicated") is not True:
                tool_name = ev.get("tool_name", "")
                normalized_tool = str(tool_name or "").strip().lower()
                if (
                    normalized_tool in self._OBSERVABILITY_QUERY_TOOLS
                    and id(ev) not in final_query_event_ids
                ):
                    continue
                result_text = ev.get("result", "") or ev.get("result_preview", "")
                status = ev.get("status", "")
                raw_structured = (
                    ev.get("structured")
                    if isinstance(ev.get("structured"), dict)
                    else {}
                )
                event_scope = self._extract_tool_event_pod_target(
                    ev,
                    require_consistent=True,
                )
                trusted_pod_uid = (
                    trusted_uid_index.get(event_scope)
                    if event_scope
                    else None
                )
                structured = self._with_trusted_pod_uid(
                    ev,
                    raw_structured,
                    trusted_uid_index,
                )
                is_observability_query = (
                    normalized_tool
                    in self._OBSERVABILITY_QUERY_TOOLS
                )
                is_kubernetes_lifecycle = (
                    normalized_tool
                    in self._KUBERNETES_LIFECYCLE_AUTHORITY_TOOLS
                )
                query_semantic_success = (
                    is_observability_event_semantic_success(ev)
                    if is_observability_query
                    else None
                )
                native_ledger_input = (
                    deepcopy(raw_structured.get("fact_ledger"))
                    if (
                        is_observability_query
                        and query_semantic_success
                        and isinstance(
                            raw_structured.get("fact_ledger"),
                            dict,
                        )
                    )
                    else None
                )
                fact_ledger = None
                if not is_observability_query:
                    fact_ledger = normalize_case_fact_ledger(
                        structured
                    )
                if (
                    native_ledger_input is None
                    and fact_ledger is None
                    and is_observability_query
                    and query_semantic_success
                ):
                    fact_ledger = build_observability_query_fact_ledger(
                        structured
                    )
                if (
                    fact_ledger is None
                    and not is_observability_query
                    and isinstance(structured, dict)
                ):
                    lifecycle_structured = dict(structured)
                    lifecycle_structured["evidence_refs"] = list(
                        dict.fromkeys([
                            *(
                                structured.get("evidence_refs")
                                if isinstance(
                                    structured.get("evidence_refs"),
                                    list,
                                )
                                else []
                            ),
                            *[
                                str(ref)
                                for ref in (
                                    ev.get("raw_ref"),
                                    ev.get("structured_ref"),
                                    ev.get("summary_ref"),
                                )
                                if str(ref or "").strip()
                            ],
                        ])
                    )
                    fact_ledger = build_kubernetes_lifecycle_fact_ledger(
                        lifecycle_structured
                    )
                ledger_input = (
                    native_ledger_input
                    if native_ledger_input is not None
                    else fact_ledger
                )
                if (result_text or ledger_input is not None) and status == "success":
                    item = {
                        "tool": tool_name,
                        "data": result_text,
                        "duration_s": ev.get("duration_seconds", 0),
                        "semantic_success": (
                            query_semantic_success
                            if is_observability_query
                            else ev.get("semantic_success", True)
                            is not False
                        ),
                        "raw_ref": ev.get("raw_ref"),
                        "structured_ref": ev.get("structured_ref"),
                        "summary_ref": ev.get("summary_ref"),
                    }
                    provider_is_canonical = False
                    if ledger_input is not None:
                        provider_ledger = normalize_fact_ledger(ledger_input)
                        if (
                            provider_ledger is not None
                            and provider_ledger.source == "mcp_canonical"
                        ):
                            compacted_payload = json.loads(
                                compact_fact_ledgers_json(
                                    [provider_ledger],
                                    max_chars=10000,
                                )
                            )
                            compacted_ledgers = compacted_payload.get(
                                "fact_ledgers"
                            )
                            if (
                                isinstance(compacted_ledgers, list)
                                and compacted_ledgers
                            ):
                                compacted_ledger = normalize_fact_ledger(
                                    compacted_ledgers[0]
                                )
                                if compacted_ledger is not None:
                                    provider_ledger = compacted_ledger
                        if provider_ledger is not None:
                            item["fact_ledger"] = provider_ledger.model_dump(
                                mode="json",
                                exclude_none=True,
                            )
                            provider_is_canonical = (
                                provider_ledger.source == "mcp_canonical"
                            )
                        else:
                            item["fact_ledger"] = deepcopy(
                                native_ledger_input
                            )
                    if not provider_is_canonical:
                        agent_context = self._build_aiops_agent_context(
                            tool_name=tool_name,
                            structured=structured,
                        )
                        if agent_context:
                            item["agent_context"] = agent_context
                        agent_facts = (
                            self._build_aiops_agent_facts(
                                tool_name=tool_name,
                                structured=structured,
                            )
                            if (
                                not is_observability_query
                                or query_semantic_success
                            )
                            else ""
                        )
                        if agent_facts:
                            item["agent_facts"] = agent_facts
                    else:
                        item.pop("data", None)
                    if ledger_input is not None:
                        case_tool_data.append(item)
                    else:
                        supplementary_tool_data.append(item)
        return case_tool_data + supplementary_tool_data

    @classmethod
    def _build_aiops_agent_facts(cls, tool_name: str, structured: Dict[str, Any]) -> str:
        """Render short immutable facts that small models can quote verbatim."""
        normalized_tool = str(tool_name or "").lower()
        if normalized_tool not in {
            "collect_aiops_case",
            "get_aiops_case",
            *cls._OBSERVABILITY_QUERY_TOOLS,
        }:
            return ""
        if not isinstance(structured, dict):
            return ""

        lines: List[str] = []
        max_chars = 10000

        def add(prefix: str, fields: List[tuple[str, Any]]) -> None:
            parts = [prefix]
            for key, value in fields:
                if value in (None, "", [], {}):
                    continue
                parts.append(f"{key}={cls._format_aiops_fact_value(value)}")
            line = " ".join(parts)
            current_chars = sum(len(item) + 1 for item in lines)
            if current_chars + len(line) <= max_chars:
                lines.append(line)

        if normalized_tool in cls._OBSERVABILITY_QUERY_TOOLS:
            add("OBSERVABILITY_QUERY", [
                ("tool", normalized_tool),
                ("status", structured.get("status")),
                ("source_system", structured.get("source_system")),
                ("dimension", structured.get("dimension")),
                ("coverage", structured.get("coverage")),
                ("directness", structured.get("directness")),
                ("purpose", structured.get("purpose")),
            ])
            entity = structured.get("entity")
            if isinstance(entity, dict):
                add("ENTITY", [
                    ("kind", entity.get("kind")),
                    ("namespace", entity.get("namespace")),
                    ("pod", entity.get("pod")),
                    ("pod_uid", entity.get("pod_uid")),
                    ("pod_ip", entity.get("pod_ip")),
                    ("node", entity.get("node")),
                ])
            add("EXECUTED_QUERY", [
                ("query", structured.get("query")),
            ])
            for fact in (structured.get("facts") or [])[:8]:
                if not isinstance(fact, dict):
                    continue
                normalized_value = (
                    normalize_topology_query_fact_value(
                        fact,
                        default_namespace=str(
                            entity.get("namespace") or ""
                        )
                        if isinstance(entity, dict)
                        else "",
                    )
                    if str(
                        fact.get("dimension")
                        or structured.get("dimension")
                        or ""
                    ).strip().lower() == "topology"
                    else None
                )
                if normalized_value:
                    add("TOPOLOGY", [
                        ("relationship", normalized_value.get("relationship")),
                        ("relation", normalized_value.get("relation")),
                        (
                            "source",
                            (
                                normalized_value.get("source") or {}
                            ).get("entity_id")
                            if isinstance(
                                normalized_value.get("source"),
                                dict,
                            )
                            else normalized_value.get("source"),
                        ),
                        (
                            "target",
                            (
                                normalized_value.get("target") or {}
                            ).get("entity_id")
                            if isinstance(
                                normalized_value.get("target"),
                                dict,
                            )
                            else normalized_value.get("target"),
                        ),
                        (
                            "source_field",
                            normalized_value.get("source_field"),
                        ),
                        (
                            "source_system",
                            fact.get("source_system")
                            or structured.get("source_system"),
                        ),
                        ("directness", fact.get("directness")),
                        ("confidence", fact.get("confidence")),
                        ("ref", fact.get("ref")),
                    ])
                add("QUERY_FACT", [
                    ("ref", fact.get("ref")),
                    (
                        "source_system",
                        fact.get("source_system")
                        or structured.get("source_system"),
                    ),
                    ("name", fact.get("name")),
                    (
                        "value",
                        normalized_value
                        if normalized_value is not None
                        else fact.get("value"),
                    ),
                    ("unit", fact.get("unit")),
                    ("labels", fact.get("labels")),
                    ("stats", fact.get("stats")),
                    ("sample_count", fact.get("sample_count")),
                    ("trend_evaluable", fact.get("trend_evaluable")),
                    ("series_role", fact.get("series_role")),
                    ("level", fact.get("level")),
                    ("trace_id", fact.get("trace_id")),
                    ("raw_ref", fact.get("raw_ref")),
                    ("directness", fact.get("directness")),
                ])
            telemetry = structured.get("telemetry")
            if isinstance(telemetry, dict):
                add("TELEMETRY", [
                    ("sources", telemetry),
                ])
            add("QUERY_LIMITATIONS", [
                ("limitations", structured.get("limitations")),
                ("error", structured.get("error")),
            ])
            add("EVIDENCE_REFS", [
                ("values", structured.get("evidence_refs")),
            ])
            return "\n".join(lines)

        add("AIOPS_CASE", [
            ("case_id", structured.get("case_id")),
            ("status", structured.get("status")),
            ("abnormal_type", structured.get("abnormal_type")),
        ])

        primary = structured.get("primary_entity")
        if isinstance(primary, dict):
            add("ENTITY", [
                ("kind", primary.get("kind")),
                ("namespace", primary.get("namespace")),
                ("name", primary.get("name")),
                ("node", primary.get("node")),
                ("pod_ip", primary.get("pod_ip")),
                ("uid", primary.get("uid")),
            ])

        coverage = structured.get("coverage")
        if isinstance(coverage, dict):
            add("COVERAGE", [(str(key), value) for key, value in coverage.items()])

        signals = structured.get("signals_summary")
        if isinstance(signals, list):
            for item in signals:
                if not isinstance(item, dict):
                    continue
                dimension = str(item.get("dimension") or "").strip().lower()
                strength = str(item.get("strength") or "").strip().lower()
                observed = item.get("observed")
                if (
                    dimension not in {"k8s", "kubernetes"}
                    or strength not in {"strong", "critical"}
                    or not isinstance(observed, str)
                    or not observed.strip()
                ):
                    continue
                add("K8S_SIGNAL", [
                    ("signal_id", item.get("signal_id")),
                    ("strength", strength),
                    ("observed", observed.strip()),
                    ("evidence_refs", item.get("evidence_refs")),
                ])
                break

        details = structured.get("dimension_details")
        if not isinstance(details, dict):
            return "\n".join(lines)

        trace_contract = cls._build_aiops_trace_contract(details)
        if trace_contract["log_tempo_trace_ids"] or trace_contract["deepflow_trace_ids"]:
            add("TRACE_CORRELATION", [
                ("log_tempo_trace_ids", trace_contract["log_tempo_trace_ids"]),
                ("deepflow_trace_ids", trace_contract["deepflow_trace_ids"]),
                ("do_not_merge", trace_contract["do_not_merge"]),
                ("log_trace_ids", trace_contract["log_trace_ids"]),
                ("tempo_trace_ids", trace_contract["tempo_trace_ids"]),
                ("shared_trace_ids", trace_contract["shared_trace_ids"]),
            ])
        if trace_contract["has_zero_duration"]:
            add("DEEPFLOW_SEMANTICS", [
                ("duration_us", 0),
                ("is_not_failure_evidence", True),
            ])
        complete = cls._aiops_case_coverage_complete(structured.get("coverage"))
        add("DIMENSION_DETAILS", [
            ("complete", complete),
            (
                "action",
                "post_case_reconciliation"
                if complete
                else "supplement_missing_dimensions",
            ),
        ])
        add("METRIC_SCOPE", [
            ("supporting_evidence_only", True),
            ("k8s_termination_reason_has_priority", True),
            ("single_or_sparse_samples_cannot_exclude_failure_mode", True),
        ])
        add("TOPOLOGY_SCOPE", [
            ("relationships_only", True),
            ("health_not_proven", True),
            ("complete_call_chain_not_proven", True),
        ])
        add("EXIT_CODE_SCOPE", [
            ("symbolic_name_requires_explicit_evidence", True),
        ])
        add("EVIDENCE_REFS", [
            ("do_not_guess_evidence_refs", True),
            ("use_only_returned_refs", True),
        ])

        metrics = details.get("metrics")
        if isinstance(metrics, dict):
            for item in (metrics.get("highlights") or [])[:3]:
                if not isinstance(item, dict):
                    continue
                add("METRIC", [
                    ("metric", item.get("metric")),
                    ("pod", item.get("pod")),
                    ("container", item.get("container")),
                    ("start", item.get("start")),
                    ("max", item.get("max")),
                    ("last", item.get("last")),
                    ("limit", item.get("limit")),
                    ("max_limit_ratio", item.get("max_limit_ratio")),
                    ("samples", item.get("samples")),
                    ("evidence_ref", item.get("evidence_ref")),
                ])

        logs = details.get("logs")
        if isinstance(logs, dict):
            for item in (logs.get("samples") or [])[:4]:
                if not isinstance(item, dict):
                    continue
                message = item.get("message")
                parsed_message: Dict[str, Any] = {}
                if isinstance(message, str):
                    try:
                        decoded = json.loads(message)
                        if isinstance(decoded, dict):
                            parsed_message = decoded
                    except json.JSONDecodeError:
                        parsed_message = {}
                fields: List[tuple[str, Any]] = [
                    ("role", item.get("role")),
                    ("source_system", item.get("source_system")),
                ]
                if parsed_message:
                    for key in (
                        "event",
                        "level",
                        "message",
                        "trace_id",
                        "span_id",
                        "parent_span_id",
                        "path",
                        "error_code",
                        "missing_config",
                        "http_status",
                        "exit_code",
                        "failure_count",
                        "alloc_mib",
                        "allocated_mib",
                        "pod",
                        "service",
                    ):
                        fields.append((key, parsed_message.get(key)))
                else:
                    fields.append(("message", message))
                fields.extend([
                    ("timestamp", item.get("timestamp")),
                    ("evidence_ref", item.get("evidence_ref")),
                ])
                add("LOG", fields)

        tracing = details.get("tracing")
        if isinstance(tracing, dict):
            for item in (tracing.get("flows") or [])[:4]:
                if not isinstance(item, dict):
                    continue
                add("DEEPFLOW", [
                    ("src", item.get("src")),
                    ("dst", item.get("dst")),
                    ("protocol", item.get("protocol")),
                    ("request", item.get("request")),
                    ("response_code", item.get("response_code")),
                    ("duration_us", item.get("duration_us")),
                    ("trace_id", item.get("trace_id")),
                    ("span_id", item.get("span_id")),
                    ("timestamp", item.get("timestamp")),
                    ("evidence_ref", item.get("evidence_ref")),
                ])
            for item in (tracing.get("spans") or [])[:4]:
                if not isinstance(item, dict):
                    continue
                fields = [
                    ("trace_id", item.get("trace_id")),
                    ("service", item.get("service")),
                    ("span", item.get("name")),
                    ("start", item.get("start")),
                    ("end", item.get("end")),
                ]
                attributes = item.get("attributes")
                if isinstance(attributes, dict):
                    preferred = (
                        "http.response.status_code",
                        "error.type",
                        "config.key",
                        "config.present",
                        "aiops.allocated_mib.before",
                        "aiops.allocated_mib.after",
                        "aiops.alloc_mib",
                        "k8s.pod.name",
                        "http.request.method",
                        "url.path",
                        "http.route",
                    )
                    for key in preferred:
                        fields.append((key, attributes.get(key)))
                fields.append(("evidence_ref", item.get("evidence_ref")))
                add("TEMPO", fields)

        topology = details.get("topology")
        if isinstance(topology, dict):
            for item in (topology.get("edges") or [])[:8]:
                if not isinstance(item, dict):
                    continue
                add("TOPOLOGY", [
                    ("relationship", item.get("relationship")),
                    ("source", item.get("source")),
                    ("target", item.get("target")),
                    ("source_system", item.get("source_system")),
                    ("directness", item.get("directness")),
                    ("confidence", item.get("confidence")),
                    ("evidence_refs", item.get("evidence_refs")),
                ])

        return "\n".join(lines)

    @staticmethod
    def _format_aiops_fact_value(value: Any) -> str:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
        if isinstance(value, bool):
            return "true" if value else "false"
        text = str(value)
        if any(char.isspace() for char in text) or "-->" in text:
            return json.dumps(text, ensure_ascii=False)
        return text

    @staticmethod
    def _build_aiops_trace_contract(details: Dict[str, Any]) -> Dict[str, Any]:
        logs = details.get("logs") if isinstance(details.get("logs"), dict) else {}
        tracing = details.get("tracing") if isinstance(details.get("tracing"), dict) else {}

        log_trace_ids: set[str] = set()
        for item in (logs.get("samples") or []):
            if not isinstance(item, dict):
                continue
            message = str(item.get("message") or "")
            try:
                parsed = json.loads(message)
            except json.JSONDecodeError:
                parsed = {}
            if isinstance(parsed, dict) and parsed.get("trace_id"):
                log_trace_ids.add(str(parsed["trace_id"]))

        tempo_trace_ids = {
            str(item.get("trace_id"))
            for item in (tracing.get("spans") or [])
            if isinstance(item, dict) and item.get("trace_id")
        }
        deepflow_trace_ids = {
            str(item.get("trace_id"))
            for item in (tracing.get("flows") or [])
            if isinstance(item, dict) and item.get("trace_id")
        }
        log_tempo_trace_ids = sorted(log_trace_ids & tempo_trace_ids)
        source_trace_sets = [
            trace_ids
            for trace_ids in (
                log_trace_ids,
                tempo_trace_ids,
                deepflow_trace_ids,
            )
            if trace_ids
        ]
        shared_trace_ids = (
            sorted(set.intersection(*source_trace_sets))
            if len(source_trace_sets) >= 2
            else []
        )
        do_not_merge = (
            len(source_trace_sets) >= 2
            and any(
                trace_ids != source_trace_sets[0]
                for trace_ids in source_trace_sets[1:]
            )
        )
        has_zero_duration = any(
            str(item.get("duration_us") or "").strip() in {"0", "0.0"}
            for item in (tracing.get("flows") or [])
            if isinstance(item, dict)
        )

        return {
            "log_trace_ids": sorted(log_trace_ids),
            "tempo_trace_ids": sorted(tempo_trace_ids),
            "log_tempo_trace_ids": log_tempo_trace_ids,
            "deepflow_trace_ids": sorted(deepflow_trace_ids),
            "shared_trace_ids": shared_trace_ids,
            "do_not_merge": do_not_merge,
            "has_zero_duration": has_zero_duration,
        }

    @staticmethod
    def _aiops_case_coverage_complete(value: Any) -> bool:
        coverage = value if isinstance(value, dict) else {}
        present = {"present", "observed"}

        def status(*keys: str) -> str:
            for key in keys:
                if key in coverage:
                    return str(coverage.get(key) or "").strip().lower()
            return ""

        required_statuses = [
            status("k8s", "kubernetes"),
            status("metrics"),
            status("logs", "logging"),
            status("tracing"),
            status("topology"),
        ]
        if "trace" in coverage:
            required_statuses.append(status("trace"))
        return bool(required_statuses) and all(item in present for item in required_statuses)

    @staticmethod
    def _build_aiops_agent_context(tool_name: str, structured: Dict[str, Any]) -> str:
        """Keep bounded, label-free observability facts for downstream agents."""
        normalized_tool = str(tool_name or "").lower()
        if normalized_tool in EvidenceCollectorNode._OBSERVABILITY_QUERY_TOOLS:
            allowed_keys = (
                "status",
                "source_system",
                "dimension",
                "entity",
                "purpose",
                "coverage",
                "directness",
                "query",
                "facts",
                "samples",
                "flows",
                "spans",
                "correlations",
                "telemetry",
                "entities",
                "edges",
                "topology_summary",
                "limitations",
                "evidence_refs",
                "truncated",
                "error",
            )
            payload = {
                key: structured.get(key)
                for key in allowed_keys
                if structured.get(key) not in (None, "", [], {})
            }
            if not payload:
                return ""
            return json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )

        if normalized_tool not in {
            "collect_aiops_case",
            "get_aiops_case",
        }:
            return ""
        if not isinstance(structured, dict):
            return ""

        canonical_ledger = normalize_fact_ledger(structured.get("fact_ledger"))
        if canonical_ledger is not None:
            return compact_fact_ledgers_json(
                [canonical_ledger],
                max_chars=12000,
            )

        allowed_keys = (
            "status",
            "case_id",
            "abnormal_type",
            "primary_entity",
            "coverage",
            "topology_summary",
            "dimension_details",
            "recommended_refs_by_dimension",
        )
        payload = {
            key: structured.get(key)
            for key in allowed_keys
            if structured.get(key) not in (None, "", [], {})
        }
        if not payload:
            return ""

        return compact_aiops_legacy_context_json(
            payload,
            max_chars=12000,
        )
