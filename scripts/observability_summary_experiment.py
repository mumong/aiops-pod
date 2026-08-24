#!/usr/bin/env python3
"""Build an evidence-first shadow projection from an observability MCP result.

This script is deliberately disconnected from the production observation path.
It is an experiment harness for comparing the current summary with a compact,
dimension-aware projection without teaching the extractor any fault names.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


CONTRACT_VERSION = "aiops.observability-agent-evidence.shadow.v1"
IDENTITY_LABELS = {"__name__", "namespace", "pod", "uid", "pod_uid"}
CONTROL_FIELDS = {
    "reason",
    "phase",
    "condition",
    "probe_type",
    "result",
    "state",
    "status",
    "container",
}
LOG_FIELDS = (
    "event",
    "level",
    "message",
    "trace_id",
    "span_id",
    "http_status",
    "path",
    "duration_ms",
    "service",
)
LOG_IDENTITY_FIELDS = {"timestamp", "case_run_id", "pod"}


def compact_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    )


def read_payload(path: str) -> dict[str, Any]:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("MCP result must be a JSON object")
    return value


def integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_timestamp(value: Any, source_system: str, local_timezone: str) -> dict[str, Any] | None:
    text = str(value or "").strip()
    if not text:
        return None
    result: dict[str, Any] = {"original": text}
    try:
        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(local_timezone))
            result["assumed_timezone"] = local_timezone
        result["utc"] = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (ValueError, ZoneInfoNotFoundError):
        result["normalization_error"] = True
    result["source_system"] = source_system
    return result


def parse_json_message(value: Any) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(value, str):
        return compact_json(value), value if isinstance(value, dict) else None
    text = value.strip()
    if not text.startswith("{"):
        return value, None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return value, None
    return value, parsed if isinstance(parsed, dict) else None


def minimal_entity(payload: dict[str, Any]) -> dict[str, Any]:
    entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
    result = {
        key: entity.get(key)
        for key in ("namespace", "pod", "pod_uid", "lifecycle_changed")
        if entity.get(key) is not None
    }
    for key in ("node", "pod_ip", "containers"):
        if entity.get(key) not in (None, "", []):
            result[key] = entity[key]
    return result


def query_window(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    window = query.get("time_range") if isinstance(query.get("time_range"), dict) else {}
    return {
        key: window.get(key)
        for key in ("start", "end")
        if window.get(key) is not None
    }


def query_ref(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    digest = str(query.get("dsl_sha256") or "").strip()
    if not digest:
        digest = hashlib.sha256(compact_json(query).encode("utf-8")).hexdigest()[:16]
    result: dict[str, Any] = {"hash": digest, "debug_available": bool(query)}
    for key in ("query_type", "identity_basis", "index"):
        if query.get(key) not in (None, ""):
            result[key] = query[key]
    if isinstance(query.get("executions"), list):
        result["execution_count"] = len(query["executions"])
    dimension = str(payload.get("dimension") or "")
    if dimension == "metrics":
        promql = str(query.get("promql") or "")
        metric_names = list(dict.fromkeys(re.findall(
            r"([A-Za-z_:][A-Za-z0-9_:]*)\s*\{",
            promql,
        )))
        if metric_names:
            result["metric_names"] = metric_names
    elif dimension == "logging":
        filters = {
            key: query.get(key)
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
    elif dimension == "tracing":
        filters = {
            key: query.get(key)
            for key in (
                "direction",
                "protocol",
                "response_code",
                "response_codes",
                "min_duration_ms",
                "peer",
                "trace_id",
                "resource",
                "service",
                "include_tempo",
            )
            if query.get(key) not in (None, "", [])
        }
        if filters:
            result["filters"] = filters
    return result


def result_counts(payload: dict[str, Any], evidence_count: int) -> dict[str, Any]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    backend_total = query.get("backend_total")
    matched = integer(backend_total.get("value")) if isinstance(backend_total, dict) else None
    if matched is None:
        matched = integer(payload.get("raw_series_count"))
    if matched is None:
        matched = integer(query.get("filtered_match_count"))
    retrieved = integer(query.get("uid_query_hits"))
    if retrieved is None and isinstance(query.get("executions"), list):
        values = [integer(item.get("hit_count")) for item in query["executions"] if isinstance(item, dict)]
        valid = [value for value in values if value is not None]
        retrieved = sum(valid) if valid else None
    counts = {
        "matched": matched,
        "retrieved": retrieved,
        "returned": evidence_count,
        "dropped": None,
        "mcp_facts": len(payload.get("facts") or []),
        "mcp_samples": len(payload.get("samples") or []),
    }
    if payload.get("dimension") == "metrics":
        counts.update({
            "raw_series": integer(payload.get("raw_series_count")),
            "projected_series": integer(payload.get("series_count")),
            "serialized_series": len(payload.get("series") or []),
        })
    if payload.get("dimension") == "tracing":
        records = (
            payload.get("fact_ledger", {}).get("records", [])
            if isinstance(payload.get("fact_ledger"), dict)
            else []
        )
        counts.update({
            "serialized_flows": len(payload.get("flows") or []),
            "serialized_spans": len(payload.get("spans") or []),
            "ledger_flows": sum(
                1 for item in records
                if isinstance(item, dict) and item.get("fact_type") == "flow"
            ),
            "ledger_spans": sum(
                1 for item in records
                if isinstance(item, dict) and item.get("fact_type") == "span"
            ),
        })
    return counts


def truncation_contract(payload: dict[str, Any]) -> dict[str, Any]:
    truncated = bool(payload.get("truncated"))
    reasons: list[str] = []
    limits = payload.get("limits") if isinstance(payload.get("limits"), dict) else {}
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    backend_total = query.get("backend_total")
    matched = integer(backend_total.get("value")) if isinstance(backend_total, dict) else None
    backend_limit = integer(limits.get("max_backend_records"))
    if truncated and matched is not None and backend_limit is not None and matched >= backend_limit:
        reasons.append("backend_limit")
    ledger = payload.get("fact_ledger") if isinstance(payload.get("fact_ledger"), dict) else {}
    if ledger.get("truncated") is True:
        reasons.append("fact_ledger_projection")
    if truncated:
        reasons.append("upstream_or_response_budget_unspecified")
    return {
        "truncated": truncated,
        "reasons": list(dict.fromkeys(reasons)),
        "reason_detail_complete": not truncated,
        "next_cursor": payload.get("next_cursor"),
    }


def record_base(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    source_system = str(record.get("source_system") or "")
    result = {
        "id": record.get("fact_id"),
        "kind": record.get("fact_type"),
        "attribute": record.get("attribute"),
        "source_system": source_system,
        "directness": record.get("directness"),
        "confidence": record.get("confidence"),
        "evidence_refs": list(record.get("evidence_refs") or []),
    }
    timestamp = normalize_timestamp(record.get("timestamp"), source_system, local_timezone)
    if timestamp:
        result["timestamp"] = timestamp
    return {key: value for key, value in result.items() if value not in (None, "", [])}


def normalize_metric(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = record_base(record, local_timezone)
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    labels = metadata.get("labels") if isinstance(metadata.get("labels"), dict) else {}
    result.update({
        "metric": record.get("attribute"),
        "value": record.get("value"),
        "unit": record.get("unit"),
        "labels": {
            key: value
            for key, value in labels.items()
            if key not in IDENTITY_LABELS and value not in (None, "")
        },
        "stats": metadata.get("stats"),
        "sample_count": metadata.get("sample_count"),
        "trend_evaluable": metadata.get("trend_evaluable"),
    })
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def normalize_log(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = record_base(record, local_timezone)
    raw_message, parsed = parse_json_message(record.get("value"))
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    result["message_raw"] = raw_message
    if parsed is not None:
        result["parsed"] = deepcopy(parsed)
        for key in LOG_FIELDS:
            if parsed.get(key) not in (None, ""):
                result[key] = parsed[key]
        attributes = {
            key: value
            for key, value in parsed.items()
            if key not in set(LOG_FIELDS) | LOG_IDENTITY_FIELDS
            and isinstance(value, (str, int, float, bool))
            and value not in (None, "")
        }
        if attributes:
            result["attributes"] = attributes
    else:
        result["message"] = raw_message
    for key in ("value_original_length", "value_sha256", "value_truncated", "raw_ref"):
        if metadata.get(key) is not None:
            result[key] = metadata[key]
    return result


def normalize_trace(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = record_base(record, local_timezone)
    value = deepcopy(record.get("value"))
    if isinstance(value, dict):
        for key in ("syscall_trace_id_request", "syscall_trace_id_response"):
            if str(value.get(key) or "") == "0":
                value.pop(key, None)
        timestamp = normalize_timestamp(
            value.get("timestamp") or record.get("timestamp"),
            str(record.get("source_system") or ""),
            local_timezone,
        )
        if timestamp:
            value["timestamp"] = timestamp
    result["trace_type"] = record.get("fact_type")
    result["data"] = value
    return result


def normalize_topology(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = record_base(record, local_timezone)
    value = deepcopy(record.get("value"))
    if isinstance(value, dict):
        result["relationship"] = {
            key: value.get(key)
            for key in ("source", "relation", "target")
            if value.get(key) is not None
        }
    else:
        result["value"] = value
    return result


def normalize_generic(record: dict[str, Any], local_timezone: str) -> dict[str, Any]:
    result = record_base(record, local_timezone)
    result["value"] = deepcopy(record.get("value"))
    result["unit"] = record.get("unit")
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def normalized_evidence(payload: dict[str, Any], local_timezone: str) -> list[dict[str, Any]]:
    ledger = payload.get("fact_ledger") if isinstance(payload.get("fact_ledger"), dict) else {}
    records = ledger.get("records") if isinstance(ledger.get("records"), list) else []
    if not records:
        records = payload.get("facts") if isinstance(payload.get("facts"), list) else []
    dimension = str(payload.get("dimension") or "")
    normalizers = {
        "metrics": normalize_metric,
        "logging": normalize_log,
        "tracing": normalize_trace,
        "topology": normalize_topology,
    }
    normalizer = normalizers.get(dimension, normalize_generic)
    evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        normalized = normalizer(record, local_timezone)
        signature = str(normalized.get("id") or compact_json(normalized))
        if signature in seen:
            continue
        seen.add(signature)
        evidence.append(normalized)
    return evidence


def compact_source_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    telemetry = payload.get("telemetry")
    if not isinstance(telemetry, dict):
        return {}
    result: dict[str, Any] = {}
    for source, raw in telemetry.items():
        if not isinstance(raw, dict):
            continue
        item = {
            key: raw.get(key)
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


def summary_evidence(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    if isinstance(result.get("message_raw"), str) and isinstance(result.get("parsed"), dict):
        result.pop("message_raw", None)
        result.pop("parsed", None)
    refs = result.get("evidence_refs")
    if isinstance(refs, list) and len(refs) > 2:
        result["evidence_refs"] = refs[:2]
        result["evidence_ref_count"] = len(refs)
    for key in ("message", "value"):
        if isinstance(result.get(key), str) and len(result[key]) > 600:
            original = result[key]
            result[key] = original[:560] + "...[summary_truncated]"
            result[f"{key}_original_length"] = len(original)
    return result


def round_robin_by_kind(evidence: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for item in evidence:
        key = str(item.get("trace_type") or item.get("kind") or item.get("attribute") or "unknown")
        buckets.setdefault(key, []).append(item)
    ordered: list[dict[str, Any]] = []
    while any(buckets.values()):
        for key in list(buckets):
            if buckets[key]:
                ordered.append(buckets[key].pop(0))
    return ordered


def build_shadow(payload: dict[str, Any], max_chars: int, local_timezone: str) -> dict[str, Any]:
    evidence = normalized_evidence(payload, local_timezone)
    structured = {
        "contract_version": CONTRACT_VERSION,
        "tool": payload.get("tool"),
        "dimension": payload.get("dimension"),
        "status": payload.get("status"),
        "coverage": payload.get("coverage"),
        "directness": payload.get("directness"),
        "entity": minimal_entity(payload),
        "window": query_window(payload),
        "counts": result_counts(payload, len(evidence)),
        "truncation": truncation_contract(payload),
        "query_ref": query_ref(payload),
        "evidence": evidence,
        "source_coverage": compact_source_coverage(payload),
        "limitations": deepcopy(payload.get("limitations") or []),
    }
    if payload.get("status") == "query_succeeded" and payload.get("coverage") in {"empty", "absent"}:
        structured["negative_observation"] = "query_completed_without_matching_evidence"
    structured = {key: value for key, value in structured.items() if value not in (None, "", [], {})}

    base = {
        key: deepcopy(structured[key])
        for key in (
            "contract_version",
            "tool",
            "dimension",
            "status",
            "coverage",
            "directness",
            "entity",
            "window",
            "counts",
            "truncation",
            "query_ref",
            "source_coverage",
            "limitations",
            "negative_observation",
        )
        if key in structured
    }
    base["evidence"] = []
    selected_ids: set[str] = set()
    for item in round_robin_by_kind(summary_evidence(value) for value in evidence):
        candidate = deepcopy(base)
        candidate["evidence"].append(item)
        candidate["summary_selection"] = {
            "selected": len(candidate["evidence"]),
            "omitted": max(0, len(evidence) - len(candidate["evidence"])),
            "strategy": "semantic_type_round_robin_no_fault_names",
        }
        if len(compact_json(candidate)) > max_chars:
            break
        base = candidate
        if item.get("id"):
            selected_ids.add(str(item["id"]))
    if "summary_selection" not in base:
        base["summary_selection"] = {
            "selected": 0,
            "omitted": len(evidence),
            "strategy": "semantic_type_round_robin_no_fault_names",
        }
    summary_text = compact_json(base)
    if len(summary_text) > max_chars:
        raise ValueError(f"control envelope exceeds summary budget: {len(summary_text)} > {max_chars}")
    return {
        "structured": structured,
        "summary": base,
        "summary_text": summary_text,
        "audit": {
            "raw_chars": len(compact_json(payload)),
            "structured_chars": len(compact_json(structured)),
            "summary_chars": len(summary_text),
            "evidence_total": len(evidence),
            "evidence_selected": len(base.get("evidence") or []),
            "selected_fact_ids": sorted(selected_ids),
            "omitted_fact_ids": sorted(
                str(item.get("id"))
                for item in evidence
                if item.get("id") and str(item.get("id")) not in selected_ids
            ),
        },
    }


def run_batch(patterns: list[str], max_chars: int, local_timezone: str, namespace_prefix: str) -> dict[str, Any]:
    paths = sorted({path for pattern in patterns for path in glob.glob(pattern)})
    aggregate: dict[str, Any] = {
        "files_scanned": len(paths),
        "payloads_evaluated": 0,
        "failures": [],
        "evidence_total": 0,
        "evidence_selected": 0,
        "evidence_omitted": 0,
        "max_summary_chars": 0,
        "max_summary_path": None,
        "current_summary_fact_ids_total": 0,
        "current_summary_fact_ids_visible": 0,
        "by_dimension": {},
    }
    for path in paths:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
            namespace = str(entity.get("namespace") or "")
            if namespace_prefix and not namespace.startswith(namespace_prefix):
                continue
            result = build_shadow(payload, max_chars=max_chars, local_timezone=local_timezone)
        except Exception as exc:
            aggregate["failures"].append({"path": path, "error": str(exc)})
            continue
        audit = result["audit"]
        dimension = str(payload.get("dimension") or "unknown")
        dimension_stats = aggregate["by_dimension"].setdefault(dimension, {
            "payloads": 0,
            "evidence_total": 0,
            "evidence_selected": 0,
            "evidence_omitted": 0,
            "max_summary_chars": 0,
            "current_summary_fact_ids_total": 0,
            "current_summary_fact_ids_visible": 0,
        })
        aggregate["payloads_evaluated"] += 1
        dimension_stats["payloads"] += 1
        if audit["summary_chars"] > aggregate["max_summary_chars"]:
            aggregate["max_summary_path"] = path
        for target in (aggregate, dimension_stats):
            target["evidence_total"] += audit["evidence_total"]
            target["evidence_selected"] += audit["evidence_selected"]
            target["evidence_omitted"] += len(audit["omitted_fact_ids"])
            target["max_summary_chars"] = max(target["max_summary_chars"], audit["summary_chars"])
        current_summary_path = path.replace(".raw.txt", ".summary.txt")
        try:
            current_summary = Path(current_summary_path).read_text(encoding="utf-8")
        except OSError:
            current_summary = ""
        fact_ids = [
            str(item.get("id"))
            for item in result["structured"].get("evidence") or []
            if item.get("id")
        ]
        visible = sum(1 for fact_id in fact_ids if fact_id in current_summary)
        for target in (aggregate, dimension_stats):
            target["current_summary_fact_ids_total"] += len(fact_ids)
            target["current_summary_fact_ids_visible"] += visible
    aggregate["failure_count"] = len(aggregate["failures"])
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", nargs="?", help="MCP raw JSON path, or - for stdin")
    parser.add_argument("--max-chars", type=int, default=3000)
    parser.add_argument("--local-timezone", default="Asia/Shanghai")
    parser.add_argument("--section", choices=("all", "structured", "summary", "audit"), default="all")
    parser.add_argument("--batch-glob", action="append", default=[])
    parser.add_argument("--namespace-prefix", default="")
    args = parser.parse_args()
    if args.batch_glob:
        value = run_batch(
            args.batch_glob,
            max_chars=args.max_chars,
            local_timezone=args.local_timezone,
            namespace_prefix=args.namespace_prefix,
        )
        print(json.dumps(value, ensure_ascii=False, indent=2, default=str))
        return 0
    if not args.raw:
        parser.error("raw is required unless --batch-glob is used")
    result = build_shadow(read_payload(args.raw), args.max_chars, args.local_timezone)
    value = result if args.section == "all" else result[args.section]
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
