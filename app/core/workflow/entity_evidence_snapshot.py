"""One authoritative per-entity evidence projection for multi-anomaly lanes."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence

from app.core.workflow.fact_contract import (
    extract_fact_ledger_inputs_from_evidence_analysis,
    extract_fact_ledgers_from_evidence_analysis,
)
from app.core.workflow.group_evidence import (
    REQUIRED_DIMENSIONS,
    _append_unique_facts,
    _compact_fact,
    aggregate_group_evidence,
)
from app.core.workflow.schemas import FactLedger, FactRecord


SNAPSHOT_CONTRACT_VERSION = "aiops.entity-evidence-snapshot.v1"
SELECTION_MANIFEST_CONTRACT_VERSION = "aiops.selection-manifest.v2"
DEFAULT_RCA_FACT_LIMIT = 48


class MandatoryEvidenceBudgetError(ValueError):
    """The authoritative facts cannot be retained whole inside the RCA limit."""


@dataclass(frozen=True)
class SelectionManifest:
    """Deterministic record-level accounting for the RCA projection."""

    eligible_support_fact_ids: tuple[str, ...]
    direct_causal_candidate_fact_ids: tuple[str, ...]
    required_context_fact_ids: tuple[str, ...]
    rca_input_fact_ids: tuple[str, ...]
    omitted_fact_ids: tuple[str, ...]
    omission_reasons: Mapping[str, str]
    contract_version: str
    max_facts: int
    total_fact_count: int
    overflowed: bool
    representative_of: Mapping[str, tuple[str, ...]]
    unselected_higher_priority_causal_fact_ids: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eligible_support_fact_ids": list(self.eligible_support_fact_ids),
            "direct_causal_candidate_fact_ids": list(
                self.direct_causal_candidate_fact_ids
            ),
            "required_context_fact_ids": list(self.required_context_fact_ids),
            "rca_input_fact_ids": list(self.rca_input_fact_ids),
            "omitted_fact_ids": list(self.omitted_fact_ids),
            "omission_reasons": dict(self.omission_reasons),
            "contract_version": self.contract_version,
            "max_facts": self.max_facts,
            "total_fact_count": self.total_fact_count,
            "overflowed": self.overflowed,
            "representative_of": {
                fact_id: list(equivalent_fact_ids)
                for fact_id, equivalent_fact_ids in self.representative_of.items()
            },
            "unselected_higher_priority_causal_fact_ids": list(
                self.unselected_higher_priority_causal_fact_ids
            ),
        }


def classify_fact_evidence_role(record: Mapping[str, Any]) -> str:
    """Classify generic source semantics without workload/case knowledge."""
    metadata = (
        record.get("metadata")
        if isinstance(record.get("metadata"), Mapping)
        else {}
    )
    dimension = str(record.get("dimension") or "").strip().lower()
    fact_type = str(record.get("fact_type") or "").strip().lower()
    attribute = str(record.get("attribute") or "").strip().lower()
    directness = str(record.get("directness") or "").strip().lower()
    confidence = str(record.get("confidence") or "").strip().lower()
    strength = str(record.get("strength") or "").strip().lower()
    labels = (
        metadata.get("labels")
        if isinstance(metadata.get("labels"), Mapping)
        else {}
    )
    valid_roles = {
        "causal_candidate",
        "symptom",
        "contradicting",
        "context",
        "negative_observation",
    }
    # Evidence producers know more about a record than this generic fallback.
    # Preserve their structured role across snapshots and compression; only
    # infer a role when the producer did not provide one.
    explicit = str(
        record.get("evidence_role")
        or metadata.get("evidence_role")
        or ""
    ).strip().lower()
    if explicit in valid_roles:
        return explicit
    try:
        numeric_value = float(record.get("value"))
    except (TypeError, ValueError):
        numeric_value = None
    categorical_labels = {
        str(key).strip().lower()
        for key, value in labels.items()
        if value not in (None, "")
    }
    if (
        dimension == "metrics"
        and numeric_value == 0.0
        and categorical_labels
        & {"condition", "phase", "reason", "state", "status"}
    ):
        return "negative_observation"
    if fact_type == "coverage" or directness == "related_context":
        return "context"
    if (
        directness == "direct"
        and confidence in {"high", "medium"}
        and strength in {"critical", "strong", "supporting"}
        and fact_type in {"event", "configuration"}
    ) or (
        "waiting_reason" in attribute
        or "waiting_message" in attribute
        or "terminated_reason" in attribute
        or "terminated_message" in attribute
    ):
        return "causal_candidate"
    if fact_type in {"measurement", "state", "log", "span", "flow"}:
        return "symptom"
    return "context"


def _support_quality(record: Mapping[str, Any]) -> bool:
    if str(record.get("fact_type") or "") == "coverage":
        return False
    directness = str(record.get("directness") or "")
    confidence = str(record.get("confidence") or "")
    if directness == "related_context" or confidence in {"low", "weak"}:
        return False
    return confidence == "high" or (
        directness == "direct" and confidence == "medium"
    )


def _is_direct_support_causal(record: Mapping[str, Any]) -> bool:
    return (
        str(record.get("evidence_role") or "") == "causal_candidate"
        and str(record.get("directness") or "") == "direct"
        and _support_quality(record)
    )


def _selection_priority(record: Mapping[str, Any]) -> tuple[Any, ...]:
    role_order = {
        "causal_candidate": 0,
        "contradicting": 1,
        "negative_observation": 2,
        "symptom": 3,
        "context": 4,
    }
    strength_order = {"critical": 0, "strong": 1, "supporting": 2, "context": 3}
    direct_order = {"direct": 0, "derived": 1, "related_context": 2}
    confidence_order = {"high": 0, "medium": 1, "low": 2, "weak": 3}
    dimension_order = {
        "kubernetes": 0,
        "metrics": 1,
        "logging": 2,
        "tracing": 3,
        "topology": 4,
        "coverage": 5,
    }
    return (
        role_order.get(str(record.get("evidence_role") or "context"), 5),
        strength_order.get(str(record.get("strength") or "context"), 4),
        direct_order.get(str(record.get("directness") or ""), 3),
        confidence_order.get(str(record.get("confidence") or ""), 4),
        dimension_order.get(str(record.get("dimension") or ""), 6),
        str(record.get("fact_id") or ""),
    )


def _causal_phase_priority(
    record: Mapping[str, Any],
    *,
    fact_id: str,
) -> tuple[Any, ...]:
    """Order causal candidates by causal quality before stable tie-breakers."""
    direct_order = {"direct": 0, "derived": 1, "related_context": 2}
    confidence_order = {"high": 0, "medium": 1, "low": 2, "weak": 3}
    strength_order = {"critical": 0, "strong": 1, "supporting": 2, "context": 3}
    dimension_order = {
        "kubernetes": 0,
        "metrics": 1,
        "logging": 2,
        "tracing": 3,
        "topology": 4,
        "coverage": 5,
    }
    return (
        direct_order.get(str(record.get("directness") or ""), 3),
        confidence_order.get(str(record.get("confidence") or ""), 4),
        strength_order.get(str(record.get("strength") or "context"), 4),
        dimension_order.get(str(record.get("dimension") or ""), 6),
        fact_id,
    )


def _stable_value_digest(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _observation_signature(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Identify equivalent observations without scenario-specific policy."""
    return (
        str(record.get("entity_id") or ""),
        str(record.get("entity_kind") or ""),
        str(record.get("namespace") or ""),
        str(record.get("entity_name") or ""),
        str(record.get("dimension") or ""),
        str(record.get("fact_type") or ""),
        str(record.get("attribute") or ""),
        _stable_value_digest(record.get("value")),
        str(record.get("directness") or ""),
        str(record.get("source_system") or ""),
    )


