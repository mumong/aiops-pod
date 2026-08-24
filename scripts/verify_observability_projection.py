#!/usr/bin/env python3
"""Replay archived MCP JSON through the production observability projection."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.context.observability_projection import (
    _selection_bucket,
    compact_json,
    project_observability_payload,
)


TOOL_BY_DIMENSION = {
    "metrics": "execute_pod_promql",
    "logging": "query_pod_logs",
    "tracing": "query_pod_tracing",
    "topology": "query_pod_topology",
}


def _read_payload(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("MCP response is not a JSON object")
    return value


def _query_texts(payload: dict[str, Any]) -> list[str]:
    query = payload.get("query") if isinstance(payload.get("query"), dict) else {}
    values: list[str] = []
    for key in ("promql", "dsl", "sql", "debug_query"):
        value = query.get(key)
        if isinstance(value, (dict, list)):
            text = compact_json(value)
        else:
            text = str(value or "")
        if len(text) >= 32:
            values.append(text)
    for execution in query.get("executions") or []:
        if not isinstance(execution, dict):
            continue
        nested = execution.get("query")
        text = compact_json(nested) if isinstance(nested, (dict, list)) else str(nested or "")
        if len(text) >= 32:
            values.append(text)
    return values


def run(patterns: list[str], max_chars: int, local_timezone: str) -> dict[str, Any]:
    paths = sorted({path for pattern in patterns for path in glob.glob(pattern)})
    report: dict[str, Any] = {
        "contract": "production_aiops.observation.v1",
        "files_scanned": len(paths),
        "payloads_evaluated": 0,
        "failures": [],
        "evidence_total": 0,
        "evidence_selected": 0,
        "evidence_omitted": 0,
        "semantic_patterns_total": 0,
        "semantic_patterns_selected": 0,
        "semantic_pattern_misses": [],
        "budget_stops": [],
        "selection_profile_gaps": [],
        "raw_ref_failures": [],
        "query_leaks": [],
        "selection_count_mismatches": [],
        "max_summary_chars": 0,
        "max_summary_path": None,
        "by_dimension": {},
    }
    for path in paths:
        try:
            payload = _read_payload(path)
            dimension = str(payload.get("dimension") or "")
            tool = TOOL_BY_DIMENSION.get(dimension)
            if tool is None:
                raise ValueError(f"unsupported dimension: {dimension or 'missing'}")
            result = project_observability_payload(
                payload,
                tool=tool,
                max_chars=max_chars,
                raw_ref=str(Path(path).resolve()),
                local_timezone=local_timezone,
            )
            summary = json.loads(result["summary"])
        except Exception as exc:
            report["failures"].append({"path": path, "error": str(exc)})
            continue

        structured_evidence = result["structured"].get("evidence") or []
        selected_evidence = summary.get("evidence") or []
        total_patterns = {_selection_bucket(item) for item in structured_evidence}
        selected_patterns = {_selection_bucket(item) for item in selected_evidence}
        missing_patterns = sorted(total_patterns - selected_patterns)
        selection = summary.get("summary_selection") or {}
        expected_omitted = len(structured_evidence) - len(selected_evidence)
        audit = result.get("audit") if isinstance(result.get("audit"), dict) else {}
        budget = audit.get("budget") if isinstance(audit.get("budget"), dict) else {}

        report["payloads_evaluated"] += 1
        report["evidence_total"] += len(structured_evidence)
        report["evidence_selected"] += len(selected_evidence)
        report["evidence_omitted"] += expected_omitted
        report["semantic_patterns_total"] += len(total_patterns)
        report["semantic_patterns_selected"] += len(selected_patterns)
        if missing_patterns:
            report["semantic_pattern_misses"].append(
                {
                    "path": path,
                    "missing_count": len(missing_patterns),
                    "missing_patterns": missing_patterns,
                }
            )
        if (
            budget.get("selection_terminated_by")
            in {"budget", "budget_scan_completed"}
            and budget.get("rejected_candidates", 0) > 0
        ):
            report["budget_stops"].append(
                {
                    "path": path,
                    "control_envelope_chars": budget.get("control_envelope_chars"),
                    "selection_chars": budget.get("selection_chars"),
                    "final_summary_chars": budget.get("final_summary_chars"),
                    "remaining_chars": budget.get("remaining_chars"),
                    "attempted_candidates": budget.get("attempted_candidates"),
                    "candidates_unattempted": budget.get("candidates_unattempted"),
                    "first_rejected": budget.get("first_rejected"),
                }
            )
        if audit.get("omitted_profile_counts"):
            report["selection_profile_gaps"].append(
                {
                    "path": path,
                    "selected": audit.get("selected_profile_counts", {}),
                    "omitted": audit.get("omitted_profile_counts", {}),
                }
            )
        if selection.get("selected") != len(selected_evidence) or selection.get("omitted") != expected_omitted:
            report["selection_count_mismatches"].append(path)
        retrieval = summary.get("retrieval") or {}
        if retrieval.get("raw_ref") != str(Path(path).resolve()) or not Path(path).is_file():
            report["raw_ref_failures"].append(path)
        if any(text in result["summary"] for text in _query_texts(payload)):
            report["query_leaks"].append(path)
        if len(result["summary"]) > report["max_summary_chars"]:
            report["max_summary_chars"] = len(result["summary"])
            report["max_summary_path"] = path

        dimension_stats = report["by_dimension"].setdefault(
            dimension,
            {
                "payloads": 0,
                "evidence_total": 0,
                "evidence_selected": 0,
                "evidence_omitted": 0,
                "semantic_patterns_total": 0,
                "semantic_patterns_selected": 0,
                "max_summary_chars": 0,
            },
        )
        dimension_stats["payloads"] += 1
        dimension_stats["evidence_total"] += len(structured_evidence)
        dimension_stats["evidence_selected"] += len(selected_evidence)
        dimension_stats["evidence_omitted"] += expected_omitted
        dimension_stats["semantic_patterns_total"] += len(total_patterns)
        dimension_stats["semantic_patterns_selected"] += len(selected_patterns)
        dimension_stats["max_summary_chars"] = max(
            dimension_stats["max_summary_chars"],
            len(result["summary"]),
        )

    report["failure_count"] = len(report["failures"])
    report["semantic_coverage_complete"] = not report["semantic_pattern_misses"]
    report["passed"] = not any(
        report[key]
        for key in (
            "failures",
            "raw_ref_failures",
            "query_leaks",
            "selection_count_mismatches",
        )
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--glob", action="append", required=True, dest="patterns")
    parser.add_argument("--max-chars", type=int, default=3000)
    parser.add_argument("--local-timezone", default="Asia/Shanghai")
    args = parser.parse_args()
    report = run(args.patterns, args.max_chars, args.local_timezone)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
