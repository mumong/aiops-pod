"""Stable, code-owned state for one autonomous diagnosis lane.

The model owns investigation and causal interpretation.  This module owns
identity, append-only fact retention, structural normalization, Fact-reference
validation, and the compact handoff consumed by reporting.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Dict, List, Literal, Mapping, Sequence

from pydantic import BaseModel, Field, field_validator

from app.core.workflow.entity_evidence_snapshot import (
    EntityEvidenceSnapshot,
    build_entity_evidence_snapshot,
)
from app.core.workflow.fact_contract import validate_rca_claims
from app.core.workflow.schemas import RCAOutput


DIAGNOSIS_STATE_CONTRACT_VERSION = "aiops.lane-diagnosis-state.v1"


class DiagnosisSubmission(BaseModel):
    """The only semantic contract the tool-capable diagnosis agent submits."""

    diagnostic_status: Literal["diagnosed", "inconclusive"] = "inconclusive"
    phenomenon: str = ""
    root_cause: str = "证据不足"
    causal_chain: List[str] = Field(default_factory=list)
    supporting_fact_ids: List[str] = Field(default_factory=list)
    contradicting_fact_ids: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_reason: str = "证据边界决定当前置信度"

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower().rstrip("%")
            words = {
                "high": 0.9,
                "medium": 0.6,
                "low": 0.3,
                "高": 0.9,
                "中": 0.6,
                "低": 0.3,
            }
            if normalized in words:
                return words[normalized]
            try:
                number = float(normalized)
                return number / 100 if number > 1 else number
            except ValueError:
                return 0.0
        return value


class EvidenceSlotDiagnosisSubmission(BaseModel):
    """Compact diagnosis whose evidence references are code-owned slots.

    Opaque Fact IDs are deliberately absent from this model-facing contract.
    The caller publishes a bounded, ordered evidence catalogue and maps the
    returned 1-based slots back to authoritative Fact IDs.
    """

    diagnostic_status: Literal["diagnosed", "inconclusive"] = "inconclusive"
    phenomenon: str = ""
    root_cause: str = "证据不足"
    causal_chain: List[str] = Field(default_factory=list)
    supporting_evidence_slots: List[int] = Field(default_factory=list)
    contradicting_evidence_slots: List[int] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_reason: str = "证据边界决定当前置信度"

    _normalize_confidence = field_validator("confidence", mode="before")(
        DiagnosisSubmission.normalize_confidence.__func__
    )


def bind_evidence_slots(
    submission: EvidenceSlotDiagnosisSubmission,
    *,
    slot_fact_ids: Sequence[str],
) -> DiagnosisSubmission:
    """Map model-selected slots to immutable Fact IDs without guessing."""

    def resolve(slots: Sequence[int]) -> List[str]:
        resolved: List[str] = []
        invalid: List[int] = []
        for raw_slot in slots:
            try:
                slot = int(raw_slot)
            except (TypeError, ValueError):
                invalid.append(raw_slot)  # type: ignore[arg-type]
                continue
            if slot < 1 or slot > len(slot_fact_ids):
                invalid.append(slot)
                continue
            fact_id = str(slot_fact_ids[slot - 1]).strip()
            if fact_id and fact_id not in resolved:
                resolved.append(fact_id)
        if invalid:
            raise ValueError(f"evidence slots outside catalogue: {invalid}")
        return resolved

    return DiagnosisSubmission(
        diagnostic_status=submission.diagnostic_status,
        phenomenon=submission.phenomenon,
        root_cause=submission.root_cause,
        causal_chain=list(submission.causal_chain),
        supporting_fact_ids=resolve(submission.supporting_evidence_slots),
        contradicting_fact_ids=resolve(submission.contradicting_evidence_slots),
        unknowns=list(submission.unknowns),
        confidence=submission.confidence,
        confidence_reason=submission.confidence_reason,
    )


def _stable_key(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return deepcopy(dict(value))
    try:
        parsed = json.loads(value) if value else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return deepcopy(parsed) if isinstance(parsed, dict) else {}


def _entity_id(entity: Mapping[str, Any]) -> str:
    namespace = str(entity.get("namespace") or "").strip()
    name = str(entity.get("name") or "").strip()
    uid = str(entity.get("uid") or "").strip()
    if not namespace or not name:
        return ""
    base = f"k8s.pod:{namespace}/{name}"
    return f"{base}:{uid}" if uid else base


def authoritative_entity_ids_from_ledgers(
    ledgers: Sequence[Any],
) -> List[str]:
    """Resolve a name-only Pod scope to its unique source-backed UID.

    Layer discovery can establish only ``namespace/name`` while a later
    Kubernetes observation records the immutable Pod UID.  Prefer that UID
    only when the current snapshot contains exactly one matching identity;
    retain the name-only scope when no UID is available or generations are
    ambiguous so validation continues to fail closed.
    """

    def values(item: Any, key: str) -> Any:
        if isinstance(item, Mapping):
            return item.get(key)
        return getattr(item, key, None)

    scope_ids = list(
        dict.fromkeys(
            str(entity_id).strip()
            for ledger in ledgers
            for entity_id in (values(ledger, "scope_entity_ids") or [])
            if str(entity_id).strip()
        )
    )
    record_ids = {
        str(entity_id).strip()
        for ledger in ledgers
        for record in (values(ledger, "records") or [])
        if (entity_id := values(record, "entity_id"))
        and str(entity_id).strip()
    }

    resolved: List[str] = []
    for scope_id in scope_ids:
        prefix = f"{scope_id}:"
        candidates = {
            record_id
            for record_id in record_ids
            if scope_id.lower().startswith("k8s.pod:")
            and record_id.startswith(prefix)
        }
        resolved.append(next(iter(candidates)) if len(candidates) == 1 else scope_id)
    return list(dict.fromkeys(resolved))


def _inconclusive_rca(reason: str, *, unknowns: Sequence[str] = ()) -> Dict[str, Any]:
    reasons = list(dict.fromkeys([
        str(item).strip()
        for item in [reason, *unknowns]
        if str(item).strip()
    ]))
    payload = RCAOutput(
        diagnostic_status="inconclusive",
        phenomenon="",
        root_cause="证据不足，尚未形成可验证的根因结论",
        root_cause_summary="证据不足，尚未形成可验证的根因结论",
        evidence_inventory=[],
        evidence_analysis=[],
        causal_chain={},
        supporting_fact_ids=[],
        contradicting_fact_ids=[],
        unknowns=reasons,
        hypotheses=[],
        confidence=0.0,
        confidence_reason=reason or "缺少可验证诊断",
        claim_validation={
            "valid": False,
            "reference_valid": False,
            "diagnosis_supported": False,
            "diagnosis_publishable": False,
            "diagnostic_status": "inconclusive",
            "valid_supporting_fact_ids": [],
            "valid_contradicting_fact_ids": [],
            "invalid_fact_ids": [],
            "reasons": reasons,
        },
        primary_runbooks=[],
        alternative_causes=[],
        limitations="；".join(reasons),
        llm_raw_analysis="",
    ).model_dump(mode="json")
    return payload


def submission_to_rca(
    submission: DiagnosisSubmission,
    *,
    authoritative_entity_ids: Sequence[str],
) -> Dict[str, Any]:
    """Expand the minimal model contract into the existing report contract.

    This is structural normalization only: it copies the model's claim and
    references without choosing a cause or inventing a Fact.
    """
    entity_id = next(
        (
            str(item)
            for item in authoritative_entity_ids
            if str(item).lower().startswith("k8s.pod:")
        ),
        str(authoritative_entity_ids[0]) if authoritative_entity_ids else "",
    )
    supporting = list(dict.fromkeys(
        str(item).strip()
        for item in submission.supporting_fact_ids
        if str(item).strip()
    ))
    contradicting = list(dict.fromkeys(
        str(item).strip()
        for item in submission.contradicting_fact_ids
        if str(item).strip()
    ))
    hypotheses = []
    if submission.root_cause.strip() and (supporting or contradicting):
        hypotheses.append({
            "hypothesis_id": "primary",
            "entity_id": entity_id or None,
            "summary": submission.root_cause.strip(),
            "supporting_fact_ids": supporting,
            "contradicting_fact_ids": contradicting,
            "unknowns": list(submission.unknowns),
            "confidence": submission.confidence,
        })
    causal_chain = {
        "steps": [
            str(item).strip()
            for item in submission.causal_chain
            if str(item).strip()
        ]
    }
    payload = RCAOutput(
        diagnostic_status=submission.diagnostic_status,
        phenomenon=submission.phenomenon,
        root_cause=submission.root_cause,
        root_cause_summary=submission.root_cause,
        evidence_inventory=[],
        evidence_analysis=[],
        causal_chain=causal_chain,
        supporting_fact_ids=supporting,
        contradicting_fact_ids=contradicting,
        unknowns=list(submission.unknowns),
        hypotheses=hypotheses,
        confidence=submission.confidence,
        confidence_reason=submission.confidence_reason,
        claim_validation={},
        primary_runbooks=[],
        alternative_causes=[],
        limitations="；".join(submission.unknowns),
        llm_raw_analysis="",
    )
    return payload.model_dump(mode="json")


class LaneDiagnosisState:
    """Append-only owner of Entity, Fact, and Diagnosis for one Pod lane."""

    def __init__(
        self,
        *,
        group_id: str,
        entities: Sequence[Mapping[str, Any]],
        status_keywords: Sequence[str] = (),
    ) -> None:
        self.group_id = str(group_id)
        self.entities = [deepcopy(dict(item)) for item in entities]
        self.status_keywords = [str(item) for item in status_keywords if str(item)]
        self._tool_events: List[Dict[str, Any]] = []
        self._tool_event_keys: set[str] = set()
        self._evidence_analyses: List[Dict[str, Any]] = []
        self._latest_group_state: Dict[str, Any] = {}
        self._snapshot: EntityEvidenceSnapshot | None = None
        self._selected_rca: Dict[str, Any] = _inconclusive_rca(
            "诊断 Agent 尚未提交结果"
        )
        self._attempts: List[Dict[str, Any]] = []

    @property
    def attempt_count(self) -> int:
        return len(self._attempts)

    @property
    def tool_events(self) -> List[Dict[str, Any]]:
        return deepcopy(self._tool_events)

    @property
    def attempts(self) -> List[Dict[str, Any]]:
        return deepcopy(self._attempts)

    @property
    def selected_rca(self) -> Dict[str, Any]:
        return deepcopy(self._selected_rca)

    @property
    def snapshot_handoff(self) -> Dict[str, Any]:
        if self._snapshot is None:
            return build_entity_evidence_snapshot(
                entities=self.entities,
                evidence_analysis={},
                thinking_events=[],
                status_keywords=self.status_keywords,
            ).to_handoff()
        return self._snapshot.to_handoff()

    @property
    def authoritative_entity_ids(self) -> List[str]:
        ids = authoritative_entity_ids_from_ledgers(
            self.snapshot_handoff.get("fact_ledgers") or []
        )
        if ids:
            return ids
        return list(dict.fromkeys(
            entity_id
            for entity in self.entities
            if (entity_id := _entity_id(entity))
        ))

    def _append_tool_events(self, events: Sequence[Mapping[str, Any]]) -> None:
        for event in events:
            if not isinstance(event, Mapping) or event.get("type") != "tool_result":
                continue
            copied = deepcopy(dict(event))
            identity = {
                key: copied.get(key)
                for key in (
                    "tool_name",
                    "tool_args",
                    "status",
                    "semantic_success",
                    "raw_ref",
                    "structured_ref",
                    "summary_ref",
                    "structured",
                    "result",
                )
            }
            key = _stable_key(identity)
            if key in self._tool_event_keys:
                continue
            self._tool_event_keys.add(key)
            self._tool_events.append(copied)

    def _merged_evidence_analysis(self) -> Dict[str, Any]:
        merged = deepcopy(self._evidence_analyses[-1]) if self._evidence_analyses else {}
        tool_data: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for analysis in self._evidence_analyses:
            for item in analysis.get("tool_data") or []:
                if not isinstance(item, Mapping):
                    continue
                copied = deepcopy(dict(item))
                key = _stable_key(copied)
                if key in seen:
                    continue
                seen.add(key)
                tool_data.append(copied)
        merged["tool_data"] = tool_data
        merged["diagnosis_state_contract"] = DIAGNOSIS_STATE_CONTRACT_VERSION
        merged["diagnosis_attempt_count"] = self.attempt_count
        return merged

    def record_attempt(
        self,
        *,
        attempt: int,
        group_state: Mapping[str, Any],
        submission: DiagnosisSubmission | Mapping[str, Any] | None,
        collector_archive_run_id: str = "",
    ) -> Dict[str, Any]:
        """Append one complete agent attempt and validate its submitted claim."""
        self._latest_group_state = deepcopy(dict(group_state))
        self._append_tool_events(group_state.get("thinking_events") or [])
        analysis = _parse_mapping(group_state.get("evidence_analysis") or {})
        if analysis:
            self._evidence_analyses.append(analysis)
        merged_analysis = self._merged_evidence_analysis()
        self._snapshot = build_entity_evidence_snapshot(
            entities=self.entities,
            evidence_analysis=merged_analysis,
            thinking_events=self._tool_events,
            status_keywords=self.status_keywords,
        )

        parsed_submission: DiagnosisSubmission | None
        try:
            parsed_submission = (
                submission
                if isinstance(submission, DiagnosisSubmission)
                else DiagnosisSubmission.model_validate(submission)
                if isinstance(submission, Mapping)
                else None
            )
        except Exception:
            parsed_submission = None

        if parsed_submission is None:
            validated = _inconclusive_rca(
                "诊断 Agent 未提交合法的 DiagnosisSubmission"
            )
        elif not self._snapshot.fact_ledgers:
            validated = _inconclusive_rca(
                "没有可供 Fact 引用校验的权威 Fact Ledger",
                unknowns=parsed_submission.unknowns,
            )
        else:
            candidate = submission_to_rca(
                parsed_submission,
                authoritative_entity_ids=self.authoritative_entity_ids,
            )
            try:
                validated = validate_rca_claims(
                    candidate,
                    self._snapshot.fact_ledgers,
                    authoritative_entity_ids=self.authoritative_entity_ids,
                )
            except Exception as exc:
                validated = _inconclusive_rca(
                    f"DiagnosisSubmission 的 Fact 引用校验失败: {exc}"
                )

        self._selected_rca = deepcopy(validated)
        attempt_record = {
            "diagnosis_attempt": int(attempt),
            "collector_archive_run_id": str(collector_archive_run_id),
            "submission_received": parsed_submission is not None,
            "model_submission": (
                parsed_submission.model_dump(mode="json")
                if parsed_submission is not None
                else None
            ),
            "validated_diagnosis": deepcopy(validated),
            "fact_count": len(self._snapshot.fact_index),
            "tool_result_count": len(self._tool_events),
        }
        self._attempts.append(attempt_record)
        return deepcopy(validated)

    def to_group_state(self) -> Dict[str, Any]:
        state = deepcopy(self._latest_group_state)
        state["thinking_events"] = self.tool_events
        state["evidence_analysis"] = json.dumps(
            self._merged_evidence_analysis(),
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        state["entity_evidence_snapshot"] = self.snapshot_handoff
        state["diagnosis_submission"] = self.selected_rca
        return state

    def rca_update(self) -> Dict[str, Any]:
        snapshot = self.snapshot_handoff
        manifest = (
            snapshot.get("selection_manifest")
            if isinstance(snapshot.get("selection_manifest"), Mapping)
            else {}
        )
        fact_index = (
            snapshot.get("fact_index")
            if isinstance(snapshot.get("fact_index"), Mapping)
            else {}
        )
        selected_ids = [
            str(fact_id)
            for fact_id in (manifest.get("rca_input_fact_ids") or [])
            if str(fact_id) in fact_index
        ]
        claim = self._selected_rca.get("claim_validation")
        if not isinstance(claim, Mapping):
            claim = {"valid": False, "diagnosis_supported": False}
        return {
            "rca_analysis": json.dumps(
                self._selected_rca,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            ),
            "claim_validation": deepcopy(dict(claim)),
            "rca_input_projection": {
                "contract_version": "aiops.rca-input-projection.v1",
                "authoritative_entity_ids": self.authoritative_entity_ids,
                "selection_manifest": deepcopy(dict(manifest)),
                "selected_facts": [
                    deepcopy(dict(fact_index[fact_id]))
                    for fact_id in selected_ids
                    if isinstance(fact_index.get(fact_id), Mapping)
                ],
            },
            "rca_attempts": self.attempts,
        }

    def retry_handoff(self, feedback: Mapping[str, Any]) -> Dict[str, Any]:
        rca_input = self.rca_update()["rca_input_projection"]
        manifest = rca_input["selection_manifest"]
        focus_ids = {
            str(fact_id)
            for fact_id in (feedback.get("focus_fact_ids") or [])
            if str(fact_id).strip()
        }
        ordered_ids = list(dict.fromkeys([
            *(manifest.get("direct_causal_candidate_fact_ids") or []),
            *(manifest.get("required_context_fact_ids") or []),
            *(manifest.get("eligible_support_fact_ids") or []),
            *(manifest.get("rca_input_fact_ids") or []),
        ]))
        fact_by_id = {
            str(fact.get("fact_id") or ""): fact
            for fact in rca_input["selected_facts"]
            if isinstance(fact, Mapping)
        }
        compact_facts: List[Dict[str, Any]] = []
        for fact_id in ordered_ids:
            fact = fact_by_id.get(str(fact_id))
            if not isinstance(fact, Mapping):
                continue
            compact_facts.append({
                "fact_id": str(fact_id),
                "dimension": fact.get("dimension"),
                "evidence_role": fact.get("evidence_role"),
                "attribute": fact.get("attribute"),
                "display_value": fact.get("display_value"),
                "directness": fact.get("directness"),
                "confidence": fact.get("confidence"),
                "focus": str(fact_id) in focus_ids,
            })
            if len(compact_facts) >= 20:
                break
        previous = self.selected_rca
        return {
            "contract_version": DIAGNOSIS_STATE_CONTRACT_VERSION,
            "attempt": self.attempt_count + 1,
            "instruction": (
                "启动一次新的完整工具型诊断。先复用以下代码保留的紧凑 Fact；"
                "只有仍存在因果缺口时才调用新工具，不要重复完全相同的查询。"
            ),
            "validation_feedback": {
                "failure_codes": list(feedback.get("failure_codes") or []),
                "reasons": list(feedback.get("reasons") or []),
                "focus_fact_ids": list(feedback.get("focus_fact_ids") or []),
            },
            "previous_diagnosis": {
                "diagnostic_status": previous.get("diagnostic_status"),
                "phenomenon": previous.get("phenomenon"),
                "root_cause": previous.get("root_cause"),
                "causal_chain": previous.get("causal_chain"),
                "supporting_fact_ids": previous.get("supporting_fact_ids") or [],
                "contradicting_fact_ids": previous.get("contradicting_fact_ids") or [],
                "unknowns": previous.get("unknowns") or [],
            },
            "selection_manifest": {
                "direct_causal_candidate_fact_ids": list(
                    manifest.get("direct_causal_candidate_fact_ids") or []
                ),
                "required_context_fact_ids": list(
                    manifest.get("required_context_fact_ids") or []
                ),
                "unselected_higher_priority_causal_fact_ids": list(
                    manifest.get("unselected_higher_priority_causal_fact_ids")
                    or []
                ),
            },
            "selected_facts": compact_facts,
        }

    def to_handoff(self) -> Dict[str, Any]:
        snapshot = self.snapshot_handoff
        return {
            "contract_version": DIAGNOSIS_STATE_CONTRACT_VERSION,
            "group_id": self.group_id,
            "entities": deepcopy(self.entities),
            "attempt_count": self.attempt_count,
            "tool_result_count": len(self._tool_events),
            "fact_count": len(snapshot.get("fact_index") or {}),
            "fact_ids": list((snapshot.get("fact_index") or {}).keys()),
            "diagnostic_status": self._selected_rca.get(
                "diagnostic_status", "inconclusive"
            ),
        }
