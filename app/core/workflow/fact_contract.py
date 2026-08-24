"""Generic Fact Ledger normalization, compaction, and RCA claim validation."""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from typing import Any, Iterable, Mapping, Sequence

from pydantic import ValidationError

from app.core.workflow.schemas import (
    FactLedger,
    FactRecord,
    RCAOutput,
)


FACT_LEDGER_VERSION = "aiops.fact-ledger.v1"
MAX_FACT_RECORDS = 48
DEFAULT_AGENT_CONTEXT_CHARS = 12000
MIN_FACT_LEDGER_JSON_CHARS = len('{"fact_ledgers":[]}')
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
_LEDGER_SOURCE_ORDER = {
    "mcp_canonical": 0,
    "robusta_legacy_adapter": 1,
}
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


def _observability_event_pod_target(
    event: Mapping[str, Any],
) -> tuple[str, str] | None:
    args = (
        event.get("tool_args")
        if isinstance(event.get("tool_args"), Mapping)
        else {}
    )
    requested_namespace = str(
        args.get("namespace") or ""
    ).strip().lower()
    requested_pod = str(
        args.get("pod")
        or args.get("pod_name")
        or (
            args.get("name")
            if str(args.get("kind") or "pod").strip().lower()
            in {"pod", "pods"}
            else ""
        )
        or ""
    ).strip().lower()
    requested = (
        (requested_namespace, requested_pod)
        if requested_namespace and requested_pod
        else None
    )

    structured = (
        event.get("structured")
        if isinstance(event.get("structured"), Mapping)
        else {}
    )
    observed = None
    for candidate, name_keys in (
        (structured.get("primary_entity"), ("name", "pod")),
        (structured.get("entity"), ("pod", "name")),
    ):
        if not isinstance(candidate, Mapping):
            continue
        kind = str(candidate.get("kind") or "Pod").strip().lower()
        namespace = str(candidate.get("namespace") or "").strip().lower()
        name = next(
            (
                str(candidate.get(key) or "").strip().lower()
                for key in name_keys
                if str(candidate.get(key) or "").strip()
            ),
            "",
        )
        if kind in {"pod", "pods"} and namespace and name:
            observed = (namespace, name)
            break

    if requested and observed and requested != observed:
        return None
    return observed or requested


def _is_source_backed_observability_fact(
    fact: Any,
    *,
    default_source_system: str,
) -> bool:
    if not isinstance(fact, Mapping):
        return False
    refs = _string_list(
        fact.get("ref")
        or fact.get("evidence_ref")
        or fact.get("evidence_refs"),
        limit=None,
    )
    source_system = str(
        fact.get("source_system") or default_source_system
    ).strip()
    return bool(refs and source_system)


def is_observability_query_result_semantically_valid(
    structured: Any,
) -> bool:
    if not isinstance(structured, Mapping):
        return False
    status = str(structured.get("status") or "").strip().lower()
    coverage = str(structured.get("coverage") or "").strip().lower()
    if status == "query_succeeded":
        return coverage in {"present", "empty", "absent", "weak"}
    if status != "query_partial" or coverage != "partial":
        return False
    default_source = str(
        structured.get("source_system") or ""
    ).strip()
    return any(
        _is_source_backed_observability_fact(
            fact,
            default_source_system=default_source,
        )
        for fact in structured.get("facts") or []
    )


def is_observability_event_semantic_success(
    event: Mapping[str, Any],
) -> bool:
    structured = (
        event.get("structured")
        if isinstance(event.get("structured"), Mapping)
        else {}
    )
    return (
        event.get("status") == "success"
        and event.get("semantic_success") is True
        and is_observability_query_result_semantically_valid(
            structured
        )
    )


def _is_observability_event_explicit_failure(
    event: Mapping[str, Any],
) -> bool:
    structured = (
        event.get("structured")
        if isinstance(event.get("structured"), Mapping)
        else {}
    )
    status = str(
        structured.get("status") or ""
    ).strip().lower()
    coverage = str(
        structured.get("coverage") or ""
    ).strip().lower()
    return (
        status in {"query_parse_failed", "query_rejected"}
        or coverage == "error"
    )


