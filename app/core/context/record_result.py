"""Generic computed-record contract; parsing is independent of diagnosis and tools."""

import json

CONTRACT_VERSION = "evidence-records.v1"


def parse_record_result(raw):
    """None means another contract. Invalid records are explicit, never empty facts."""
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None
    if not isinstance(value, dict) or value.get("contract_version") != CONTRACT_VERSION:
        return None
    parsed = {**value}
    if value.get("status") == "error" and value.get("error"):
        return {**parsed, "parse_status": "parsed"}, False
    try:
        if value.get("status") != "success" or value.get("record_unit") not in {"pod", "container"}:
            raise ValueError("invalid execution status or row unit")
        source = value.get("source_metadata")
        if not isinstance(source, dict) or not isinstance(source.get("scope"), dict):
            raise ValueError("missing source scope")
        if not isinstance(source.get("observed_at"), str) or not source["observed_at"]:
            raise ValueError("missing source time")
        if source.get("coverage") not in {"present", "empty", "partial", "unknown"}:
            raise ValueError("invalid source coverage")
        pagination = value.get('pagination')
        if value.get("coverage") != source["coverage"] and not (pagination and value.get('coverage') == 'partial'):
            raise ValueError("source coverage mismatch")
        if not isinstance(value.get("executed_query"), dict):
            raise ValueError("missing executed query")
        counts = [value.get(k) for k in ("input_rows", "matched_rows", "unknown_filter_rows")]
        if any(type(n) is not int or n < 0 for n in counts) or counts[1] + counts[2] > counts[0]:
            raise ValueError("invalid row counts")
        if pagination is not None:
            if not isinstance(pagination, dict):
                raise ValueError('invalid pagination')
            offset, returned, total, remaining = [pagination.get(k) for k in ('offset', 'returned_rows', 'total_rows', 'remaining_rows')]
            if any(type(n) is not int or n < 0 for n in (offset, returned, total, remaining)):
                raise ValueError('invalid page counts')
            if offset + returned + remaining != total or (remaining and not returned):
                raise ValueError('inconsistent page counts')
            if type(pagination.get('source_has_more')) is not bool or not isinstance(pagination.get('snapshot_id'), str):
                raise ValueError('missing snapshot identity')
            more = remaining > 0 or pagination['source_has_more']
            if bool(pagination.get('next_continue_token')) != more:
                raise ValueError('missing or unexpected continuation')
            if more and value.get('coverage') != 'partial':
                raise ValueError('incomplete results must be partial')
            if pagination.get('next_continue_token') != source.get('next_continue_token'):
                raise ValueError('continuation mismatch')
        if value.get("result_type") == "records":
            columns, rows = value.get("columns"), value.get("rows")
            if (not isinstance(columns, list) or not columns or
                    any(not isinstance(c, str) for c in columns) or len(set(columns)) != len(columns)):
                raise ValueError("invalid columns")
            expected_count = pagination['returned_rows'] if pagination else counts[1]
            if pagination and pagination['total_rows'] != counts[1]:
                raise ValueError('snapshot record count mismatch')
            if not isinstance(rows, list) or len(rows) != expected_count:
                raise ValueError("record count mismatch")
            if any(not isinstance(row, dict) or set(row) != set(columns) for row in rows):
                raise ValueError("row/column mismatch")
        elif value.get("result_type") == "groups":
            field, groups = value["executed_query"].get("group_by"), value.get("groups")
            if not isinstance(field, str) or not isinstance(groups, list):
                raise ValueError("invalid grouping")
            seen, total = set(), 0
            for group in groups:
                if (not isinstance(group, dict) or set(group) != {field, "count"} or
                        type(group["count"]) is not int or group["count"] < 1 or
                        isinstance(group[field], (dict, list))):
                    raise ValueError("invalid group")
                key = json.dumps(group[field], allow_nan=False)
                if key in seen:
                    raise ValueError("duplicate group")
                seen.add(key)
                total += group["count"]
            if pagination and len(groups) != pagination['returned_rows']:
                raise ValueError('group page count mismatch')
            if (not pagination and total != counts[1]) or (pagination and total > counts[1]):
                raise ValueError("group count mismatch")
        else:
            raise ValueError("unknown record result type")
        return {**parsed, "parse_status": "parsed"}, True
    except (ValueError, TypeError, KeyError) as exc:
        return {**parsed, "parse_status": "failed", "parse_error": str(exc)}, False


def record_observation(raw, tool, archive):
    """Archive computed packets without applying another lossy tool summary."""
    result = parse_record_result(raw)
    if result is None:
        return None
    structured, success = result
    refs = archive(structured)
    return {"tool": tool, "status": "success", "semantic_success": success,
            "summary": raw, "structured": structured, "raw_chars": len(raw),
            "summary_chars": len(raw), "processed": True,
            "processor": "evidence_records+lossless", **refs}


def record_display(raw, raw_ref, limit=20):
    parsed = parse_record_result(raw)
    if parsed is None:
        return None
    value, success = parsed
    source = value.get("source_metadata") or {}
    rows = value.get("groups") if value.get("result_type") == "groups" else value.get("rows")
    rows = rows if success and isinstance(rows, list) else []
    return {
        "contract_version": CONTRACT_VERSION, "parse_status": value["parse_status"],
        "execution_status": value.get("status"), "semantic_success": success,
        "coverage": value.get("coverage"), "source_metadata": source,
        "query": value.get("executed_query"), "result_type": value.get("result_type"),
        "record_unit": value.get("record_unit"),
        "pagination": value.get('pagination'),
        **{key: value.get(key) for key in ("input_rows", "matched_rows", "unknown_filter_rows")},
        "columns": value.get("columns"), "records": rows[:limit],
        "records_omitted": max(0, len(rows) - limit),
        "error": value.get("error") or value.get("parse_error"),
        "result_excerpt": raw[:12000], "result_excerpt_truncated": len(raw) > 12000,
        "raw_ref": raw_ref,
    }
