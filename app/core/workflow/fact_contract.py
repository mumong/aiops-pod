"""Generic Fact Ledger normalization, compaction, and RCA claim validation."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from pydantic import ValidationError

from app.core.workflow.schemas import FactLedger, FactRecord, RCAOutput


FACT_LEDGER_VERSION = "aiops.fact-ledger.v1"
MAX_FACT_RECORDS = 48
DEFAULT_AGENT_CONTEXT_CHARS = 12000
MIN_FACT_LEDGER_JSON_CHARS = len('{"fact_ledgers":[]}')

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
    if any(is_forbidden_fact_key(key) for key in value):
        return True
    if is_forbidden_fact_key(value.get("attribute")):
        return True
    return _contains_evaluator_fields(value)


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
    return (
        0 if record.fact_type == "coverage" else 1,
        _STRENGTH_ORDER.get(str(record.strength or ""), 5),
        _DIRECTNESS_ORDER.get(record.directness, 3),
        _CONFIDENCE_ORDER.get(record.confidence, 4),
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
    scope_entity_ids = _string_list(raw.get("scope_entity_ids"), limit=MAX_FACT_RECORDS)
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
    }
    payload["fact_id"] = _fact_id(payload)
    return _normalize_record(payload)


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


def _json_dumps(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


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
        if (ledger := (
            value if isinstance(value, FactLedger) else normalize_fact_ledger(value)
        )) is not None
    ]
    full_payload = {
        "fact_ledgers": [
            _ledger_dump(ledger, ledger.records)
            for ledger in normalized
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

    max_record_count = max(
        (len(ledger.records) for ledger in normalized),
        default=0,
    )
    for record_index in range(max_record_count):
        for ledger_index, ledger in enumerate(normalized):
            if record_index >= len(ledger.records):
                continue
            candidate = [list(items) for items in selected]
            candidate[ledger_index].append(ledger.records[record_index])
            candidate_payload = {
                "fact_ledgers": [
                    _ledger_dump(item, candidate[index])
                    for index, item in enumerate(normalized)
                ]
            }
            if len(_json_dumps(candidate_payload)) <= max_chars:
                selected = candidate

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


def bounded_json_dumps(value: Any, *, max_chars: int) -> str:
    """Bound JSON by pruning values before serialization, never serialized text."""
    if max_chars < 2:
        raise ValueError("max_chars is below the minimum JSON object envelope")
    sanitized = _bounded_value(
        value,
        mapping_limit=None,
        list_limit=None,
        string_limit=None,
    )
    text = _json_dumps(sanitized)
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
        text = _json_dumps(candidate)
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


def _fact_ledger_from_agent_context(value: Any) -> FactLedger | None:
    context = _agent_context_mapping(value)
    if context is None:
        return None

    direct = normalize_fact_ledger(context)
    if direct is not None:
        return direct

    fact_ledgers = context.get("fact_ledgers")
    if isinstance(fact_ledgers, list):
        for candidate in fact_ledgers:
            ledger = normalize_fact_ledger(candidate)
            if ledger is not None:
                return ledger

    return normalize_case_fact_ledger(context)


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

    structured_context = _agent_context_mapping(copied.get("agent_context"))
    if structured_context is not None:
        bounded_context = bounded_json_dumps(
            structured_context,
            max_chars=DEFAULT_AGENT_CONTEXT_CHARS,
        )
        if _has_substantive_value(json.loads(bounded_context)):
            metadata["agent_context"] = bounded_context
            return metadata, False

    agent_facts = str(copied.get("agent_facts") or "").strip()
    if agent_facts:
        metadata["agent_facts"] = agent_facts[:DEFAULT_AGENT_CONTEXT_CHARS]
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
        copied = dict(item)
        native_ledger = normalize_fact_ledger(copied.get("fact_ledger"))
        if native_ledger is not None:
            copied["fact_ledger"] = native_ledger.model_dump(
                mode="json",
                exclude_none=True,
            )
            case_items.append(copied)
        elif _normalized_key(copied.get("tool")) not in {
            "readcontextarchive",
            "fetchrunbook",
        }:
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
    return case_items + supplementary[:max(0, supplementary_limit)]


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
        adapter = _fact_ledger_from_agent_context(item.get("agent_context"))
        if adapter is not None:
            ledgers.append(adapter)
    return ledgers


def _append_unique(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        text = str(value or "").strip()
        if text and text not in target:
            target.append(text)


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


def validate_rca_claims(
    value: Mapping[str, Any] | RCAOutput,
    ledgers: Sequence[FactLedger | Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate model fact references and downgrade unsupported diagnoses."""
    parsed = value if isinstance(value, RCAOutput) else RCAOutput.model_validate(value)
    mismatched_fact_ids, collision_fact_ids = _ledger_identity_diagnostics(ledgers)
    normalized_ledgers = [
        ledger
        for item in ledgers
        if (ledger := normalize_fact_ledger(item)) is not None
    ]
    if not normalized_ledgers:
        return parsed.model_dump(mode="json")

    record_index: dict[str, FactRecord] = {}
    scope_entities: list[str] = []
    for ledger in normalized_ledgers:
        _append_unique(scope_entities, ledger.scope_entity_ids)
        for record in ledger.records:
            if record.fact_id not in collision_fact_ids:
                record_index[record.fact_id] = record

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

    for hypothesis in parsed.hypotheses:
        entity_id = str(hypothesis.entity_id or "").strip()
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
        elif entity_id not in scope_entities:
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
        for entity_id in scope_entities
        if entity_id.lower().startswith("k8s.pod:")
    ] or list(scope_entities)
    downgrade_reasons: list[str] = []
    if parsed.diagnostic_status == "diagnosed":
        if not valid_supporting:
            downgrade_reasons.append("no valid supporting facts remain")
        if invalid_fact_ids:
            downgrade_reasons.append(
                "one or more fact references failed validation"
            )
        if invalid_hypothesis_scopes:
            downgrade_reasons.append(
                "one or more hypotheses have invalid entity scope"
            )
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

    if should_downgrade:
        generic_summary = "Current facts are insufficient for a validated root-cause conclusion"
        result["diagnostic_status"] = "inconclusive"
        result["root_cause"] = generic_summary
        result["root_cause_summary"] = generic_summary
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

    result["claim_validation"] = {
        "valid": not reasons and not invalid_fact_ids,
        "diagnostic_status": result["diagnostic_status"],
        "valid_supporting_fact_ids": valid_supporting,
        "valid_contradicting_fact_ids": valid_contradicting,
        "invalid_fact_ids": invalid_fact_ids,
        "reasons": reasons,
        "legacy_contract": any(ledger.legacy_contract for ledger in normalized_ledgers),
    }
    return result