def project_final_observability_events(
    thinking_events: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Project final query state without collapsing independent successes."""
    grouped: dict[
        tuple[str, str, str, str],
        list[tuple[int, Mapping[str, Any]]],
    ] = {}
    selected: list[tuple[int, Mapping[str, Any]]] = []
    for index, event in enumerate(thinking_events or []):
        if (
            event.get("type") != "tool_result"
            or event.get("deduplicated") is True
        ):
            continue
        tool_name = str(event.get("tool_name") or "").strip().lower()
        dimension = OBSERVABILITY_QUERY_TOOL_DIMENSIONS.get(tool_name)
        if not dimension:
            continue
        target = _observability_event_pod_target(event)
        if not target:
            continue
        structured = (
            event.get("structured")
            if isinstance(event.get("structured"), Mapping)
            else {}
        )
        semantic_success = (
            is_observability_event_semantic_success(event)
        )
        if (
            not semantic_success
            and not _is_observability_event_explicit_failure(event)
        ):
            continue
        dimension = str(
            structured.get("dimension") or dimension
        ).strip().lower()
        args = (
            event.get("tool_args")
            if isinstance(event.get("tool_args"), Mapping)
            else {}
        )
        purpose = " ".join(
            str(
                structured.get("purpose")
                or args.get("purpose")
                or ""
            ).split()
        ).casefold()
        if not purpose:
            continue
        grouped.setdefault(
            (target[0], target[1], dimension, purpose),
            [],
        ).append((index, event))

    for attempts in grouped.values():
        successes = [
            indexed_event
            for indexed_event in attempts
            if is_observability_event_semantic_success(
                indexed_event[1]
            )
        ]
        selected.extend(successes if successes else attempts)
    return [
        event
        for _, event in sorted(selected, key=lambda item: item[0])
    ]


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


def _global_record_priority(
    ledger: FactLedger,
    record: FactRecord,
) -> tuple[Any, ...]:
    record_priority = _record_priority(record)
    return (
        *record_priority[:4],
        _LEDGER_SOURCE_ORDER.get(ledger.source, 2),
        *record_priority[4:],
    )


def _is_source_backed_deployment_ownership(
    record: FactRecord,
) -> bool:
    if (
        record.dimension != "topology"
        or record.fact_type != "relationship"
        or record.directness != "direct"
        or not record.evidence_refs
        or not isinstance(record.value, Mapping)
    ):
        return False
    source = (
        record.value.get("source")
        if isinstance(record.value.get("source"), Mapping)
        else {}
    )
    target = (
        record.value.get("target")
        if isinstance(record.value.get("target"), Mapping)
        else {}
    )
    return (
        str(record.value.get("relation") or "").casefold() == "owned_by"
        and str(source.get("kind") or "").casefold() == "replicaset"
        and str(target.get("kind") or "").casefold() == "deployment"
    )


def _representative_record_priority(
    record: FactRecord,
) -> tuple[Any, ...]:
    priority = _record_priority(record)
    return (
        *priority[:4],
        0 if _is_source_backed_deployment_ownership(record) else 1,
        0
        if (
            record.dimension == "tracing"
            and record.fact_type == "span"
            and record.attribute == "application_span"
        )
        else 1,
        record.source_system,
        *priority[4:],
    )


def _natural_text_sort_key(value: str) -> tuple[tuple[int, Any], ...]:
    return tuple(
        (1, int(part))
        if part.isdigit()
        else (0, part)
        for part in re.split(r"(\d+)", str(value or "").casefold())
        if part
    )


def _ledger_sort_key(ledger: FactLedger) -> tuple[Any, ...]:
    return (
        tuple(
            _natural_text_sort_key(entity_id)
            for entity_id in ledger.scope_entity_ids
        ),
        _natural_text_sort_key(ledger.case_id),
        _LEDGER_SOURCE_ORDER.get(ledger.source, 2),
        tuple(sorted(record.fact_id for record in ledger.records)),
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


def _entity_id(primary: Mapping[str, Any]) -> str:
    kind = str(primary.get("kind") or "Pod").strip()
    namespace = str(primary.get("namespace") or "").strip()
    name = str(primary.get("name") or "").strip()
    uid = str(primary.get("uid") or "").strip()
    prefix = f"k8s.{kind.lower()}"
    scoped_name = f"{namespace}/{name}" if namespace else name
    return f"{prefix}:{scoped_name}:{uid}" if uid else f"{prefix}:{scoped_name}"


def _fact_id(payload: Mapping[str, Any]) -> str:
    return _canonical_fact_id(payload)


def _evidence_refs(value: Mapping[str, Any]) -> list[str]:
    refs = _string_list(value.get("evidence_refs"), limit=None)
    single = str(value.get("evidence_ref") or "").strip()
    if single and single not in refs:
        refs.append(single)
    return refs


def _legacy_record(
    *,
    entity_id: str,
    primary: Mapping[str, Any],
    dimension: str,
    fact_type: str,
    attribute: str,
    value: Any,
    source_system: str,
    evidence_refs: Sequence[str],
    directness: str = "direct",
    confidence: str = "medium",
    strength: str = "supporting",
    unit: Any = None,
    timestamp: Any = None,
    start: Any = None,
    end: Any = None,
    metadata: Mapping[str, Any] | None = None,
) -> FactRecord | None:
    if _contains_evaluator_fields(value):
        return None
    refs = _string_list(evidence_refs, limit=None)
    if fact_type != "coverage" and not refs:
        return None
    if directness == "related_context" and confidence == "high":
        confidence = "weak"
    payload = {
        "entity_id": entity_id,
        "entity_kind": str(primary.get("kind") or "Pod"),
        "namespace": str(primary.get("namespace") or "") or None,
        "entity_name": str(primary.get("name") or "") or None,
        "dimension": _normalize_dimension(dimension),
        "fact_type": fact_type,
        "attribute": attribute,
        "value": deepcopy(value),
        "unit": str(unit) if unit not in (None, "") else None,
        "timestamp": str(timestamp) if timestamp not in (None, "") else None,
        "start": str(start) if start not in (None, "") else None,
        "end": str(end) if end not in (None, "") else None,
        "source_system": source_system,
        "directness": directness,
        "confidence": confidence,
        "strength": strength,
        "evidence_refs": refs,
        "metadata": (
            deepcopy(dict(metadata))
            if isinstance(metadata, Mapping)
            else {}
        ),
    }
    payload["fact_id"] = _fact_id(payload)
    return _normalize_record(payload)


def _query_fact_type(dimension: str, attribute: str) -> str:
    if dimension == "metrics":
        return "measurement"
    if dimension == "logging":
        return "log"
    if dimension == "tracing":
        return "span" if "span" in _normalized_key(attribute) else "flow"
    if dimension == "topology":
        return "relationship"
    return "state"


def _observability_query_scope(
    structured: Mapping[str, Any],
) -> Mapping[str, Any]:
    query = (
        structured.get("query")
        if isinstance(structured.get("query"), Mapping)
        else {}
    )
    scope = query.get("scope")
    return scope if isinstance(scope, Mapping) else query


def _topology_entity_index(
    structured: Mapping[str, Any],
    *,
    default_namespace: str,
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in structured.get("entities") or []:
        if not isinstance(item, Mapping):
            continue
        canonical = _canonical_topology_endpoint(
            item,
            default_namespace=default_namespace,
        )
        if not isinstance(canonical, Mapping):
            continue
        entity_id = str(canonical.get("entity_id") or "").strip()
        if entity_id:
            index[entity_id] = dict(canonical)
    return index


def _resolve_observability_primary_entity(
    structured: Mapping[str, Any],
) -> dict[str, Any]:
    raw_entity = (
        dict(structured.get("entity"))
        if isinstance(structured.get("entity"), Mapping)
        else {}
    )
    scope = _observability_query_scope(structured)
    scope_namespace = str(scope.get("namespace") or "").strip()
    scope_name = str(
        scope.get("pod")
        or scope.get("pod_name")
        or scope.get("name")
        or ""
    ).strip()
    scope_kind = str(scope.get("kind") or "Pod").strip() or "Pod"
    entity_index = _topology_entity_index(
        structured,
        default_namespace=scope_namespace,
    )

    matched_entity: Mapping[str, Any] = {}
    raw_entity_id = str(raw_entity.get("entity_id") or "").strip()
    if raw_entity_id:
        matched_entity = entity_index.get(raw_entity_id, {})
    if not matched_entity and scope_name:
        for candidate in entity_index.values():
            candidate_kind = str(candidate.get("kind") or "").strip()
            candidate_namespace = str(
                candidate.get("namespace") or ""
            ).strip()
            candidate_name = str(candidate.get("name") or "").strip()
            if (
                candidate_kind.casefold() == scope_kind.casefold()
                and candidate_name == scope_name
                and (
                    not scope_namespace
                    or candidate_namespace == scope_namespace
                )
            ):
                matched_entity = candidate
                break

    raw_name = str(
        raw_entity.get("name") or raw_entity.get("pod") or ""
    ).strip()
    raw_namespace = str(raw_entity.get("namespace") or "").strip()
    matched_name = str(matched_entity.get("name") or "").strip()
    matched_namespace = str(
        matched_entity.get("namespace") or ""
    ).strip()
    names = {value for value in (raw_name, scope_name, matched_name) if value}
    namespaces = {
        value
        for value in (raw_namespace, scope_namespace, matched_namespace)
        if value
    }
    if len(names) > 1 or len(namespaces) > 1:
        return {}

    return {
        "kind": str(
            matched_entity.get("kind")
            or raw_entity.get("kind")
            or scope_kind
            or "Pod"
        ).strip() or "Pod",
        "namespace": next(iter(namespaces), ""),
        "name": next(iter(names), ""),
        "uid": str(
            matched_entity.get("uid")
            or raw_entity.get("uid")
            or raw_entity.get("pod_uid")
            or ""
        ).strip(),
    }


def _canonical_topology_endpoint(
    value: Any,
    *,
    default_namespace: str,
) -> Any:
    if not isinstance(value, Mapping):
        return deepcopy(value)
    endpoint = {
        str(key): deepcopy(item)
        for key, item in value.items()
    }
    kind = str(
        endpoint.get("kind")
        or endpoint.get("entity_kind")
        or ""
    ).strip()
    name = str(
        endpoint.get("name")
        or endpoint.get("entity_name")
        or ""
    ).strip()
    if not kind or not name:
        return endpoint

    cluster_scoped_kinds = {
        "namespace",
        "node",
        "persistentvolume",
        "storageclass",
    }
    namespace = str(endpoint.get("namespace") or "").strip()
    if not namespace and kind.strip().lower() not in cluster_scoped_kinds:
        namespace = default_namespace
    uid = str(endpoint.get("uid") or "").strip()
    entity_id = str(
        endpoint.get("entity_id")
        or endpoint.get("entityId")
        or ""
    ).strip()
    if not entity_id:
        entity_id = _entity_id({
            "kind": kind,
            "namespace": namespace,
            "name": name,
            "uid": uid,
        })
    endpoint["entity_id"] = entity_id
    endpoint["kind"] = kind
    endpoint["name"] = name
    if namespace:
        endpoint["namespace"] = namespace
    if uid:
        endpoint["uid"] = uid
    return endpoint


def _resolve_topology_endpoint(
    value: Any,
    *,
    default_namespace: str,
    entity_index: Mapping[str, Mapping[str, Any]] | None,
) -> Any:
    if isinstance(value, str):
        resolved = (entity_index or {}).get(value)
        return deepcopy(resolved) if resolved is not None else value
    if isinstance(value, Mapping):
        entity_id = str(
            value.get("entity_id") or value.get("entityId") or ""
        ).strip()
        resolved = (entity_index or {}).get(entity_id)
        if resolved is not None:
            merged = dict(resolved)
            merged.update({
                str(key): deepcopy(item)
                for key, item in value.items()
                if item not in (None, "")
            })
            value = merged
    return _canonical_topology_endpoint(
        value,
        default_namespace=default_namespace,
    )


def normalize_topology_query_fact_value(
    item: Mapping[str, Any],
    *,
    default_namespace: str = "",
    entity_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize MCP topology facts into complete typed relationship values."""
    raw_value = (
        dict(item.get("value"))
        if isinstance(item.get("value"), Mapping)
        else {}
    )
    relation = str(
        raw_value.get("relation")
        or raw_value.get("relationship_type")
        or item.get("relation")
        or ""
    ).strip()
    source = _resolve_topology_endpoint(
        raw_value.get("source", item.get("source")),
        default_namespace=default_namespace,
        entity_index=entity_index,
    )
    target = _resolve_topology_endpoint(
        raw_value.get("target", item.get("target")),
        default_namespace=default_namespace,
        entity_index=entity_index,
    )
    source_field = str(
        raw_value.get("source_field")
        or item.get("source_field")
        or ""
    ).strip()
    relationship = str(
        raw_value.get("relationship")
        or item.get("relationship")
        or ""
    ).strip()
    if (
        not relationship
        and relation
        and isinstance(source, Mapping)
        and isinstance(target, Mapping)
    ):
        relationship = (
            f"{source.get('kind') or 'Entity'} "
            f"--{relation}--> "
            f"{target.get('kind') or 'Entity'}"
        )

    normalized = {
        str(key): deepcopy(value)
        for key, value in raw_value.items()
        if key not in {
            "relation",
            "relationship",
            "source",
            "target",
            "source_field",
        }
    }
    if relation:
        normalized["relation"] = relation
    if relationship:
        normalized["relationship"] = relationship
    if source not in (None, "", {}):
        normalized["source"] = source
    if target not in (None, "", {}):
        normalized["target"] = target
    if source_field:
        normalized["source_field"] = source_field
    return normalized


TopologyEndpointIdentity = tuple[str, ...]
TopologyRelationshipKey = tuple[
    str,
    TopologyEndpointIdentity,
    TopologyEndpointIdentity,
]


def _topology_endpoint_identity(
    value: Any,
    *,
    default_namespace: str,
) -> TopologyEndpointIdentity | None:
    if isinstance(value, Mapping):
        explicit_entity_id = str(
            value.get("entity_id")
            or value.get("entityId")
            or ""
        ).strip()
        if explicit_entity_id:
            return ("entity_id", explicit_entity_id)

        canonical = _canonical_topology_endpoint(
            value,
            default_namespace=default_namespace,
        )
        if not isinstance(canonical, Mapping):
            return None
        kind = str(
            canonical.get("kind")
            or canonical.get("entity_kind")
            or ""
        ).strip()
        namespace = str(canonical.get("namespace") or "").strip()
        name = str(
            canonical.get("name")
            or canonical.get("entity_name")
            or ""
        ).strip()
        uid = str(canonical.get("uid") or "").strip()
        if not kind or not name:
            return None
        return (
            "canonical",
            kind.casefold(),
            namespace,
            name,
            uid,
        )

    if isinstance(value, str) and value:
        return ("text", default_namespace, value)
    return None


def _topology_relationship_key(
    item: Mapping[str, Any],
    *,
    default_namespace: str,
    entity_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> TopologyRelationshipKey | None:
    normalized = normalize_topology_query_fact_value(
        item,
        default_namespace=default_namespace,
        entity_index=entity_index,
    )
    relationship = str(
        normalized.get("relationship")
        or normalized.get("relation")
        or ""
    ).strip()
    source = _topology_endpoint_identity(
        normalized.get("source"),
        default_namespace=default_namespace,
    )
    target = _topology_endpoint_identity(
        normalized.get("target"),
        default_namespace=default_namespace,
    )
    if not relationship or not source or not target:
        return None
    return (relationship.casefold(), source, target)


def _merge_topology_fact_with_edge(
    fact: Mapping[str, Any],
    edge: Mapping[str, Any],
    *,
    default_namespace: str,
    entity_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    merged = {str(key): deepcopy(value) for key, value in fact.items()}
    fact_value = normalize_topology_query_fact_value(
        fact,
        default_namespace=default_namespace,
        entity_index=entity_index,
    )
    edge_value = normalize_topology_query_fact_value(
        edge,
        default_namespace=default_namespace,
        entity_index=entity_index,
    )
    for key, value in edge_value.items():
        if fact_value.get(key) in (None, "", {}, []):
            fact_value[key] = deepcopy(value)
    merged["value"] = fact_value

    for key in (
        "source_system",
        "directness",
        "strength",
    ):
        if merged.get(key) in (None, "") and edge.get(key) not in (
            None,
            "",
        ):
            merged[key] = deepcopy(edge[key])

    fact_confidence = str(merged.get("confidence") or "").strip()
    edge_confidence = str(edge.get("confidence") or "").strip()
    if (
        fact_confidence not in _CONFIDENCE_ORDER
        and edge_confidence in _CONFIDENCE_ORDER
    ):
        merged["confidence"] = edge_confidence

    refs = list(dict.fromkeys([
        *_string_list(fact.get("ref"), limit=None),
        *_evidence_refs(fact),
        *_string_list(edge.get("ref"), limit=None),
        *_evidence_refs(edge),
    ]))
    if refs:
        merged["evidence_refs"] = refs
    return merged


def _topology_edge_candidate_rank(
    edge: Mapping[str, Any],
    *,
    default_namespace: str,
    default_source_system: str,
    default_directness: str,
    entity_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[Any, ...]:
    """Rank scored source candidates without relying on input position."""
    confidence = str(edge.get("confidence") or "").strip()
    directness = str(
        edge.get("directness") or default_directness
    ).strip()
    strength = str(edge.get("strength") or "").strip()
    source_system = str(
        edge.get("source_system") or default_source_system
    ).strip()
    value = normalize_topology_query_fact_value(
        edge,
        default_namespace=default_namespace,
        entity_index=entity_index,
    )
    source_field = str(value.get("source_field") or "")
    evidence_refs = tuple(sorted(set([
        *_string_list(edge.get("ref"), limit=None),
        *_evidence_refs(edge),
    ])))
    canonical_source = json.dumps(
        edge,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return (
        _CONFIDENCE_ORDER.get(confidence, len(_CONFIDENCE_ORDER)),
        _DIRECTNESS_ORDER.get(directness, len(_DIRECTNESS_ORDER)),
        _STRENGTH_ORDER.get(strength, len(_STRENGTH_ORDER)),
        source_system.casefold(),
        source_field,
        evidence_refs,
        canonical_source,
    )


def _select_topology_edge_candidates(
    edges: Sequence[Mapping[str, Any]],
    *,
    default_namespace: str,
    default_source_system: str,
    default_directness: str,
    entity_index: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[TopologyRelationshipKey, Mapping[str, Any]]:
    grouped: dict[
        TopologyRelationshipKey,
        list[Mapping[str, Any]],
    ] = {}
    for edge in edges:
        if not _is_source_backed_observability_fact(
            edge,
            default_source_system=default_source_system,
        ):
            continue
        confidence = str(edge.get("confidence") or "").strip()
        if confidence not in _CONFIDENCE_ORDER:
            continue
        key = _topology_relationship_key(
            edge,
            default_namespace=default_namespace,
            entity_index=entity_index,
        )
        if key is None:
            continue
        grouped.setdefault(key, []).append(edge)

    return {
        key: min(
            candidates,
            key=lambda candidate: _topology_edge_candidate_rank(
                candidate,
                default_namespace=default_namespace,
                default_source_system=default_source_system,
                default_directness=default_directness,
                entity_index=entity_index,
            ),
        )
        for key, candidates in grouped.items()
    }


def build_observability_query_fact_ledger(
    structured: Any,
) -> FactLedger | None:
    """Adapt generic Pod observability query output into a bounded ledger."""
    if not isinstance(structured, Mapping):
        return None
    if not is_observability_query_result_semantically_valid(
        structured
    ):
        return None

    primary = _resolve_observability_primary_entity(structured)
    name = str(primary.get("name") or "").strip()
    if not name:
        return None
    entity_id = _entity_id(primary)
    default_dimension = _normalize_dimension(structured.get("dimension"))
    default_source = str(
        structured.get("source_system") or "observability"
    ).strip() or "observability"
    partial_result = (
        str(structured.get("status") or "").strip().lower()
        == "query_partial"
    )
    default_directness = str(
        structured.get("directness") or "direct"
    ).strip()
    if default_directness not in _DIRECTNESS_ORDER:
        default_directness = "direct"

    default_namespace = str(primary.get("namespace") or "")
    topology_entity_index = _topology_entity_index(
        structured,
        default_namespace=default_namespace,
    )
    topology_edges = [
        edge
        for edge in (structured.get("edges") or [])
        if isinstance(edge, Mapping)
    ]
    topology_edge_index = _select_topology_edge_candidates(
        topology_edges,
        default_namespace=default_namespace,
        default_source_system=default_source,
        default_directness=default_directness,
        entity_index=topology_entity_index,
    )

    query_items: list[Mapping[str, Any]] = []
    matched_edge_keys: set[TopologyRelationshipKey] = set()
    for raw_item in structured.get("facts") or []:
        if not isinstance(raw_item, Mapping):
            continue
        item: Mapping[str, Any] = raw_item
        dimension = _normalize_dimension(
            item.get("dimension") or default_dimension
        )
        if dimension == "topology":
            edge_key = _topology_relationship_key(
                item,
                default_namespace=default_namespace,
                entity_index=topology_entity_index,
            )
            matched_edge = (
                topology_edge_index.get(edge_key)
                if edge_key is not None
                else None
            )
            if matched_edge is not None:
                item = _merge_topology_fact_with_edge(
                    item,
                    matched_edge,
                    default_namespace=default_namespace,
                    entity_index=topology_entity_index,
                )
                matched_edge_keys.add(edge_key)
        query_items.append(item)

    structured_refs = _evidence_refs(structured)
    for edge_key in sorted(topology_edge_index):
        if edge_key in matched_edge_keys:
            continue
        edge = topology_edge_index[edge_key]
        edge_item = {str(key): deepcopy(value) for key, value in edge.items()}
        edge_item.setdefault("dimension", "topology")
        edge_item.setdefault("name", "topology.relationship")
        edge_item["value"] = normalize_topology_query_fact_value(
            edge,
            default_namespace=default_namespace,
            entity_index=topology_entity_index,
        )
        edge_refs = list(dict.fromkeys([
            *_string_list(edge.get("ref"), limit=None),
            *_evidence_refs(edge),
        ]))
        if not edge_refs:
            edge_refs = list(structured_refs)
        if edge_refs:
            edge_item["evidence_refs"] = edge_refs
        query_items.append(edge_item)
        matched_edge_keys.add(edge_key)

    records: list[FactRecord] = []
    emitted_relationship_keys: set[TopologyRelationshipKey] = set()
    for item in query_items:
        if not isinstance(item, Mapping):
            continue
        if (
            partial_result
            and not _is_source_backed_observability_fact(
                item,
                default_source_system=default_source,
            )
        ):
            continue
        dimension = _normalize_dimension(
            item.get("dimension") or default_dimension
        )
        if dimension not in {
            "kubernetes",
            "metrics",
            "logging",
            "tracing",
            "topology",
        }:
            continue
        relationship_key = (
            _topology_relationship_key(
                item,
                default_namespace=default_namespace,
                entity_index=topology_entity_index,
            )
            if dimension == "topology"
            else None
        )
        if (
            relationship_key is not None
            and relationship_key in emitted_relationship_keys
        ):
            continue
        attribute = str(
            item.get("name") or item.get("attribute") or f"{dimension}.observed"
        ).strip()
        directness = str(
            item.get("directness") or default_directness
        ).strip()
        if directness not in _DIRECTNESS_ORDER:
            directness = default_directness
        confidence = str(item.get("confidence") or "").strip()
        if confidence not in _CONFIDENCE_ORDER:
            if dimension == "topology":
                continue
            confidence = "medium" if directness != "related_context" else "weak"
        strength = str(item.get("strength") or "").strip()
        if strength not in _STRENGTH_ORDER or not strength:
            strength = "strong" if directness == "direct" else "supporting"
        evidence_refs = list(dict.fromkeys([
            *_string_list(item.get("ref"), limit=None),
            *_evidence_refs(item),
        ]))
        value = (
            normalize_topology_query_fact_value(
                item,
                default_namespace=default_namespace,
                entity_index=topology_entity_index,
            )
            if dimension == "topology"
            else item.get("value")
        )
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension=dimension,
            fact_type=_query_fact_type(dimension, attribute),
            attribute=attribute,
            value=value,
            unit=item.get("unit"),
            source_system=str(
                item.get("source_system") or default_source
            ).strip() or default_source,
            evidence_refs=evidence_refs,
            directness=directness,
            confidence=confidence,
            strength=strength,
            timestamp=item.get("observed_at") or item.get("timestamp"),
            start=item.get("start"),
            end=item.get("end"),
        )
        if record is not None:
            records.append(record)
            if relationship_key is not None:
                emitted_relationship_keys.add(relationship_key)

    if structured_refs:
        for attribute, value in (
            ("topology.entities", structured.get("entities")),
            ("topology.summary", structured.get("topology_summary")),
        ):
            if value in (None, "", [], {}):
                continue
            record = _legacy_record(
                entity_id=entity_id,
                primary=primary,
                dimension="topology",
                fact_type="state",
                attribute=attribute,
                value=deepcopy(value),
                source_system=default_source,
                evidence_refs=structured_refs,
                directness=default_directness,
                confidence="medium",
                strength="supporting",
            )
            if record is not None:
                records.append(record)

    if partial_result:
        evidence_refs = list(structured_refs)
        if not evidence_refs:
            evidence_refs = list(dict.fromkeys(
                ref
                for record in records
                for ref in record.evidence_refs
            ))
        coverage_value: dict[str, Any] = {
            "coverage": "partial",
        }
        if structured.get("limitations") not in (
            None,
            "",
            [],
            {},
        ):
            coverage_value["limitations"] = deepcopy(
                structured.get("limitations")
            )
        coverage_record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension=default_dimension,
            fact_type="coverage",
            attribute=f"{default_dimension}.coverage",
            value=coverage_value,
            source_system=default_source,
            evidence_refs=evidence_refs,
            directness=default_directness,
            confidence="medium",
            strength="supporting",
        )
        if coverage_record is not None:
            records.append(coverage_record)

    selected, truncated = _select_records(records)
    if not selected:
        return None
    case_seed = _json_dumps({
        "entity_id": entity_id,
        "dimensions": sorted({record.dimension for record in selected}),
        "source_systems": sorted({record.source_system for record in selected}),
        "evidence_refs": sorted({
            ref
            for record in selected
            for ref in record.evidence_refs
        }),
    })
    case_id = (
        "query-"
        + hashlib.sha256(case_seed.encode("utf-8")).hexdigest()[:16]
    )
    return FactLedger.model_validate({
        "contract_version": FACT_LEDGER_VERSION,
        "case_id": case_id,
        "scope_entity_ids": [entity_id],
        "records": [
            record.model_dump(mode="json", exclude_none=True)
            for record in selected
        ],
        "record_count": len(selected),
        "truncated": truncated,
        "source": "robusta_legacy_adapter",
        "legacy_contract": True,
    })


def _integer_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def build_kubernetes_lifecycle_fact_ledger(
    structured: Any,
) -> FactLedger | None:
    """Adapt source-backed Pod lifecycle observations into a bounded ledger."""
    if not isinstance(structured, Mapping):
        return None

    name = str(structured.get("name") or "").strip()
    namespace = str(structured.get("namespace") or "").strip()
    if not name:
        return None
    evidence_refs = _evidence_refs(structured)
    if not evidence_refs:
        return None

    primary = {
        "kind": "Pod",
        "namespace": namespace,
        "name": name,
        "uid": str(structured.get("uid") or "").strip(),
    }
    entity_id = _entity_id(primary)
    records: list[FactRecord] = []

    def add_record(
        *,
        attribute: str,
        value: Any,
        fact_type: str = "state",
        unit: Any = None,
        source_path: str = "",
        evidence_role: str = "symptom",
        timestamp: Any = None,
    ) -> None:
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension="kubernetes",
            fact_type=fact_type,
            attribute=attribute,
            value=value,
            unit=unit,
            source_system="kubernetes",
            evidence_refs=evidence_refs,
            directness="direct",
            confidence="high",
            strength="strong",
            timestamp=timestamp,
            metadata={
                key: item
                for key, item in {
                    "source_path": source_path,
                    "evidence_role": evidence_role,
                }.items()
                if item
            },
        )
        if record is not None:
            records.append(record)

    phase = str(structured.get("phase") or "").strip()
    if phase:
        add_record(
            attribute="pod.phase",
            value={"phase": phase},
            source_path="status.phase",
        )

    status = str(structured.get("status") or "").strip()
    internal_statuses = {
        "command_failed",
        "describe_summarized",
        "events_found",
        "extract_failed",
        "json_summarized",
        "kept_small_output",
        "logs_summarized",
        "pod_described",
        "query_parse_failed",
        "query_rejected",
        "query_succeeded",
        "text_summarized",
        "yaml_parse_failed",
        "yaml_summarized",
    }
    if status and status.lower() not in internal_statuses:
        add_record(
            attribute="pod.status",
            value={"status": status},
            source_path="status",
        )

    conditions = [
        item
        for item in (
            structured.get("conditions")
            if isinstance(structured.get("conditions"), list)
            else []
        )
        if isinstance(item, Mapping)
    ]
    for index, condition in enumerate(conditions):
        condition_type = str(condition.get("type") or "").strip()
        condition_status = str(condition.get("status") or "").strip()
        if not condition_type and not condition_status:
            continue
        reason = str(condition.get("reason") or "").strip()
        message = str(condition.get("message") or "").strip()[:2048]
        add_record(
            attribute="pod.condition",
            value={
                key: item
                for key, item in {
                    "type": condition_type,
                    "status": condition_status,
                    "reason": reason,
                    "message": message,
                }.items()
                if item
            },
            source_path=f"status.conditions[{index}]",
            # A Pod condition reports lifecycle impact. Its reason/message is
            # valuable supporting evidence, but the condition itself is not a
            # generic root cause. More direct events/logs retain causal roles.
            evidence_role="symptom",
            timestamp=(
                condition.get("lastTransitionTime")
                or condition.get("last_transition_time")
            ),
        )

    spec_containers = [
        item
        for item in (
            structured.get("containers")
            if isinstance(structured.get("containers"), list)
            else []
        )
        if isinstance(item, Mapping)
    ]
    status_containers = [
        item
        for item in (
            structured.get("containerStatuses")
            if isinstance(structured.get("containerStatuses"), list)
            else []
        )
        if isinstance(item, Mapping)
    ]

    for container in spec_containers:
        container_name = str(container.get("name") or "").strip()
        if not container_name:
            continue

        resources = (
            container.get("resources")
            if isinstance(container.get("resources"), Mapping)
            else {}
        )
        for resource_group, attribute_group in (
            ("limits", "resource_limit"),
            ("requests", "resource_request"),
        ):
            quantities = (
                resources.get(resource_group)
                if isinstance(resources.get(resource_group), Mapping)
                else {}
            )
            for resource_name in ("cpu", "memory"):
                quantity = quantities.get(resource_name)
                if quantity in (None, ""):
                    continue
                add_record(
                    attribute=(
                        f"container.{attribute_group}.{resource_name}"
                    ),
                    value={
                        "container": container_name,
                        "value": str(quantity),
                    },
                    fact_type="configuration",
                    unit="kubernetes_quantity",
                    source_path=(
                        f"spec.containers[{container_name}]"
                        f".resources.{resource_group}.{resource_name}"
                    ),
                    evidence_role="context",
                )

        for env_index, env in enumerate(container.get("env") or []):
            if not isinstance(env, Mapping):
                continue
            value_from = (
                env.get("valueFrom")
                if isinstance(env.get("valueFrom"), Mapping)
                else env.get("value_from")
                if isinstance(env.get("value_from"), Mapping)
                else {}
            )
            for ref_key, kind in (
                ("secretKeyRef", "Secret"),
                ("configMapKeyRef", "ConfigMap"),
                ("secret_key_ref", "Secret"),
                ("config_map_key_ref", "ConfigMap"),
            ):
                ref = value_from.get(ref_key)
                if not isinstance(ref, Mapping) or not ref.get("name"):
                    continue
                add_record(
                    attribute="container.environment_reference",
                    value={
                        "container": container_name,
                        "environment": str(env.get("name") or ""),
                        "kind": kind,
                        "name": str(ref.get("name")),
                        "key": str(ref.get("key") or ""),
                        "optional": bool(ref.get("optional", False)),
                    },
                    fact_type="configuration",
                    source_path=(
                        f"spec.containers[{container_name}].env[{env_index}]"
                        f".valueFrom.{ref_key}"
                    ),
                    evidence_role="context",
                )
                break

    lifecycle_containers = status_containers or spec_containers
    for container in lifecycle_containers:
        container_name = str(container.get("name") or "").strip()
        if not container_name:
            continue

        last_state_mapping = (
            container.get("lastState")
            if isinstance(container.get("lastState"), Mapping)
            else container.get("last_state")
            if isinstance(container.get("last_state"), Mapping)
            else {}
        )
        state_mapping = (
            container.get("state")
            if isinstance(container.get("state"), Mapping)
            else {}
        )
        last_terminated = (
            container.get("lastTerminated")
            if isinstance(container.get("lastTerminated"), Mapping)
            else container.get("last_terminated")
            if isinstance(container.get("last_terminated"), Mapping)
            else last_state_mapping.get("terminated")
            if isinstance(last_state_mapping.get("terminated"), Mapping)
            else {}
        )
        current_terminated = (
            container.get("terminated")
            if isinstance(container.get("terminated"), Mapping)
            else state_mapping.get("terminated")
            if isinstance(state_mapping.get("terminated"), Mapping)
            else {}
        )
        terminated = last_terminated or current_terminated
        last_state = str(
            container.get("last_state")
            or container.get("lastState")
            or ""
        ).strip()
        current_state = (
            ""
            if state_mapping
            else str(container.get("state") or "").strip()
        )
        is_terminated = (
            bool(terminated)
            or last_state.lower() == "terminated"
            or current_state.lower() == "terminated"
        )

        reason = str(
            terminated.get("reason")
            or container.get("last_terminated_reason")
            or (container.get("reason") if is_terminated else "")
            or ""
        ).strip()
        if reason:
            add_record(
                attribute="container.last_terminated_reason",
                value={"container": container_name, "reason": reason},
                source_path=(
                    f"status.containerStatuses[{container_name}]"
                    ".lastState.terminated.reason"
                ),
                evidence_role="causal_candidate",
            )

        terminated_message = str(terminated.get("message") or "").strip()[:2048]
        if terminated_message:
            add_record(
                attribute="container.last_terminated_message",
                value={
                    "container": container_name,
                    "message": terminated_message,
                },
                source_path=(
                    f"status.containerStatuses[{container_name}]"
                    ".lastState.terminated.message"
                ),
                evidence_role="causal_candidate",
            )

        exit_code = _integer_value(
            terminated.get("exitCode")
            if "exitCode" in terminated
            else terminated.get("exit_code")
            if "exit_code" in terminated
            else container.get("exit_code")
            if "exit_code" in container
            else container.get("exitCode")
        )
        if exit_code is not None:
            add_record(
                attribute="container.last_exit_code",
                value={"container": container_name, "exit_code": exit_code},
                source_path=(
                    f"status.containerStatuses[{container_name}]"
                    ".lastState.terminated.exitCode"
                ),
            )

        waiting = (
            container.get("waiting")
            if isinstance(container.get("waiting"), Mapping)
            else state_mapping.get("waiting")
            if isinstance(state_mapping.get("waiting"), Mapping)
            else {}
        )
        waiting_reason = str(waiting.get("reason") or "").strip()
        if waiting_reason:
            add_record(
                attribute="container.waiting_reason",
                value={"container": container_name, "reason": waiting_reason},
                source_path=(
                    f"status.containerStatuses[{container_name}]"
                    ".state.waiting.reason"
                ),
                evidence_role="causal_candidate",
            )
        waiting_message = str(waiting.get("message") or "").strip()[:2048]
        if waiting_message:
            add_record(
                attribute="container.waiting_message",
                value={"container": container_name, "message": waiting_message},
                source_path=(
                    f"status.containerStatuses[{container_name}]"
                    ".state.waiting.message"
                ),
                evidence_role="causal_candidate",
            )

        restart_count = _integer_value(
            container.get("restart_count")
            if "restart_count" in container
            else container.get("restartCount")
        )
        if restart_count is not None:
            add_record(
                attribute="container.restart_count",
                value={
                    "container": container_name,
                    "restart_count": restart_count,
                },
                fact_type="measurement",
                unit="count",
                source_path=(
                    f"status.containerStatuses[{container_name}].restartCount"
                ),
            )

    event_seen: set[str] = set()
    event_index = 0
    for event_field in ("events", "selected_events", "key_events"):
        candidates = (
            structured.get(event_field)
            if isinstance(structured.get(event_field), list)
            else []
        )
        for item in candidates:
            if isinstance(item, Mapping):
                event_type = str(item.get("type") or "").strip()
                reason = str(item.get("reason") or "").strip()
                message = str(item.get("message") or "").strip()[:2048]
                source = item.get("source")
                if isinstance(source, Mapping):
                    source = source.get("component") or source.get("host")
                source = str(source or item.get("from") or "").strip()
                timestamp = (
                    item.get("lastTimestamp")
                    or item.get("eventTime")
                    or item.get("firstTimestamp")
                    or item.get("timestamp")
                )
            else:
                text = str(item or "").strip()
                normalized_header = " ".join(text.lower().split())
                if (
                    not text
                    or (
                        "last seen" in normalized_header
                        and "type" in normalized_header
                        and "reason" in normalized_header
                        and "message" in normalized_header
                    )
                ):
                    continue
                event_row = re.match(
                    r"^(Normal|Warning)\s+(\S+)\s+.+$",
                    text,
                    flags=re.IGNORECASE,
                )
                event_type = event_row.group(1) if event_row else ""
                reason = event_row.group(2) if event_row else ""
                message = text[:2048]
                source = ""
                timestamp = None
            signature = _json_dumps({
                "type": event_type,
                "reason": reason,
                "message": message,
                "source": source,
                "timestamp": timestamp,
            })
            if not message or signature in event_seen:
                continue
            event_seen.add(signature)
            add_record(
                attribute="event.message",
                value={
                    key: value
                    for key, value in {
                        "type": event_type,
                        "reason": reason,
                        "message": message,
                        "source": source,
                    }.items()
                    if value
                },
                fact_type="event",
                source_path=f"{event_field}[{event_index}]",
                evidence_role=(
                    "causal_candidate"
                    if event_type.lower() == "warning" or reason
                    else "context"
                ),
                timestamp=timestamp,
            )
            event_index += 1

    selected, truncated = _select_records(records)
    if not selected:
        return None
    case_seed = _json_dumps({
        "entity_id": entity_id,
        "evidence_refs": evidence_refs,
        "attributes": sorted(record.attribute for record in selected),
    })
    return FactLedger.model_validate({
        "contract_version": FACT_LEDGER_VERSION,
        "case_id": (
            "kubernetes-lifecycle-"
            + hashlib.sha256(case_seed.encode("utf-8")).hexdigest()[:16]
        ),
        "scope_entity_ids": [entity_id],
        "records": [
            record.model_dump(mode="json", exclude_none=True)
            for record in selected
        ],
        "record_count": len(selected),
        "truncated": truncated,
        "source": "robusta_legacy_adapter",
        "legacy_contract": True,
    })


def build_legacy_fact_ledger(structured: Any) -> FactLedger | None:
    """Build a diagnosis-free ledger from legacy source observations."""
    if not isinstance(structured, Mapping):
        return None
    primary = (
        structured.get("primary_entity")
        if isinstance(structured.get("primary_entity"), Mapping)
        else {}
    )
    if not primary or not str(primary.get("name") or "").strip():
        return None
    case_id = str(structured.get("case_id") or "").strip()
    if not case_id:
        return None

    entity_id = _entity_id(primary)
    records: list[FactRecord] = []
    coverage = structured.get("coverage") if isinstance(structured.get("coverage"), Mapping) else {}
    for raw_dimension, status in sorted(coverage.items(), key=lambda item: str(item[0])):
        dimension = _normalize_dimension(raw_dimension)
        if dimension not in {"kubernetes", "metrics", "logging", "tracing", "topology"}:
            continue
        status_text = str(status or "").strip()
        weak = status_text.lower() in {
            "weak",
            "weak_context",
            "related_context",
            "absent",
            "empty",
            "error",
            "unavailable",
        }
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension=dimension,
            fact_type="coverage",
            attribute=f"{dimension}.coverage",
            value={"dimension": dimension, "status": status_text},
            source_system="robusta",
            evidence_refs=[],
            directness="related_context",
            confidence="weak" if weak else "medium",
            strength="context",
        )
        if record is not None:
            records.append(record)

    details = (
        structured.get("dimension_details")
        if isinstance(structured.get("dimension_details"), Mapping)
        else {}
    )
    metrics = details.get("metrics") if isinstance(details.get("metrics"), Mapping) else {}
    for item in metrics.get("highlights") or []:
        if not isinstance(item, Mapping):
            continue
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension="metrics",
            fact_type="measurement",
            attribute=str(item.get("metric") or "metrics.highlight"),
            value=dict(item),
            unit=item.get("unit"),
            source_system=str(item.get("source_system") or "prometheus"),
            evidence_refs=_evidence_refs(item),
            timestamp=item.get("timestamp"),
            start=item.get("start"),
            end=item.get("end"),
        )
        if record is not None:
            records.append(record)

    logs = details.get("logs") if isinstance(details.get("logs"), Mapping) else {}
    for item in logs.get("samples") or []:
        if not isinstance(item, Mapping):
            continue
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension="logging",
            fact_type="log",
            attribute="log.message",
            value=dict(item),
            source_system=str(item.get("source_system") or "elasticsearch"),
            evidence_refs=_evidence_refs(item),
            timestamp=item.get("timestamp"),
        )
        if record is not None:
            records.append(record)

    tracing = details.get("tracing") if isinstance(details.get("tracing"), Mapping) else {}
    for item in tracing.get("flows") or []:
        if not isinstance(item, Mapping):
            continue
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension="tracing",
            fact_type="flow",
            attribute="network.flow",
            value=dict(item),
            source_system=str(item.get("source_system") or "deepflow"),
            evidence_refs=_evidence_refs(item),
            directness=str(item.get("directness") or "direct"),
            confidence=str(item.get("confidence") or "medium"),
            timestamp=item.get("timestamp"),
        )
        if record is not None:
            records.append(record)
    for item in tracing.get("spans") or []:
        if not isinstance(item, Mapping):
            continue
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension="tracing",
            fact_type="span",
            attribute="trace.span",
            value=dict(item),
            source_system=str(item.get("source_system") or "tempo"),
            evidence_refs=_evidence_refs(item),
            timestamp=item.get("timestamp") or item.get("start"),
            start=item.get("start"),
            end=item.get("end"),
        )
        if record is not None:
            records.append(record)

    topology = details.get("topology") if isinstance(details.get("topology"), Mapping) else {}
    for item in topology.get("edges") or []:
        if not isinstance(item, Mapping):
            continue
        record = _legacy_record(
            entity_id=entity_id,
            primary=primary,
            dimension="topology",
            fact_type="relationship",
            attribute="topology.relationship",
            value=dict(item),
            source_system=str(item.get("source_system") or "topology"),
            evidence_refs=_evidence_refs(item),
            directness=str(item.get("directness") or "related_context"),
            confidence=str(item.get("confidence") or "weak"),
            strength="supporting",
        )
        if record is not None:
            records.append(record)

    selected, truncated = _select_records(records)
    if not selected:
        return None
    return FactLedger.model_validate({
        "contract_version": FACT_LEDGER_VERSION,
        "case_id": case_id,
        "scope_entity_ids": [entity_id],
        "records": [record.model_dump(mode="json", exclude_none=True) for record in selected],
        "record_count": len(selected),
        "truncated": truncated,
        "source": "robusta_legacy_adapter",
        "legacy_contract": True,
    })


