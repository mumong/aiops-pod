"""Generic, reversible evidence views; no tool names or diagnostic rules.

Raw archives remain authoritative. JSON pointers always address that raw JSON,
never an encoded preview. Incomplete views are indexes, not negative evidence.
"""
from __future__ import annotations

import json
from typing import Any

from .budget import estimate_tokens

VERSION = "evidence-view.v1"
DEFAULT_TOKENS = 4096
MAX_JSON_CHARS = 4_000_000


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _escape(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")


def _child(pointer: str, key: Any) -> str:
    return pointer + "/" + _escape(str(key))


def resolve_pointer(value: Any, pointer: str) -> Any:
    """RFC 6901 subset: exact object keys and nonnegative array indices only."""
    if not pointer:
        return value
    if not pointer.startswith("/"):
        raise ValueError("json_pointer must be empty or start with /")
    for segment in pointer[1:].split("/"):
        if any(part and part[0] not in "01" for part in segment.split("~")[1:]):
            raise ValueError("invalid JSON pointer escape")
        if segment.endswith("~"):
            raise ValueError("invalid JSON pointer escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            value = value[key]
        elif isinstance(value, list) and key.isascii() and key.isdigit():
            if len(key) > 1 and key.startswith("0"):
                raise ValueError("array index must not have leading zeros")
            value = value[int(key)]
        else:
            raise ValueError("pointer does not address a container")
    return value


def encode_json(value: Any) -> dict[str, Any]:
    """Factor identical fields only when the complete encoding is smaller.

    shared_paths disambiguates generated wrappers from identically named user
    fields. Rows retain their order, multiplicity, types and every varying field.
    """
    paths: list[str] = []
    table_paths: list[str] = []

    def visit(item: Any, pointer: str, depth: int) -> Any:
        if depth > 24:
            return item
        if isinstance(item, list) and len(item) > 1 and all(isinstance(r, dict) for r in item):
            # Homogeneous records can share their column names without choosing
            # any domain-specific fields. Keep sparse/heterogeneous rows literal.
            keys = list(item[0])
            if keys and all(list(row) == keys for row in item):
                table = {"columns": keys, "rows": [[row[k] for k in keys] for row in item]}
                if len(compact_json(table)) + len(pointer) + 200 < len(compact_json(item)):
                    # Compare against common-field factoring too: long repeated
                    # values benefit more from the existing representation.
                    common = {k: item[0][k] for k in keys
                              if all(compact_json(r[k]) == compact_json(item[0][k]) for r in item[1:])}
                    factored = {"common": common,
                                "rows": [{k: v for k, v in r.items() if k not in common} for r in item]}
                    if not common or len(compact_json(table)) + 200 < len(compact_json(factored)):
                        table_paths.append(pointer)
                        return table
            common = dict(item[0])
            for row in item[1:]:
                common = {k: v for k, v in common.items()
                          if k in row and compact_json(v) == compact_json(row[k])}
                if not common:
                    break
            if common:
                candidate = {"common": common,
                             "rows": [{k: v for k, v in r.items() if k not in common} for r in item]}
                if len(compact_json(candidate)) + len(pointer) + 4 < len(compact_json(item)):
                    paths.append(pointer)
                    return candidate
        if isinstance(item, dict):
            return {k: visit(v, _child(pointer, k), depth + 1) for k, v in item.items()}
        if isinstance(item, list):
            return [visit(v, _child(pointer, i), depth + 1) for i, v in enumerate(item)]
        return item

    encoded = visit(value, "", 0)
    original = {"encoding": "json", "value": value}
    if not paths and not table_paths:
        return original
    factored = {"encoding": "shared-fields.v1", "shared_paths": paths,
                "decode": "At each shared_path, each original record = common merged with its row; order unchanged.",
                "value": encoded}
    if table_paths:
        factored.update(encoding="record-tables.v1", table_paths=table_paths,
                        decode="At table_paths, each row is an ordered values array mapped to columns. "
                               "At shared_paths, merge common with each row. Other values stay literal. "
                               "Paths address the original JSON; order, duplicates, null and types are unchanged.")
    return factored if len(compact_json(factored)) < len(compact_json(original)) else original


def decode_json(encoded: dict[str, Any]) -> Any:
    """Reference inverse used to check that structural compaction loses no data."""
    shared = set(encoded.get("shared_paths", []))
    tables = set(encoded.get("table_paths", []))

    def visit(item: Any, pointer: str) -> Any:
        if pointer in tables:
            return [dict(zip(item["columns"], row, strict=True)) for row in item["rows"]]
        if pointer in shared:
            return [{**item["common"], **row} for row in item["rows"]]
        if isinstance(item, dict):
            return {k: visit(v, _child(pointer, k)) for k, v in item.items()}
        if isinstance(item, list):
            return [visit(v, _child(pointer, i)) for i, v in enumerate(item)]
        return item

    return visit(encoded["value"], "")


def _descriptor(value: Any, pointer: str) -> dict[str, Any]:
    info: dict[str, Any] = {"pointer": pointer, "deferred": True,
                            "type": type(value).__name__}
    if isinstance(value, (dict, list, str)):
        info["count"] = len(value)
    # Keys can themselves be very large; the index remains paginated below.
    if isinstance(value, dict):
        keys = list(value)[:12]
        if estimate_tokens(keys) < 200:
            info["keys"] = keys
            info["keys_complete"] = len(keys) == len(value)
    return info


def _parse(raw: str) -> tuple[Any, str]:
    if len(raw) > MAX_JSON_CHARS:
        return raw, "text_json_size_limit"
    try:
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result

        value = json.loads(raw, object_pairs_hook=unique_object,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        # The same serializer used below must support this document.
        compact_json(value).encode("utf-8")
        return value, "json"
    except (ValueError, RecursionError, UnicodeError):
        return raw, "text"


def _dataset_index(value: Any, pointer: str) -> list[dict[str, Any]]:
    """Expose nested collections without a chain of one-field archive reads."""
    result: list[dict[str, Any]] = []

    def visit(item: Any, path: str, depth: int):
        if depth > 5 or len(result) >= 12:
            return
        if isinstance(item, list):
            descriptor = {"pointer": path, "type": "list", "count": len(item)}
            # Schema discovery is independent of field meaning and input order.
            fields = list(dict.fromkeys(k for row in item if isinstance(row, dict) for k in row))
            if fields and estimate_tokens(fields[:20]) < 160:
                descriptor.update(item_fields=fields[:20], fields_complete=len(fields) <= 20)
            if estimate_tokens([*result, descriptor]) <= 350:
                result.append(descriptor)
            # Inspect singleton envelopes, not every record of a large dataset.
            if len(item) == 1:
                visit(item[0], _child(path, 0), depth + 1)
        elif isinstance(item, dict):
            for key, child in item.items():
                visit(child, _child(path, key), depth + 1)

    visit(value, pointer, 0)
    return result


def explicit_execution_failure(raw: str) -> bool:
    """Read common top-level execution signals, never nested resource health."""
    value, source_format = _parse(raw)
    if source_format != "json" or not isinstance(value, dict):
        return False
    return (value.get("ok") is False or value.get("success") is False
            or value.get("status") in ("error", "failed", "failure", "query_rejected", "query_parse_failed"))


def build_evidence_view(
    raw: str, raw_ref: str, *, max_tokens: int = DEFAULT_TOKENS,
    json_pointer: str = "", start: int = 0, limit: int = 50,
    search: str = "", fields: list[str] | None = None,
) -> dict[str, Any]:
    """Return a bounded view, or an exact, actionable error.

    start indexes the returned subtree, not the upstream service. Search is a
    case-insensitive literal match over each complete immediate record/line.
    fields are top-level names or relative JSON pointers; missing fields are
    marked, not null-filled. Names are escaped, never interpreted as code.
    A view is complete only when no pagination, filtering or deferred value exists.
    """
    budget = max(512, min(int(max_tokens), 16384))
    start = max(0, int(start))
    limit = max(1, min(int(limit), 200))
    if (len(raw_ref) > 2048 or len(json_pointer) > 2048 or len(search) > 512
            or len(fields or []) > 32 or any(len(f) > 512 for f in (fields or []))):
        return {"contract_version": VERSION, "status": "invalid_selector",
                "view_complete": False, "error": "Selector exceeds bounded read limits."}
    value, source_format = _parse(raw)
    base: dict[str, Any] = {
        "contract_version": VERSION, "raw_ref": raw_ref,
        "source_format": source_format, "scope": "received_tool_response_not_entire_datasource",
        "json_pointer": json_pointer, "view_complete": False,
        "budget": {"max_tokens": budget, "counter": "estimated_utf8_bytes_div_3"},
        "retrieval": {"tool": "read_context_archive", "archive_path": raw_ref,
                      "view": "compact", "json_pointer": json_pointer},
    }

    def fits(candidate: dict[str, Any]) -> bool:
        return estimate_tokens(compact_json(candidate)) <= budget

    def finish(candidate: dict[str, Any]) -> dict[str, Any]:
        if fits(candidate):
            return candidate
        return {"contract_version": VERSION, "status": "view_budget_too_small",
                "view_complete": False, "error": "Navigation metadata exceeds budget; narrow selectors or raise budget."}

    def complete(data: dict[str, Any]) -> dict[str, Any]:
        # An archive address is provenance, not an instruction to repeat a read.
        result = {k: v for k, v in base.items() if k != "retrieval"}
        result.update(view_complete=True, integrity=("lossless_selected_subtree" if json_pointer
                                                    else "lossless_received_response"),
                      omitted_records=0, data=data)
        return result

    try:
        if json_pointer and source_format != "json":
            raise ValueError("JSON pointer requires parsed JSON; use raw offset/length for text")
        value = resolve_pointer(value, json_pointer)
    except (KeyError, IndexError, ValueError) as exc:
        return finish({**base, "status": "invalid_pointer", "error": str(exc)})

    filtered = bool(search or fields)
    if source_format == "json" and not start and not filtered:
        encoded = encode_json(value)
        full = complete(encoded)
        if fits(full) and (not isinstance(value, list) or len(value) <= limit):
            return full
    elif source_format != "json" and not start and not filtered:
        # Exact consecutive-line folding preserves chronology and multiplicity.
        runs: list[dict[str, Any]] = []
        for line in raw.splitlines(keepends=True):
            if runs and runs[-1]["line"] == line:
                runs[-1]["repeat"] += 1
            else:
                runs.append({"line": line, "repeat": 1})
        full = complete({"encoding": "text-runs.v1", "runs": runs,
                         "decode": "Repeat each exact line repeat times in order; concatenate."})
        if fits(full):
            return full

    text_mode = source_format != "json"
    missing_fields: set[str] = set()
    if text_mode:
        records = list(enumerate(raw.splitlines(keepends=True)))
        unit = "line"
    elif isinstance(value, dict):
        if fields:
            records, unit = [], "selected_field"
            for field in fields:
                pointer = field if field.startswith("/") else _child("", field)
                try:
                    records.append((pointer, resolve_pointer(value, pointer)))
                except (KeyError, IndexError, ValueError):
                    records.append((pointer, None))
                    missing_fields.add(pointer)
        else:
            records, unit = list(value.items()), "field"
    elif isinstance(value, list):
        records, unit = list(enumerate(value)), "record"
    else:
        # Oversized scalar: provide an exact prefix and an explicit char cursor.
        scalar = value if isinstance(value, str) else compact_json(value)
        result = {**base, "unit": "character", "total": len(scalar), "start": start,
                  "next_start": None, "data": ""}
        lo, hi = 0, len(scalar[start:])
        while lo < hi:
            mid = (lo + hi + 1) // 2
            test = {**result, "data": scalar[start:start + mid], "next_start": start + mid}
            if fits(test):
                lo = mid
            else:
                hi = mid - 1
        end = start + lo
        result.update(data=scalar[start:end], next_start=end if end < len(scalar) else None,
                      view_complete=start == 0 and end >= len(scalar))
        return finish(result)

    result = {**base, "unit": unit, "total": len(records), "start": start,
              "selection": "source_order", "search": search or None,
              "fields": fields or None, "records": [], "next_start": None,
              "search_complete": None, "matched_in_scanned_suffix": None,
              "note": "Deferred/unshown records may contain relevant evidence. Read by pointer/page/search; this is not an absence finding."}
    if not text_mode:
        index = _dataset_index(value, json_pointer)
        if estimate_tokens(compact_json({**result, "datasets": index})) < budget // 2:
            result["datasets"] = index
    deferred = False
    scanned = start
    matched = 0
    for index in range(start, len(records)):
        key, item = records[index]
        if search and search.casefold() not in compact_json(item).casefold():
            scanned = index + 1
            continue
        pointer = (json_pointer + key if unit == "selected_field" else _child(json_pointer, key)) if not text_mode else ""
        selected = item
        if fields and unit != "selected_field":
            selected = {}
            for field in fields:
                field_pointer = field if field.startswith("/") else _child("", field)
                try:
                    selected[field] = {"value": resolve_pointer(item, field_pointer)}
                except (KeyError, IndexError, ValueError):
                    selected[field] = {"missing": True}
        entry = {"index": index, "pointer": pointer, "data": encode_json(selected)}
        if unit == "selected_field" and key in missing_fields:
            entry = {"index": index, "pointer": pointer, "missing": True}
        if text_mode:
            entry["line"] = key
        candidate = {**result, "records": [*result["records"], entry], "next_start": index + 1}
        if not fits(candidate):
            # Do not skip a big record: expose its address, then allow navigation.
            entry = {"index": index, **_descriptor(item, pointer)}
            if text_mode:
                entry.update(line=key, raw_char_offset=sum(len(r[1]) for r in records[:index]))
            candidate = {**result, "records": [*result["records"], entry], "next_start": index + 1}
            if not fits(candidate):
                if not result["records"]:
                    return {"contract_version": VERSION, "raw_ref": raw_ref,
                            "status": "view_budget_too_small", "view_complete": False,
                            "error": "Record address/envelope exceeds budget; increase max_tokens or use raw offset/length."}
                break
            deferred = True
        result["records"].append(entry)
        matched += 1
        scanned = index + 1
        if len(result["records"]) >= limit:
            break
    result["next_start"] = scanned if scanned < len(records) else None
    result["view_complete"] = not (deferred or filtered or start or result["next_start"] is not None)
    # A complete search is not a complete data view. No new upstream coverage claims.
    result["search_complete"] = scanned >= len(records) if search else None
    result["matched_in_scanned_suffix"] = matched if search else None
    return finish(result)
