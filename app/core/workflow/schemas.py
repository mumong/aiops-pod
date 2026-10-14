"""Structured workflow contracts for LLM boundary outputs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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
    "configuration",
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


class GroupEntity(BaseModel):
    kind: str = "Pod"
    namespace: str = ""
    name: str = ""


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

    @field_validator("source_system", mode="before")
    @classmethod
    def normalize_source_system(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        source_system = value.strip()
        if not source_system:
            raise ValueError("source_system must not be blank")
        return source_system

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