def normalize_case_fact_ledger(structured: Any) -> FactLedger | None:
    if not isinstance(structured, Mapping):
        return None
    canonical = normalize_fact_ledger(structured.get("fact_ledger"))
    return canonical if canonical is not None else build_legacy_fact_ledger(structured)


def _ledger_dump(ledger: FactLedger, records: Sequence[FactRecord]) -> dict[str, Any]:
    return {
        "contract_version": FACT_LEDGER_VERSION,
        "case_id": ledger.case_id,
        "scope_entity_ids": ledger.scope_entity_ids,
        "records": [
            record.model_dump(mode="json", exclude_none=True)
            for record in records
        ],
        "record_count": len(records),
        "truncated": ledger.truncated or len(records) < len(ledger.records),
        "source": ledger.source,
        "legacy_contract": ledger.legacy_contract,
    }


def _json_dumps(value: Any, *, indent: int | None = None) -> str:
    kwargs: dict[str, Any] = {
        "ensure_ascii": False,
        "sort_keys": True,
        "default": str,
    }
    if indent is None:
        kwargs["separators"] = (",", ":")
    else:
        kwargs["indent"] = indent
    return json.dumps(value, **kwargs)


def compact_fact_ledgers_json(
    ledgers: Sequence[FactLedger | Mapping[str, Any]],
    *,
    max_chars: int = DEFAULT_AGENT_CONTEXT_CHARS,
) -> str:
    """Serialize whole records only, preserving valid deterministic JSON."""
    if max_chars < MIN_FACT_LEDGER_JSON_CHARS:
        raise ValueError(
            "max_chars is below the minimum Fact Ledger JSON envelope"
        )
    normalized = [
        ledger
        for value in ledgers
        if (ledger := normalize_fact_ledger(value)) is not None
    ]
    normalized.sort(key=_ledger_sort_key)
    prioritized_records = [
        sorted(ledger.records, key=_representative_record_priority)
        for ledger in normalized
    ]
    full_payload = {
        "fact_ledgers": [
            _ledger_dump(ledger, prioritized_records[index])
            for index, ledger in enumerate(normalized)
        ]
    }
    full_text = _json_dumps(full_payload)
    if len(full_text) <= max_chars:
        return full_text

    selected: list[list[FactRecord]] = [[] for _ in normalized]
    base_payload = {
        "fact_ledgers": [
            _ledger_dump(ledger, [])
            for ledger in normalized
        ]
    }
    if len(_json_dumps(base_payload)) > max_chars:
        case_index = [
            {
                "case_id": ledger.case_id,
                "ledger_ref": (
                    "ledger-"
                    + hashlib.sha256(_json_dumps({
                        "case_id": ledger.case_id,
                        "scope_entity_ids": ledger.scope_entity_ids,
                        "source": ledger.source,
                    }).encode("utf-8")).hexdigest()[:12]
                ),
                "scope_entity_ids": ledger.scope_entity_ids,
            }
            for ledger in normalized
        ]
        index_payload = {
            "case_index": case_index,
            "fact_ledgers": [],
            "omitted_case_count": len(normalized),
            "truncated": True,
        }
        index_text = _json_dumps(index_payload)
        if len(index_text) > max_chars:
            raise ValueError(
                "max_chars is below the minimum required for the "
                "Fact Ledger case identity index"
            )
        return index_text

    selected_ids: set[str] = set()

    def add_candidate(ledger_index: int, record: FactRecord) -> bool:
        nonlocal selected
        if record.fact_id in selected_ids:
            return False
        candidate = [list(items) for items in selected]
        candidate[ledger_index].append(record)
        candidate_payload = {
            "fact_ledgers": [
                _ledger_dump(item, candidate[index])
                for index, item in enumerate(normalized)
            ]
        }
        if len(_json_dumps(candidate_payload)) <= max_chars:
            selected = candidate
            selected_ids.add(record.fact_id)
            return True
        return False

    grouped_records: dict[
        tuple[int, str, str],
        list[FactRecord],
    ] = {}
    for ledger_index, records in enumerate(prioritized_records):
        for record in records:
            grouped_records.setdefault(
                (ledger_index, record.entity_id, record.dimension),
                [],
            ).append(record)

    def candidate_order(
        ledger_index: int,
        record: FactRecord,
    ) -> tuple[Any, ...]:
        return (
            _global_record_priority(normalized[ledger_index], record),
            _ledger_sort_key(normalized[ledger_index]),
            _representative_record_priority(record),
        )

    first_representatives = sorted(
        (
            (ledger_index, records[0])
            for (
                ledger_index,
                _entity_id,
                _dimension,
            ), records in grouped_records.items()
            if records
        ),
        key=lambda item: candidate_order(*item),
    )
    for ledger_index, record in first_representatives:
        add_candidate(ledger_index, record)

    source_representatives = sorted(
        (
            (ledger_index, record)
            for (
                ledger_index,
                _entity_id,
                _dimension,
            ), records in grouped_records.items()
            for source_system in sorted({
                item.source_system
                for item in records
            })
            if (
                record := next(
                    (
                        item
                        for item in records
                        if item.source_system == source_system
                    ),
                    None,
                )
            )
            is not None
        ),
        key=lambda item: candidate_order(*item),
    )
    for ledger_index, record in source_representatives:
        add_candidate(ledger_index, record)

    second_representatives = sorted(
        (
            (ledger_index, records[1])
            for (
                ledger_index,
                _entity_id,
                _dimension,
            ), records in grouped_records.items()
            if len(records) > 1
        ),
        key=lambda item: candidate_order(*item),
    )
    for ledger_index, record in second_representatives:
        add_candidate(ledger_index, record)

    global_candidates = sorted(
        (
            (ledger_index, record)
            for ledger_index, records in enumerate(prioritized_records)
            for record in records
        ),
        key=lambda item: candidate_order(*item),
    )
    for ledger_index, record in global_candidates:
        add_candidate(ledger_index, record)

    return _json_dumps({
        "fact_ledgers": [
            _ledger_dump(ledger, selected[index])
            for index, ledger in enumerate(normalized)
        ]
    })


