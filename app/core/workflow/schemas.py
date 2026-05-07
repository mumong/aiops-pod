"""Structured workflow contracts for LLM boundary outputs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


EvidenceLevelName = Literal["critical", "important", "optional", "reference"]


class EvidencePlanItem(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    level: EvidenceLevelName = "important"
    tool: str = Field(min_length=1)
    command: str = Field(min_length=1)
    purpose: str = ""


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
    evidence_inventory: list[dict[str, Any]] = Field(default_factory=list)
    missing_reasons: list[str] = Field(default_factory=list)
    early_stop: dict[str, Any] = Field(default_factory=dict)


class RCAOutput(BaseModel):
    phenomenon: str = ""
    evidence_inventory: list[dict[str, Any]] = Field(default_factory=list)
    evidence_analysis: list[dict[str, Any]] = Field(default_factory=list)
    causal_chain: dict[str, Any] = Field(default_factory=dict)
    root_cause: str = ""
    root_cause_summary: str = ""
    confidence: float = Field(default=0.1, ge=0.0, le=1.0)
    confidence_reason: str = ""
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
        return self
