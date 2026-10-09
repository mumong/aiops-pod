"""Both metric protocols share presentation, not query/diagnosis policy."""
from copy import deepcopy
import json

import pytest

from app.core.context.prometheus_result import normalize_prometheus_result
from app.core.context.observation import ObservationProcessor
from app.core.workflow.stream_contract import project_query_tool_event


def native(kind, result):
    return {"status": "success", "data": {"resultType": kind, "result": result}}


def display(payload, **extra):
    event = {"type": "tool_result", "tool_name": "execute_prometheus_instant_query",
             "tool_args": {"query": "arbitrary_expression"}, "result": json.dumps(payload), **extra}
    original = deepcopy(event)
    result = project_query_tool_event(event)["tool_display"]
    assert event == original
    return result


@pytest.mark.parametrize("value", ["1.419618055555557", "0", "NaN", "+Inf", "-Inf"])
def test_native_vector_preserves_exact_value_and_does_not_infer_percent(value):
    row = {"metric": {"instance": "node:9100"}, "value": [1791450642.501, value]}
    result = display(native("vector", [row]))
    point = result["measurements"][0]
    assert result["coverage"] == "present"
    assert point["value"] == value
    assert point["labels"] == row["metric"]
    assert point["unit"] == "unknown"
    assert point["observed_at"] == "2026-10-08T09:10:42.501000+00:00"
    assert result["query"] == {"query": "arbitrary_expression"}


def test_matrix_explicitly_shows_latest_point_not_average():
    result = display(native("matrix", [{"metric": {"__name__": "sample"},
                                        "values": [[200, "4"], [100, "2"], [150, "9"]]}]))
    point = result["measurements"][0]
    assert point["value"] == "4"
    assert point["sample_count"] == 3
    assert point["point_policy"] == "latest_per_series"
    assert point["sample_window"]["start"] == "1970-01-01T00:01:40+00:00"


@pytest.mark.parametrize("kind,value,value_kind", [("scalar", "0", "number"), ("string", "OK", "text")])
def test_scalar_and_string_are_one_result(kind, value, value_kind):
    result = display(native(kind, [100, value]))
    assert result["series_count"] == 1
    assert result["measurements"][0]["value"] == value
    assert result["measurements"][0]["value_kind"] == value_kind


@pytest.mark.parametrize("kind", ["vector", "matrix"])
def test_empty_is_not_zero(kind):
    result = display(native(kind, []))
    assert result["coverage"] == "empty"
    assert result["measurements"] == []


def test_display_limit_counts_omissions_without_changing_raw():
    payload = native("vector", [{"metric": {"instance": str(i)}, "value": [100, str(i)]} for i in range(25)])
    result = display(payload)
    assert len(result["measurements"]) == 20
    assert result["measurements_omitted"] == 5
    assert result["series_count"] == 25
    assert json.loads(result["result_excerpt"]) == payload


def test_pod_metrics_contract_preserves_units_labels_stats():
    payload = {"coverage": "present", "query": {"promql": "pod_expression"}, "facts": [
        {"name": "memory", "value": 1048576, "unit": "bytes", "labels": {"pod": "p"},
         "observed_at": "2026-10-08T00:00:00Z", "sample_count": 3, "stats": {"max": 1048576}}]}
    result = display(payload, tool_name="execute_pod_promql")
    assert result["measurements"][0]["unit"] == "bytes"
    assert result["measurements"][0]["stats"] == {"max": 1048576}
    assert result["query"] == payload["query"]


@pytest.mark.parametrize("payload", [
    native("unknown", []), native("vector", [{"histogram": [100, {}]}]),
    native("vector", [{"value": ["bad_time", "5"]}]), native("scalar", [100]),
])
def test_unsupported_or_malformed_is_not_empty(payload):
    result = display(payload)
    assert result["coverage"] == "unknown"
    assert result["parse_status"] == "unsupported"


def test_partial_parse_and_prometheus_warnings_are_visible():
    payload = native("vector", [{"value": [100, "1"]}, {"histogram": [100, {}]}])
    payload["warnings"] = ["partial response"]
    payload["infos"] = ["source notice"]
    result = display(payload)
    assert result["parse_status"] == "partial"
    assert result["unparsed_series"] == 1
    assert result["warnings"] == payload["warnings"]
    assert result["infos"] == payload["infos"]


def test_backend_error_is_not_empty():
    assert display({"status": "error", "error": "bad query"})["coverage"] == "error"


def test_structured_projection_survives_summarized_raw_and_bounds():
    payload = native("vector", [{"metric": {}, "value": [100, "2"]}] * 22)
    structured = normalize_prometheus_result(payload)
    projected = project_query_tool_event({"type": "tool_result", "result": "summary text", "structured": structured})
    assert len(projected["tool_display"]["measurements"]) == 20
    assert projected["tool_display"]["measurements_omitted"] == 2


def test_observation_parser_keeps_raw_model_input_unchanged():
    raw = json.dumps(native("vector", [{"metric": {}, "value": [100, "22.64"]}]))
    processor = ObservationProcessor.__new__(ObservationProcessor)
    structured, summary, kind = processor._extract_prometheus_result("execute_prometheus_instant_query", raw)
    assert summary == raw
    assert kind == "prometheus_result"
    assert structured["result_count"] == 1
    assert structured["facts"][0]["value"] == "22.64"


@pytest.mark.parametrize("tool,kind", [
    ("execute_prometheus_instant_query", "vector"),
    ("execute_prometheus_range_query", "matrix"),
])
@pytest.mark.parametrize("case", ["empty", "zero", "error", "unsupported"])
def test_native_processing_to_stream_preserves_execution_and_coverage(tmp_path, tool, kind, case):
    if case == "error":
        payload = {"status": "error", "error": "bad expression", "errorType": "bad_data"}
    elif case == "unsupported":
        payload = native("future_type", [])
    else:
        row = {"metric": {"instance": "a:9100"},
               **({"value": [100, "0"]} if kind == "vector" else {"values": [[100, "0"]]})}
        payload = native(kind, [] if case == "empty" else [row])
    raw = json.dumps(payload)
    processed = ObservationProcessor(archive_root=str(tmp_path)).process(
        run_id="metric-states", node_id="query_collect", sequence=1,
        tool_name=tool, raw_content=raw, preserve_raw=True,
    )
    assert processed["summary"] == raw
    assert processed["semantic_success"] is (case != "error")
    projected = display(payload, structured=processed["structured"])
    assert projected["coverage"] == {"empty": "empty", "zero": "present", "error": "error", "unsupported": "unknown"}[case]
    if case == "zero":
        assert projected["measurements"][0]["value"] == "0"
    if case == "unsupported":
        assert projected["parse_status"] == "unsupported"


@pytest.mark.parametrize("coverage", ["present", "empty", "absent"])
def test_pod_execution_success_is_independent_of_coverage(coverage):
    assert ObservationProcessor._is_semantically_successful(
        {"status": "query_succeeded", "coverage": coverage}, "raw pod response"
    )
    assert not ObservationProcessor._is_semantically_successful(
        {"status": "query_rejected", "coverage": coverage}, "scope rejected"
    )
