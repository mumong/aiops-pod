import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[3] / "scripts" / "observability_summary_experiment.py"
SPEC = importlib.util.spec_from_file_location("observability_summary_experiment", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
build_shadow = MODULE.build_shadow


def _base_payload(dimension: str) -> dict:
    return {
        "status": "query_succeeded",
        "dimension": dimension,
        "coverage": "present",
        "directness": "direct",
        "entity": {
            "namespace": "team-a",
            "pod": "api-1",
            "pod_uid": "uid-1",
            "lifecycle_changed": False,
        },
        "query": {
            "time_range": {
                "start": "2026-08-20T08:00:00Z",
                "end": "2026-08-20T08:30:00Z",
            },
            "debug_query": "x" * 4000,
        },
        "facts": [],
        "samples": [],
        "evidence_refs": [],
        "truncated": True,
        "limits": {"max_serialized_bytes": 6144},
    }


def test_metrics_shadow_prioritizes_all_canonical_facts_over_query_text():
    payload = _base_payload("metrics")
    payload["fact_ledger"] = {
        "truncated": True,
        "records": [
            {
                "fact_id": "fact-a",
                "fact_type": "measurement",
                "attribute": "container_state_reason",
                "value": "1",
                "unit": "unitless",
                "timestamp": "2026-08-20T08:29:00Z",
                "source_system": "prometheus",
                "directness": "direct",
                "confidence": "high",
                "evidence_refs": ["metric-a"],
                "metadata": {
                    "labels": {
                        "__name__": "container_state_reason",
                        "namespace": "team-a",
                        "pod": "api-1",
                        "container": "app",
                        "reason": "Terminated",
                    },
                    "stats": {"first": 1, "min": 1, "max": 1, "last": 1},
                    "sample_count": 1,
                    "trend_evaluable": False,
                },
            },
            {
                "fact_id": "fact-b",
                "fact_type": "measurement",
                "attribute": "container_restarts_total",
                "value": "4",
                "unit": "count",
                "timestamp": "2026-08-20T08:29:00Z",
                "source_system": "prometheus",
                "directness": "direct",
                "confidence": "high",
                "evidence_refs": ["metric-b"],
                "metadata": {
                    "labels": {"container": "app"},
                    "stats": {"first": 2, "min": 2, "max": 4, "last": 4},
                    "sample_count": 8,
                    "trend_evaluable": True,
                },
            },
        ],
    }

    result = build_shadow(payload, max_chars=3000, local_timezone="Asia/Shanghai")

    assert len(result["summary_text"]) <= 3000
    assert result["audit"]["selected_fact_ids"] == ["fact-a", "fact-b"]
    assert "debug_query" not in result["summary_text"]
    assert "Terminated" in result["summary_text"]
    assert "trend_evaluable" in result["summary_text"]


def test_log_shadow_parses_json_and_preserves_unknown_scalar_attributes():
    payload = _base_payload("logging")
    payload["fact_ledger"] = {
        "truncated": False,
        "records": [{
            "fact_id": "fact-log",
            "fact_type": "log",
            "attribute": "log.message",
            "value": (
                '{"event":"request","level":"info","message":"state advanced",'
                '"trace_id":"trace-1","http_status":200,"path":"/work",'
                '"business_counter":48}'
            ),
            "timestamp": "2026-08-20T08:29:00Z",
            "source_system": "elasticsearch",
            "directness": "direct",
            "confidence": "high",
            "evidence_refs": ["log-a"],
            "metadata": {
                "value_original_length": 160,
                "value_truncated": False,
                "raw_ref": {"index": "logs-*", "document_id": "doc-1"},
            },
        }],
    }

    result = build_shadow(payload, max_chars=3000, local_timezone="Asia/Shanghai")
    evidence = result["summary"]["evidence"][0]

    assert evidence["trace_id"] == "trace-1"
    assert evidence["message"] == "state advanced"
    assert evidence["attributes"] == {"business_counter": 48}
    assert "message_raw" not in evidence


def test_trace_shadow_normalizes_naive_time_and_keeps_per_source_coverage():
    payload = _base_payload("tracing")
    payload["telemetry"] = {
        "deepflow": {"coverage": "present", "directness": "direct"},
        "tempo": {
            "coverage": "weak",
            "executed": True,
            "query_meta": {
                "queried_trace_ids": ["trace-1", "trace-2"],
                "failed_trace_count": 1,
                "successful_lookup_count": 1,
            },
        },
    }
    payload["fact_ledger"] = {
        "truncated": True,
        "records": [{
            "fact_id": "fact-flow",
            "fact_type": "flow",
            "attribute": "l7_flow",
            "value": {
                "timestamp": "2026-08-20 16:30:21",
                "trace_id": "trace-1",
                "request_type": "GET",
                "request_resource": "/health",
                "response_code": 200,
                "syscall_trace_id_request": "0",
            },
            "timestamp": "2026-08-20 16:30:21",
            "source_system": "deepflow",
            "directness": "direct",
            "confidence": "high",
            "evidence_refs": ["flow-a"],
        }],
    }

    result = build_shadow(payload, max_chars=3000, local_timezone="Asia/Shanghai")
    evidence = result["summary"]["evidence"][0]

    assert evidence["data"]["timestamp"]["utc"] == "2026-08-20T08:30:21Z"
    assert "syscall_trace_id_request" not in evidence["data"]
    assert result["summary"]["source_coverage"]["tempo"] == {
        "coverage": "weak",
        "executed": True,
        "failed_trace_count": 1,
        "successful_lookup_count": 1,
        "queried_trace_count": 2,
    }