def _allocation_signature(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Group distinct observations for fair record-level allocation."""
    return (
        str(record.get("entity_id") or ""),
        str(record.get("entity_kind") or ""),
        str(record.get("namespace") or ""),
        str(record.get("entity_name") or ""),
        str(record.get("dimension") or ""),
        str(record.get("fact_type") or ""),
        str(record.get("attribute") or ""),
    )


def _signature_diverse_order(
    candidates: Sequence[tuple[str, Mapping[str, Any]]],
) -> List[tuple[str, Mapping[str, Any]]]:
    """Return quality-ordered rounds with one record per signature first."""
    buckets: Dict[
        tuple[str, ...], List[tuple[str, Mapping[str, Any]]]
    ] = {}
    for candidate in candidates:
        buckets.setdefault(_allocation_signature(candidate[1]), []).append(
            candidate
        )
    ordered: List[tuple[str, Mapping[str, Any]]] = []
    offset = 0
    while True:
        added = False
        for bucket in buckets.values():
            if offset >= len(bucket):
                continue
            ordered.append(bucket[offset])
            added = True
        if not added:
            return ordered
        offset += 1


def build_selection_manifest(
    fact_index: Mapping[str, Mapping[str, Any]],
    *,
    max_facts: int,
) -> SelectionManifest:
    selection_limit = max(0, int(max_facts))
    indexed_records = sorted(
        (
            (str(index_fact_id), record)
            for index_fact_id, record in fact_index.items()
        ),
        key=lambda item: (*_selection_priority(item[1]), item[0]),
    )
    fact_ids = [fact_id for fact_id, _ in indexed_records]
    eligible_support = [
        fact_id
        for fact_id, record in indexed_records
        if str(record.get("evidence_role") or "")
        in {"causal_candidate", "symptom"}
        and _support_quality(record)
    ]
    required_context = [
        fact_id
        for fact_id, record in indexed_records
        if str(record.get("evidence_role") or "")
        in {"contradicting", "negative_observation"}
        or (
            str(record.get("fact_type") or "") == "configuration"
            and str(record.get("directness") or "") == "direct"
            and str(record.get("strength") or "") in {"critical", "strong"}
        )
    ]

    representatives: List[tuple[str, Mapping[str, Any]]] = []
    representative_by_signature: Dict[tuple[str, ...], str] = {}
    equivalence_classes: Dict[str, List[str]] = {}
    equivalent_fact_ids: set[str] = set()
    for fact_id, record in indexed_records:
        signature = _observation_signature(record)
        representative = representative_by_signature.get(signature)
        if representative is None:
            representative_by_signature[signature] = fact_id
            representatives.append((fact_id, record))
            equivalence_classes[fact_id] = [fact_id]
            continue
        equivalence_classes[representative].append(fact_id)
        equivalent_fact_ids.add(fact_id)

    selected: List[str] = []
    selected_set: set[str] = set()
    representatives_by_dimension: Dict[
        str, List[tuple[str, Mapping[str, Any]]]
    ] = {}
    for fact_id, record in representatives:
        dimension = str(record.get("dimension") or "")
        representatives_by_dimension.setdefault(dimension, []).append(
            (fact_id, record)
        )

    available_required_dimensions = [
        dimension
        for dimension in REQUIRED_DIMENSIONS
        if representatives_by_dimension.get(dimension)
    ]
    required_dimension_set = set(available_required_dimensions)

    def missing_required_dimensions() -> set[str]:
        selected_dimensions = {
            str(record.get("dimension") or "")
            for fact_id, record in representatives
            if fact_id in selected_set
        }
        return required_dimension_set - selected_dimensions

    def select_candidate(
        fact_id: str,
        record: Mapping[str, Any],
        *,
        protect_feasible_coverage: bool,
    ) -> bool:
        if fact_id in selected_set or len(selected) >= selection_limit:
            return False
        missing = missing_required_dimensions()
        remaining = selection_limit - len(selected)
        if protect_feasible_coverage and remaining >= len(missing):
            candidate_dimension = str(record.get("dimension") or "")
            missing_after = len(missing - {candidate_dimension})
            if remaining - 1 < missing_after:
                return False
        selected.append(fact_id)
        selected_set.add(fact_id)
        return True

    def select_phase(
        candidates: Sequence[tuple[str, Mapping[str, Any]]],
    ) -> None:
        for fact_id, record in _signature_diverse_order(candidates):
            select_candidate(
                fact_id,
                record,
                protect_feasible_coverage=True,
            )

    causal_candidates = [
        candidate
        for candidate in representatives
        if _is_direct_support_causal(candidate[1])
    ]
    causal_candidates.sort(
        key=lambda candidate: _causal_phase_priority(
            candidate[1],
            fact_id=candidate[0],
        )
    )
    select_phase(causal_candidates)
    select_phase([
        candidate
        for candidate in representatives
        if str(candidate[1].get("evidence_role") or "")
        in {"contradicting", "negative_observation"}
        and str(candidate[1].get("directness") or "") == "direct"
    ])

    seen_missing_dimensions: set[str] = set()
    for fact_id, record in representatives:
        dimension = str(record.get("dimension") or "")
        if (
            dimension not in missing_required_dimensions()
            or dimension in seen_missing_dimensions
        ):
            continue
        seen_missing_dimensions.add(dimension)
        select_candidate(
            fact_id,
            record,
            protect_feasible_coverage=False,
        )

    select_phase([
        candidate
        for candidate in representatives
        if str(candidate[1].get("fact_type") or "") == "configuration"
        or str(candidate[1].get("evidence_role") or "") == "context"
    ])

    extra_dimensions = sorted(
        (
            dimension
            for dimension in representatives_by_dimension
            if dimension not in REQUIRED_DIMENSIONS
        ),
        key=lambda dimension: (
            _selection_priority(
                representatives_by_dimension[dimension][0][1]
            ),
            dimension,
        ),
    )
    dimension_order = [
        *available_required_dimensions,
        *extra_dimensions,
    ]
    diverse_dimension_buckets = {
        dimension: _signature_diverse_order(
            representatives_by_dimension[dimension]
        )
        for dimension in dimension_order
    }
    bucket_offsets = {dimension: 0 for dimension in dimension_order}
    while len(selected) < selection_limit:
        added = False
        for dimension in dimension_order:
            bucket = diverse_dimension_buckets[dimension]
            offset = bucket_offsets[dimension]
            while offset < len(bucket) and bucket[offset][0] in selected_set:
                offset += 1
            bucket_offsets[dimension] = offset
            if offset >= len(bucket):
                continue
            select_candidate(
                bucket[offset][0],
                bucket[offset][1],
                protect_feasible_coverage=False,
            )
            bucket_offsets[dimension] = offset + 1
            added = True
            if len(selected) >= selection_limit:
                break
        if not added:
            break

    required_dimension_representatives = [
        representatives_by_dimension[dimension][0][0]
        for dimension in available_required_dimensions
    ]
    required_context.extend(
        fact_id
        for fact_id, record in representatives
        if fact_id in required_dimension_representatives
        and fact_id in selected_set
        and fact_id not in eligible_support
        and str(record.get("directness") or "") == "direct"
    )
    representative_of = {
        representative: tuple(equivalent_ids)
        for representative, equivalent_ids in equivalence_classes.items()
        if representative in selected_set and len(equivalent_ids) > 1
    }
    omitted = [
        fact_id for fact_id in fact_ids if fact_id not in selected_set
    ]
    omission_reasons = {
        fact_id: (
            "equivalent_observation"
            if fact_id in equivalent_fact_ids
            else "rca_fact_count_limit"
        )
        for fact_id in omitted
    }
    record_by_fact_id = dict(indexed_records)
    unselected_causal = [
        fact_id
        for fact_id in omitted
        if omission_reasons[fact_id] == "rca_fact_count_limit"
        and _is_direct_support_causal(record_by_fact_id[fact_id])
    ]
    selected_eligible_support = [
        fact_id for fact_id in eligible_support if fact_id in selected_set
    ]
    selected_direct_causal = [
        fact_id
        for fact_id, record in indexed_records
        if fact_id in selected_set and _is_direct_support_causal(record)
    ]
    selected_required_context = [
        fact_id for fact_id in required_context if fact_id in selected_set
    ]
    return SelectionManifest(
        eligible_support_fact_ids=tuple(
            dict.fromkeys(selected_eligible_support)
        ),
        direct_causal_candidate_fact_ids=tuple(
            dict.fromkeys(selected_direct_causal)
        ),
        required_context_fact_ids=tuple(
            dict.fromkeys(selected_required_context)
        ),
        rca_input_fact_ids=tuple(selected),
        omitted_fact_ids=tuple(omitted),
        omission_reasons=omission_reasons,
        contract_version=SELECTION_MANIFEST_CONTRACT_VERSION,
        max_facts=selection_limit,
        total_fact_count=len(fact_index),
        overflowed=len(fact_index) > selection_limit,
        representative_of=representative_of,
        unselected_higher_priority_causal_fact_ids=tuple(unselected_causal),
    )


def _entity_key(namespace: Any, name: Any) -> str:
    return f"{str(namespace or '').strip()}/{str(name or '').strip()}"


def _key_from_entity_id(entity_id: Any) -> str:
    value = str(entity_id or "").strip()
    prefix = "k8s.pod:"
    if not value.lower().startswith(prefix):
        return ""
    scoped = value[len(prefix):]
    namespace, separator, remainder = scoped.partition("/")
    if not separator:
        return ""
    name = remainder.split(":", 1)[0]
    return _entity_key(namespace, name) if namespace and name else ""


def _record_entity_key(record: FactRecord) -> str:
    direct = _entity_key(record.namespace, record.entity_name)
    return direct if direct != "/" else _key_from_entity_id(record.entity_id)


@dataclass(frozen=True)
class EntityEvidenceSnapshot:
    """Immutable owner of the facts used by RCA, validation, and reporting."""

    entities: tuple[Dict[str, Any], ...]
    fact_ledgers: tuple[FactLedger, ...]
    fact_index: Mapping[str, Dict[str, Any]]
    dimension_evidence_by_entity: Mapping[str, Dict[str, Dict[str, Any]]]
    limitations: tuple[str, ...]
    archive_refs: tuple[str, ...]
    selection_manifest: SelectionManifest

    def to_handoff(self) -> Dict[str, Any]:
        """Return a JSON-safe strong handoff without regenerating any fact."""
        return {
            "contract_version": SNAPSHOT_CONTRACT_VERSION,
            "entities": deepcopy(list(self.entities)),
            "fact_ledgers": [
                ledger.model_dump(mode="json", exclude_none=True)
                for ledger in self.fact_ledgers
            ],
            "fact_index": deepcopy(dict(self.fact_index)),
            "dimension_evidence_by_entity": deepcopy(
                dict(self.dimension_evidence_by_entity)
            ),
            "limitations": list(self.limitations),
            "archive_refs": list(self.archive_refs),
            "selection_manifest": self.selection_manifest.to_dict(),
        }


def build_entity_evidence_snapshot(
    *,
    entities: Sequence[Mapping[str, Any]],
    evidence_analysis: Any,
    thinking_events: Sequence[Mapping[str, Any]],
    status_keywords: Sequence[str] = (),
    max_rca_facts: int = DEFAULT_RCA_FACT_LIMIT,
) -> EntityEvidenceSnapshot:
    """Normalize Fact Ledgers once and index them for all downstream users."""
    copied_entities = tuple(
        deepcopy(dict(entity))
        for entity in entities
        if isinstance(entity, Mapping)
        and _entity_key(entity.get("namespace"), entity.get("name")) != "/"
    )
    dimensions = aggregate_group_evidence(
        list(copied_entities),
        [dict(event) for event in thinking_events if isinstance(event, Mapping)],
        status_keywords=list(status_keywords),
        include_event_facts=False,
    )
    all_ledgers = tuple(
        extract_fact_ledgers_from_evidence_analysis(evidence_analysis)
    )
    raw_record_index: Dict[str, Dict[str, Any]] = {}
    raw_record_collisions: set[str] = set()
    for raw_ledger in extract_fact_ledger_inputs_from_evidence_analysis(
        evidence_analysis
    ):
        raw_payload = (
            raw_ledger.model_dump(mode="json", exclude_none=True)
            if isinstance(raw_ledger, FactLedger)
            else raw_ledger
        )
        if not isinstance(raw_payload, Mapping):
            continue
        for raw_record in raw_payload.get("records") or []:
            if not isinstance(raw_record, Mapping):
                continue
            raw_fact_id = str(raw_record.get("fact_id") or "").strip()
            if not raw_fact_id:
                continue
            copied_raw = deepcopy(dict(raw_record))
            existing_raw = raw_record_index.get(raw_fact_id)
            if existing_raw is not None and existing_raw != copied_raw:
                raw_record_collisions.add(raw_fact_id)
                raw_record_index.pop(raw_fact_id, None)
                continue
            if raw_fact_id not in raw_record_collisions:
                raw_record_index[raw_fact_id] = copied_raw
    allowed_keys = set(dimensions)
    fact_index: Dict[str, Dict[str, Any]] = {}
    limitations: List[str] = []
    archive_refs: List[str] = []

    scoped_ledgers: List[FactLedger] = []
    for ledger in all_ledgers:
        if ledger.truncated:
            limitations.append(
                f"Fact Ledger {ledger.case_id} was source-truncated"
            )
        scoped_records: List[FactRecord] = []
        for record in ledger.records:
            entity_key = _record_entity_key(record)
            if entity_key not in allowed_keys:
                limitations.append(
                    f"Fact {record.fact_id} is outside the diagnostic entity scope"
                )
                continue
            scoped_records.append(record)
            dimension = str(record.dimension).strip().lower()
            if dimension not in REQUIRED_DIMENSIONS:
                continue
            record_payload = record.model_dump(mode="json", exclude_none=True)
            raw_record = raw_record_index.get(record.fact_id)
            if raw_record is not None:
                for key, value in raw_record.items():
                    if key not in record_payload:
                        record_payload[key] = deepcopy(value)
            compact = _compact_fact(
                record_payload,
                fallback_seed=f"{entity_key}:{dimension}:canonical",
            )
            compact["evidence_role"] = classify_fact_evidence_role(
                record_payload
            )
            existing = fact_index.get(record.fact_id)
            if existing is not None and existing != compact:
                limitations.append(
                    f"Fact ID collision excluded from snapshot: {record.fact_id}"
                )
                continue
            fact_index[record.fact_id] = compact
            summary = dimensions[entity_key][dimension]
            _append_unique_facts(summary, [compact])
            summary["source_systems"] = sorted(set(
                [*summary.get("source_systems", []), record.source_system]
            ))
            summary["status"] = "present"
            for ref in record.evidence_refs:
                if ref not in archive_refs:
                    archive_refs.append(ref)

        scoped_entity_ids = [
            entity_id
            for entity_id in ledger.scope_entity_ids
            if _key_from_entity_id(entity_id) in allowed_keys
        ]
        for record in scoped_records:
            if record.entity_id and record.entity_id not in scoped_entity_ids:
                scoped_entity_ids.append(record.entity_id)
        if scoped_entity_ids:
            payload = ledger.model_dump(mode="json", exclude_none=True)
            payload["scope_entity_ids"] = scoped_entity_ids
            payload["records"] = [
                record.model_dump(mode="json", exclude_none=True)
                for record in scoped_records
            ]
            scoped_ledgers.append(FactLedger.model_validate(payload))

    return EntityEvidenceSnapshot(
        entities=copied_entities,
        fact_ledgers=tuple(scoped_ledgers),
        fact_index=deepcopy(fact_index),
        dimension_evidence_by_entity=deepcopy(dimensions),
        limitations=tuple(dict.fromkeys(limitations)),
        archive_refs=tuple(archive_refs),
        selection_manifest=build_selection_manifest(
            fact_index,
            max_facts=max_rca_facts,
        ),
    )