def _bounded_value(
    value: Any,
    *,
    mapping_limit: int | None,
    list_limit: int | None,
    string_limit: int | None,
) -> Any:
    if isinstance(value, Mapping):
        items = [
            (key, item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if not is_forbidden_fact_key(key)
        ]
        if mapping_limit is not None:
            items = items[:mapping_limit]
        return {
            str(key): _bounded_value(
                item,
                mapping_limit=mapping_limit,
                list_limit=list_limit,
                string_limit=string_limit,
            )
            for key, item in items
        }
    if isinstance(value, (list, tuple)):
        items = list(value)
        if list_limit is not None:
            items = items[:list_limit]
        return [
            _bounded_value(
                item,
                mapping_limit=mapping_limit,
                list_limit=list_limit,
                string_limit=string_limit,
            )
            for item in items
        ]
    if (
        isinstance(value, str)
        and string_limit is not None
        and len(value) > string_limit
    ):
        return value[:string_limit] + f"...[value truncated from {len(value)} chars]"
    return value


def bounded_json_dumps(
    value: Any,
    *,
    max_chars: int,
    indent: int | None = None,
) -> str:
    """Bound JSON by pruning values before serialization, never serialized text."""
    if max_chars < 2:
        raise ValueError("max_chars is below the minimum JSON object envelope")
    sanitized = _bounded_value(
        value,
        mapping_limit=None,
        list_limit=None,
        string_limit=None,
    )
    text = _json_dumps(sanitized, indent=indent)
    if len(text) <= max_chars:
        return text
    for mapping_limit, list_limit, string_limit in (
        (48, 24, 1000),
        (24, 12, 500),
        (12, 6, 250),
        (6, 3, 160),
        (3, 1, 96),
        (1, 0, 64),
        (0, 0, 64),
    ):
        candidate = _bounded_value(
            sanitized,
            mapping_limit=mapping_limit,
            list_limit=list_limit,
            string_limit=string_limit,
        )
        text = _json_dumps(candidate, indent=indent)
        if len(text) <= max_chars:
            return text
    return "{}"


def compact_aiops_legacy_context_json(
    value: Mapping[str, Any],
    *,
    max_chars: int = DEFAULT_AGENT_CONTEXT_CHARS,
) -> str:
    """Compact legacy AIOps context while reserving exact case/Pod identity."""
    if max_chars < 2:
        raise ValueError("max_chars is below the minimum JSON object envelope")
    sanitized = sanitize_evidence_value(value)
    if not isinstance(sanitized, Mapping) or not sanitized:
        return ""

    case_id = str(sanitized.get("case_id") or "").strip()
    primary = (
        sanitized.get("primary_entity")
        if isinstance(sanitized.get("primary_entity"), Mapping)
        else {}
    )
    name = str(primary.get("name") or "").strip()
    if not case_id or not name:
        rendered = bounded_json_dumps(sanitized, max_chars=max_chars)
        if rendered == "{}":
            raise ValueError(
                "non-empty partial AIOps context cannot fit the context budget"
            )
        return rendered

    mandatory_primary = {
        "kind": str(primary.get("kind") or "Pod").strip() or "Pod",
    }
    for key in ("namespace", "name", "uid"):
        text = str(primary.get(key) or "").strip()
        if text:
            mandatory_primary[key] = text
    mandatory = {
        "case_id": case_id,
        "primary_entity": mandatory_primary,
    }
    minimum_text = _json_dumps(mandatory)
    if len(minimum_text) > max_chars:
        raise ValueError(
            "mandatory AIOps case and primary Pod identity exceed context budget"
        )

    optional = {
        key: item
        for key, item in sanitized.items()
        if key not in {"case_id", "primary_entity"}
    }
    optional_primary = {
        key: item
        for key, item in primary.items()
        if key not in {"kind", "namespace", "name", "uid"}
    }

    for mapping_limit, list_limit, string_limit in (
        (None, None, None),
        (48, 24, 1000),
        (24, 12, 500),
        (12, 6, 250),
        (6, 3, 160),
        (3, 1, 96),
        (1, 0, 64),
        (0, 0, 64),
    ):
        candidate = _bounded_value(
            optional,
            mapping_limit=mapping_limit,
            list_limit=list_limit,
            string_limit=string_limit,
        )
        bounded_primary = _bounded_value(
            optional_primary,
            mapping_limit=mapping_limit,
            list_limit=list_limit,
            string_limit=string_limit,
        )
        candidate["case_id"] = case_id
        candidate["primary_entity"] = {
            **bounded_primary,
            **mandatory_primary,
        }
        text = _json_dumps(candidate)
        if len(text) <= max_chars:
            return text

    return minimum_text


def _agent_context_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
    return dict(parsed) if isinstance(parsed, Mapping) else None


def _minimal_aiops_identity_envelope(value: Any) -> dict[str, Any] | None:
    context = _agent_context_mapping(value)
    if context is None:
        return None

    envelope: dict[str, Any] = {}
    case_id = str(context.get("case_id") or "").strip()
    if case_id:
        envelope["case_id"] = case_id

    primary = context.get("primary_entity")
    if isinstance(primary, Mapping):
        projected_primary = {
            key: primary.get(key)
            for key in ("kind", "namespace", "name", "uid")
            if primary.get(key) not in (None, "")
        }
        if projected_primary:
            envelope["primary_entity"] = projected_primary

    return envelope or None


def _fact_ledgers_from_agent_context(value: Any) -> list[FactLedger]:
    context = _agent_context_mapping(value)
    if context is None:
        return []

    native = normalize_fact_ledger(context.get("fact_ledger"))
    if native is not None:
        return [native]

    direct = normalize_fact_ledger(context)
    if direct is not None:
        return [direct]

    normalized: list[FactLedger] = []
    fact_ledgers = context.get("fact_ledgers")
    if isinstance(fact_ledgers, list):
        for candidate in fact_ledgers:
            ledger = normalize_fact_ledger(candidate)
            if ledger is not None:
                normalized.append(ledger)
        if normalized:
            return normalized

    query_ledger = build_observability_query_fact_ledger(context)
    if query_ledger is not None:
        return [query_ledger]

    adapted = normalize_case_fact_ledger(context)
    return [adapted] if adapted is not None else []


def _fact_ledger_from_agent_context(value: Any) -> FactLedger | None:
    """Compatibility wrapper for callers that only consume one ledger."""
    ledgers = _fact_ledgers_from_agent_context(value)
    return ledgers[0] if ledgers else None


def _has_substantive_value(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_has_substantive_value(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_substantive_value(item) for item in value)
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def _single_aiops_representation(
    item: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    copied = dict(item)
    representation_keys = {
        "data",
        "agent_facts",
        "agent_context",
        "fact_ledger",
    }
    metadata = {
        key: value
        for key, value in copied.items()
        if key not in representation_keys
    }

    adapter_ledger = _fact_ledger_from_agent_context(
        copied.get("agent_context")
    )
    if adapter_ledger is not None:
        metadata["fact_ledger"] = adapter_ledger.model_dump(
            mode="json",
            exclude_none=True,
        )
        return metadata, True

    identity_envelope = _minimal_aiops_identity_envelope(
        copied.get("agent_context")
    )
    agent_facts = str(copied.get("agent_facts") or "").strip()
    if agent_facts:
        if identity_envelope is not None:
            metadata["identity_envelope"] = identity_envelope
        metadata["agent_facts"] = agent_facts[:DEFAULT_AGENT_CONTEXT_CHARS]
        return metadata, False

    structured_context = _agent_context_mapping(copied.get("agent_context"))
    if structured_context is not None:
        bounded_context = bounded_json_dumps(
            structured_context,
            max_chars=DEFAULT_AGENT_CONTEXT_CHARS,
        )
        if _has_substantive_value(json.loads(bounded_context)):
            if identity_envelope is not None:
                metadata["identity_envelope"] = identity_envelope
            metadata["agent_context"] = bounded_context
            return metadata, False

    metadata["data"] = str(copied.get("data") or "")[:DEFAULT_AGENT_CONTEXT_CHARS]
    return metadata, False


def select_tool_data_for_rca(
    tool_data: Sequence[Mapping[str, Any]],
    *,
    supplementary_limit: int = 10,
) -> list[dict[str, Any]]:
    """Keep every case ledger before applying a limit to supplementary tools."""
    case_items: list[dict[str, Any]] = []
    supplementary: list[dict[str, Any]] = []
    for item in tool_data or []:
        if not isinstance(item, Mapping) or item.get("deduplicated") is True:
            continue
        if not tool_item_allows_fact_ledger_projection(item):
            continue
        copied = dict(item)
        native_ledger = normalize_fact_ledger(copied.get("fact_ledger"))
        if native_ledger is not None:
            if native_ledger.source == "mcp_canonical":
                for key in ("data", "agent_facts", "agent_context"):
                    copied.pop(key, None)
            copied["fact_ledger"] = native_ledger.model_dump(
                mode="json",
                exclude_none=True,
            )
            case_items.append(copied)
        elif _normalized_key(copied.get("tool")) not in {
            "readcontextarchive",
            "fetchrunbook",
        }:
            adapter_ledgers = _fact_ledgers_from_agent_context(
                copied.get("agent_context")
            )
            if adapter_ledgers:
                representation_keys = {
                    "data",
                    "agent_facts",
                    "agent_context",
                    "fact_ledger",
                }
                metadata = {
                    key: value
                    for key, value in copied.items()
                    if key not in representation_keys
                }
                case_items.extend({
                    **metadata,
                    "fact_ledger": ledger.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                } for ledger in adapter_ledgers)
                continue
            has_aiops_representation = any(
                key in copied
                for key in (
                    "fact_ledger",
                    "agent_context",
                    "agent_facts",
                )
            )
            if has_aiops_representation:
                projected, is_case = _single_aiops_representation(copied)
                if is_case:
                    case_items.append(projected)
                else:
                    supplementary.append(projected)
            else:
                supplementary.append(copied)
    detail_limit = max(0, supplementary_limit)
    selected_supplementary = supplementary[:detail_limit]
    for item in supplementary[detail_limit:]:
        identity_envelope = item.get("identity_envelope")
        if not isinstance(identity_envelope, Mapping) or not identity_envelope:
            continue
        identity_only = {
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
        identity_only["identity_envelope"] = dict(identity_envelope)
        selected_supplementary.append(identity_only)
    return case_items + selected_supplementary


def extract_fact_ledgers_from_tool_data(
    tool_data: Sequence[Mapping[str, Any]],
) -> list[FactLedger]:
    ledgers: list[FactLedger] = []
    for item in select_tool_data_for_rca(tool_data, supplementary_limit=0):
        ledger = normalize_fact_ledger(item.get("fact_ledger"))
        if ledger is not None:
            ledgers.append(ledger)
    return ledgers


def extract_fact_ledgers_from_evidence_analysis(value: Any) -> list[FactLedger]:
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, Mapping):
        return []
    tool_data = data.get("tool_data")
    return extract_fact_ledgers_from_tool_data(
        tool_data if isinstance(tool_data, list) else []
    )


def extract_fact_ledger_inputs_from_evidence_analysis(
    value: Any,
) -> list[FactLedger | dict[str, Any]]:
    """Return unsanitized ledger inputs for trust-boundary ID diagnostics."""
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, Mapping):
        return []

    tool_data = data.get("tool_data")
    if not isinstance(tool_data, list):
        return []

    ledgers: list[FactLedger | dict[str, Any]] = []
    for item in tool_data:
        if not isinstance(item, Mapping) or item.get("deduplicated") is True:
            continue
        if not tool_item_allows_fact_ledger_projection(item):
            continue
        raw_ledger = item.get("fact_ledger")
        if isinstance(raw_ledger, FactLedger):
            ledgers.append(raw_ledger)
            continue
        if (
            isinstance(raw_ledger, Mapping)
            and normalize_fact_ledger(raw_ledger) is not None
        ):
            ledgers.append(dict(raw_ledger))
            continue
        ledgers.extend(
            _fact_ledgers_from_agent_context(item.get("agent_context"))
        )
    return ledgers


def _append_unique(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        text = str(value or "").strip()
        if text and text not in target:
            target.append(text)


def tool_item_allows_fact_ledger_projection(
    item: Mapping[str, Any],
) -> bool:
    """结构校验：item 要么没有 ledger，要么携带可规范化的 ledger。

    早期的 report-authority 指纹校验机制已移除（过度设计）：
    fact ledger 的可信度由 normalize/validate 阶段保证。
    """
    raw_ledger = item.get("fact_ledger")
    if raw_ledger is None:
        return True
    if isinstance(raw_ledger, FactLedger):
        return True
    if not isinstance(raw_ledger, Mapping):
        return False
    return normalize_fact_ledger(raw_ledger) is not None


def _support_quality(record: FactRecord) -> bool:
    if record.fact_type == "coverage":
        return False
    if record.directness == "related_context":
        return False
    if record.confidence in {"low", "weak"}:
        return False
    return record.confidence == "high" or (
        record.directness == "direct"
        and record.confidence == "medium"
    )




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


def _in_entity_scope(record: FactRecord, entity_id: str) -> bool:
    if record.entity_id == entity_id:
        return True
    return (
        record.dimension == "topology"
        and record.fact_type == "relationship"
        and record.directness == "direct"
        and record.confidence == "high"
        and entity_id in _typed_topology_endpoints(record)
    )


def _record_scope_entities(
    record: FactRecord,
    scope_entities: Sequence[str],
) -> set[str]:
    allowed = set(scope_entities)
    matched = {record.entity_id} & allowed
    if (
        record.dimension == "topology"
        and record.fact_type == "relationship"
        and record.directness == "direct"
        and record.confidence == "high"
    ):
        matched.update(_typed_topology_endpoints(record) & allowed)
    return matched


def _raw_ledger_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, FactLedger):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _ledger_identity_diagnostics(
    ledgers: Sequence[FactLedger | Mapping[str, Any]],
) -> tuple[set[str], set[str]]:
    payloads_by_id: dict[str, set[str]] = {}
    mismatched: set[str] = set()
    for item in ledgers:
        raw = _raw_ledger_mapping(item)
        if raw is None:
            continue
        for record in raw.get("records") or []:
            if not isinstance(record, Mapping):
                continue
            fact_id = str(record.get("fact_id") or "").strip()
            if not fact_id or _record_contains_evaluator_fields(record):
                continue
            canonical = _canonical_record_json(record)
            payloads_by_id.setdefault(fact_id, set()).add(canonical)
            if fact_id != _canonical_fact_id(record):
                mismatched.add(fact_id)
    collisions = {
        fact_id
        for fact_id, payloads in payloads_by_id.items()
        if len(payloads) > 1
    }
    return mismatched, collisions




































_LONG_FACT_ID_PREFIX = re.compile(r"^fact-[0-9a-f]{11,}$")
_QWEN_FACT_ID_ALIAS = re.compile(r"^f-([0-9a-f]{12})$")


def _strip_resolved_fact_reference_text(
    value: Any,
    *,
    resolved_prefixes: set[str],
) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_resolved_fact_reference_text(
                item,
                resolved_prefixes=resolved_prefixes,
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            cleaned
            for item in value
            if (
                cleaned := _strip_resolved_fact_reference_text(
                    item,
                    resolved_prefixes=resolved_prefixes,
                )
            )
            not in ("", None)
        ]
    if not isinstance(value, str):
        return value

    text = value
    for prefix in resolved_prefixes:
        text = re.sub(
            rf"(?:unknown\s+)?(?:supporting|contradicting|top-level)\s+"
            rf"fact\s+reference\s*:\s*{re.escape(prefix)}",
            "",
            text,
            flags=re.IGNORECASE,
        )
    text = re.sub(
        r"(?:^|[;；]\s*)one or more fact references failed validation"
        r"(?=$|[;；。])",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"Fact-reference validation did not support a diagnosed result\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(r"^[\s;；。]+|[\s;；]+$", "", text).strip()


def _correct_unique_fact_id_prefixes(
    value: Mapping[str, Any] | RCAOutput,
    *,
    record_ids: Sequence[str],
) -> dict[str, Any]:
    payload = (
        value.model_dump(mode="json")
        if isinstance(value, RCAOutput)
        else deepcopy(dict(value))
    )
    canonical_ids = sorted(set(record_ids))
    corrections: dict[str, str] = {}

    def resolve(reference: Any) -> Any:
        text = str(reference or "").strip()
        if text in canonical_ids:
            return reference
        qwen_alias = _QWEN_FACT_ID_ALIAS.fullmatch(text)
        if qwen_alias:
            canonical_prefix = f"fact-{qwen_alias.group(1)}"
            matches = [
                fact_id
                for fact_id in canonical_ids
                if fact_id.startswith(canonical_prefix)
            ]
        elif _LONG_FACT_ID_PREFIX.fullmatch(text):
            matches = [
                fact_id
                for fact_id in canonical_ids
                if fact_id.startswith(text)
            ]
        else:
            return reference
        if len(matches) == 1:
            corrections[text] = matches[0]
            return matches[0]
        return reference

    for key in ("supporting_fact_ids", "contradicting_fact_ids"):
        if isinstance(payload.get(key), list):
            payload[key] = [resolve(item) for item in payload[key]]
    for hypothesis in payload.get("hypotheses") or []:
        if not isinstance(hypothesis, dict):
            continue
        for key in ("supporting_fact_ids", "contradicting_fact_ids"):
            if isinstance(hypothesis.get(key), list):
                hypothesis[key] = [resolve(item) for item in hypothesis[key]]
    for item in payload.get("evidence_inventory") or []:
        if isinstance(item, dict) and "id" in item:
            item["id"] = resolve(item["id"])
    for item in payload.get("evidence_analysis") or []:
        if isinstance(item, dict) and "evidence_id" in item:
            item["evidence_id"] = resolve(item["evidence_id"])

    if corrections:
        payload = _strip_resolved_fact_reference_text(
            payload,
            resolved_prefixes=set(corrections),
        )
        if not str(payload.get("confidence_reason") or "").strip():
            payload["confidence_reason"] = (
                "Fact references normalized against the current ledger."
            )
    return payload


def validate_rca_claims(
    value: Mapping[str, Any] | RCAOutput,
    ledgers: Sequence[FactLedger | Mapping[str, Any]],
    *,
    authoritative_entity_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate model fact references and downgrade unsupported diagnoses."""
    mismatched_fact_ids, collision_fact_ids = _ledger_identity_diagnostics(ledgers)
    normalized_ledgers = [
        ledger
        for item in ledgers
        if (ledger := normalize_fact_ledger(item)) is not None
    ]
    if not normalized_ledgers:
        parsed = (
            value
            if isinstance(value, RCAOutput)
            else RCAOutput.model_validate(value)
        )
        return parsed.model_dump(mode="json")

    record_index: dict[str, FactRecord] = {}
    scope_entities: list[str] = []
    for ledger in normalized_ledgers:
        _append_unique(scope_entities, ledger.scope_entity_ids)
        for record in ledger.records:
            if record.fact_id not in collision_fact_ids:
                record_index[record.fact_id] = record

    authoritative_scope = list(dict.fromkeys(
        str(entity_id).strip()
        for entity_id in (authoritative_entity_ids or [])
        if str(entity_id or "").strip()
    ))
    validation_scope = authoritative_scope or scope_entities
    single_authoritative_entity = (
        authoritative_scope[0] if len(authoritative_scope) == 1 else ""
    )

    parsed = RCAOutput.model_validate(
        _correct_unique_fact_id_prefixes(
            value,
            record_ids=list(record_index),
        )
    )
    invalid_fact_ids: list[str] = sorted(
        mismatched_fact_ids | collision_fact_ids
    )
    reasons: list[str] = []
    for fact_id in sorted(mismatched_fact_ids):
        reasons.append(f"canonical fact ID mismatch: {fact_id}")
    for fact_id in sorted(collision_fact_ids):
        reasons.append(f"cross-ledger fact ID collision: {fact_id}")
    valid_hypotheses: list[dict[str, Any]] = []
    invalid_hypothesis_scopes: list[str] = []
    supported_entities: set[str] = set()
    valid_supporting: list[str] = []
    valid_contradicting: list[str] = []
    model_entity_overrides: list[dict[str, str]] = []
    supporting_fact_promotions: list[dict[str, Any]] = []

    for hypothesis in parsed.hypotheses:
        model_entity_id = str(hypothesis.entity_id or "").strip()
        entity_id = model_entity_id
        if single_authoritative_entity:
            entity_id = single_authoritative_entity
            if model_entity_id and model_entity_id != entity_id:
                model_entity_overrides.append({
                    "model_entity_id": model_entity_id,
                    "authoritative_entity_id": entity_id,
                })
        referenced_records = [
            record_index[fact_id]
            for fact_id in [
                *hypothesis.supporting_fact_ids,
                *hypothesis.contradicting_fact_ids,
            ]
            if fact_id in record_index
        ]
        if not entity_id:
            inferred_entities: set[str] = set()
            for record in referenced_records:
                inferred_entities.update(
                    _record_scope_entities(record, scope_entities)
                )
            if len(inferred_entities) == 1:
                entity_id = next(iter(inferred_entities))
            elif len(inferred_entities) > 1:
                _append_unique(
                    invalid_hypothesis_scopes,
                    [hypothesis.hypothesis_id],
                )
                reasons.append(
                    f"ambiguous entity scope for hypothesis {hypothesis.hypothesis_id}"
                )
            else:
                _append_unique(
                    invalid_hypothesis_scopes,
                    [hypothesis.hypothesis_id],
                )
                reasons.append(
                    f"unresolvable entity scope for hypothesis {hypothesis.hypothesis_id}"
                )
        elif entity_id not in validation_scope:
            _append_unique(
                invalid_hypothesis_scopes,
                [hypothesis.hypothesis_id],
            )
            reasons.append(f"hypothesis entity is outside current scope: {entity_id}")

        hypothesis_supporting: list[str] = []
        hypothesis_contradicting: list[str] = []
        for fact_id in hypothesis.supporting_fact_ids:
            record = record_index.get(fact_id)
            if record is None:
                _append_unique(invalid_fact_ids, [fact_id])
                reasons.append(f"unknown supporting fact reference: {fact_id}")
                continue
            if not entity_id or not _in_entity_scope(record, entity_id):
                _append_unique(invalid_fact_ids, [fact_id])
                reasons.append(
                    f"cross-entity supporting fact reference: {fact_id} "
                    f"belongs to {record.entity_id}, not {entity_id}"
                )
                continue
            if not _support_quality(record):
                _append_unique(invalid_fact_ids, [fact_id])
                reasons.append(
                    "weak, low-confidence, related-context, or coverage-only "
                    f"supporting fact cannot diagnose: {fact_id}"
                )
                continue
            _append_unique(hypothesis_supporting, [fact_id])
            _append_unique(valid_supporting, [fact_id])

        for fact_id in hypothesis.contradicting_fact_ids:
            record = record_index.get(fact_id)
            if record is None:
                _append_unique(invalid_fact_ids, [fact_id])
                reasons.append(f"unknown contradicting fact reference: {fact_id}")
                continue
            if not entity_id or not _in_entity_scope(record, entity_id):
                _append_unique(invalid_fact_ids, [fact_id])
                reasons.append(
                    f"cross-entity contradicting fact reference: {fact_id}"
                )
                continue
            _append_unique(hypothesis_contradicting, [fact_id])
            _append_unique(valid_contradicting, [fact_id])

        if entity_id and hypothesis_supporting:
            supported_entities.add(entity_id)
        valid_hypotheses.append({
            **hypothesis.model_dump(mode="json", exclude_none=True),
            "entity_id": entity_id or None,
            "supporting_fact_ids": hypothesis_supporting,
            "contradicting_fact_ids": hypothesis_contradicting,
        })

    # Small models commonly place valid Fact IDs at RCA top level but omit the
    # same IDs from their sole hypothesis. For one authoritative entity and one
    # hypothesis the mapping is unambiguous, so normalize that structural
    # omission without inventing a claim or choosing between hypotheses.
    if (
        len(validation_scope) == 1
        and len(valid_hypotheses) == 1
        and not valid_hypotheses[0].get("supporting_fact_ids")
    ):
        hypothesis = valid_hypotheses[0]
        entity_id = str(hypothesis.get("entity_id") or "").strip()
        promoted: list[str] = []
        for fact_id in parsed.supporting_fact_ids:
            record = record_index.get(fact_id)
            if (
                record is not None
                and entity_id
                and _in_entity_scope(record, entity_id)
                and _support_quality(record)
            ):
                _append_unique(promoted, [fact_id])
        if promoted:
            hypothesis["supporting_fact_ids"] = promoted
            _append_unique(valid_supporting, promoted)
            supported_entities.add(entity_id)
            supporting_fact_promotions.append({
                "hypothesis_id": str(hypothesis.get("hypothesis_id") or ""),
                "entity_id": entity_id,
                "fact_ids": promoted,
                "source": "top_level_supporting_fact_ids",
            })

    top_level_refs = [
        *parsed.supporting_fact_ids,
        *parsed.contradicting_fact_ids,
    ]
    for fact_id in top_level_refs:
        if fact_id not in record_index or fact_id in collision_fact_ids:
            _append_unique(invalid_fact_ids, [fact_id])
            reasons.append(f"unknown top-level fact reference: {fact_id}")

    required_entities = [
        entity_id
        for entity_id in validation_scope
        if entity_id.lower().startswith("k8s.pod:")
    ] or list(validation_scope)
    downgrade_reasons: list[str] = []
    if parsed.diagnostic_status == "diagnosed":
        if not valid_supporting:
            downgrade_reasons.append("no valid supporting facts remain")
        if not parsed.causal_chain:
            downgrade_reasons.append("no evidence-bound causal chain was provided")
        for entity_id in required_entities:
            if entity_id not in supported_entities:
                downgrade_reasons.append(
                    f"no valid supported hypothesis for required entity {entity_id}"
                )
        reasons.extend(downgrade_reasons)

    reasons = list(dict.fromkeys(reasons))
    should_downgrade = (
        parsed.diagnostic_status == "diagnosed"
        and bool(downgrade_reasons)
    )
    result = parsed.model_dump(mode="json")
    result["hypotheses"] = valid_hypotheses
    result["supporting_fact_ids"] = valid_supporting
    result["contradicting_fact_ids"] = valid_contradicting
    # 早期版本在此对 limitations/trace-gap 措辞做正则重写（过度设计，已移除）：
    # RCA 的 limitations 保持 LLM 原文，可信度由 fact-id 校验保证。

    rejected_claim: dict[str, Any] = {}
    if should_downgrade:
        rejected_claim = {
            "phenomenon": result.get("phenomenon"),
            "root_cause": result.get("root_cause"),
            "root_cause_summary": result.get("root_cause_summary"),
            "causal_chain": deepcopy(result.get("causal_chain") or {}),
            "confidence": result.get("confidence"),
            "confidence_reason": result.get("confidence_reason"),
        }
        generic_summary = "现有事实不足以发布经过校验的根因结论"
        result["diagnostic_status"] = "inconclusive"
        result["root_cause"] = generic_summary
        result["root_cause_summary"] = generic_summary
        result["causal_chain"] = {}
        result["confidence"] = min(float(result.get("confidence") or 0.0), 0.49)
        result["confidence_reason"] = "; ".join(reasons)
        _append_unique(result["unknowns"], reasons)
        limitations = str(result.get("limitations") or "").strip()
        validation_limit = "Fact-reference validation did not support a diagnosed result."
        result["limitations"] = (
            f"{limitations}\n{validation_limit}".strip()
            if limitations
            else validation_limit
        )

    reference_valid = not reasons and not invalid_fact_ids
    diagnosis_publishable = (
        result["diagnostic_status"] == "diagnosed"
        and not should_downgrade
        and bool(valid_supporting)
        and all(entity_id in supported_entities for entity_id in required_entities)
    )
    result["claim_validation"] = {
        # `valid` remains a compatibility alias for reference validity. It is
        # deliberately not the publication decision: a supported diagnosis
        # may contain an audited extra bad reference, while an inconclusive
        # result may have perfectly valid references.
        "valid": reference_valid,
        "reference_valid": reference_valid,
        # A model may attach an extra weak/unknown reference to an otherwise
        # source-backed diagnosis. Invalid references are removed and audited,
        # but they are fatal only when no valid supported hypothesis remains
        # for the authoritative entity scope.
        "diagnosis_supported": diagnosis_publishable,
        "diagnosis_publishable": diagnosis_publishable,
        "diagnostic_status": result["diagnostic_status"],
        "valid_supporting_fact_ids": valid_supporting,
        "valid_contradicting_fact_ids": valid_contradicting,
        "invalid_fact_ids": invalid_fact_ids,
        "reasons": reasons,
        # Preserve the model-authored claim for audit without publishing it as
        # the formal root cause. Phenomenon, evidence analysis and raw model
        # text remain in their original top-level fields.
        "rejected_claim": rejected_claim,
        "model_entity_overrides": model_entity_overrides,
        "supporting_fact_promotions": supporting_fact_promotions,
        "legacy_contract": any(ledger.legacy_contract for ledger in normalized_ledgers),
    }
    return result
