"""Deterministic per-entity/per-dimension evidence aggregation.

The multi-anomaly report consumes this compact contract instead of selecting
one arbitrary tool call or truncating an LLM paragraph.  Independent queries
remain independent: an empty follow-up never erases facts collected earlier.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from app.core.workflow.fact_contract import OBSERVABILITY_QUERY_TOOL_DIMENSIONS


REQUIRED_DIMENSIONS = ("kubernetes", "metrics", "logging", "tracing")
_PRE_RUNTIME_STATUSES = {
    "pending",
    "containercreating",
    "createcontainerconfigerror",
    "errimagepull",
    "imagepullbackoff",
    "failedscheduling",
    "failedmount",
    "failedcreatepodsandbox",
}

_METRIC_IDENTITY_LABELS = {
    "__name__",
    "container",
    "endpoint",
    "id",
    "image",
    "instance",
    "job",
    "metrics_path",
    "name",
    "namespace",
    "node",
    "pod",
    "service",
    "uid",
}


def _entity_key(namespace: Any, name: Any) -> str:
    return f"{str(namespace or '').strip()}/{str(name or '').strip()}"


def _empty_dimension(dimension: str) -> Dict[str, Any]:
    return {
        "dimension": dimension,
        "status": "unselected",
        "source_systems": [],
        "query_count": 0,
        "present_query_count": 0,
        "empty_query_count": 0,
        "facts": [],
        "limitations": [],
    }


def _event_target(event: Mapping[str, Any]) -> Optional[Tuple[str, str]]:
    structured = event.get("structured") if isinstance(event.get("structured"), Mapping) else {}
    entity = structured.get("entity") if isinstance(structured.get("entity"), Mapping) else {}
    if not entity and isinstance(structured.get("primary_entity"), Mapping):
        entity = structured["primary_entity"]
    args = event.get("tool_args") if isinstance(event.get("tool_args"), Mapping) else {}
    namespace = entity.get("namespace") or args.get("namespace")
    name = (
        entity.get("pod")
        or entity.get("name")
        or args.get("pod")
        or args.get("pod_name")
        or args.get("name")
        or args.get("resource_name")
    )
    if namespace and name:
        return str(namespace), str(name)
    return None


def _source_list(structured: Mapping[str, Any], records: Iterable[Mapping[str, Any]]) -> List[str]:
    sources = {
        str(item.get("source_system") or "").strip()
        for item in records
        if str(item.get("source_system") or "").strip()
    }
    raw = str(structured.get("source_system") or "").strip()
    if raw and not sources:
        sources.update(part for part in raw.replace("+", ",").split(",") if part)
    return sorted(sources)


def _render_fact_value(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return value
        if isinstance(parsed, Mapping):
            return _render_fact_value(parsed)
        return value
    if not isinstance(value, Mapping):
        return str(value)

    method = value.get("request_type") or value.get("http.request.method")
    resource = value.get("request_resource") or value.get("http.route") or value.get("path")
    code = value.get("response_code") or value.get("http.response.status_code") or value.get("http_status")
    trace_id = value.get("trace_id")
    message = value.get("message")
    if method or resource or code is not None:
        parts = [str(part) for part in (method, resource) if part]
        if code is not None:
            parts.append(f"-> HTTP {code}")
        if message:
            parts.append(str(message))
        if trace_id:
            parts.append(f"trace_id={trace_id}")
        return " ".join(parts)

    attrs = value.get("attributes") if isinstance(value.get("attributes"), Mapping) else {}
    if attrs:
        method = attrs.get("http.request.method")
        resource = attrs.get("http.route") or value.get("name")
        code = attrs.get("http.response.status_code")
        parts = [str(part) for part in (method, resource) if part]
        if code is not None:
            parts.append(f"-> HTTP {code}")
        if value.get("trace_id"):
            parts.append(f"trace_id={value['trace_id']}")
        if parts:
            return " ".join(parts)

    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _format_metric_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == int(number):
        return str(int(number))
    return f"{number:g}"


def _humanize_bytes(value: Any) -> Optional[str]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number >= 1024 ** 3:
        return f"≈{number / 1024 ** 3:.1f} GiB"
    if number >= 1024 ** 2:
        return f"≈{number / 1024 ** 2:.1f} MiB"
    return None


def _render_metric_fact(record: Mapping[str, Any]) -> Optional[str]:
    """Render metric facts as `name=value unit（趋势）` instead of a bare number."""
    if str(record.get("dimension") or "").strip().lower() != "metrics":
        return None
    name = str(record.get("name") or record.get("attribute") or "").strip()
    if not name or name.lower() == "value":
        return None

    rendered = f"{name}={_format_metric_number(record.get('value'))}"
    unit = str(record.get("unit") or "").strip()
    if unit:
        rendered += f" {unit}"

    annotations: List[str] = []
    if unit == "bytes":
        humanized = _humanize_bytes(record.get("value"))
        if humanized:
            annotations.append(humanized)

    metadata = record.get("metadata") if isinstance(record.get("metadata"), Mapping) else {}
    labels = metadata.get("labels") if isinstance(metadata.get("labels"), Mapping) else {}
    semantic_labels = [
        f"{key}={labels[key]}"
        for key in sorted(labels)
        if key not in _METRIC_IDENTITY_LABELS and labels[key] not in (None, "")
    ]
    if semantic_labels:
        annotations.extend(semantic_labels[:8])
        if len(semantic_labels) > 8:
            annotations.append(f"另有 {len(semantic_labels) - 8} 个标签")

    stats = record.get("stats") if isinstance(record.get("stats"), Mapping) else metadata.get("stats")
    if isinstance(stats, Mapping) and stats.get("first") is not None and stats.get("last") is not None:
        try:
            first, last = float(stats["first"]), float(stats["last"])
            low = float(stats.get("min", first))
            high = float(stats.get("max", last))
        except (TypeError, ValueError):
            first = last = low = high = None
        if first is not None:
            if first == last == low == high:
                annotations.append("持平")
            elif last > first:
                annotations.append(f"上升 {_format_metric_number(first)} → {_format_metric_number(last)}")
            elif last < first:
                annotations.append(f"下降 {_format_metric_number(first)} → {_format_metric_number(last)}")
            else:
                annotations.append(
                    f"波动 min={_format_metric_number(low)} max={_format_metric_number(high)}"
                )

    if annotations:
        rendered += "（" + "，".join(annotations) + "）"
    return rendered


def _records_from_structured(structured: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    ledger = structured.get("fact_ledger") if isinstance(structured.get("fact_ledger"), Mapping) else {}
    records = ledger.get("records") if isinstance(ledger.get("records"), list) else []
    if records:
        return [item for item in records if isinstance(item, Mapping)]
    facts = structured.get("facts") if isinstance(structured.get("facts"), list) else []
    return [item for item in facts if isinstance(item, Mapping)]


def _display_fact_value(record: Mapping[str, Any]) -> str:
    metric = _render_metric_fact(record)
    if metric:
        return metric
    rendered = _render_fact_value(record.get("value"))
    if str(record.get("dimension") or "").strip().lower() == "kubernetes":
        attribute = str(record.get("attribute") or "").strip()
        if attribute:
            return f"{attribute}={rendered}"
    return rendered


def _compact_fact(record: Mapping[str, Any], *, fallback_seed: str) -> Dict[str, Any]:
    """Preserve the complete canonical record and add a presentation value.

    Unknown record fields are intentionally forwarded.  Multi-group handoff
    consumers can therefore learn new canonical extensions without changing
    this projector, while the report still has a compact readable value.
    """
    refs = record.get("evidence_refs") or record.get("ref") or record.get("evidence_ref") or []
    if isinstance(refs, str):
        refs = [refs]
    refs = [str(item) for item in refs if str(item).strip()]
    fact_id = str(record.get("fact_id") or "").strip()
    if not fact_id:
        digest = hashlib.sha256(
            (fallback_seed + json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)).encode("utf-8")
        ).hexdigest()[:12]
        fact_id = f"fact-derived-{digest}"
    fact = deepcopy(dict(record))
    fact.update({
        "fact_id": fact_id,
        "source_system": str(record.get("source_system") or "unknown"),
        "evidence_refs": refs,
        "display_value": _display_fact_value(record),
    })
    return fact


def _append_unique_facts(target: Dict[str, Any], facts: Iterable[Dict[str, Any]]) -> None:
    seen = {
        (str(item.get("fact_id") or ""), tuple(item.get("evidence_refs") or []))
        for item in target["facts"]
    }
    seen_rendered = {
        (
            str(item.get("source_system") or ""),
            str(item.get("display_value") or item.get("value") or ""),
        )
        for item in target["facts"]
    }
    for fact in facts:
        key = (str(fact.get("fact_id") or ""), tuple(fact.get("evidence_refs") or []))
        rendered_key = (
            str(fact.get("source_system") or ""),
            str(fact.get("display_value") or fact.get("value") or ""),
        )
        if key in seen or rendered_key in seen_rendered:
            continue
        seen.add(key)
        seen_rendered.add(rendered_key)
        target["facts"].append(fact)


def _kubernetes_fact_rows(event: Mapping[str, Any]) -> List[Dict[str, Any]]:
    structured = event.get("structured") if isinstance(event.get("structured"), Mapping) else {}
    values: List[str] = []
    for key in ("selected_events", "key_events", "conditions", "container_statuses"):
        raw = structured.get(key)
        if isinstance(raw, list):
            values.extend(
                item if isinstance(item, str) else json.dumps(item, ensure_ascii=False, default=str)
                for item in raw
            )
    for key in ("status", "reason", "message", "phase", "exit_code", "restart_count"):
        if structured.get(key) not in (None, "", [], {}):
            values.append(f"{key}={structured[key]}")
    if not values:
        result = str(event.get("result") or event.get("result_preview") or "").strip()
        if result:
            values.append(result)
    rows = []
    tool = str(event.get("tool_name") or "kubernetes")
    for value in values:
        digest = hashlib.sha256(f"{tool}:{value}".encode("utf-8")).hexdigest()[:12]
        rows.append({
            "fact_id": f"fact-k8s-{digest}",
            "source_system": "kubernetes",
            "value": value,
            "display_value": value,
            "evidence_refs": [],
        })
    return rows


def _finalize_status(summary: Dict[str, Any]) -> None:
    statuses = summary.pop("_query_statuses", [])
    if summary["facts"] or summary["present_query_count"]:
        summary["status"] = "present"
    elif any(status in {"weak", "partial", "unknown"} for status in statuses):
        summary["status"] = "unknown"
    elif statuses and all(status == "error" for status in statuses):
        summary["status"] = "error"
    elif any(status in {"empty", "absent"} for status in statuses):
        summary["status"] = "absent"

    if summary["status"] == "present" and summary["empty_query_count"]:
        summary["limitations"].append(
            f"另有 {summary['empty_query_count']} 次补充查询未命中，但不覆盖已采集真实事实"
        )


def aggregate_group_evidence(
    entities: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    status_keywords: Optional[List[str]] = None,
    *,
    include_event_facts: bool = True,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Aggregate independent observations without last-query-wins loss.

    ``include_event_facts=False`` is used by the authoritative snapshot path:
    thinking events then contribute query coverage and limitations only.  The
    diagnostic facts themselves come exclusively from normalized Fact Ledgers.
    """
    result: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for entity in entities or []:
        key = _entity_key(entity.get("namespace"), entity.get("name"))
        if key == "/":
            continue
        result[key] = {dimension: _empty_dimension(dimension) for dimension in REQUIRED_DIMENSIONS}
        for summary in result[key].values():
            summary["_query_statuses"] = []

    for index, event in enumerate(events or []):
        if event.get("type") != "tool_result" or event.get("status") != "success":
            continue
        target = _event_target(event)
        if not target:
            continue
        entity_key = _entity_key(*target)
        if entity_key not in result:
            continue
        tool = str(event.get("tool_name") or "").strip().lower()
        structured = event.get("structured") if isinstance(event.get("structured"), Mapping) else {}
        dimension = str(
            structured.get("dimension")
            or OBSERVABILITY_QUERY_TOOL_DIMENSIONS.get(tool)
            or ("kubernetes" if tool.startswith("kubectl_") else "")
        ).lower()

        if dimension in REQUIRED_DIMENSIONS:
            summary = result[entity_key][dimension]
            records = _records_from_structured(structured) if include_event_facts else []
            facts = [
                _compact_fact(record, fallback_seed=f"{entity_key}:{dimension}:{index}")
                for record in records
                if str(record.get("dimension") or dimension).strip().lower() == dimension
            ]
            if include_event_facts and dimension == "kubernetes" and not facts:
                facts = _kubernetes_fact_rows(event)
            coverage = str(
                structured.get("coverage")
                or ("present" if facts or dimension == "kubernetes" else "empty")
            ).strip().lower()
            summary["query_count"] += 1
            summary["_query_statuses"].append(coverage)
            if facts or coverage == "present":
                summary["present_query_count"] += 1
            if coverage in {"empty", "absent"} and not facts:
                summary["empty_query_count"] += 1
            summary["source_systems"] = sorted(set(summary["source_systems"]) | set(_source_list(structured, records)))
            _append_unique_facts(summary, facts)
            for limitation in structured.get("limitations") or []:
                if str(limitation).strip() and str(limitation) not in summary["limitations"]:
                    summary["limitations"].append(str(limitation))
            continue

    normalized_statuses = {str(item).strip().lower() for item in (status_keywords or [])}
    is_pre_runtime = bool(normalized_statuses & _PRE_RUNTIME_STATUSES)
    for dimensions in result.values():
        for summary in dimensions.values():
            _finalize_status(summary)
        if is_pre_runtime:
            for dimension in ("logging", "tracing"):
                summary = dimensions[dimension]
                if summary["status"] != "present":
                    summary["status"] = "not_applicable"
                    summary["limitations"].append("容器未启动，物理上不会产生应用日志或业务 Trace")
    return result
