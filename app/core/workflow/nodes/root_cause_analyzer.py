"""
节点3：根因分析

职责：
- 调用 LLM 基于证据进行根因推理
- 构建因果链
- 输出：root_cause, causal_chain, rca_analysis

设计：
- 有自己的专用 prompt
- 支持两种 LLM 调用模式（通过 config/环境变量切换）：
  - lite: AICall.call_simple 直接调用（不带工具），避免重复采集
  - full: AICall.call 全工具模式（LangChain create_agent）
- 结合规则引擎验证结论
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Mapping, Optional

from app.core.workflow.fact_contract import (
    bounded_json_dumps,
    compact_fact_ledgers_json,
    extract_fact_ledger_inputs_from_evidence_analysis,
    extract_fact_ledgers_from_evidence_analysis,
    extract_fact_ledgers_from_tool_data,
    select_tool_data_for_rca,
    validate_rca_claims,
)
from app.core.workflow.entity_evidence_snapshot import (
    build_entity_evidence_snapshot,
    build_selection_manifest,
    classify_fact_evidence_role,
)
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import RCAOutput
from app.core.workflow.state import WorkflowState
from app.core.skills.models import (
    Layer, DeterministicDecision, EvidenceItem,
    EvidenceLevel, Confidence
)
from app.core.prompts import get_workflow_prompt
from app.core.text_helpers import truncate_question

logger = logging.getLogger(__name__)


RCA_TEXT_FIELD_LIMIT = 500
RCA_LIST_LIMIT = 12
RCA_CONTEXT_MAX_CHARS = 52000
RCA_HANDOFF_MAX_CHARS = 7000
RCA_TOOL_CONTEXT_MAX_CHARS = 36000
RCA_FACT_LEDGER_MAX_CHARS = 24000
RCA_QUALITY_MAX_CHARS = 4000
RCA_SUPPLEMENTARY_MAX_CHARS = 7000
RCA_AUXILIARY_MAX_CHARS = 3000
RCA_RAW_OUTPUT_MAX_CHARS = 12000


class RootCauseAnalyzerNode(WorkflowNode):
    """
    根因分析节点

    每次执行都会调用 LLM 进行根因推理
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog
    
    @property
    def node_id(self) -> str:
        return "rca"
    
    @property
    def node_name(self) -> str:
        return "根因分析"


    def _get_rca_prompt(self) -> str:
        return get_workflow_prompt("rca", prompt_language=self._get_prompt_language())
    
    def get_required_fields(self) -> List[str]:
        return ["question", "layer", "evidence_items"]
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行根因分析逻辑
        
        1. 整理证据摘要
        2. 调用 LLM 进行根因推理
        3. 可选：用规则引擎验证
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }
        
        try:
            question = state.get("question", "")
            layer = state.get("layer")
            evidence_items = state.get("evidence_items", [])
            evidence_analysis = state.get("evidence_analysis", "{}")

            logger.info(f"🔍 根因分析: 层级={layer}, 证据数量={len(evidence_items)}")
            logger.debug(f"🔍 [DEBUG] RCA 输入: question={question[:100]}, "
                        f"evidence_analysis长度={len(evidence_analysis)}, "
                        f"layer_handoff长度={len(json.dumps(state.get('layer_handoff') or {}, ensure_ascii=False, default=str))}")

            entity_evidence_snapshot = self._resolve_entity_evidence_snapshot(
                state,
                evidence_analysis,
            )
            state_with_rca_input = {
                **state,
                "entity_evidence_snapshot": entity_evidence_snapshot,
            }
            rca_input = self._build_rca_input_projection(
                state_with_rca_input,
                evidence_analysis,
            )
            state_with_rca_input["rca_input_projection"] = rca_input
            evidence_summary = self._build_rca_context(state_with_rca_input)
            self._archive_node_input({
                "node": self.node_id,
                "question": question,
                "layer": layer.value if isinstance(layer, Layer) else layer,
                "rca_input_projection": rca_input,
                "evidence_summary": evidence_summary,
            })
            thinking_events = []

            # 使用 LLM 分析
            ai_call = getattr(self, 'ai_call', None)
            if ai_call is not None:
                raw_result, thinking_events = self._analyze_with_llm(
                    question, layer, evidence_summary
                )
            else:
                # 无 LLM 时仅保留通用低置信度兜底
                logger.info("⚠️ 无 LLM 服务，使用通用低置信度兜底")
                raw_result = self._build_llm_fallback(
                    question=question,
                    layer=layer,
                    reason="LLM 不可用，无法完成可靠根因分析",
                )
                thinking_events = []

            attempts: List[Dict[str, Any]] = []
            self._archive_node_output(
                raw_result or {},
                artifact_name="rca.attempt-1.model",
            )
            validation_enabled = self._is_rca_validation_enabled(default=True)
            if validation_enabled:
                validated_result = self._validate_rca_result_against_evidence(
                    raw_result or {},
                    evidence_analysis,
                    question=question,
                    layer=layer,
                )
            else:
                logger.info(
                    "⏭️ [rca] 事实绑定与 claim validation 已关闭；"
                    "直接采用本次 LLM RCA"
                )
                validated_result = dict(raw_result or {})
            self._archive_node_output(
                validated_result,
                artifact_name="rca.attempt-1.validated",
            )
            attempts.append({
                "attempt": 1,
                "model_output": raw_result or {},
                "validated_output": validated_result,
            })

            if validation_enabled and self._should_repair_rca(
                validated_result,
                rca_input,
            ):
                repair_context = self._build_rca_repair_context(
                    rca_input,
                    validated_result,
                )
                repaired_raw, repair_events = self._analyze_with_llm(
                    question,
                    layer,
                    repair_context,
                )
                thinking_events.extend(repair_events or [])
                self._archive_node_output(
                    repaired_raw or {},
                    artifact_name="rca.attempt-2.model",
                )
                repaired_validated = self._validate_rca_result_against_evidence(
                    repaired_raw or {},
                    evidence_analysis,
                    question=question,
                    layer=layer,
                )
                self._archive_node_output(
                    repaired_validated,
                    artifact_name="rca.attempt-2.validated",
                )
                attempts.append({
                    "attempt": 2,
                    "model_output": repaired_raw or {},
                    "validated_output": repaired_validated,
                })
                validated_result = self._select_preferred_rca_result(
                    validated_result,
                    repaired_validated,
                )

            rca_result = self._sanitize_rca_result(validated_result)
            if validation_enabled:
                claim_validation = (
                    rca_result.get("claim_validation")
                    if isinstance(rca_result.get("claim_validation"), dict)
                    else {
                        "enabled": True,
                        "valid": False,
                        "diagnostic_status": rca_result.get(
                            "diagnostic_status", "inconclusive"
                        ),
                        "reasons": ["formal claim validation was not available"],
                    }
                )
                claim_validation.setdefault("enabled", True)
            else:
                claim_validation = {
                    "enabled": False,
                    "skipped": True,
                    "valid": None,
                    "diagnostic_status": rca_result.get(
                        "diagnostic_status", "inconclusive"
                    ),
                    "reasons": [
                        "RCA fact binding and publication validation disabled by configuration"
                    ],
                }
                rca_result["claim_validation"] = claim_validation
            self._archive_node_output(
                rca_result,
                artifact_name="rca.output",
            )
            self._archive_node_output(
                claim_validation,
                artifact_name="claim_validation.output",
            )
            
            # 构建决策对象
            decision = self._build_decision(layer, evidence_items, rca_result)
            
            new_state.update({
                "deterministic_decision": decision,
                "root_cause": rca_result.get("root_cause", ""),
                "causal_chain": rca_result.get("causal_chain", {}),
                "rca_analysis": json.dumps(rca_result, ensure_ascii=False),
                "rca_input_projection": rca_input,
                "rca_attempts": attempts,
                "claim_validation": claim_validation,
                "entity_evidence_snapshot": entity_evidence_snapshot,
                # AI 判定的核心 Runbook（从 primary_runbooks 列表取第一个）
                "primary_runbook_id": ", ".join(rca_result.get("primary_runbooks", []) or []) or None,
            })

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

            logger.info(f"✅ 根因分析完成: {rca_result.get('root_cause', '')[:50]}...")

        except Exception as e:
            logger.error(f"根因分析失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "deterministic_decision": None,
                "root_cause": f"根因分析失败: {str(e)}",
                "causal_chain": {},
                "rca_analysis": "{}",
            })
            self._save_thinking(state, new_state, [])

        return new_state

    @staticmethod
    def _resolve_entity_evidence_snapshot(
        state: WorkflowState,
        evidence_analysis: Any,
    ) -> Dict[str, Any]:
        existing = state.get("entity_evidence_snapshot")
        if (
            isinstance(existing, Mapping)
            and existing.get("contract_version")
            == "aiops.entity-evidence-snapshot.v1"
        ):
            return dict(existing)
        ledgers = extract_fact_ledgers_from_evidence_analysis(evidence_analysis)
        entities: List[Dict[str, Any]] = []
        seen = set()
        for ledger in ledgers:
            for record in ledger.records:
                namespace = str(record.namespace or "").strip()
                name = str(record.entity_name or "").strip()
                key = (namespace, name)
                if not namespace or not name or key in seen:
                    continue
                seen.add(key)
                entities.append({
                    "kind": record.entity_kind or "Pod",
                    "namespace": namespace,
                    "name": name,
                })
        if not entities:
            return {}
        return build_entity_evidence_snapshot(
            entities=entities,
            evidence_analysis=evidence_analysis,
            thinking_events=state.get("thinking_events") or [],
        ).to_handoff()

    def _build_rca_input_projection(
        self,
        state: WorkflowState,
        evidence_analysis: Any,
    ) -> Dict[str, Any]:
        """Create one code-owned, record-complete RCA handoff."""
        snapshot = (
            state.get("entity_evidence_snapshot")
            if isinstance(state.get("entity_evidence_snapshot"), Mapping)
            else {}
        )
        snapshot_fact_index = (
            snapshot.get("fact_index")
            if isinstance(snapshot.get("fact_index"), Mapping)
            else {}
        )
        if snapshot.get("contract_version") == "aiops.entity-evidence-snapshot.v1":
            # A lane snapshot has already applied the authoritative entity
            # boundary. Re-expanding from the collector's unscoped ledgers here
            # would reintroduce sibling Pod facts into this lane.
            fact_index = {
                str(fact_id): dict(record)
                for fact_id, record in snapshot_fact_index.items()
                if isinstance(record, Mapping)
            }
            authoritative_entity_ids = list(dict.fromkeys(
                str(record.get("entity_id") or "").strip()
                for record in fact_index.values()
                if str(record.get("entity_id") or "").lower().startswith(
                    "k8s.pod:"
                )
            ))
            if not authoritative_entity_ids:
                authoritative_entity_ids = list(dict.fromkeys(
                    str(entity_id)
                    for ledger in (snapshot.get("fact_ledgers") or [])
                    if isinstance(ledger, Mapping)
                    for entity_id in (ledger.get("scope_entity_ids") or [])
                    if str(entity_id).lower().startswith("k8s.pod:")
                ))
        else:
            ledgers = extract_fact_ledgers_from_evidence_analysis(
                evidence_analysis
            )
            authoritative_entity_ids = list(dict.fromkeys(
                entity_id
                for ledger in ledgers
                for entity_id in ledger.scope_entity_ids
                if str(entity_id).lower().startswith("k8s.pod:")
            ))
            fact_index: Dict[str, Dict[str, Any]] = {}
            for ledger in ledgers:
                for record in ledger.records:
                    payload = record.model_dump(mode="json", exclude_none=True)
                    payload["evidence_role"] = classify_fact_evidence_role(
                        payload
                    )
                    fact_index[record.fact_id] = payload
        raw_manifest = snapshot.get("selection_manifest")
        if isinstance(raw_manifest, Mapping):
            manifest = dict(raw_manifest)
        else:
            manifest = build_selection_manifest(
                fact_index,
                max_facts=48,
            ).to_dict()

        selected_fact_ids = [
            str(fact_id)
            for fact_id in manifest["rca_input_fact_ids"]
            if str(fact_id) in fact_index
        ]
        return {
            "contract_version": "aiops.rca-input-projection.v1",
            "authoritative_entity_ids": authoritative_entity_ids,
            "selection_manifest": manifest,
            "selected_facts": [
                fact_index[fact_id] for fact_id in selected_fact_ids
            ],
            "snapshot_contract_version": snapshot.get("contract_version"),
            "snapshot_limitations": list(snapshot.get("limitations") or []),
        }

    def _should_repair_rca(
        self,
        validated_result: Mapping[str, Any],
        rca_input: Mapping[str, Any],
    ) -> bool:
        if bool(getattr(self, "disable_internal_repair", False)):
            return False
        if getattr(self, "ai_call", None) is None:
            return False
        cancel_event = getattr(self, "cancel_event", None)
        if cancel_event is not None and cancel_event.is_set():
            return False
        manifest = rca_input.get("selection_manifest")
        eligible = (
            manifest.get("eligible_support_fact_ids")
            if isinstance(manifest, Mapping)
            else []
        )
        if not eligible:
            return False
        claim = validated_result.get("claim_validation")
        diagnosis_publishable = (
            bool(
                claim.get(
                    "diagnosis_publishable",
                    claim.get("diagnosis_supported", False),
                )
            )
            if isinstance(claim, Mapping)
            else False
        )
        return (
            str(validated_result.get("diagnostic_status") or "inconclusive")
            == "inconclusive"
            or not diagnosis_publishable
        )

    @staticmethod
    def _select_preferred_rca_result(
        first: Mapping[str, Any],
        repaired: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Use a repair only when it improves claim publication quality."""
        def score(value: Mapping[str, Any]) -> tuple[int, int, int]:
            claim = (
                value.get("claim_validation")
                if isinstance(value.get("claim_validation"), Mapping)
                else {}
            )
            publishable = bool(
                claim.get(
                    "diagnosis_publishable",
                    claim.get("diagnosis_supported", False),
                )
            )
            valid_support = len(claim.get("valid_supporting_fact_ids") or [])
            diagnosed = str(value.get("diagnostic_status") or "") == "diagnosed"
            return (int(publishable), valid_support, int(diagnosed))

        return dict(repaired if score(repaired) > score(first) else first)

    @staticmethod
    def _build_rca_repair_context(
        rca_input: Mapping[str, Any],
        first_result: Mapping[str, Any],
    ) -> str:
        manifest = (
            rca_input.get("selection_manifest")
            if isinstance(rca_input.get("selection_manifest"), Mapping)
            else {}
        )
        eligible_ids = set(manifest.get("eligible_support_fact_ids") or [])
        required_ids = set(manifest.get("required_context_fact_ids") or [])
        selected_facts = [
            fact
            for fact in (rca_input.get("selected_facts") or [])
            if isinstance(fact, Mapping)
        ]
        claim = (
            first_result.get("claim_validation")
            if isinstance(first_result.get("claim_validation"), Mapping)
            else {}
        )
        repair_payload = {
            "contract_version": "aiops.rca-repair-input.v1",
            "authoritative_entity_ids": list(
                rca_input.get("authoritative_entity_ids") or []
            ),
            "previous_claim": (
                claim.get("rejected_claim")
                if isinstance(claim.get("rejected_claim"), Mapping)
                else {
                    "phenomenon": first_result.get("phenomenon"),
                    "root_cause": first_result.get("root_cause"),
                    "causal_chain": first_result.get("causal_chain") or {},
                }
            ),
            "eligible_support_facts": [
                fact
                for fact in selected_facts
                if str(fact.get("fact_id") or "") in eligible_ids
            ],
            "required_context_facts": [
                fact
                for fact in selected_facts
                if str(fact.get("fact_id") or "") in required_ids
            ],
            "validation_reasons": list(claim.get("reasons") or []),
            "invalid_fact_ids": list(claim.get("invalid_fact_ids") or []),
            "instruction": (
                "只修复 RCA 发布合同，不重新采集。若 previous_claim 的语义被事实支持，"
                "保留其内容并用本 payload 中精确 fact_id 填写顶层 supporting_fact_ids、"
                "唯一 hypothesis 及 evidence_analysis；causal_chain 至少填写 trigger、"
                "mechanism、manifestation。若不受支持则输出 inconclusive。"
            ),
        }
        return "## AIOps Fact Ledger — constrained repair\n" + bounded_json_dumps(
            repair_payload,
            max_chars=RCA_CONTEXT_MAX_CHARS - 48,
        )

    def _build_evidence_summary(
        self,
        evidence_items: List[EvidenceItem],
        *,
        max_chars: int = 6000,
    ) -> str:
        """构建证据摘要"""
        lines = []
        for i, item in enumerate(evidence_items[:24], 1):
            status = "✅ 已采集" if item.collected else "❌ 未采集"
            compact_value = self._compact_text_value(item.value, limit=500)
            value = f"= {compact_value}" if compact_value else ""
            lines.append(f"{i}. [{status}] {item.description} {value}")
        if len(evidence_items) > 24:
            lines.append(f"... 截断，原始 {len(evidence_items)} 项")
        rendered = "\n".join(lines) if lines else "暂无证据"
        return self._compact_text_value(rendered, limit=max_chars)

    def _build_rca_context(self, state: WorkflowState) -> str:
        """Build compact RCA input from handoff + bounded evidence facts."""
        evidence_items = state.get("evidence_items", [])
        evidence_analysis = state.get("evidence_analysis", "{}")
        fact_ledgers = extract_fact_ledgers_from_evidence_analysis(evidence_analysis)
        layer_handoff = state.get("layer_handoff")
        if not layer_handoff:
            layer_handoff = self._layer_analysis_to_handoff(state.get("layer_analysis", ""))

        compact_handoff = self._compact_layer_handoff_for_rca(
            layer_handoff or {}
        )
        parts = [
            "# 问题定位结构化交接 layer_handoff",
            compact_handoff,
        ]
        rca_input_projection = state.get("rca_input_projection")
        if isinstance(rca_input_projection, Mapping):
            parts.extend([
                "",
                "# 代码权威 RCA 输入投影",
                bounded_json_dumps(
                    rca_input_projection,
                    max_chars=RCA_FACT_LEDGER_MAX_CHARS,
                ),
            ])
        if fact_ledgers:
            parts.extend([
                "",
                "# Fact Ledger 证据合同",
                "Fact Ledger 是 AIOps 根因分析的主证据输入；只能引用当前 ledger 中的 fact_id。",
            ])
        else:
            parts.extend([
                "",
                "# 证据采集结果",
                self._build_evidence_summary(
                    evidence_items,
                    max_chars=RCA_AUXILIARY_MAX_CHARS,
                ),
            ])

        facts = state.get("evidence_facts") or []
        conflicts = state.get("evidence_conflicts") or []
        missing = state.get("missing_evidence") or []
        if facts and not fact_ledgers:
            parts.extend([
                "",
                "# 已验证事实",
                bounded_json_dumps(
                    facts,
                    max_chars=RCA_AUXILIARY_MAX_CHARS,
                ),
            ])
        if conflicts:
            parts.extend([
                "",
                "# 冲突/负向证据",
                bounded_json_dumps(
                    conflicts,
                    max_chars=RCA_AUXILIARY_MAX_CHARS,
                ),
            ])
        if missing:
            parts.extend([
                "",
                "# 缺失证据",
                bounded_json_dumps(
                    missing,
                    max_chars=RCA_AUXILIARY_MAX_CHARS,
                ),
            ])

        base_context = "\n".join(parts)
        remaining_chars = max(
            2,
            min(
                RCA_TOOL_CONTEXT_MAX_CHARS,
                RCA_CONTEXT_MAX_CHARS - len(base_context) - 32,
            ),
        )
        extra_data = self._extract_tool_data_for_rca(
            evidence_analysis,
            max_chars=remaining_chars,
        )
        if extra_data:
            parts.extend(["", "# 工具采集摘要", extra_data])

        context = "\n".join(parts)
        if len(context) > RCA_CONTEXT_MAX_CHARS:
            logger.warning(
                "⚠️ [rca] section budgets exceeded final context cap: %d > %d",
                len(context),
                RCA_CONTEXT_MAX_CHARS,
            )
            context = context[:RCA_CONTEXT_MAX_CHARS]
        return context

    @classmethod
    def _compact_layer_handoff_for_rca(cls, value: Any) -> str:
        """Keep RCA-relevant handoff fields without repeated model reasoning."""
        handoff = dict(value) if isinstance(value, dict) else {}
        abnormal_pod_entity_index = cls._build_abnormal_pod_entity_index(
            handoff.get("abnormal_pods")
        )
        compact: Dict[str, Any] = {}
        scalar_keys = (
            "diagnosis_scope",
            "layer",
            "derived_layer",
            "layers",
            "primary_pod",
            "pod_status_keyword",
            "abnormal_pods",
            "must_verify",
            "do_not_change",
        )
        for key in scalar_keys:
            if handoff.get(key) not in (None, {}, []):
                compact[key] = handoff.get(key)

        issue_groups = handoff.get("issue_groups")
        if not isinstance(issue_groups, list):
            issue_groups = handoff.get("abnormal_groups")
        if isinstance(issue_groups, list) and issue_groups:
            compact["issue_groups"] = [
                {
                    key: group.get(key)
                    for key in ("group_id", "status_keywords", "entities")
                    if group.get(key) not in (None, "", [], {})
                }
                for group in issue_groups
                if isinstance(group, dict)
            ]

        current_summary = handoff.get("current_abnormal_summary")
        if isinstance(current_summary, dict):
            compact["current_abnormal_summary"] = {
                key: current_summary.get(key)
                for key in (
                    "source",
                    "status_counts",
                    "total_abnormal",
                    "selected_rows",
                )
                if current_summary.get(key) not in (None, {}, [])
            }

        if not abnormal_pod_entity_index:
            return bounded_json_dumps(
                compact,
                max_chars=RCA_HANDOFF_MAX_CHARS,
            )

        compact.pop("abnormal_pods", None)
        entity_index_text = json.dumps(
            {"abnormal_pod_entity_index": abnormal_pod_entity_index},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        if len(entity_index_text) > RCA_HANDOFF_MAX_CHARS:
            raise ValueError(
                "abnormal Pod identity index exceeds RCA handoff budget: "
                f"{len(entity_index_text)} > {RCA_HANDOFF_MAX_CHARS}"
            )

        detail_budget = RCA_HANDOFF_MAX_CHARS - len(entity_index_text) + 1
        compact_detail_text = bounded_json_dumps(
            compact,
            max_chars=detail_budget,
        )
        if compact_detail_text == "{}":
            return entity_index_text
        return f"{entity_index_text[:-1]},{compact_detail_text[1:]}"

    @staticmethod
    def _build_abnormal_pod_entity_index(value: Any) -> List[Dict[str, Any]]:
        """Project abnormal Pods into a small identity set before compression."""
        if not isinstance(value, list):
            return []

        entities: List[Dict[str, Any]] = []
        seen = set()
        for item in value:
            if not isinstance(item, dict):
                continue
            entity = {
                key: item.get(key)
                for key in ("namespace", "name", "status", "uid")
                if item.get(key) not in (None, "")
            }
            if not entity:
                continue
            identity = tuple(
                entity.get(key)
                for key in ("namespace", "name", "status", "uid")
            )
            if identity in seen:
                continue
            seen.add(identity)
            entities.append(entity)
        return entities

    @staticmethod
    def _layer_analysis_to_handoff(layer_analysis: str) -> Dict[str, Any]:
        try:
            data = json.loads(layer_analysis) if layer_analysis else {}
            if isinstance(data, dict):
                return {
                    "layer": data.get("layer"),
                    "derived_layer": data.get("derived_layer", data.get("layer")),
                    "confidence": data.get("confidence"),
                    "primary_problem": data.get("reasoning", ""),
                    "abnormal_pods": data.get("abnormal_pods", []),
                    "abnormal_groups": data.get("abnormal_groups", data.get("issue_groups", [])),
                    "issue_groups": data.get("issue_groups", data.get("abnormal_groups", [])),
                    "pod_status_keyword": data.get("pod_status_keyword"),
                    "pod_abnormal_type": data.get("pod_abnormal_type"),
                    "status_category": data.get("status_category"),
                    "active_entities": data.get("key_entities", []),
                    "possible_scenarios": data.get("possible_scenarios", []),
                    "matched_runbooks": data.get("matched_runbooks", []),
                }
        except (json.JSONDecodeError, TypeError):
            pass
        return {}
    
    def _get_rca_mode(self) -> str:
        """
        获取 RCA 调用模式，优先级: 环境变量 > config.yaml > 默认值(lite)

        Returns:
            "lite" 或 "full"
        """
        # 1. 环境变量
        env_val = os.getenv("WORKFLOW_RCA_MODE", "").lower()
        if env_val in ("lite", "full"):
            return env_val
        # 2. config.yaml → workflow.rca_mode
        if self.holmes_service:
            wf_config = getattr(self.holmes_service, "workflow_config", {}) or {}
            config_val = wf_config.get("rca_mode", "")
            if str(config_val).lower() in ("lite", "full"):
                return str(config_val).lower()
        # 3. 默认 lite（不带工具，避免重复执行）
        return "lite"

    def _analyze_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """使用 LLM 进行根因分析（自动路由 lite/full 模式）

        Returns:
            (rca_result_dict, intermediate_events_list)
        """
        mode = self._get_rca_mode()
        logger.info(f"🔍 RCA 调用模式: {mode}")

        if mode == "lite":
            return self._analyze_with_llm_lite(question, layer, evidence_summary)
        else:
            return self._analyze_with_llm_full(question, layer, evidence_summary)

    def _analyze_with_llm_lite(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """lite 模式：AICall.call_simple 直接调用（不带工具），避免重复采集"""
        try:
            layer_str = layer.value if layer else "ABNORMAL"
            system_prompt = self._get_rca_prompt().format(
                layer=layer_str,
                evidence_summary="证据上下文只在 user message 中提供，system prompt 不承载动态证据。"
            )

            user_message = f"""# 用户问题
{question}

# 已采集证据
{evidence_summary}

请直接基于以上证据进行根因分析，并通过 RCAOutput Pydantic schema 生成结构化结果。"""
            start_time = time.time()

            ai_call = getattr(self, 'ai_call', None)
            if ai_call is None:
                raise RuntimeError("[rca] ai_call 未设置，无法执行 lite 模式")

            logger.info("📍 [rca] Pydantic structured lite 模式开始")
            structured, response, thinking_events = self._call_structured_agent(
                schema=RCAOutput,
                system_prompt=system_prompt,
                question=user_message,
                use_tools=False,
                allow_text_fallback=True,
            )
            parsed = structured.model_dump() if structured is not None else None
            content = response.result if response is not None else ""

            duration_ms = (time.time() - start_time) * 1000

            if self.metrics:
                self.metrics.record_llm_call("rca", duration_ms)

            logger.info("✅ [rca] lite 模式完成 (%.0fms, 输出=%d字)",
                       duration_ms, len(content or ""))

            if parsed:
                return parsed, thinking_events

            recovered = self._recover_tolerant_rca_output(
                (response.result if response is not None else "") or "",
            )
            if recovered is not None:
                logger.warning(
                    "⚠️ [rca] Pydantic 整体校验失败；tolerant 模式已保留核心 RCA，warnings=%s",
                    recovered.get("parse_warnings") or [],
                )
                return recovered, thinking_events

            logger.warning("⚠️ [rca] lite 模式未返回合法 Pydantic RCAOutput，使用通用低置信度兜底")
            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason="LLM 返回结果不符合 RCA 结构化输出合同",
            ), []

        except Exception as e:
            logger.warning(f"[rca] lite 模式失败，使用通用低置信度兜底: {e}")
            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason=f"LLM 根因分析失败: {str(e)}",
            ), []


    def _analyze_with_llm_full(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """full 模式：仍使用 RCAOutput Pydantic schema，不调用工具、不解析手写结构化文本。"""
        try:
            layer_str = layer.value if layer else "ABNORMAL"

            system_prompt = self._get_rca_prompt().format(
                layer=layer_str,
                evidence_summary=evidence_summary
            )

            # 告诉 LLM 不要重复采集数据，基于已有证据分析
            system_prompt += """

# ⚠️ 重要：不要重复采集数据
上面的「已采集证据」和「工具采集的原始数据」已经包含了所有需要的信息。
请直接基于这些数据进行分析，**不要重新调用工具采集数据**。
如果数据不足，在 limitations 中说明即可。"""

            user_message = f"""# 用户问题
{question}

# 已采集证据
{evidence_summary}

请直接基于以上证据进行根因分析，并通过 RCAOutput Pydantic schema 生成结构化结果。"""
            structured, response, thinking_events = self._call_structured_agent(
                schema=RCAOutput,
                system_prompt=system_prompt,
                question=user_message,
                use_tools=False,
                allow_text_fallback=True,
            )
            if structured is not None:
                return structured.model_dump(), thinking_events

            recovered = self._recover_tolerant_rca_output(
                (response.result if response is not None else "") or "",
            )
            if recovered is not None:
                logger.warning(
                    "⚠️ [rca] full 模式 Pydantic 整体校验失败；"
                    "tolerant 模式已保留核心 RCA，warnings=%s",
                    recovered.get("parse_warnings") or [],
                )
                return recovered, thinking_events

            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason=f"LLM 未返回有效 RCAOutput，无法完成可靠根因分析: {((response.result if response else '') or '')[:200]}",
            ), []

        except Exception as e:
            logger.warning(f"LLM 分析失败，使用通用低置信度兜底: {e}")
            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason=f"LLM 根因分析失败: {str(e)}",
            ), []
    
    @staticmethod
    def _normalize_rca_result(parsed: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(parsed, dict):
            return None
        try:
            return RCAOutput.model_validate(parsed).model_dump()
        except Exception as exc:
            logger.warning("⚠️ [rca] RCA 结构化校验失败: %s", exc)
            return None

    @staticmethod
    def _tolerant_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (list, tuple)):
            return "；".join(
                str(item).strip() for item in value if str(item).strip()
            )
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value).strip()

    @staticmethod
    def _tolerant_string_list(value: Any, *, fact_ids: bool = False) -> List[str]:
        if value is None:
            return []
        values = value if isinstance(value, (list, tuple, set)) else [value]
        normalized: List[str] = []
        for item in values:
            text = str(item or "").strip()
            if not text:
                continue
            if fact_ids:
                matches = re.findall(r"fact-[A-Za-z0-9]+", text)
                if matches:
                    normalized.extend(matches)
                    continue
            normalized.append(text)
        return list(dict.fromkeys(normalized))

    @classmethod
    def _normalize_tolerant_dict_items(
        cls,
        value: Any,
        *,
        field_name: str,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        if value is None:
            return []
        values = value if isinstance(value, list) else [value]
        if not isinstance(value, list):
            warnings.append(f"{field_name}: expected array; wrapped input as array")
        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(values):
            if isinstance(item, dict):
                normalized.append(dict(item))
                continue
            text = cls._tolerant_text(item)
            if not text:
                warnings.append(f"{field_name}.{index}: empty non-object item dropped")
                continue
            warnings.append(f"{field_name}.{index}: string item normalized to object")
            if field_name == "evidence_analysis":
                fact_matches = re.findall(r"fact-[A-Za-z0-9]+", text)
                entry: Dict[str, Any] = {
                    "relevance": text,
                    "role": "supporting_context",
                }
                if fact_matches:
                    entry["fact_id"] = fact_matches[0]
                    if len(fact_matches) > 1:
                        entry["fact_ids"] = list(dict.fromkeys(fact_matches))
                normalized.append(entry)
            else:
                normalized.append({"summary": text})
        return normalized

    @classmethod
    def _normalize_tolerant_hypotheses(
        cls,
        value: Any,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        if value is None:
            return []
        values = value if isinstance(value, list) else [value]
        if not isinstance(value, list):
            warnings.append("hypotheses: expected array; wrapped input as array")
        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(values):
            if isinstance(item, dict):
                normalized.append(dict(item))
                continue
            text = cls._tolerant_text(item)
            if not text:
                warnings.append(f"hypotheses.{index}: empty item dropped")
                continue
            warnings.append(f"hypotheses.{index}: string item normalized to object")
            normalized.append({
                "hypothesis_id": f"h-recovered-{index + 1}",
                "summary": text,
                "confidence": 0.5,
            })
        return normalized

    def _recover_tolerant_rca_output(self, raw: str) -> Optional[Dict[str, Any]]:
        """Recover a publishable core RCA from repairable JSON shape drift.

        This does not infer a root cause from arbitrary prose. It only salvages
        an already-present root_cause/root_cause_summary from a parsed JSON
        object, normalizes optional fields, then re-validates the result.
        """
        if self._get_rca_structured_output_mode(default="tolerant") != "tolerant":
            return None

        from app.core.aicall.client import AICall

        parsed = AICall.extract_json_payload(raw)
        if not isinstance(parsed, dict):
            return None

        payload = dict(parsed)
        warnings: List[str] = []
        root_cause = self._tolerant_text(
            payload.get("root_cause_summary") or payload.get("root_cause")
        )
        if not root_cause:
            # Content-first mode still needs one explicit model-authored core
            # claim; arbitrary narrative is not promoted into a diagnosis.
            return None

        for field_name in (
            "phenomenon",
            "root_cause",
            "root_cause_summary",
            "confidence_reason",
            "limitations",
            "llm_raw_analysis",
        ):
            if field_name in payload:
                original = payload.get(field_name)
                normalized = self._tolerant_text(original)
                if not isinstance(original, str):
                    warnings.append(f"{field_name}: normalized to string")
                payload[field_name] = normalized

        payload["root_cause"] = root_cause
        payload["root_cause_summary"] = root_cause
        if payload.get("diagnostic_status") not in {"diagnosed", "inconclusive"}:
            payload["diagnostic_status"] = "inconclusive"
            warnings.append("diagnostic_status: missing/invalid; defaulted to inconclusive")

        confidence = payload.get("confidence")
        if confidence is None:
            payload["confidence"] = 0.5
            warnings.append("confidence: missing; defaulted to 0.5")
        elif isinstance(confidence, (int, float)) and confidence > 1:
            payload["confidence"] = min(float(confidence) / 100.0, 1.0)
            warnings.append("confidence: percentage normalized to 0.0-1.0")

        if not self._tolerant_text(payload.get("confidence_reason")):
            payload["confidence_reason"] = (
                "保留模型已给出的根因内容；辅助结构字段经过确定性容错恢复"
            )
            warnings.append("confidence_reason: missing; recovery reason inserted")

        payload["evidence_inventory"] = self._normalize_tolerant_dict_items(
            payload.get("evidence_inventory"),
            field_name="evidence_inventory",
            warnings=warnings,
        )
        payload["evidence_analysis"] = self._normalize_tolerant_dict_items(
            payload.get("evidence_analysis"),
            field_name="evidence_analysis",
            warnings=warnings,
        )
        payload["hypotheses"] = self._normalize_tolerant_hypotheses(
            payload.get("hypotheses"), warnings
        )

        for field_name in (
            "supporting_fact_ids",
            "contradicting_fact_ids",
        ):
            original = payload.get(field_name)
            if original is not None and not isinstance(original, list):
                warnings.append(f"{field_name}: normalized to string array")
            payload[field_name] = self._tolerant_string_list(
                original, fact_ids=True
            )
        for field_name in ("unknowns", "primary_runbooks"):
            original = payload.get(field_name)
            if original is not None and not isinstance(original, list):
                warnings.append(f"{field_name}: normalized to string array")
            payload[field_name] = self._tolerant_string_list(original)

        causal_chain = payload.get("causal_chain")
        if not isinstance(causal_chain, dict):
            causal_text = self._tolerant_text(causal_chain)
            payload["causal_chain"] = (
                {"mechanism": causal_text} if causal_text else {}
            )
            if causal_chain is not None:
                warnings.append("causal_chain: normalized to object")
        if not isinstance(payload.get("claim_validation"), dict):
            payload["claim_validation"] = {}
            warnings.append("claim_validation: normalized to object")
        if not isinstance(payload.get("alternative_causes"), list):
            alternative = payload.get("alternative_causes")
            payload["alternative_causes"] = [] if alternative is None else [alternative]
            if alternative is not None:
                warnings.append("alternative_causes: normalized to array")

        if not self._tolerant_text(payload.get("llm_raw_analysis")):
            payload["llm_raw_analysis"] = raw[:RCA_RAW_OUTPUT_MAX_CHARS]
            warnings.append("llm_raw_analysis: preserved from raw structured response")

        try:
            recovered = RCAOutput.model_validate(payload).model_dump()
        except Exception as exc:
            logger.warning("⚠️ [rca] tolerant 字段归一化后仍未通过校验: %s", exc)
            # Drop every optional complex field, but retain the explicit
            # model-authored core claim and raw output for later inspection.
            minimal = {
                "diagnostic_status": payload.get("diagnostic_status", "inconclusive"),
                "phenomenon": self._tolerant_text(payload.get("phenomenon")),
                "root_cause": root_cause,
                "root_cause_summary": root_cause,
                "confidence": payload.get("confidence", 0.5),
                "confidence_reason": payload.get("confidence_reason"),
                "llm_raw_analysis": raw[:RCA_RAW_OUTPUT_MAX_CHARS],
            }
            try:
                recovered = RCAOutput.model_validate(minimal).model_dump()
                warnings.append(
                    "optional_fields: unrecoverable fields dropped; core RCA preserved"
                )
            except Exception as core_exc:
                logger.warning("⚠️ [rca] tolerant 核心 RCA 仍未通过校验: %s", core_exc)
                return None

        recovered["structured_quality"] = "partial"
        recovered["structured_output_mode"] = "tolerant"
        recovered["parse_warnings"] = list(dict.fromkeys(warnings))
        return recovered

    @classmethod
    def _compact_text_value(cls, value: Any, limit: int = RCA_TEXT_FIELD_LIMIT) -> Any:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + f"\n... 截断，原始 {len(text)} 字符"

    @classmethod
    def _compact_nested_value(cls, value: Any, limit: int = RCA_TEXT_FIELD_LIMIT) -> Any:
        if isinstance(value, str):
            return cls._compact_text_value(value, limit=limit)
        if isinstance(value, list):
            compacted = [cls._compact_nested_value(item, limit=limit) for item in value[:RCA_LIST_LIMIT]]
            if len(value) > RCA_LIST_LIMIT:
                compacted.append(f"... 截断，原始 {len(value)} 项")
            return compacted
        if isinstance(value, dict):
            return {
                str(k): cls._compact_nested_value(v, limit=limit)
                for k, v in value.items()
            }
        return value

    @classmethod
    def _sanitize_rca_result(cls, rca_result: Dict[str, Any]) -> Dict[str, Any]:
        """Bound RCA handoff size without changing diagnostic semantics.

        RCA should hand off conclusions, causal links and concise evidence
        references. Full raw evidence remains available in evidence archives and
        should not be copied into rca_analysis, otherwise conclusion receives the
        same large facts twice and loses prompt focus.
        """
        if not isinstance(rca_result, dict):
            return {}

        sanitized: Dict[str, Any] = {}
        for key, value in rca_result.items():
            if key in {"evidence_inventory", "evidence_analysis"} and isinstance(value, list):
                sanitized[key] = [
                    cls._compact_nested_value(item, limit=RCA_TEXT_FIELD_LIMIT)
                    for item in value[:RCA_LIST_LIMIT]
                ]
                if len(value) > RCA_LIST_LIMIT:
                    sanitized[key].append({"summary": f"... 截断，原始 {len(value)} 项"})
            elif key == "llm_raw_analysis":
                sanitized[key] = cls._compact_text_value(value, limit=RCA_TEXT_FIELD_LIMIT)
            else:
                sanitized[key] = cls._compact_nested_value(value, limit=RCA_TEXT_FIELD_LIMIT)

        try:
            original_size = len(json.dumps(rca_result, ensure_ascii=False, default=str))
            compact_size = len(json.dumps(sanitized, ensure_ascii=False, default=str))
            if compact_size < original_size:
                logger.info(
                    "📦 [rca] 输出上下文裁剪: %d → %d chars (%.0f%%)",
                    original_size,
                    compact_size,
                    compact_size / max(original_size, 1) * 100,
                )
        except Exception:
            pass
        return sanitized

    def _build_llm_fallback(
        self,
        question: str,
        layer: Optional[Layer],
        reason: str,
    ) -> Dict:
        """LLM 不可用或未返回有效结构化结果时的通用低置信度回退。"""
        layer_str = layer.value if layer else "ABNORMAL"
        question_short = truncate_question(question)
        return {
            "diagnostic_status": "inconclusive",
            "phenomenon": question_short,
            "evidence_analysis": [],
            "causal_chain": {
                "trigger": "LLM 未生成可靠因果链",
                "mechanism": "缺少可用的结构化根因分析结果",
                "manifestation": question_short
            },
            "root_cause": f"[{layer_str}层] 当前无法基于 LLM 输出确定根本原因",
            "root_cause_summary": f"[{layer_str}层] 当前无法基于 LLM 输出确定根本原因",
            "supporting_fact_ids": [],
            "contradicting_fact_ids": [],
            "unknowns": [reason],
            "hypotheses": [],
            "confidence": 0.1,
            "confidence_reason": reason,
            "alternative_causes": []
        }

    def _validate_rca_result_against_evidence(
        self,
        rca_result: Dict[str, Any],
        evidence_analysis: Any,
        *,
        question: str,
        layer: Optional[Layer],
    ) -> Dict[str, Any]:
        fact_ledgers = extract_fact_ledgers_from_evidence_analysis(evidence_analysis)
        if not fact_ledgers:
            return rca_result
        validation_ledgers = (
            extract_fact_ledger_inputs_from_evidence_analysis(
                evidence_analysis
            )
            or fact_ledgers
        )
        authoritative_entity_ids = list(dict.fromkeys(
            entity_id
            for ledger in fact_ledgers
            for entity_id in ledger.scope_entity_ids
            if str(entity_id).lower().startswith("k8s.pod:")
        ))
        try:
            return validate_rca_claims(
                rca_result,
                validation_ledgers,
                authoritative_entity_ids=authoritative_entity_ids,
            )
        except Exception as exc:
            logger.warning(
                "⚠️ [rca] Fact Ledger 引用校验失败，仅降级根因 claim: %s",
                exc,
            )
            preserved = self._sanitize_rca_result(rca_result)
            rejected_claim = {
                "phenomenon": preserved.get("phenomenon"),
                "root_cause": preserved.get("root_cause"),
                "root_cause_summary": preserved.get("root_cause_summary"),
                "causal_chain": preserved.get("causal_chain") or {},
                "confidence": preserved.get("confidence"),
                "confidence_reason": preserved.get("confidence_reason"),
            }
            reason = f"RCA 事实引用校验执行失败: {exc}"
            preserved.update({
                "diagnostic_status": "inconclusive",
                "root_cause": "现有事实不足以发布经过校验的根因结论",
                "root_cause_summary": "现有事实不足以发布经过校验的根因结论",
                "causal_chain": {},
                "confidence": min(float(preserved.get("confidence") or 0.0), 0.49),
                "confidence_reason": reason,
            })
            unknowns = list(preserved.get("unknowns") or [])
            if reason not in unknowns:
                unknowns.append(reason)
            preserved["unknowns"] = unknowns
            preserved["claim_validation"] = {
                "enabled": True,
                "valid": False,
                "reference_valid": False,
                "diagnosis_supported": False,
                "diagnosis_publishable": False,
                "diagnostic_status": "inconclusive",
                "valid_supporting_fact_ids": [],
                "valid_contradicting_fact_ids": [],
                "invalid_fact_ids": [],
                "reasons": [str(exc)],
                "rejected_claim": rejected_claim,
                "legacy_contract": any(
                    ledger.legacy_contract for ledger in fact_ledgers
                ),
            }
            return preserved
    
    def _build_decision(
        self,
        layer: Optional[Layer],
        evidence_items: List[EvidenceItem],
        rca_result: Dict
    ) -> DeterministicDecision:
        """构建决策对象"""
        collected = [e for e in evidence_items if e.collected]
        missing = [e for e in evidence_items if not e.collected]

        confidence_score = rca_result.get("confidence", 0.5)
        confidence = Confidence.from_score(confidence_score)

        # QUERY 模式：非故障，issue_found=False
        is_query = layer == Layer.QUERY

        return DeterministicDecision(
            layer=layer or Layer.ABNORMAL,
            scenario=rca_result.get("phenomenon", "")[:50],
            category="DataQuery" if is_query else "LLMAnalysis",
            confidence=confidence,
            confidence_score=confidence_score,
            issue_found=not is_query,
            issue_summary=rca_result.get("root_cause", ""),
            context={},
            matched_rules=[],
            excluded_rules=[],
            collected_evidence=[e.id for e in collected],
            missing_evidence=[e.description for e in missing],
            critical_missing=[
                e.description for e in missing 
                if e.level == EvidenceLevel.CRITICAL
            ],
            evidence_details=[],
            causal_chain=rca_result.get("causal_chain", {}),
            remediation_steps=[],
            verification_steps=[],
            next_steps=[],
            facts=[]
        )

    @classmethod
    def _compact_quality_contract(
        cls,
        value: Dict[str, Any],
        *,
        max_chars: int,
    ) -> str:
        quality_keys = (
            "source_coverage",
            "case_target_coverage",
            "detail_retrieval",
            "diagnostic_sufficiency_summary",
            "unresolved_questions",
        )
        quality_contract = {
            key: value.get(key)
            for key in quality_keys
        }
        minimum_contract = {
            key: (
                []
                if isinstance(quality_contract[key], list)
                else {}
                if isinstance(quality_contract[key], dict)
                else None
            )
            for key in quality_keys
        }
        minimum_text = json.dumps(
            minimum_contract,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        if len(minimum_text) > max_chars:
            raise ValueError(
                "quality contract field envelope exceeds RCA quality budget"
            )

        field_budget = max(
            2,
            (max_chars - len(minimum_text)) // len(quality_keys),
        )
        while True:
            compacted: Dict[str, Any] = {}
            for key in quality_keys:
                field_text = bounded_json_dumps(
                    quality_contract[key],
                    max_chars=field_budget,
                    indent=2,
                )
                compacted[key] = json.loads(field_text)

            rendered = json.dumps(
                compacted,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            if len(rendered) <= max_chars:
                return rendered
            if field_budget <= 2:
                return minimum_text
            overflow_per_field = max(
                1,
                (len(rendered) - max_chars) // len(quality_keys) + 1,
            )
            field_budget = max(2, field_budget - overflow_per_field)

    def _extract_tool_data_for_rca(
        self,
        evidence_analysis: str,
        *,
        max_chars: int = RCA_TOOL_CONTEXT_MAX_CHARS,
    ) -> str:
        """
        从 evidence_analysis JSON 中提取工具采集的真实数据，
        供 RCA prompt 使用，确保根因分析基于实际数据。
        """
        try:
            data = json.loads(evidence_analysis) if isinstance(evidence_analysis, str) else evidence_analysis
            if not isinstance(data, dict):
                return ""

            if max_chars < 2:
                return ""
            sections: List[tuple[str, str]] = []

            quality_keys = (
                "source_coverage",
                "case_target_coverage",
                "detail_retrieval",
                "diagnostic_sufficiency_summary",
                "unresolved_questions",
            )
            quality_values = {
                key: data.get(key)
                for key in quality_keys
            }
            if any(
                value not in (None, {}, [])
                for value in quality_values.values()
            ):
                quality_budget = min(
                    RCA_QUALITY_MAX_CHARS,
                    max(2, max_chars // 4),
                )
                quality_text = self._compact_quality_contract(
                    quality_values,
                    max_chars=quality_budget,
                )
                sections.append((
                    "## 证据质量合同",
                    "source_coverage/case_target_coverage 只表示采集覆盖，"
                    "不能替代 diagnostic_sufficiency；未回答问题必须进入结论限制。\n"
                    + quality_text,
                ))

            tool_data = data.get("tool_data", [])
            if not isinstance(tool_data, list):
                tool_data = []
            selected_tool_data = select_tool_data_for_rca(
                tool_data,
                supplementary_limit=10,
            )
            fact_ledgers = extract_fact_ledgers_from_tool_data(
                selected_tool_data
            )

            if fact_ledgers:
                ledger_budget = min(
                    RCA_FACT_LEDGER_MAX_CHARS,
                    max(
                        2,
                        max_chars
                        - sum(len(title) + len(content) + 4 for title, content in sections)
                        - 512,
                    ),
                )
                sections.append((
                    "## AIOps Fact Ledger",
                    compact_fact_ledgers_json(
                        fact_ledgers,
                        max_chars=ledger_budget,
                    ),
                ))
                supplementary = [
                    item
                    for item in selected_tool_data
                    if item.get("fact_ledger") is None
                ]
                if supplementary:
                    supplementary_budget = min(
                        RCA_SUPPLEMENTARY_MAX_CHARS,
                        max(
                            2,
                            max_chars
                            - sum(
                                len(title) + len(content) + 4
                                for title, content in sections
                            )
                            - 128,
                        ),
                    )
                    sections.append((
                        "## 补充工具输出",
                        self._compact_supplementary_tool_data(
                            supplementary,
                            max_chars=supplementary_budget,
                        ),
                    ))
                return self._join_rca_sections(
                    sections,
                    max_chars=max_chars,
                )

            # 1. LLM 的分析文本（包含工具调用结果的总结）
            llm_analysis = data.get("llm_analysis", "")
            if llm_analysis:
                sections.append((
                    "## LLM 证据分析",
                    self._compact_text_value(llm_analysis, limit=2000),
                ))

            # 2. MCP 工具的原始输出
            if selected_tool_data:
                current_size = sum(
                    len(title) + len(content) + 4
                    for title, content in sections
                )
                supplementary_budget = max(
                    2,
                    min(
                        RCA_SUPPLEMENTARY_MAX_CHARS,
                        max_chars - current_size - 128,
                    ),
                )
                sections.extend(
                    self._compact_supplementary_tool_sections(
                        selected_tool_data,
                        max_chars=supplementary_budget,
                    )
                )

            return self._join_rca_sections(
                sections,
                max_chars=max_chars,
            )
        except (json.JSONDecodeError, TypeError):
            return ""

    @classmethod
    def _compact_supplementary_tool_data(
        cls,
        items: List[Dict[str, Any]],
        *,
        max_chars: int,
    ) -> str:
        identity_index = cls._build_supplementary_identity_index(items)
        minimum_payload: Dict[str, Any] = {"supplementary_tool_data": []}
        if identity_index:
            minimum_payload["supplementary_identity_index"] = identity_index
        minimum_text = json.dumps(
            minimum_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        if len(minimum_text) > max_chars:
            if identity_index:
                raise ValueError(
                    "supplementary identity index exceeds RCA budget: "
                    f"{len(minimum_text)} > {max_chars}"
                )
            return "{}"

        def build_projection(
            item: Dict[str, Any],
            *,
            representation_limit: int,
        ) -> Dict[str, Any]:
            projected: Dict[str, Any] = {
                key: item.get(key)
                for key in (
                    "tool",
                    "status",
                    "semantic_success",
                    "dimension",
                    "source_system",
                    "coverage",
                    "purpose",
                    "raw_ref",
                    "structured_ref",
                    "summary_ref",
                )
                if item.get(key) not in (None, "", {}, [])
            }
            if representation_limit <= 0:
                return projected
            if item.get("agent_facts"):
                projected["agent_facts"] = cls._compact_text_value(
                    item.get("agent_facts"),
                    limit=representation_limit,
                )
            elif item.get("agent_context"):
                raw_context = item.get("agent_context")
                if isinstance(raw_context, str):
                    try:
                        raw_context = json.loads(raw_context)
                    except (json.JSONDecodeError, TypeError):
                        pass
                if isinstance(raw_context, (dict, list)):
                    projected["agent_context"] = json.loads(
                        bounded_json_dumps(
                            raw_context,
                            max_chars=max(2, representation_limit),
                        )
                    )
                else:
                    projected["agent_context"] = cls._compact_text_to_chars(
                        raw_context,
                        max_chars=representation_limit,
                    )
            else:
                projected["data"] = cls._compact_text_to_chars(
                    item.get("data", ""),
                    max_chars=representation_limit,
                )
            return projected

        def render(representation_limit: int) -> str:
            payload: Dict[str, Any] = {
                "supplementary_tool_data": [
                    build_projection(
                        item,
                        representation_limit=representation_limit,
                    )
                    for item in items
                ],
            }
            if identity_index:
                payload["supplementary_identity_index"] = identity_index
            return json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )

        metadata_only = render(0)
        if len(metadata_only) > max_chars:
            return minimum_text

        low = 0
        high = 1200
        best = metadata_only
        while low <= high:
            middle = (low + high) // 2
            candidate = render(middle)
            if len(candidate) <= max_chars:
                best = candidate
                low = middle + 1
            else:
                high = middle - 1
        return best

    @classmethod
    def _build_supplementary_identity_index(
        cls,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        identities: List[Dict[str, Any]] = []
        seen = set()
        for item in items:
            identity = cls._supplementary_identity_envelope(item)
            if not identity:
                continue
            serialized = json.dumps(
                identity,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            if serialized in seen:
                continue
            seen.add(serialized)
            identities.append(identity)
        return identities

    @staticmethod
    def _supplementary_identity_envelope(
        item: Mapping[str, Any],
    ) -> Dict[str, Any]:
        raw_identity = item.get("identity_envelope")
        if not isinstance(raw_identity, Mapping):
            raw_context = item.get("agent_context")
            if isinstance(raw_context, str):
                try:
                    raw_context = json.loads(raw_context)
                except (json.JSONDecodeError, TypeError):
                    raw_context = None
            raw_identity = raw_context if isinstance(raw_context, Mapping) else {}

        identity: Dict[str, Any] = {}
        case_id = str(raw_identity.get("case_id") or "").strip()
        if case_id:
            identity["case_id"] = case_id

        primary = raw_identity.get("primary_entity")
        if isinstance(primary, Mapping):
            compact_primary = {
                key: primary.get(key)
                for key in ("kind", "namespace", "name", "uid")
                if primary.get(key) not in (None, "")
            }
            if compact_primary:
                identity["primary_entity"] = compact_primary
        return identity

    @classmethod
    def _compact_supplementary_tool_sections(
        cls,
        items: List[Dict[str, Any]],
        *,
        max_chars: int,
    ) -> List[tuple[str, str]]:
        fact_blocks: List[str] = []
        context_blocks: List[str] = []
        raw_blocks: List[str] = []

        for index, item in enumerate(items, 1):
            tool = str(item.get("tool") or "unknown")
            if item.get("agent_facts"):
                fact_parts = [f"[{tool}]"]
                fact_parts.append(str(item.get("agent_facts")).strip())
                fact_blocks.append("\n".join(fact_parts))
                continue
            if item.get("agent_context"):
                context = item.get("agent_context")
                if isinstance(context, str):
                    try:
                        context = json.loads(context)
                    except (json.JSONDecodeError, TypeError):
                        context = context.strip()
                if isinstance(context, (dict, list)):
                    context = json.dumps(
                        context,
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                        default=str,
                    )
                context_blocks.append(f"[{tool}]\n{context}")
                continue
            raw = cls._compact_text_value(
                item.get("data", ""),
                limit=500,
            )
            if raw:
                raw_blocks.append(f"{index}. [{tool}]: {raw}")

        optional_groups = [
            (
                "## AIOps 确定性可观测事实",
                "\n".join(fact_blocks),
            ),
            (
                "## AIOps 结构化可观测性上下文",
                "\n".join(context_blocks),
            ),
            (
                "## 工具原始输出",
                "\n".join(raw_blocks),
            ),
        ]
        optional_groups = [
            (title, content)
            for title, content in optional_groups
            if content
        ]

        groups: List[tuple[str, str]] = []
        identity_index = cls._build_supplementary_identity_index(items)
        if identity_index:
            identity_text = json.dumps(
                {"supplementary_identity_index": identity_index},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            identity_title = "## AIOps 补充实体索引"
            identity_chars = len(identity_title) + 1 + len(identity_text)
            if identity_chars > max_chars:
                raise ValueError(
                    "supplementary identity index exceeds RCA budget: "
                    f"{identity_chars} > {max_chars}"
                )
            groups.append((identity_title, identity_text))

        if not optional_groups:
            return groups

        used_chars = sum(
            len(title) + 1 + len(content)
            for title, content in groups
        )
        if groups:
            used_chars += len(groups) - 1

        selected_optional: List[tuple[str, str]] = []
        for title, content in optional_groups:
            minimum_addition = (1 if groups or selected_optional else 0) + len(title) + 2
            if used_chars + minimum_addition > max_chars:
                continue
            selected_optional.append((title, content))
            used_chars += minimum_addition

        if not selected_optional:
            return groups

        all_groups = groups + selected_optional
        fixed_chars = (
            sum(len(title) + 1 for title, _content in all_groups)
            + len(all_groups)
            - 1
        )
        content_budget = max_chars - fixed_chars
        identity_content_chars = sum(
            len(content)
            for title, content in groups
            if title == "## AIOps 补充实体索引"
        )
        optional_content_budget = content_budget - identity_content_chars
        if optional_content_budget < len(selected_optional):
            return groups

        base_share = optional_content_budget // len(selected_optional)
        allocations = [
            min(len(content), base_share)
            for _title, content in selected_optional
        ]
        remaining = optional_content_budget - sum(allocations)
        for index, (_title, content) in enumerate(selected_optional):
            if remaining <= 0:
                break
            extra = min(len(content) - allocations[index], remaining)
            allocations[index] += extra
            remaining -= extra

        groups.extend([
            (
                title,
                cls._compact_text_to_chars(
                    content,
                    max_chars=allocations[index],
                ),
            )
            for index, (title, content) in enumerate(selected_optional)
        ])
        if not groups:
            return []
        return groups

    @staticmethod
    def _compact_text_to_chars(value: Any, *, max_chars: int) -> str:
        text = str(value or "").strip()
        if len(text) <= max_chars:
            return text
        marker = f"\n... 截断，原始 {len(text)} 字符"
        if len(marker) >= max_chars:
            return marker[:max_chars]
        prefix_chars = max_chars - len(marker)
        return text[:prefix_chars].rstrip() + marker

    @staticmethod
    def _join_rca_sections(
        sections: List[tuple[str, str]],
        *,
        max_chars: int,
    ) -> str:
        rendered: List[str] = []
        used = 0
        for title, content in sections:
            block = f"{title}\n{content}".strip()
            separator = "\n" if rendered else ""
            if used + len(separator) + len(block) > max_chars:
                continue
            rendered.append(block)
            used += len(separator) + len(block)
        return "\n".join(rendered)
