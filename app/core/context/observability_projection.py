"""Evidence-first projection for observability MCP results.

The MCP response is the archived fact source.  This module creates a compact
working observation for the model without making fault-specific decisions.
All lossy choices are explicit in ``summary_selection`` and the complete MCP
response remains addressable through ``retrieval.raw_ref``.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


CONTRACT_VERSION = "aiops.observation.v1"
SELECTION_STRATEGY = (
    "information_ranked_pattern_round_robin_budget_scan_no_fault_names"
)
DEFAULT_LOCAL_TIMEZONE = "Asia/Shanghai"
IDENTITY_LABELS = {"__name__", "namespace", "pod", "uid", "pod_uid"}
LOG_FIELDS = (
    "event",
    "level",
    "message",
    "trace_id",
    "span_id",
    "http_status",
    "path",
    "duration_ms",
    "duration",
    "service",
)
LOG_IDENTITY_FIELDS = {"timestamp", "case_run_id", "pod", "pod_uid", "namespace"}
NOISY_METRIC_LABELS = {
    "id",
    "image_id",
    "name",
    "node",
    "instance",
    "job",
    "metrics_path",
    "service",
}


def compact_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    )


def _integer(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_timestamp(
    value: Any,
    source_system: str,
    local_timezone: str,
) -> Optional[dict[str, Any]]:
    text = str(value or "").strip()
    if not text:
        return None
    result: dict[str, Any] = {"original": text, "source_system": source_system}
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(local_timezone))
            result["assumed_timezone"] = local_timezone
        result["utc"] = parsed.astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
    except (ValueError, ZoneInfoNotFoundError):
        result["normalization_error"] = True
    return result


def _parse_json_message(value: Any) -> tuple[str, Optional[dict[str, Any]]]:
    if isinstance(value, dict):
        return compact_json(value), value
    if not isinstance(value, str):
        return str(value), None
    text = value.strip()
    if not text.startswith("{"):
        return value, None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return value, None
    return value, parsed if isinstance(parsed, dict) else None


def _minimal_entity(payload: dict[str, Any]) -> dict[str, Any]:
    entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
    result = {
        key: entity.get(key)
        for key in ("namespace", "pod", "pod_uid", "lifecycle_changed")
        if entity.get(key) is not None
    }
    for key in ("node", "pod_ip", "containers"):
        if entity.get(key) not in (None, "", []):
            result[key] = deepcopy(entity[key])
    return result


def _query_window(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    window = query.get("time_range") if isinstance(query.get("time_range"), dict) else {}
    return {
        key: window.get(key)
        for key in ("start", "end")
        if window.get(key) is not None
    }


def _query_ref(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    digest = str(query.get("dsl_sha256") or "").strip()
    if not digest:
        digest = hashlib.sha256(compact_json(query).encode("utf-8")).hexdigest()[:16]
    result: dict[str, Any] = {
        "hash": digest,
        "debug_available": bool(query),
    }
    for key in ("query_type", "identity_basis", "index"):
        if query.get(key) not in (None, ""):
            result[key] = deepcopy(query[key])
    if isinstance(query.get("executions"), list):
        result["execution_count"] = len(query["executions"])
    if payload.get("dimension") == "metrics":
        promql = str(query.get("promql") or "")
        metric_names = list(
            dict.fromkeys(re.findall(r"([A-Za-z_:][A-Za-z0-9_:]*)\s*\{", promql))
        )
        if metric_names:
            result["metric_names"] = metric_names
    elif payload.get("dimension") == "logging":
        filters = {
            key: deepcopy(query.get(key))
            for key in (
                "container",
                "keywords",
                "keyword_mode",
                "levels",
                "trace_id",
                "fields",
            )
            if query.get(key) not in (None, "", [])
        }
        if filters:
            result["filters"] = filters
    elif payload.get("dimension") == "tracing":
        filters = {
            key: deepcopy(query.get(key))
            for key in (
                "direction",
                "protocols",
                "response_codes",
                "response_statuses",
                "min_duration_us",
                "peer_ip",
                "trace_id",
                "request_resource",
                "service",
                "include_tempo",
            )
            if query.get(key) not in (None, "", [])
        }
        if filters:
            result["filters"] = filters
    return result


def _canonical_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = payload.get("fact_ledger") if isinstance(payload.get("fact_ledger"), dict) else {}
    records = ledger.get("records") if isinstance(ledger.get("records"), list) else []
    if not records:
        records = payload.get("facts") if isinstance(payload.get("facts"), list) else []
    canonical = [deepcopy(record) for record in records if isinstance(record, dict)]
    if str(payload.get("dimension") or "") != "logging" or not canonical:
        return canonical

    facts = payload.get("facts") if isinstance(payload.get("facts"), list) else []
    samples = payload.get("samples") if isinstance(payload.get("samples"), list) else []
    facts_by_ref = {
        str(item.get("ref")): item
        for item in facts
        if isinstance(item, dict) and item.get("ref")
    }
    samples_by_ref = {
        str(item.get("ref")): item
        for item in samples
        if isinstance(item, dict) and item.get("ref")
    }
    entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}

    for record in canonical:
        refs = [
            str(ref)
            for ref in (record.get("evidence_refs") or [])
            if str(ref or "").strip()
        ]
        source_fact = next(
            (facts_by_ref[ref] for ref in refs if ref in facts_by_ref),
            {},
        )
        source_sample = next(
            (samples_by_ref[ref] for ref in refs if ref in samples_by_ref),
            {},
        )
        metadata = (
            deepcopy(record.get("metadata"))
            if isinstance(record.get("metadata"), dict)
            else {}
        )

        def first_value(*values: Any) -> Any:
            return next(
                (value for value in values if value not in (None, "", [], {})),
                None,
            )

        enriched = {
            "container": first_value(
                metadata.get("container"),
                source_fact.get("container"),
                source_sample.get("container"),
            ),
            "pod_uid": first_value(
                metadata.get("pod_uid"),
                record.get("pod_uid"),
                source_fact.get("pod_uid"),
                source_sample.get("pod_uid"),
                entity.get("pod_uid"),
            ),
            "identity_basis": first_value(
                metadata.get("identity_basis"),
                source_fact.get("identity_basis"),
                source_sample.get("identity_basis"),
                query.get("identity_basis"),
            ),
            "value_original_length": first_value(
                metadata.get("value_original_length"),
                source_fact.get("value_original_length"),
                source_sample.get("message_original_length"),
            ),
            "value_sha256": first_value(
                metadata.get("value_sha256"),
                source_fact.get("value_sha256"),
                source_sample.get("message_sha256"),
            ),
            "value_truncated": first_value(
                metadata.get("value_truncated"),
                source_fact.get("value_truncated"),
                source_sample.get("message_truncated"),
            ),
            "raw_ref": first_value(
                metadata.get("raw_ref"),
                source_fact.get("raw_ref"),
                source_sample.get("raw_ref"),
            ),
        }
        metadata.update(
            {
                key: value
                for key, value in enriched.items()
                if value is not None
            }
        )
        if metadata:
            record["metadata"] = metadata
    return canonical


def _record_base(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    source_system = str(record.get("source_system") or "")
    result = {
        "id": record.get("fact_id") or record.get("ref"),
        "kind": record.get("fact_type") or record.get("name") or "evidence",
        "attribute": record.get("attribute") or record.get("name"),
        "source_system": source_system,
        "directness": record.get("directness"),
        "confidence": record.get("confidence"),
        "evidence_refs": list(
            record.get("evidence_refs")
            or ([record.get("ref")] if record.get("ref") else [])
        ),
    }
    timestamp = _normalize_timestamp(record.get("timestamp"), source_system, local_timezone)
    if timestamp:
        result["timestamp"] = timestamp
    return {key: value for key, value in result.items() if value not in (None, "", [])}


def _normalize_metric(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = _record_base(record, local_timezone)
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    labels = metadata.get("labels") if isinstance(metadata.get("labels"), dict) else {}
    if not labels and isinstance(record.get("labels"), dict):
        labels = record["labels"]
    result.update(
        {
            "metric": record.get("attribute") or record.get("name"),
            "value": deepcopy(record.get("value")),
            "unit": record.get("unit"),
            "labels": {
                key: deepcopy(value)
                for key, value in labels.items()
                if key not in IDENTITY_LABELS and value not in (None, "")
            },
            "stats": deepcopy(metadata.get("stats")),
            "sample_count": metadata.get("sample_count"),
            "trend_evaluable": metadata.get("trend_evaluable"),
        }
    )
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def _normalize_log(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = _record_base(record, local_timezone)
    raw_message, parsed = _parse_json_message(record.get("value"))
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if parsed is not None:
        result["message_raw"] = raw_message
        result["parsed"] = deepcopy(parsed)
        for key in LOG_FIELDS:
            if parsed.get(key) not in (None, ""):
                result[key] = deepcopy(parsed[key])
        attributes = {
            key: deepcopy(value)
            for key, value in parsed.items()
            if key not in set(LOG_FIELDS) | LOG_IDENTITY_FIELDS
            and isinstance(value, (str, int, float, bool))
            and value not in (None, "")
        }
        if attributes:
            result["attributes"] = attributes
    else:
        result["message"] = raw_message
    for key in (
        "container",
        "pod_uid",
        "identity_basis",
        "value_original_length",
        "value_sha256",
        "value_truncated",
        "raw_ref",
    ):
        value = metadata.get(key) if metadata.get(key) is not None else record.get(key)
        if value is not None:
            result[key] = deepcopy(value)
    return result


def _normalize_trace(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = _record_base(record, local_timezone)
    value = deepcopy(record.get("value"))
    if isinstance(value, dict):
        for key in ("syscall_trace_id_request", "syscall_trace_id_response"):
            if str(value.get(key) or "") == "0":
                value.pop(key, None)
        timestamp = _normalize_timestamp(
            value.get("timestamp") or record.get("timestamp"),
            str(record.get("source_system") or ""),
            local_timezone,
        )
        if timestamp:
            value["timestamp"] = timestamp
    result["trace_type"] = record.get("fact_type") or record.get("name")
    result["data"] = value
    return result


def _normalize_topology(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = _record_base(record, local_timezone)
    value = deepcopy(record.get("value"))
    if isinstance(value, dict):
        result["relationship"] = {
            key: value.get(key)
            for key in ("source", "relation", "target")
            if value.get(key) is not None
        }
        if value.get("relationship") is not None:
            result["relationship"]["description"] = value["relationship"]
    else:
        result["value"] = value
    return result


def _normalize_generic(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = _record_base(record, local_timezone)
    result["value"] = deepcopy(record.get("value"))
    result["unit"] = record.get("unit")
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def _normalized_evidence(
    payload: dict[str, Any],
    local_timezone: str,
) -> list[dict[str, Any]]:
    normalizer = {
        "metrics": _normalize_metric,
        "logging": _normalize_log,
        "tracing": _normalize_trace,
        "topology": _normalize_topology,
    }.get(str(payload.get("dimension") or ""), _normalize_generic)
    evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in _canonical_records(payload):
        normalized = normalizer(record, local_timezone)
        signature = str(normalized.get("id") or compact_json(normalized))
        if signature in seen:
            continue
        seen.add(signature)
        evidence.append(normalized)
    return evidence


def _source_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    telemetry = payload.get("telemetry")
    if not isinstance(telemetry, dict):
        return {}
    result: dict[str, Any] = {}
    for source, raw in telemetry.items():
        if not isinstance(raw, dict):
            continue
        item = {
            key: deepcopy(raw.get(key))
            for key in ("coverage", "directness", "executed", "reason", "identity_basis")
            if raw.get(key) is not None
        }
        meta = raw.get("query_meta") if isinstance(raw.get("query_meta"), dict) else {}
        for key in (
            "failed_trace_count",
            "successful_lookup_count",
            "invalid_tempo_trace_id_count",
        ):
            if meta.get(key) is not None:
                item[key] = meta[key]
        queried = meta.get("queried_trace_ids")
        if isinstance(queried, list):
            item["queried_trace_count"] = len(queried)
        if raw.get("error"):
            item["error"] = str(raw["error"])
        if item:
            result[str(source)] = item
    return result


def _counts(payload: dict[str, Any], evidence_count: int) -> dict[str, Any]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    upstream = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    backend_total = query.get("backend_total")
    matched = _integer(upstream.get("matched"))
    if matched is None:
        matched = _integer(backend_total.get("value")) if isinstance(backend_total, dict) else None
    if matched is None:
        matched = _integer(payload.get("raw_series_count"))
    if matched is None:
        matched = _integer(query.get("filtered_match_count"))
    retrieved = _integer(upstream.get("retrieved"))
    if retrieved is None:
        retrieved = _integer(query.get("uid_query_hits"))
    if retrieved is None and isinstance(query.get("executions"), list):
        hits = [
            _integer(item.get("hit_count"))
            for item in query["executions"]
            if isinstance(item, dict)
        ]
        retrieved = sum(value for value in hits if value is not None) if any(
            value is not None for value in hits
        ) else None
    normalized = _integer(upstream.get("normalized"))
    if normalized is None:
        normalized = evidence_count
    returned = _integer(upstream.get("returned"))
    if returned is None:
        returned = evidence_count
    dropped = _integer(upstream.get("dropped"))
    if dropped is None and matched is not None:
        dropped = max(0, matched - returned)
    result = {
        "matched": matched,
        "retrieved": retrieved,
        "normalized": normalized,
        "returned": returned,
        "dropped": dropped,
        "mcp_facts": len(payload.get("facts") or []),
        "mcp_samples": len(payload.get("samples") or []),
    }
    if payload.get("dimension") == "metrics":
        result.update(
            {
                "raw_series": _integer(payload.get("raw_series_count")),
                "projected_series": _integer(payload.get("series_count")),
                "serialized_series": len(payload.get("series") or []),
            }
        )
    if payload.get("dimension") == "tracing":
        records = _canonical_records(payload)
        result.update(
            {
                "serialized_flows": len(payload.get("flows") or []),
                "serialized_spans": len(payload.get("spans") or []),
                "ledger_flows": sum(item.get("fact_type") == "flow" for item in records),
                "ledger_spans": sum(item.get("fact_type") == "span" for item in records),
            }
        )
    return {key: value for key, value in result.items() if value is not None}


def _truncation(payload: dict[str, Any]) -> dict[str, Any]:
    upstream = payload.get("truncation") if isinstance(payload.get("truncation"), dict) else {}
    legacy_truncated = bool(upstream.get("truncated", payload.get("truncated")))
    limits = payload.get("limits") if isinstance(payload.get("limits"), dict) else {}
    serialization = payload.get("serialization") if isinstance(payload.get("serialization"), dict) else {}
    response_truncated = serialization.get("response_truncated")
    reasons: list[str] = []
    stages = upstream.get("stages") if isinstance(upstream.get("stages"), list) else []
    for stage in stages:
        if isinstance(stage, dict) and stage.get("reason"):
            reasons.append(str(stage["reason"]))
    if legacy_truncated:
        reasons.append("source_or_collection_limit")
    if limits.get("max_serialized_bytes"):
        reasons.append("legacy_mcp_response_budget_possible")
        if response_truncated is None:
            response_truncated = legacy_truncated
    if response_truncated is True:
        reasons.append("mcp_response_budget")
    return {
        "truncated": legacy_truncated or response_truncated is True,
        "source_or_collection_truncated": legacy_truncated,
        "mcp_response_truncated": response_truncated,
        "reasons": list(dict.fromkeys(reasons)),
        "stages": deepcopy(stages),
        "reason_detail_complete": bool(stages) or not legacy_truncated,
        "next_cursor": payload.get("next_cursor"),
    }


def _message_template(message: str) -> str:
    value = message.lower()
    value = re.sub(r"\b[0-9a-f]{16,}\b", "<id>", value)
    value = re.sub(r"\b\d+(?:\.\d+)?\b", "<n>", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:160]


def _selection_bucket(item: dict[str, Any]) -> str:
    if item.get("trace_type"):
        data = item.get("data") if isinstance(item.get("data"), dict) else {}
        return compact_json(
            [
                "trace",
                item.get("trace_type"),
                data.get("response_code") or data.get("status_code"),
                data.get("response_status") or data.get("status"),
                _message_template(
                    str(
                        data.get("request_resource")
                        or data.get("resource")
                        or data.get("span_name")
                        or ""
                    )
                ),
            ]
        )
    if item.get("metric"):
        labels = item.get("labels") if isinstance(item.get("labels"), dict) else {}
        controls = {
            key: labels.get(key)
            for key in ("container", "phase", "reason", "condition", "probe_type", "result")
            if labels.get(key) is not None
        }
        return compact_json(["metric", item.get("metric"), controls])
    message = str(item.get("message") or item.get("message_raw") or "")
    if message:
        return compact_json(
            ["log", item.get("level"), item.get("event"), _message_template(message)]
        )
    relationship = item.get("relationship")
    if isinstance(relationship, dict):
        return compact_json(["topology", relationship.get("relation")])
    return compact_json([item.get("kind"), item.get("attribute")])


def _selection_value_state(item: dict[str, Any]) -> str:
    """Classify value presence for projection auditing without fault semantics."""
    value = item.get("value")
    if value is None and isinstance(item.get("stats"), dict):
        value = item["stats"].get("last")
    if value is None:
        return "missing"
    if isinstance(value, bool):
        return "nonzero" if value else "zero"
    try:
        return "zero" if float(value) == 0 else "nonzero"
    except (TypeError, ValueError):
        return "text_or_object"


def _selection_profile(item: dict[str, Any]) -> str:
    """Return a compact, case-agnostic signal profile for audit aggregation."""
    relationship = (
        item.get("relationship")
        if isinstance(item.get("relationship"), dict)
        else {}
    )
    signal = (
        item.get("metric")
        or item.get("trace_type")
        or item.get("event")
        or relationship.get("relation")
        or item.get("attribute")
        or item.get("kind")
        or "unknown"
    )
    kind = (
        "metric"
        if item.get("metric")
        else "trace"
        if item.get("trace_type")
        else "log"
        if item.get("message") or item.get("message_raw")
        else "topology"
        if relationship
        else str(item.get("kind") or "unknown")
    )
    return compact_json(
        {
            "confidence": item.get("confidence") or "unknown",
            "directness": item.get("directness") or "unknown",
            "kind": kind,
            "signal": signal,
            "value_state": _selection_value_state(item),
        }
    )


def _selection_family(item: dict[str, Any]) -> str:
    """Group patterns by their contract-level signal, never by fault names."""
    relationship = (
        item.get("relationship")
        if isinstance(item.get("relationship"), dict)
        else {}
    )
    if item.get("metric"):
        return compact_json(["metric", item.get("metric")])
    if item.get("trace_type"):
        return compact_json(["trace", item.get("trace_type")])
    if item.get("message") or item.get("message_raw"):
        return compact_json(["log", item.get("event") or "unclassified"])
    if relationship:
        return compact_json(["topology", relationship.get("relation")])
    return compact_json([item.get("kind"), item.get("attribute")])


def _selection_profile_counts(
    evidence: Iterable[dict[str, Any]],
) -> dict[str, int]:
    counts: "OrderedDict[str, int]" = OrderedDict()
    for item in evidence:
        profile = _selection_profile(item)
        counts[profile] = counts.get(profile, 0) + 1
    return dict(counts)


def _selection_priority(item: dict[str, Any]) -> tuple[int, int, int, int]:
    """Rank information without case names, fault names, or severity keywords."""
    value_rank = {
        "nonzero": 3,
        "text_or_object": 2,
        "missing": 1,
        "zero": 0,
    }[_selection_value_state(item)]
    directness_rank = {
        "direct": 2,
        "related_context": 1,
    }.get(str(item.get("directness") or ""), 0)
    confidence_rank = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }.get(str(item.get("confidence") or ""), 0)
    trend_rank = 1 if item.get("trend_evaluable") is True else 0
    return value_rank, directness_rank, confidence_rank, trend_rank


def _diverse_order(evidence: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: "OrderedDict[str, list[dict[str, Any]]]" = OrderedDict()
    for item in evidence:
        buckets.setdefault(_selection_bucket(item), []).append(item)
    ordered: list[dict[str, Any]] = []
    original_counts = {key: len(values) for key, values in buckets.items()}
    keys = list(buckets)
    stratified_keys: list[str] = []
    if keys:
        stratified_keys.append(keys[0])
    if len(keys) > 1:
        stratified_keys.append(keys[-1])
    intervals = [(1, len(keys) - 2)] if len(keys) > 2 else []
    while intervals:
        next_intervals: list[tuple[int, int]] = []
        for lower, upper in intervals:
            if lower > upper:
                continue
            midpoint = (lower + upper) // 2
            stratified_keys.append(keys[midpoint])
            next_intervals.extend(
                ((lower, midpoint - 1), (midpoint + 1, upper))
            )
        intervals = next_intervals

    # Preserve temporal stratification for equal signals, but let contract
    # quality and information state move useful representatives ahead of
    # zero-valued or weak context.  Python's stable sort keeps the prior
    # first/tail/midpoint ordering when priorities tie.
    stratified_keys.sort(
        key=lambda key: _selection_priority(buckets[key][0]),
        reverse=True,
    )

    # First wave: one representative from every semantic pattern. Give each
    # contract-level signal family its first opportunity before a second
    # pattern from the same family. This guarantees, for example, that trace
    # Flow and Span compete for the bounded view before another Flow pattern.
    # No case, pod, fault name, or severity keyword participates in ordering.
    family_keys: "OrderedDict[str, list[str]]" = OrderedDict()
    for key in stratified_keys:
        family_keys.setdefault(_selection_family(buckets[key][0]), []).append(key)
    first_wave_keys: list[str] = []
    while any(family_keys.values()):
        for values in family_keys.values():
            if values:
                first_wave_keys.append(values.pop(0))

    for key in first_wave_keys:
        values = buckets[key]
        if values:
            item = deepcopy(values.pop(0))
            item["pattern_count"] = original_counts[key]
            item["pattern_exemplar"] = "head"
            ordered.append(item)
    # Second wave: retain the other temporal edge before near-duplicates in
    # the middle. This protects change/progression context without keywords.
    for key in first_wave_keys:
        values = buckets[key]
        if values:
            item = deepcopy(values.pop(-1))
            item["pattern_count"] = original_counts[key]
            item["pattern_exemplar"] = "tail"
            ordered.append(item)
    while any(buckets.values()):
        for key in first_wave_keys:
            values = buckets[key]
            if values:
                item = deepcopy(values.pop(0))
                item["pattern_count"] = original_counts[key]
                item["pattern_exemplar"] = "middle"
                ordered.append(item)
    return ordered


def _compact_timestamp_for_summary(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    # UTC is the model-facing comparison value. The original representation
    # and timezone assumption remain losslessly available in structured.json.
    if value.get("utc") not in (None, ""):
        return {"utc": deepcopy(value["utc"])}
    return {
        key: deepcopy(value[key])
        for key in ("original", "assumed_timezone")
        if value.get(key) not in (None, "")
    }


def _summary_evidence(
    value: dict[str, Any],
    *,
    compact: bool = False,
) -> dict[str, Any]:
    result = deepcopy(value)
    if isinstance(result.get("message_raw"), str) and isinstance(result.get("parsed"), dict):
        result.pop("message_raw", None)
        result.pop("parsed", None)
    refs = result.get("evidence_refs")
    if refs == [result.get("id")]:
        result.pop("evidence_refs", None)
        refs = None
    if isinstance(refs, list) and len(refs) > 2:
        result["evidence_refs"] = refs[:2]
        result["evidence_ref_count"] = len(refs)
    if result.get("metric"):
        if result.get("attribute") == result.get("metric"):
            result.pop("attribute", None)
        if result.get("kind") == result.get("metric"):
            result.pop("kind", None)
        labels = result.get("labels")
        if isinstance(labels, dict):
            result["labels"] = {
                key: item
                for key, item in labels.items()
                if key not in NOISY_METRIC_LABELS
            }
            if not result["labels"]:
                result.pop("labels")
    elif result.get("trace_type"):
        if result.get("kind") == result.get("trace_type"):
            result.pop("kind", None)
        result.pop("attribute", None)
        data = result.get("data")
        if isinstance(data, dict):
            timestamp = data.get("timestamp")
            if isinstance(timestamp, dict):
                timestamp.pop("source_system", None)
    elif result.get("kind") == result.get("attribute"):
        result.pop("kind", None)
    for key in ("message", "value"):
        if isinstance(result.get(key), str) and len(result[key]) > 600:
            original = result[key]
            result[key] = original[:560] + "...[summary_truncated]"
            result[f"{key}_original_length"] = len(original)
    if compact:
        # The complete normalized evidence stays in structured.json.  The
        # model view removes fields repeated by the control envelope or raw
        # archive while retaining fact identity, quality, values, labels,
        # correlations, raw document references, and temporal information.
        result.pop("evidence_refs", None)
        result.pop("kind", None)
        result.pop("identity_basis", None)
        result.pop("pod_uid", None)
        result.pop("value_sha256", None)
        if result.get("value_truncated") is False:
            result.pop("value_truncated", None)
            result.pop("value_original_length", None)
        if "timestamp" in result:
            result["timestamp"] = _compact_timestamp_for_summary(
                result.get("timestamp")
            )
        data = result.get("data")
        if isinstance(data, dict) and "timestamp" in data:
            data["timestamp"] = _compact_timestamp_for_summary(
                data.get("timestamp")
            )
            # Trace normalization exposes the same instant at the evidence
            # root and inside data. Keep a single model-facing copy.
            if result.get("trace_type") and result.get("timestamp") == data.get("timestamp"):
                result.pop("timestamp", None)
    return result


def _compact_control_envelope(base: dict[str, Any]) -> dict[str, Any]:
    """Remove recursively redundant control fields from the model view."""
    result = deepcopy(base)
    entity = result.get("entity")
    if isinstance(entity, dict):
        result["entity"] = {
            key: deepcopy(entity[key])
            for key in (
                "kind",
                "namespace",
                "pod",
                "pod_uid",
                "containers",
                "node",
                "pod_ip",
                "lifecycle_changed",
            )
            if entity.get(key) not in (None, "", [], {})
            and not (key == "lifecycle_changed" and entity.get(key) is False)
        }
    truncation = result.get("truncation")
    if isinstance(truncation, dict):
        result["truncation"] = {
            key: deepcopy(truncation[key])
            for key in (
                "truncated",
                "source_or_collection_truncated",
                "mcp_response_truncated",
                "reasons",
                "reason_detail_complete",
                "next_cursor",
            )
            if truncation.get(key) not in (None, "", [], {})
            or key
            in {
                "truncated",
                "source_or_collection_truncated",
                "mcp_response_truncated",
            }
        }
    retrieval = result.get("retrieval")
    if isinstance(retrieval, dict):
        result["retrieval"] = {
            key: deepcopy(retrieval[key])
            for key in ("raw_ref", "mcp_response_complete", "tool")
            if retrieval.get(key) not in (None, "")
        }
    return result


def render_observability_summary(
    structured: dict[str, Any],
    max_chars: int,
) -> tuple[str, dict[str, Any]]:
    """Render an evidence-first bounded JSON observation and selection audit."""
    control_keys = (
        "contract_version",
        "tool",
        "source_system",
        "dimension",
        "status",
        "coverage",
        "directness",
        "entity",
        "window",
        "counts",
        "truncation",
        "retrieval",
        "source_coverage",
        "negative_observation",
    )
    base = _compact_control_envelope({
        key: deepcopy(structured[key])
        for key in control_keys
        if structured.get(key) not in (None, "", [], {})
    })
    counts = base.get("counts")
    if isinstance(counts, dict):
        for key in ("mcp_facts", "mcp_samples"):
            counts.pop(key, None)
    evidence = structured.get("evidence") if isinstance(structured.get("evidence"), list) else []
    base["evidence"] = []
    ordered = [
        _summary_evidence(item, compact=len(evidence) > 1)
        for item in _diverse_order(evidence)
    ]
    selected_ids: list[str] = []
    empty_selection = {
        "selected": 0,
        "omitted": len(evidence),
        "strategy": SELECTION_STRATEGY,
    }
    control_probe = deepcopy(base)
    control_probe["summary_selection"] = empty_selection
    control_envelope_chars = len(compact_json(control_probe))
    attempted_candidates = 0
    first_rejected: dict[str, Any] | None = None
    rejected_candidates = 0
    for position, item in enumerate(ordered):
        attempted_candidates += 1
        candidate = deepcopy(base)
        candidate["evidence"].append(item)
        candidate["summary_selection"] = {
            "selected": len(candidate["evidence"]),
            "omitted": max(0, len(evidence) - len(candidate["evidence"])),
            "strategy": SELECTION_STRATEGY,
        }
        candidate_chars = len(compact_json(candidate))
        if candidate_chars > max_chars:
            current_chars = (
                len(compact_json(base))
                if "summary_selection" in base
                else control_envelope_chars
            )
            rejected_candidates += 1
            rejection = {
                "candidate_fact_id": item.get("id"),
                "candidate_position": position,
                "candidate_chars": candidate_chars,
                "evidence_chars": len(compact_json(item)),
                "remaining_chars_before_candidate": max(0, max_chars - current_chars),
                "pattern": _selection_bucket(item),
                "profile": _selection_profile(item),
                "reason": "candidate_exceeds_remaining_budget",
            }
            if first_rejected is None:
                first_rejected = rejection
            # A large candidate must not prevent later, smaller semantic
            # patterns from using the remaining budget.
            continue
        base = candidate
        if item.get("id"):
            selected_ids.append(str(item["id"]))
    if "summary_selection" not in base:
        base["summary_selection"] = empty_selection
    selection_chars = len(compact_json(base))
    optional_fields_included: list[str] = []
    for optional_key in ("limitations", "query_ref"):
        value = structured.get(optional_key)
        if value in (None, "", [], {}):
            continue
        candidate = deepcopy(base)
        candidate[optional_key] = deepcopy(value)
        if len(compact_json(candidate)) <= max_chars:
            base = candidate
            optional_fields_included.append(optional_key)
    summary = compact_json(base)
    if len(summary) > max_chars:
        # A pathological envelope must remain explicit instead of falling back
        # to an opaque head truncation.
        minimal = {
            key: base[key]
            for key in ("contract_version", "tool", "dimension", "status", "coverage", "truncation")
            if key in base
        }
        minimal["summary_selection"] = {
            "selected": 0,
            "omitted": len(evidence),
            "strategy": "control_envelope_exceeded",
        }
        summary = compact_json(minimal)
    selected_set = set(selected_ids)
    omitted_ids = [
        str(item.get("id"))
        for item in evidence
        if item.get("id") and str(item.get("id")) not in selected_set
    ]
    selected_evidence = base.get("evidence") or []
    all_patterns = list(dict.fromkeys(_selection_bucket(item) for item in evidence))
    selected_patterns = {
        _selection_bucket(item)
        for item in selected_evidence
    }
    omitted_patterns = [
        pattern for pattern in all_patterns if pattern not in selected_patterns
    ]
    audit = {
        "evidence_total": len(evidence),
        "evidence_selected": len(selected_evidence),
        "evidence_omitted": max(0, len(evidence) - len(selected_evidence)),
        "selected_fact_ids": selected_ids,
        "omitted_fact_ids": omitted_ids,
        "semantic_patterns_total": len(all_patterns),
        "semantic_patterns_selected": len(selected_patterns),
        "semantic_patterns_omitted": len(omitted_patterns),
        "omitted_pattern_preview": omitted_patterns[:12],
        "selected_profile_counts": _selection_profile_counts(selected_evidence),
        "omitted_profile_counts": _selection_profile_counts(
            item
            for item in evidence
            if not item.get("id") or str(item.get("id")) not in selected_set
        ),
        "budget": {
            "max_chars": max_chars,
            "control_envelope_chars": control_envelope_chars,
            "selection_chars": selection_chars,
            "final_summary_chars": len(summary),
            "remaining_chars": max(0, max_chars - len(summary)),
            "attempted_candidates": attempted_candidates,
            "candidates_unattempted": max(0, len(ordered) - attempted_candidates),
            "selection_terminated_by": (
                "budget_scan_completed" if first_rejected else "exhausted"
            ),
            "rejected_candidates": rejected_candidates,
            "first_rejected": first_rejected,
            "optional_fields_included": optional_fields_included,
        },
        "summary_chars": len(summary),
        "strategy": base["summary_selection"]["strategy"],
    }
    return summary, audit


def project_observability_payload(
    payload: dict[str, Any],
    *,
    tool: str,
    max_chars: int,
    raw_ref: Optional[str] = None,
    local_timezone: str = DEFAULT_LOCAL_TIMEZONE,
) -> dict[str, Any]:
    evidence = _normalized_evidence(payload, local_timezone)
    structured: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "tool": tool,
        "source_system": payload.get("source_system"),
        "dimension": payload.get("dimension"),
        "status": payload.get("status"),
        "coverage": payload.get("coverage"),
        "directness": payload.get("directness"),
        "entity": _minimal_entity(payload),
        "window": _query_window(payload),
        "counts": _counts(payload, len(evidence)),
        "truncation": _truncation(payload),
        "query_ref": _query_ref(payload),
        "evidence": evidence,
        "source_coverage": _source_coverage(payload),
        "limitations": deepcopy(payload.get("limitations") or []),
        "evidence_refs": deepcopy(payload.get("evidence_refs") or []),
    }
    # Transitional code-consumption view.  It is never rendered into the model
    # summary; existing workflow consumers can migrate to canonical evidence[]
    # without making this release an all-at-once schema break.
    for key in (
        "ok",
        "purpose",
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
        "fact_ledger",
    ):
        if payload.get(key) not in (None, "", [], {}):
            structured[key] = deepcopy(payload[key])
    if payload.get("error"):
        structured["error"] = deepcopy(payload["error"])
    if payload.get("status") == "query_succeeded" and payload.get("coverage") in {
        "empty",
        "absent",
    }:
        structured["negative_observation"] = "query_completed_without_matching_evidence"
    if raw_ref:
        structured["retrieval"] = {
            "available": True,
            "tool": "read_context_archive",
            "raw_ref": raw_ref,
            "scope": "complete_mcp_response",
            "mcp_response_complete": structured["truncation"].get(
                "mcp_response_truncated"
            )
            is not True,
        }
    structured = {
        key: value
        for key, value in structured.items()
        if value not in (None, "", [], {})
    }
    structured.setdefault("evidence_refs", [])
    summary, audit = render_observability_summary(structured, max_chars)
    structured["agent_projection"] = deepcopy(audit)
    return {"structured": structured, "summary": summary, "audit": audit}
