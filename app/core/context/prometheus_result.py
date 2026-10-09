"""Bounded presentation of the Prometheus API; no PromQL or unit inference."""

from datetime import datetime, timezone
import math
from typing import Any


def normalize_prometheus_result(payload: Any, limit: int = 20) -> dict[str, Any]:
    """Keep original values; matrix facts represent the latest point per series.

    The caller retains the full raw response. Histogram-only/unsupported results
    must not be reported as empty or silently converted into numeric samples.
    """
    result: dict[str, Any] = {
        "coverage": "unknown", "parse_status": "unsupported",
        "facts": [], "facts_omitted": 0,
    }
    if not isinstance(payload, dict):
        return result
    if payload.get("status") == "error" or payload.get("error"):
        return {**result, "coverage": "error", "parse_status": "error"}
    data = payload.get("data")
    if not isinstance(data, dict):
        return result
    kind, values = data.get("resultType"), data.get("result")
    result["result_type"] = kind
    result["warnings"] = payload.get("warnings") or []
    result["infos"] = payload.get("infos") or []
    if kind not in {"vector", "matrix", "scalar", "string"} or not isinstance(values, list):
        return result
    rows = values if kind in {"vector", "matrix"} else [{"value": values}]
    result.update(result_count=len(rows), series_count=len(rows))
    if not rows:
        return {**result, "coverage": "empty", "parse_status": "parsed"}
    total, invalid = 0, 0
    for row in rows:
        if not isinstance(row, dict):
            invalid += 1
            continue
        labels = row.get("metric") if isinstance(row.get("metric"), dict) else {}
        points = row.get("values") if kind == "matrix" else [row.get("value")]
        if not isinstance(points, list) or not points:
            invalid += 1
            continue
        timestamps = []
        for point in points:
            if not isinstance(point, list) or len(point) != 2:
                break
            try:
                stamp = float(point[0])
                if not math.isfinite(stamp) or not isinstance(point[1], (str, int, float)):
                    break
                if kind != "string":
                    float(point[1])  # Prometheus NaN/Inf strings remain verbatim.
                datetime.fromtimestamp(stamp, timezone.utc)
            except (ValueError, TypeError, OverflowError, OSError):
                break
            timestamps.append(stamp)
        if len(timestamps) != len(points):
            invalid += 1
            continue
        index = max(range(len(points)), key=timestamps.__getitem__)
        point = points[index]
        fact = {
            "name": labels.get("__name__") or ("prometheus_text" if kind == "string" else "prometheus_sample"),
            "value": point[1], "unit": "unknown", "labels": labels,
            "observed_at": datetime.fromtimestamp(timestamps[index], timezone.utc).isoformat(),
            "timestamp": point[0], "sample_count": len(points),
            "value_kind": "text" if kind == "string" else "number",
        }
        if kind == "matrix":
            fact["point_policy"] = "latest_per_series"
            fact["sample_window"] = {
                "start": datetime.fromtimestamp(min(timestamps), timezone.utc).isoformat(),
                "end": fact["observed_at"],
            }
        if row.get("histogram") or row.get("histograms"):
            invalid += 1
        total += 1
        if len(result["facts"]) < limit:
            result["facts"].append(fact)
    result.update(
        coverage="present" if total else "unknown",
        parse_status=("partial" if total else "unsupported") if invalid else "parsed",
        facts_omitted=max(0, total - limit), unparsed_series=invalid,
    )
    return result
