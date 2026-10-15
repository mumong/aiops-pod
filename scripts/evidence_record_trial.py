"""Experimental generic row operations plus a lifecycle-to-rows adapter.

No diagnosis rules, I/O, expressions or dynamic code. Not registered as an MCP
tool. Row schema and defaults belong to each source adapter, not the query engine.
"""
from __future__ import annotations

import copy
import json

POD_FIELDS = ["namespace", "pod", "uid", "node", "phase", "reason", "created_at",
              "deletion_timestamp", "conditions"]
CONTAINER_FIELDS = POD_FIELDS + [
    "container", "role", "status_observed", "ready", "restart_count_total",
    "restart_count_in_window", "state", "last_state", "last_termination_reason",
    "last_exit_code", "last_finished_at", "latest_observed_termination_at",
    "termination_within_window", "resources",
]
DEFAULT_FIELDS = {
    "pod": ["namespace", "pod", "uid", "node", "phase"],
    "container": ["namespace", "pod", "uid", "container", "role", "ready", "state",
                  "last_termination_reason", "last_exit_code", "last_finished_at",
                  "restart_count_total", "restart_count_in_window", "termination_within_window"],
}


def lifecycle_rows(payload, record_type):
    """Copy observed fields; never classify health or derive restart-window counts."""
    rows = []
    for pod in payload["pods"]:
        parent = {field: pod.get("name" if field == "pod" else field) for field in POD_FIELDS}
        if record_type == "pod":
            rows.append(parent)
            continue
        for container in pod.get("containers", []):
            row = parent | {field: container.get(field) for field in CONTAINER_FIELDS if field not in POD_FIELDS}
            previous = (container.get("last_state") or {}).get("terminated") or {}
            row.update(container=container.get("name"), last_termination_reason=previous.get("reason"),
                       last_exit_code=previous.get("exitCode"), last_finished_at=previous.get("finishedAt"))
            rows.append(row)
    return rows


def _compare(actual, op, expected):
    if op in {"eq", "ne"}:
        # Distinguish JSON booleans from numeric zero/one; explicit null is queryable.
        if actual is None and expected is not None:
            return None
        equal = (type(actual) is type(expected) or
                 type(actual) in (int, float) and type(expected) in (int, float)) and actual == expected
        return equal if op == "eq" else not equal
    if actual is None:
        return None
    if type(actual) not in (int, float) or type(expected) not in (int, float):
        raise ValueError("ordered comparisons require numeric values, not strings/booleans")
    return {"gt": actual > expected, "gte": actual >= expected,
            "lt": actual < expected, "lte": actual <= expected}[op]


def select_records(rows, *, known_fields, fields, where=(), match="all", group_by=None,
                   identity_fields=()):
    """Filter complete supplied rows, then group/count or select exact fields."""
    if match not in {"all", "any"}:
        raise ValueError("match must be all or any")
    if not isinstance(fields, list) or not fields or len(fields) > 40:
        raise ValueError("fields must be a nonempty list of at most 40 field names")
    invalid = [field for field in fields if not isinstance(field, str) or field not in known_fields]
    if invalid:
        raise ValueError(f"unknown fields for this record type: {invalid}; available fields: {known_fields}")
    if not isinstance(where, (list, tuple)) or len(where) > 12:
        raise ValueError("where must be a list of at most 12 conditions")
    for condition in where:
        if (not isinstance(condition, dict) or set(condition) != {"field", "op", "value"}
                or condition["field"] not in known_fields
                or condition["op"] not in {"eq", "ne", "gt", "gte", "lt", "lte"}):
            raise ValueError("invalid filter: use field, op, value")
    if group_by is not None and (not isinstance(group_by, str) or group_by not in known_fields):
        raise ValueError("unknown group_by field")
    selected, unknown = [], 0
    for row in rows:
        decisions = [_compare(row.get(c["field"]), c["op"], c["value"]) for c in where]
        if not decisions:
            matched = True
        elif match == "all":
            matched = False if False in decisions else None if None in decisions else True
        else:
            matched = True if True in decisions else None if None in decisions else False
        if matched is None:
            unknown += 1
        elif matched:
            selected.append(row)
    result = {"input_rows": len(rows), "matched_rows": len(selected), "unknown_filter_rows": unknown}
    if group_by is not None:
        groups = {}
        for row in selected:
            value = row.get(group_by)
            if isinstance(value, (dict, list)):
                raise ValueError("group_by requires a scalar field")
            key = json.dumps(value, ensure_ascii=False, allow_nan=False)
            groups.setdefault(key, {group_by: value, "count": 0})["count"] += 1
        result["groups"] = list(groups.values())
    else:
        columns = list(dict.fromkeys([*identity_fields, *fields]))
        result["rows"] = [{field: copy.deepcopy(row.get(field)) for field in columns} for row in selected]
    return result


