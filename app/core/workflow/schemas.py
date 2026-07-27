"""Structured workflow contracts for LLM boundary outputs."""

from __future__ import annotations

import re

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


EvidenceLevelName = Literal["critical", "important", "optional", "reference"]
FactDimension = Literal[
    "kubernetes",
    "metrics",
    "logging",
    "tracing",
    "topology",
    "coverage",
]
FactTypeName = Literal[
    "state",
    "measurement",
    "event",
    "log",
    "span",
    "flow",
    "relationship",
    "coverage",
]
FactDirectness = Literal["direct", "derived", "related_context"]
FactConfidence = Literal["high", "medium", "low", "weak"]
FactStrength = Literal["critical", "strong", "supporting", "context"]
EvidenceToolName = Literal[
    "kubectl_describe",
    "kubectl_get_by_name",
    "kubectl_get_by_kind_in_namespace",
    "kubectl_get_by_kind_in_cluster",
    "kubectl_find_resource",
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
    "kubernetes_jq_query",
    "kubernetes_tabular_query",
    "kubernetes_count",
    "get_prometheus_target",
    "kubectl_lineage_children",
    "kubectl_lineage_parents",
    "run_bash_command",
    "kubectl_run_image",
    "list_prometheus_rules",
    "get_metric_names",
    "get_label_values",
    "get_all_labels",
    "get_series",
    "get_metric_metadata",
    "execute_prometheus_instant_query",
    "execute_prometheus_range_query",
    "execute_pod_promql",
    "query_pod_logs",
    "query_pod_tracing",
    "query_pod_topology",
    "fetch_runbook",
    "collect_aiops_case",
    "get_aiops_case",
    "get_aiops_case_evidence",
    "search_aiops_cases",
    "resolve_aiops_entity",
    "query_aiops_k8s_snapshot",
    "query_aiops_metrics",
    "query_aiops_logs",
    "query_aiops_deepflow_flows",
    "build_aiops_topology",
]


class PodRef(BaseModel):
    name: str = ""
    namespace: str = ""
    status: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_ref(cls, value: Any) -> Any:
        if isinstance(value, str):
            text = value.strip()
            if "/" in text:
                namespace, name = text.split("/", 1)
                return {"namespace": namespace, "name": name}
            return {"name": text}
        return value

    @model_validator(mode="after")
    def normalize_empty_status(self) -> "PodRef":
        if self.status == "":
            self.status = None  # type: ignore[assignment]
        return self


class EntityRef(BaseModel):
    type: str = ""
    name: str = ""
    namespace: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_entity(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"type": "Unknown", "name": value}
        if isinstance(value, dict):
            item = dict(value)
            if "type" not in item and "kind" in item:
                item["type"] = item.get("kind")
            if "name" not in item:
                item["name"] = item.get("value", "")
            return item
        return value


class ScenarioItem(BaseModel):
    scenario: str = ""
    probability: str = ""
    reason: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_scenario(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"scenario": value}
        return value


class GroupEntity(BaseModel):
    kind: str = "Pod"
    namespace: str = ""
    name: str = ""


