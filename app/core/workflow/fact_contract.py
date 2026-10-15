"""Generic Fact Ledger normalization, compaction, and RCA claim validation."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from pydantic import ValidationError

from app.core.workflow.schemas import (
    FactLedger,
    FactRecord,
)

FACT_LEDGER_VERSION = "aiops.fact-ledger.v1"
MAX_FACT_RECORDS = 48
OBSERVABILITY_QUERY_TOOL_DIMENSIONS = {
    "execute_pod_promql": "metrics",
    "query_pod_logs": "logging",
    "query_pod_tracing": "tracing",
    "query_pod_topology": "topology",
}
OBSERVABILITY_QUERY_TOOLS = frozenset(
    OBSERVABILITY_QUERY_TOOL_DIMENSIONS
)

_FORBIDDEN_KEYS = {
    "diagnosis",
    "diagnostic_role",
    "expected_remediation",
    "expected_root_cause",
    "evaluation_label",
    "evaluator",
    "evaluator_only",
    "fault_label",
    "ground_truth",
    "label",
    "labels",
    "remediation",
    "role",
    "root_cause",
    "root_cause_label",
}
_FORBIDDEN_NORMALIZED_KEYS = {
    "".join(character for character in key.lower() if character.isalnum())
    for key in _FORBIDDEN_KEYS
}
_FORBIDDEN_NORMALIZED_KEY_FAMILIES = {
    "causalrole",
    "diagnosis",
    "diagnosticrole",
    "evaluator",
    "groundtruth",
    "label",
    "prefailure",
    "remediation",
    "requestdriver",
    "rootcause",
}
_RECORD_FIELDS = {
    "fact_id",
    "entity_id",
    "entity_kind",
    "namespace",
    "entity_name",
    "dimension",
    "fact_type",
    "attribute",
    "value",
    "unit",
    "timestamp",
    "start",
    "end",
    "source_system",
    "directness",
    "confidence",
    "strength",
    "evidence_refs",
    "metadata",
}
_REQUIRED_RECORD_FIELDS = {
    "fact_id",
    "entity_id",
    "entity_kind",
    "dimension",
    "fact_type",
    "attribute",
    "value",
    "source_system",
    "directness",
    "confidence",
    "evidence_refs",
}
_LEDGER_FIELDS = {
    "contract_version",
    "case_id",
    "scope_entity_ids",
    "records",
    "record_count",
    "truncated",
    "source",
    "legacy_contract",
}
_CANONICAL_OPTIONAL_FIELDS = {
    "namespace",
    "entity_name",
    "strength",
    "unit",
    "timestamp",
    "start",
    "end",
    "metadata",
}
_DIMENSION_ALIASES = {
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "metric": "metrics",
    "metrics": "metrics",
    "prometheus": "metrics",
    "log": "logging",
    "logs": "logging",
    "logging": "logging",
    "trace": "tracing",
    "traces": "tracing",
    "tracing": "tracing",
    "topology": "topology",
    "coverage": "coverage",
}
_STRENGTH_ORDER = {
    "critical": 0,
    "strong": 1,
    "supporting": 2,
    "context": 3,
    "": 4,
}
_DIRECTNESS_ORDER = {"direct": 0, "derived": 1, "related_context": 2}
_CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2, "weak": 3}
_ALLOWED_TOPOLOGY_RELATIONS = frozenset({
    "calls",
    "ownedby",
    "ownscontainer",
    "scheduledon",
    "selectedby",
    "selects",
})
_TOPOLOGY_RELATIONS_BY_SOURCE = {
    "kubernetes": frozenset({
        "ownedby",
        "ownscontainer",
        "scheduledon",
        "selectedby",
        "selects",
    }),
    "deepflow": frozenset({"calls"}),
}
_CANONICAL_TOPOLOGY_SCOPE_ALIAS = "k8s.pod:scope/current"
_MAX_CANONICAL_TOPOLOGY_ENTITY_ID_CHARS = 192


def _normalized_key(value: Any) -> str:
    return "".join(
        character
        for character in str(value or "").lower()
        if character.isalnum()
    )


def is_forbidden_fact_key(value: Any) -> bool:
    normalized = _normalized_key(value)
    if not normalized:
        return False
    return (
        normalized in _FORBIDDEN_NORMALIZED_KEYS
        or any(
            family in normalized
            for family in _FORBIDDEN_NORMALIZED_KEY_FAMILIES
        )
    )


def sanitize_evidence_value(value: Any) -> Any:
    """Remove forbidden structural keys without inspecting source text values."""
    if isinstance(value, Mapping):
        return {
            str(key): sanitize_evidence_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if not is_forbidden_fact_key(key)
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_evidence_value(item) for item in value]
    return deepcopy(value)


def _contains_evaluator_fields(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if is_forbidden_fact_key(key):
                return True
            if _contains_evaluator_fields(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_evaluator_fields(item) for item in value)
    return False


def _record_contains_evaluator_fields(value: Mapping[str, Any]) -> bool:
    metadata = value.get("metadata")
    for key, item in value.items():
        if key == "metadata":
            continue
        if is_forbidden_fact_key(key) or _contains_evaluator_fields(item):
            return True
    if is_forbidden_fact_key(value.get("attribute")):
        return True

    if not isinstance(metadata, Mapping):
        return _contains_evaluator_fields(metadata)
    allow_prometheus_labels = (
        _normalized_key(value.get("source_system")) == "prometheus"
        and _normalized_key(value.get("dimension")) == "metrics"
        and _normalized_key(value.get("fact_type")) == "measurement"
    )
    for key, item in metadata.items():
        if _normalized_key(key) == "labels" and allow_prometheus_labels:
            if not isinstance(item, Mapping) or _contains_evaluator_fields(item):
                return True
            continue
        if is_forbidden_fact_key(key) or _contains_evaluator_fields(item):
            return True
    return False


def _ledger_contains_evaluator_fields(value: Mapping[str, Any]) -> bool:
    for key, item in value.items():
        if key == "records" and isinstance(item, list):
            if any(
                _record_contains_evaluator_fields(record)
                for record in item
                if isinstance(record, Mapping)
            ):
                return True
            continue
        if is_forbidden_fact_key(key) or _contains_evaluator_fields(item):
            return True
    return False


def _string_list(
    value: Any,
    *,
    limit: int | None = 32,
) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple, set)) else [value]
    source_items = list(items)
    if limit is not None:
        source_items = source_items[:limit]
    return list(dict.fromkeys(
        text
        for item in source_items
        if (text := str(item or "").strip())
    ))


def _normalize_dimension(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _DIMENSION_ALIASES.get(text, text)


def _canonical_record_payload(value: Mapping[str, Any] | FactRecord) -> dict[str, Any]:
    raw = (
        value.model_dump(mode="json", exclude_none=True)
        if isinstance(value, FactRecord)
        else dict(value)
    )
    payload = {
        key: deepcopy(raw[key])
        for key in _RECORD_FIELDS
        if key != "fact_id"
        and key in raw
        and (
            key not in _CANONICAL_OPTIONAL_FIELDS
            or raw[key] not in (None, {}, [])
        )
    }
    payload["dimension"] = _normalize_dimension(payload.get("dimension"))
    payload["evidence_refs"] = sorted(set(
        _string_list(payload.get("evidence_refs"), limit=None)
    ))
    return payload


def _canonical_record_json(value: Mapping[str, Any] | FactRecord) -> str:
    return json.dumps(
        _canonical_record_payload(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _canonical_fact_id(value: Mapping[str, Any] | FactRecord) -> str:
    canonical = _canonical_record_json(value)
    return "fact-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def _normalize_record(value: Any) -> FactRecord | None:
    if isinstance(value, FactRecord):
        value = value.model_dump(mode="json", exclude_none=True)
    if not isinstance(value, Mapping) or _record_contains_evaluator_fields(value):
        return None

    payload = {
        key: deepcopy(value[key])
        for key in _RECORD_FIELDS
        if key in value
    }
    payload["dimension"] = _normalize_dimension(payload.get("dimension"))
    payload["evidence_refs"] = sorted(set(
        _string_list(payload.get("evidence_refs"), limit=None)
    ))
    if not isinstance(payload.get("metadata"), dict):
        payload["metadata"] = {}
    try:
        record = FactRecord.model_validate(payload)
    except ValidationError:
        return None
    if record.fact_id != _canonical_fact_id(record):
        return None
    return record


def _record_priority(record: FactRecord) -> tuple[Any, ...]:
    semantic_priority = (
        0
        if record.attribute in {
            "container.waiting_reason",
            "container.waiting_message",
            "container.last_terminated_reason",
            "container.last_terminated_message",
            "event.message",
        }
        else 1
        if record.attribute in {"container.last_exit_code", "pod.condition"}
        else 2
        if record.fact_type == "configuration"
        else 3
        if record.attribute == "container.restart_count"
        else 4
    )
    return (
        1 if record.fact_type == "coverage" else 0,
        _STRENGTH_ORDER.get(str(record.strength or ""), 5),
        _DIRECTNESS_ORDER.get(record.directness, 3),
        _CONFIDENCE_ORDER.get(record.confidence, 4),
        semantic_priority,
        record.entity_id,
        record.dimension,
        record.fact_id,
    )


def _select_records(
    records: Iterable[FactRecord],
    *,
    max_records: int = MAX_FACT_RECORDS,
) -> tuple[list[FactRecord], bool]:
    deduplicated: list[FactRecord] = []
    seen_ids: set[str] = set()
    seen_payloads: set[str] = set()
    for record in records:
        payload_key = json.dumps(
            _canonical_record_payload(record),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if record.fact_id in seen_ids or payload_key in seen_payloads:
            continue
        seen_ids.add(record.fact_id)
        seen_payloads.add(payload_key)
        deduplicated.append(record)

    ordered = sorted(deduplicated, key=_record_priority)
    selected = ordered[:max_records]
    return selected, len(selected) < len(ordered)


def normalize_fact_ledger(value: Any) -> FactLedger | None:
    """Sanitize a native or adapter ledger without evaluator fields."""
    if isinstance(value, FactLedger):
        raw = value.model_dump(mode="json", exclude_none=True)
    elif isinstance(value, Mapping):
        raw = dict(value)
    else:
        return None
    if raw.get("contract_version") != FACT_LEDGER_VERSION:
        return None

    records = [
        record
        for item in (raw.get("records") or [])
        if (record := _normalize_record(item)) is not None
    ]
    selected, truncated = _select_records(records)
    scope_entity_ids = _string_list(
        raw.get("scope_entity_ids"),
        limit=None,
    )
    if not scope_entity_ids:
        scope_entity_ids = list(dict.fromkeys(record.entity_id for record in selected))
    case_id = str(raw.get("case_id") or "").strip()
    if not case_id:
        return None

    source = str(raw.get("source") or "mcp_canonical").strip()
    if source not in {"mcp_canonical", "robusta_legacy_adapter"}:
        source = "mcp_canonical"
    legacy_contract = source == "robusta_legacy_adapter" or bool(
        raw.get("legacy_contract")
    )
    if legacy_contract:
        source = "robusta_legacy_adapter"

    try:
        return FactLedger.model_validate({
            "contract_version": FACT_LEDGER_VERSION,
            "case_id": case_id,
            "scope_entity_ids": scope_entity_ids,
            "records": [record.model_dump(mode="json", exclude_none=True) for record in selected],
            "record_count": len(selected),
            "truncated": bool(raw.get("truncated")) or truncated,
            "source": source,
            "legacy_contract": legacy_contract,
        })
    except ValidationError:
        return None


def _topology_record_is_source_backed(record: FactRecord) -> bool:
    if (
        record.dimension != "topology"
        or record.fact_type != "relationship"
        or not isinstance(record.value, Mapping)
    ):
        return False
    endpoint_ids = _typed_topology_endpoints(record)
    relation = _normalized_key(
        record.value.get("relation")
        or record.value.get("relationship")
    )
    source_system = _normalized_key(record.source_system)
    source_relations = _TOPOLOGY_RELATIONS_BY_SOURCE.get(
        source_system,
        frozenset(),
    )
    return (
        len(endpoint_ids) == 2
        and record.entity_id in endpoint_ids
        and relation in _ALLOWED_TOPOLOGY_RELATIONS
        and relation in source_relations
        and record.directness == "direct"
        and bool(record.evidence_refs)
    )


def _topology_graph_is_scope_connected(
    records: Sequence[FactRecord],
    scope_entity_ids: set[str],
    *,
    allow_bounded_scope_alias: bool,
) -> bool:
    endpoint_sets = [
        _typed_topology_endpoints(record)
        for record in records
        if record.dimension == "topology"
        and record.fact_type == "relationship"
    ]
    if not endpoint_sets:
        return True

    reachable = set(scope_entity_ids)
    if (
        allow_bounded_scope_alias
        and len(scope_entity_ids) == 1
        and len(next(iter(scope_entity_ids)))
        > _MAX_CANONICAL_TOPOLOGY_ENTITY_ID_CHARS
    ):
        reachable.add(_CANONICAL_TOPOLOGY_SCOPE_ALIAS)
    pending = list(endpoint_sets)
    while pending:
        remaining: list[set[str]] = []
        progressed = False
        for endpoints in pending:
            if endpoints & reachable:
                reachable.update(endpoints)
                progressed = True
            else:
                remaining.append(endpoints)
        if not progressed:
            return False
        pending = remaining
    return True


def _strict_authority_ledger(
    value: FactLedger | Mapping[str, Any],
) -> tuple[FactLedger | None, list[str]]:
    raw = (
        value.model_dump(mode="json", exclude_none=True)
        if isinstance(value, FactLedger)
        else deepcopy(dict(value))
    )
    reasons: list[str] = []

    if _ledger_contains_evaluator_fields(raw):
        reasons.append("evaluator_field_present")
    if set(raw) != _LEDGER_FIELDS:
        reasons.append("malformed_ledger")
    if raw.get("contract_version") != FACT_LEDGER_VERSION:
        reasons.append("malformed_ledger")
    if not str(raw.get("case_id") or "").strip():
        reasons.append("malformed_ledger")

    scopes = raw.get("scope_entity_ids")
    if (
        not isinstance(scopes, list)
        or not scopes
        or any(not str(item or "").strip() for item in scopes)
        or len(set(str(item) for item in scopes)) != len(scopes)
    ):
        reasons.append("malformed_ledger")
        scope_entity_ids: set[str] = set()
    else:
        scope_entity_ids = {
            str(item).strip()
            for item in scopes
        }

    records = raw.get("records")
    if not isinstance(records, list):
        records = []
        reasons.append("malformed_ledger")
    if (
        not isinstance(raw.get("record_count"), int)
        or raw.get("record_count") != len(records)
        or not isinstance(raw.get("truncated"), bool)
        or not isinstance(raw.get("legacy_contract"), bool)
    ):
        reasons.append("malformed_ledger")

    source = str(raw.get("source") or "").strip()
    legacy_contract = raw.get("legacy_contract")
    if (
        (source == "mcp_canonical" and legacy_contract is not False)
        or (
            source == "robusta_legacy_adapter"
            and legacy_contract is not True
        )
        or source not in {
            "mcp_canonical",
            "robusta_legacy_adapter",
        }
    ):
        reasons.append("malformed_ledger")

    parsed_records: list[FactRecord] = []
    payload_by_id: dict[str, str] = {}
    for item in records:
        if not isinstance(item, Mapping):
            reasons.append("malformed_ledger")
            continue
        raw_record = dict(item)
        if (
            set(raw_record) - _RECORD_FIELDS
            or _REQUIRED_RECORD_FIELDS - set(raw_record)
        ):
            reasons.append("malformed_ledger")
            continue
        if _record_contains_evaluator_fields(raw_record):
            reasons.append("evaluator_field_present")
            continue
        source_system = str(
            raw_record.get("source_system") or ""
        ).strip()
        if not source_system:
            reasons.append("blank_source_system")
            continue
        refs = _string_list(
            raw_record.get("evidence_refs"),
            limit=None,
        )
        if (
            raw_record.get("fact_type") != "coverage"
            and not refs
        ):
            reasons.append("missing_evidence_ref")
            continue
        try:
            record = FactRecord.model_validate(raw_record)
        except ValidationError:
            reasons.append("malformed_ledger")
            continue
        if record.fact_id != _canonical_fact_id(record):
            reasons.append("fact_id_mismatch")
            continue
        if (
            record.dimension == "topology"
            and record.fact_type == "relationship"
            and not _topology_record_is_source_backed(record)
        ):
            reasons.append("untrusted_topology_relationship")
            continue
        if (
            record.entity_id not in scope_entity_ids
            and not (
                record.dimension == "topology"
                and record.fact_type == "relationship"
            )
        ):
            reasons.append("cross_entity_fact")
            continue
        payload = _canonical_record_json(record)
        prior = payload_by_id.get(record.fact_id)
        if prior is not None and prior != payload:
            reasons.append("fact_id_collision")
            continue
        payload_by_id[record.fact_id] = payload
        parsed_records.append(record)

    if not _topology_graph_is_scope_connected(
        parsed_records,
        scope_entity_ids,
        allow_bounded_scope_alias=(source == "mcp_canonical"),
    ):
        reasons.append("untrusted_topology_relationship")

    fatal_reasons = {
        "evaluator_field_present",
        "fact_id_collision",
        "fact_id_mismatch",
        "malformed_ledger",
    }
    unique_reasons = list(dict.fromkeys(reasons))
    if fatal_reasons.intersection(unique_reasons):
        return None, unique_reasons
    if len(parsed_records) != len(records):
        return None, unique_reasons
    try:
        ledger = FactLedger.model_validate({
            **raw,
            "records": [
                record.model_dump(mode="json", exclude_none=True)
                for record in parsed_records
            ],
        })
    except ValidationError:
        return None, list(dict.fromkeys([
            *unique_reasons,
            "malformed_ledger",
        ]))
    return ledger, unique_reasons


def validate_canonical_fact_ledger_contract(
    value: FactLedger | Mapping[str, Any],
) -> tuple[FactLedger | None, tuple[str, ...]]:
    """Validate a native Ledger without assigning current-report authority."""
    raw = (
        value.model_dump(mode="json", exclude_none=True)
        if isinstance(value, FactLedger)
        else dict(value)
    )
    ledger, reasons = _strict_authority_ledger(value)
    if (
        str(raw.get("source") or "").strip() != "mcp_canonical"
        or raw.get("legacy_contract") is not False
    ):
        reasons.append("malformed_ledger")
    reasons = list(dict.fromkeys(reasons))
    if ledger is None or reasons:
        return None, tuple(reasons or ["malformed_ledger"])
    return ledger, ()


def _typed_entity_kind(entity_id: str) -> str:
    prefix, separator, remainder = str(entity_id or "").strip().partition(":")
    if (
        not separator
        or not prefix.lower().startswith("k8s.")
        or not prefix[4:]
        or not remainder
    ):
        return ""
    return _normalized_key(prefix[4:])


def _endpoint_entity_id(value: Any) -> str:
    if isinstance(value, Mapping):
        normalized = {
            _normalized_key(key): item
            for key, item in value.items()
        }
        entity_id = str(
            normalized.get("entityid")
            or normalized.get("id")
            or ""
        ).strip()
        kind = str(
            normalized.get("entitykind")
            or normalized.get("kind")
            or ""
        ).strip()
        entity_kind = _typed_entity_kind(entity_id)
        normalized_kind = _normalized_key(kind)
        if normalized_kind.startswith("k8s"):
            normalized_kind = normalized_kind[3:]
        if not entity_kind or not normalized_kind or normalized_kind != entity_kind:
            return ""
        return entity_id
    entity_id = str(value or "").strip()
    return entity_id if _typed_entity_kind(entity_id) else ""


def _typed_topology_endpoints(record: FactRecord) -> set[str]:
    if (
        record.dimension != "topology"
        or record.fact_type != "relationship"
        or not isinstance(record.value, Mapping)
    ):
        return set()
    normalized = {
        _normalized_key(key): item
        for key, item in record.value.items()
    }
    relation = normalized.get("relation") or normalized.get("relationship")
    if not isinstance(relation, str) or not relation.strip():
        return set()

    if (
        "sourceentityid" in normalized
        or "targetentityid" in normalized
    ):
        source = _endpoint_entity_id(normalized.get("sourceentityid"))
        target = _endpoint_entity_id(normalized.get("targetentityid"))
    else:
        source = _endpoint_entity_id(normalized.get("source"))
        target = _endpoint_entity_id(normalized.get("target"))
    if not source or not target or source == target:
        return set()
    return {source, target}