def record_schema():
    fields = list(dict.fromkeys(CONTAINER_FIELDS))
    return {"type": "function", "function": {
        "name": "query_pod_lifecycle",
        "description": (
            "Read frozen lifecycle evidence using simple field selection/filtering/counts. "
            "record_type=pod gives only Pod identity/phase/conditions, NOT container state. "
            "record_type=container gives readiness/restarts/termination plus parent Pod identity, "
            "one row per container, "
            "including init/ephemeral. Filters are on the SAME row. group_by computes exact "
            "counts by a field, in the chosen record unit, not by the LLM. "
            "last_termination_reason/last_exit_code/last_finished_at copy last_state.terminated. "
            "pod is the original Pod name. Other fields have their original names. "
            "Missing data is unknown, and unknown_filter_rows is disclosed. "
            "Running/Ready does not rule out recent termination. Restart totals are lifetime "
            "counts, not window counts. Only the current snapshot/last termination is available. "
            "Source metadata includes observation time, recent window, paging and raw_ref. "
            "This is a received snapshot, not guaranteed complete datasource history."
        ),
        "parameters": {"type": "object", "additionalProperties": False, "properties": {
            "namespace": {"type": "string"}, "pod": {"type": "string"},
            "record_type": {"type": "string", "enum": ["pod", "container"], "default": "pod",
                            "description": "pod: inventory/counts. container: readiness/restarts/termination; includes parent Pod fields."},
            "fields": {"type": "array", "items": {"type": "string", "enum": fields},
                       "description": "For pod rows only: " + ", ".join(POD_FIELDS) +
                       ". All listed fields are available for container rows. Omit for essentials; identities retained."},
            "where": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                       "properties": {"field": {"type": "string", "enum": fields},
                                      "op": {"type": "string", "enum": ["eq", "ne", "gt", "gte", "lt", "lte"]},
                                      "value": {"type": ["string", "number", "boolean", "null"]}},
                       "required": ["field", "op", "value"]}},
            "match": {"type": "string", "enum": ["all", "any"], "default": "all"},
            "group_by": {"type": "string", "enum": fields,
                         "description": "Return exact count per distinct scalar value instead of rows."},
        }},
    }}


def query_records(payload, arguments, *, max_bytes=12000):
    from scripts.evaluate_evidence_computation import METADATA, encode

    if payload.get("status") != "success":
        return copy.deepcopy(payload)
    try:
        if set(arguments) - {"namespace", "pod", "record_type", "fields", "where", "match", "group_by"}:
            raise ValueError("unknown arguments")
        kind = arguments.get("record_type", "pod")
        if kind not in {"pod", "container"}:
            raise ValueError("record_type must be pod or container")
        if arguments.get("pod") and not arguments.get("namespace"):
            raise ValueError("pod requires namespace")
        if any(not isinstance(arguments[key], str) for key in ("namespace", "pod") if key in arguments):
            raise ValueError("scope arguments must be strings")
        rows = lifecycle_rows(payload, kind)
        rows = [row for row in rows if all(row.get(field) == arguments[field]
                for field in ("namespace", "pod") if arguments.get(field))]
        selected = select_records(
            rows, known_fields=POD_FIELDS if kind == "pod" else CONTAINER_FIELDS,
            fields=arguments.get("fields", DEFAULT_FIELDS[kind]), where=arguments.get("where", []),
            match=arguments.get("match", "all"), group_by=arguments.get("group_by"),
            identity_fields=["namespace", "pod", "uid"] + (["container", "role"] if kind == "container" else []))
        packet = {"status": "success", "record_unit": kind,
                  "source_metadata": {key: payload[key] for key in METADATA if key in payload},
                  "executed_query": arguments, **selected}
        if len(encode(packet).encode()) > max_bytes:
            return {"status": "error", "error": "result_too_large", "matched_rows": selected["matched_rows"],
                    "detail": "Select fewer fields or filter/group; no result rows were silently truncated."}
        return packet
    except (ValueError, KeyError, TypeError) as exc:
        return {"status": "error", "error": "invalid_query", "detail": str(exc)}