class IssueGroup(BaseModel):
    group_id: str = ""
    status_keywords: list[str] = Field(default_factory=list)
    pod_abnormal_type: str = ""
    compatible_layers: list[str] = Field(default_factory=list)
    entities: list[GroupEntity] = Field(default_factory=list)
    evidence_plan: list[dict[str, Any]] = Field(default_factory=list)
    possible_scenarios: list[ScenarioItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_entities(cls, value: Any) -> Any:
        if isinstance(value, dict):
            item = dict(value)
            if "entities" not in item and "primary_entities" in item:
                item["entities"] = item.get("primary_entities") or []
            item.pop("primary_entities", None)
            item.pop("is_primary", None)
            return item
        return value


class CurrentAbnormalSummary(BaseModel):
    source: str = ""
    status_counts: dict[str, int] = Field(default_factory=dict)
    total_abnormal: int = 0
    selected_rows: list[str] = Field(default_factory=list)
    raw_ref: str | None = None
    summary_ref: str | None = None
    structured_ref: str | None = None


class LayerOutput(BaseModel):
    layer: str
    derived_layer: str = ""
    layers: list[str] = Field(default_factory=list)
    layer_name: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str
    abnormal_pods: list[PodRef] = Field(default_factory=list)
    pod_status_keyword: str = ""
    pod_abnormal_type: str = ""
    status_category: str = ""
    key_entities: list[EntityRef] = Field(default_factory=list)
    possible_scenarios: list[ScenarioItem] = Field(default_factory=list)
    query_result: dict[str, Any] | None = None
    full_analysis: str = ""

    @field_validator("layers", mode="before")
    @classmethod
    def normalize_layers(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


class LayerHandoff(BaseModel):
    diagnosis_scope: str = "question_scope"
    layer: str = ""
    derived_layer: str = ""
    layers: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    primary_problem: str = ""
    abnormal_pods: list[PodRef] = Field(default_factory=list)
    abnormal_groups: list[IssueGroup] = Field(default_factory=list)
    issue_groups: list[IssueGroup] = Field(default_factory=list)
    current_abnormal_summary: CurrentAbnormalSummary = Field(default_factory=CurrentAbnormalSummary)
    pod_status_keyword: str = ""
    pod_abnormal_type: str = ""
    status_category: str = ""
    active_entities: list[EntityRef] = Field(default_factory=list)
    active_signals: list[dict[str, Any]] = Field(default_factory=list)
    possible_scenarios: list[ScenarioItem] = Field(default_factory=list)
    matched_runbooks: list[str] = Field(default_factory=list)
    must_verify: list[str] = Field(default_factory=list)
    do_not_change: list[str] = Field(default_factory=list)
    archive_ref: str | None = None

    @field_validator("layers", mode="before")
    @classmethod
    def normalize_layers(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


class QueryColumn(BaseModel):
    key: str
    label: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_column(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"key": value, "label": value}
        if isinstance(value, dict) and "key" not in value and "name" in value:
            item = dict(value)
            item["key"] = str(item.get("name") or "")
            item.setdefault("label", item["key"])
            return item
        return value

    @model_validator(mode="after")
    def default_label(self) -> "QueryColumn":
        if not self.label:
            self.label = self.key
        return self


class QueryMissingItem(BaseModel):
    field: str = "result"
    reason: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_missing(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"field": "result", "reason": value}
        return value


class QuerySource(BaseModel):
    tool: str = "-"
    query: str = "-"

    @model_validator(mode="before")
    @classmethod
    def normalize_source(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"tool": "-", "query": value}
        if isinstance(value, dict):
            item = dict(value)
            if "tool" not in item and "type" in item:
                item["tool"] = str(item.get("type") or "-")
            return item
        return value


class QueryResult(BaseModel):
    query_target: str = ""
    collection_summary: str = ""
    columns: list[QueryColumn] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    missing: list[QueryMissingItem] = Field(default_factory=list)
    sources: list[QuerySource] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_query_result(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        item = dict(value)

        summary = item.get("collection_summary")
        if isinstance(summary, dict):
            item["collection_summary"] = "; ".join(
                f"{key}={val}" for key, val in summary.items()
            )
        elif summary is not None and not isinstance(summary, str):
            item["collection_summary"] = str(summary)

        for key in ("notes", "missing", "sources"):
            val = item.get(key)
            if val is None or isinstance(val, list):
                continue
            item[key] = [val]

        columns = item.get("columns")
        if isinstance(columns, dict):
            item["columns"] = [
                {"key": str(key), "label": str(value)}
                for key, value in columns.items()
            ]
        return item


class EvidencePlanItem(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    level: EvidenceLevelName = "important"
    tool: EvidenceToolName
    command: str = Field(min_length=1)
    tool_args: dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""
    evidence_type: str = ""
    target_scope: str = ""
    acceptable_tools: list[EvidenceToolName] = Field(default_factory=list)
    counts_for_completeness: bool = True


class EvidencePlanOutput(BaseModel):
    layer: str = ""
    evidence_plan: list[EvidencePlanItem] = Field(default_factory=list)
    collection_strategy: str = ""


class ToolObservationCandidate(BaseModel):
    index: int
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    structured: dict[str, Any] = Field(default_factory=dict)
    result_preview: str = ""
    raw_ref: str | None = None
    summary_ref: str | None = None
    structured_ref: str | None = None


class ToolObservationSummary(BaseModel):
    summary: str = ""
    key_facts: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    raw_ref: str = ""


class FactRecord(BaseModel):
    fact_id: str = Field(pattern=r"^fact-[A-Za-z0-9_-]{8,64}$")
    entity_id: str = Field(min_length=1)
    entity_kind: str = Field(min_length=1)
    namespace: str | None = None
    entity_name: str | None = None
    dimension: FactDimension
    fact_type: FactTypeName
    attribute: str = Field(min_length=1)
    value: Any
    unit: str | None = None
    timestamp: str | None = None
    start: str | None = None
    end: str | None = None
    source_system: str = Field(min_length=1)
    directness: FactDirectness
    confidence: FactConfidence
    strength: FactStrength | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_evidence_semantics(self) -> "FactRecord":
        if self.directness == "related_context" and self.confidence == "high":
            raise ValueError("related_context facts cannot have high confidence")
        if self.fact_type != "coverage" and not self.evidence_refs:
            raise ValueError("non-coverage facts require evidence_refs")
        return self


class FactLedger(BaseModel):
    contract_version: Literal["aiops.fact-ledger.v1"] = "aiops.fact-ledger.v1"
    case_id: str = Field(min_length=1)
    scope_entity_ids: list[str] = Field(min_length=1)
    records: list[FactRecord] = Field(default_factory=list)
    record_count: int = Field(default=0, ge=0)
    truncated: bool = False
    source: Literal["mcp_canonical", "robusta_legacy_adapter"]
    legacy_contract: bool = False

    @model_validator(mode="after")
    def normalize_record_count(self) -> "FactLedger":
        self.scope_entity_ids = list(dict.fromkeys(
            entity_id for entity_id in self.scope_entity_ids if entity_id
        ))
        if not self.scope_entity_ids:
            raise ValueError("Fact Ledger requires at least one scope entity")
        self.record_count = len(self.records)
        return self


class RCAHypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=1)
    entity_id: str | None = Field(default=None, min_length=1)
    summary: str = Field(min_length=1)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    contradicting_fact_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class EvidenceMatchItem(BaseModel):
    plan_id: str = Field(min_length=1)
    tool_result_index: int | None = None
    matched: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class EvidenceMatchOutput(BaseModel):
    matches: list[EvidenceMatchItem] = Field(default_factory=list)
    unmatched_plan_ids: list[str] = Field(default_factory=list)
    unplanned_tool_result_indexes: list[int] = Field(default_factory=list)


class EvidenceCollectionOutput(BaseModel):
    evidence_plan: list[EvidencePlanItem] = Field(default_factory=list)
    tool_results: list[str] = Field(default_factory=list)
    tool_data: list[dict[str, Any]] = Field(default_factory=list)
    llm_analysis: str = ""
    collection_summary: str = ""
    plan_total: int = Field(ge=0)
    plan_collected: int = Field(ge=0)
    plan_completeness: float = Field(ge=0.0, le=1.0)
    environment_evidence_total: int = Field(ge=0)
    environment_evidence_collected: int = Field(ge=0)
    environment_evidence_completeness: float = Field(ge=0.0, le=1.0)
    executed_tool_count: int = Field(default=0, ge=0)
    matched_tool_count: int = Field(default=0, ge=0)
    unplanned_tool_count: int = Field(default=0, ge=0)
    case_tool_count: int = Field(default=0, ge=0)
    supplemental_tool_count: int = Field(default=0, ge=0)
    skipped_plan_count: int = Field(default=0, ge=0)
    observability_target_total: int = Field(default=0, ge=0)
    observability_target_collected: int = Field(default=0, ge=0)
    observability_target_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    diagnostic_evidence_total: int = Field(default=0, ge=0)
    diagnostic_evidence_collected: int = Field(default=0, ge=0)
    diagnostic_evidence_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    diagnostic_evidence_missing: list[str] = Field(default_factory=list)
    dimension_coverage_total: int = Field(default=0, ge=0)
    dimension_coverage_collected: int = Field(default=0, ge=0)
    dimension_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    diagnostic_sufficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    diagnostic_sufficiency_label: str = ""
    source_coverage: dict[str, Any] = Field(default_factory=dict)
    case_target_coverage: dict[str, Any] = Field(default_factory=dict)
    detail_retrieval: dict[str, Any] = Field(default_factory=dict)
    diagnostic_sufficiency_summary: dict[str, Any] = Field(default_factory=dict)
    unresolved_questions: list[str] = Field(default_factory=list)
    evidence_inventory: list[dict[str, Any]] = Field(default_factory=list)
    missing_reasons: list[str] = Field(default_factory=list)
    early_stop: dict[str, Any] = Field(default_factory=dict)


class ContextCompactionSummary(BaseModel):
    process_summary: list[str] = Field(default_factory=list)
    evidence_plan: list[dict[str, Any]] = Field(default_factory=list)
    completed_items: list[dict[str, Any]] = Field(default_factory=list)
    open_items: list[dict[str, Any]] = Field(default_factory=list)
    key_facts: list[str] = Field(default_factory=list)
    negative_facts: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    discarded_noise: list[str] = Field(default_factory=list)
    next_focus: list[str] = Field(default_factory=list)


class RCAOutput(BaseModel):
    diagnostic_status: Literal["diagnosed", "inconclusive"] = "diagnosed"
    phenomenon: str = ""
    evidence_inventory: list[dict[str, Any]] = Field(default_factory=list)
    evidence_analysis: list[dict[str, Any]] = Field(default_factory=list)
    causal_chain: dict[str, Any] = Field(default_factory=dict)
    root_cause: str = ""
    root_cause_summary: str = ""
    supporting_fact_ids: list[str] = Field(default_factory=list)
    contradicting_fact_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    hypotheses: list[RCAHypothesis] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reason: str = Field(min_length=1)
    claim_validation: dict[str, Any] = Field(default_factory=dict)
    primary_runbooks: list[str] = Field(default_factory=list)
    alternative_causes: list[Any] = Field(default_factory=list)
    limitations: str = ""
    llm_raw_analysis: str = ""

    @model_validator(mode="after")
    def require_and_normalize_root_cause(self) -> "RCAOutput":
        root = (self.root_cause or "").strip()
        summary = (self.root_cause_summary or "").strip()
        if not root and summary:
            self.root_cause = summary
        elif root and not summary:
            self.root_cause_summary = root
        elif root and summary:
            # Downstream historically reads root_cause as the concise final
            # conclusion; prefer the summary when both are present.
            self.root_cause = summary

        if not (self.root_cause or "").strip():
            raise ValueError("RCA output requires root_cause or root_cause_summary")
        if not (self.confidence_reason or "").strip():
            raise ValueError("RCA output requires confidence_reason")
        return self


class ConclusionOutput(BaseModel):
    title: str = ""
    diagnosis_overview: dict[str, Any] = Field(default_factory=dict)
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    root_cause: str = ""
    impact: str = ""
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    markdown_report: str = Field(min_length=1)

    @field_validator("markdown_report")
    @classmethod
    def validate_markdown_report_format(cls, value: str) -> str:
        text = value.strip()
        text = cls._normalize_flattened_markdown(text)
        if "##" not in text:
            raise ValueError("markdown_report must contain Markdown section headings")
        return text

    @staticmethod
    def _normalize_flattened_markdown(text: str) -> str:
        normalized = text
        normalized = re.sub(r"---\s*(?=##)", "---\n", normalized)
        normalized = re.sub(r"\s+(?=#{2,6}\s)", "\n\n", normalized)
        normalized = re.sub(r"(?m)^(#{2,6}\s[^|\n]+?)\s+(\|)", r"\1\n\2", normalized)
        normalized = re.sub(r"\|\s*\|(?=\s*(?:[-: ]+\|)+)", "|\n|", normalized)
        normalized = re.sub(r"\|\s*\|(?=\s*(?:\*\*|`|[^|\s]))", "|\n|", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        normalized = re.sub(r"^---\n\n+(?=##)", "---\n", normalized)
        return normalized.strip()


class QueryConclusionOutput(BaseModel):
    markdown_report: str = Field(
        min_length=1,
        description="面向用户的 Markdown 查询结果，只基于输入中的真实 query_result/tool_data 总结。",
    )
