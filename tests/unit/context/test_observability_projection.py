import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.context.observability_projection import project_observability_payload


def _payload(dimension: str, records: list[dict], **extra) -> dict:
    value = {
        "ok": True,
        "status": "query_succeeded",
        "source_system": {
            "metrics": "prometheus",
            "logging": "elasticsearch",
            "tracing": "deepflow+tempo",
        }.get(dimension, "kubernetes"),
        "dimension": dimension,
        "entity": {
            "namespace": "demo",
            "pod": "api-1",
            "pod_uid": "uid-1",
            "lifecycle_changed": False,
        },
        "purpose": "let the agent inspect real evidence",
        "coverage": "present",
        "directness": "direct",
        "query": {
            "time_range": {
                "start": "2026-08-20T08:00:00Z",
                "end": "2026-08-20T08:30:00Z",
            },
            "debug_query": "SELECT " + ("unused_query_text " * 500),
        },
        "facts": [],
        "samples": [],
        "evidence_refs": [],
        "fact_ledger": {"records": records, "truncated": False},
        "truncated": False,
        "limits": {"response_serialization": "lossless"},
        "serialization": {
            "policy": "lossless",
            "response_truncated": False,
            "serialized_bytes": 20000,
        },
    }
    value.update(extra)
    return value


def _record(fact_id: str, dimension: str, value, **extra) -> dict:
    item = {
        "fact_id": fact_id,
        "fact_type": {
            "metrics": "measurement",
            "logging": "log",
            "tracing": "flow",
        }.get(dimension, "relationship"),
        "attribute": {
            "metrics": "container_restarts_total",
            "logging": "log.message",
            "tracing": "l7_flow",
        }.get(dimension, "topology.relationship"),
        "value": value,
        "source_system": {
            "metrics": "prometheus",
            "logging": "elasticsearch",
            "tracing": "deepflow",
        }.get(dimension, "kubernetes"),
        "directness": "direct",
        "confidence": "high",
        "evidence_refs": [f"ref:{fact_id}"],
    }
    item.update(extra)
    return item


def test_projection_keeps_evidence_and_raw_ref_but_not_full_query():
    records = [
        _record(
            "fact-restarts",
            "metrics",
            "8",
            unit="count",
            metadata={
                "labels": {"container": "api"},
                "stats": {"first": 4, "min": 4, "max": 8, "last": 8},
                "sample_count": 11,
                "trend_evaluable": True,
            },
        ),
        _record(
            "fact-reason",
            "metrics",
            "1",
            attribute="container_last_terminated_reason",
            metadata={"labels": {"container": "api", "reason": "OOMKilled"}},
        ),
    ]

    result = project_observability_payload(
        _payload("metrics", records),
        tool="execute_pod_promql",
        max_chars=2200,
        raw_ref="/archive/tools/001.raw.txt",
    )
    summary = json.loads(result["summary"])

    assert len(result["summary"]) <= 2200
    assert {item["id"] for item in summary["evidence"]} == {
        "fact-restarts",
        "fact-reason",
    }
    assert summary["retrieval"]["raw_ref"] == "/archive/tools/001.raw.txt"
    assert summary["retrieval"]["mcp_response_complete"] is True
    assert "unused_query_text" not in result["summary"]
    assert result["audit"]["evidence_omitted"] == 0


def test_metric_projection_keeps_zero_active_states_stats_and_honest_counts():
    records = [
        _record(
            "fact-restarts",
            "metrics",
            5,
            attribute="kube_pod_container_status_restarts_total",
            unit="count",
            timestamp="2026-08-20T08:29:00Z",
            metadata={
                "labels": {"container": "api"},
                "stats": {"first": 2, "min": 2, "max": 5, "last": 5},
                "sample_count": 11,
                "trend_evaluable": True,
            },
        ),
        _record(
            "fact-waiting-zero",
            "metrics",
            0,
            attribute="kube_pod_container_status_waiting_reason",
            unit="count",
            metadata={
                "labels": {
                    "container": "api",
                    "reason": "CrashLoopBackOff",
                },
                "sample_count": 1,
                "trend_evaluable": False,
            },
        ),
        _record(
            "fact-running-active",
            "metrics",
            1,
            attribute="kube_pod_status_phase",
            unit="boolean",
            metadata={"labels": {"phase": "Running"}},
        ),
    ]
    payload = _payload(
        "metrics",
        records,
        counts={
            "matched": 12,
            "retrieved": 12,
            "normalized": 3,
            "returned": 3,
            "dropped": 9,
        },
        truncation={
            "truncated": True,
            "stages": [
                {
                    "stage": "max_series",
                    "input": 12,
                    "output": 3,
                    "dropped": 9,
                    "reason": "query_series_limit",
                }
            ],
        },
    )

    result = project_observability_payload(
        payload,
        tool="execute_pod_promql",
        max_chars=3000,
        raw_ref="/archive/metrics.raw.txt",
    )
    summary = json.loads(result["summary"])
    evidence = {item["id"]: item for item in summary["evidence"]}

    assert evidence["fact-restarts"]["value"] == 5
    assert evidence["fact-restarts"]["unit"] == "count"
    assert evidence["fact-restarts"]["stats"]["max"] == 5
    assert evidence["fact-restarts"]["sample_count"] == 11
    assert evidence["fact-restarts"]["trend_evaluable"] is True
    assert evidence["fact-waiting-zero"]["value"] == 0
    assert evidence["fact-waiting-zero"]["labels"]["reason"] == "CrashLoopBackOff"
    assert evidence["fact-running-active"]["labels"]["phase"] == "Running"
    assert {
        key: summary["counts"][key]
        for key in ("matched", "retrieved", "normalized", "returned", "dropped")
    } == {
        "matched": 12,
        "retrieved": 12,
        "normalized": 3,
        "returned": 3,
        "dropped": 9,
    }
    assert summary["truncation"]["truncated"] is True
    assert summary["truncation"]["reasons"] == ["query_series_limit", "source_or_collection_limit"]
    assert summary["retrieval"]["raw_ref"] == "/archive/metrics.raw.txt"


def test_json_logs_are_structured_and_pattern_selection_keeps_non_error_signal():
    repeated = [
        _record(
            f"fact-error-{index}",
            "logging",
            json.dumps(
                {
                    "event": "request",
                    "level": "error",
                    "message": f"dependency timeout attempt={index}",
                    "trace_id": f"trace-{index}",
                    "http_status": 503,
                }
            ),
        )
        for index in range(20)
    ]
    normal_but_decisive = _record(
        "fact-normal",
        "logging",
        json.dumps(
            {
                "event": "probe",
                "level": "info",
                "message": "liveness handler returned normally",
                "http_status": 200,
                "business_counter": 48,
            }
        ),
    )

    result = project_observability_payload(
        _payload("logging", [*repeated, normal_but_decisive]),
        tool="query_pod_logs",
        max_chars=2200,
        raw_ref="/archive/logs.raw.txt",
    )
    summary = json.loads(result["summary"])
    selected = summary["evidence"]

    assert any(item.get("http_status") == 503 for item in selected)
    assert any(item.get("http_status") == 200 for item in selected)
    normal = next(item for item in selected if item.get("http_status") == 200)
    assert normal["attributes"] == {"business_counter": 48}
    assert normal["message"] == "liveness handler returned normally"
    assert all("parsed" not in item and "message_raw" not in item for item in selected)


def test_log_projection_joins_ledger_fact_and_sample_identity_without_losing_raw_ref():
    ref = "log-demo-api-1-decisive"
    raw_ref = {
        "source_system": "elasticsearch",
        "index": ".ds-filebeat-2026.08.20-000001",
        "document_id": "doc-42",
    }
    message = json.dumps(
        {
            "event": "dependency_check",
            "level": "warn",
            "message": "cache unavailable",
            "trace_id": "trace-42",
            "span_id": "span-42",
            "http_status": 503,
            "retry_budget": 0,
        }
    )
    ledger_record = _record(
        "fact-log-identity",
        "logging",
        message,
        evidence_refs=[ref],
        timestamp="2026-08-20T08:21:00Z",
        metadata={
            "raw_ref": raw_ref,
            "value_original_length": len(message),
            "value_sha256": "sha-42",
            "value_truncated": False,
        },
    )
    payload = _payload(
        "logging",
        [ledger_record],
        query={
            "identity_basis": "pod_uid",
            "time_range": {
                "start": "2026-08-20T08:00:00Z",
                "end": "2026-08-20T08:30:00Z",
            },
        },
        facts=[
            {
                "ref": ref,
                "source_system": "elasticsearch",
                "dimension": "logging",
                "name": "log.message",
                "value": message,
                "pod_uid": "uid-1",
                "raw_ref": raw_ref,
            }
        ],
        samples=[
            {
                "ref": ref,
                "timestamp": "2026-08-20T08:21:00Z",
                "message": message,
                "container": "sidecar-cache",
                "pod_uid": "uid-1",
                "message_original_length": len(message),
                "message_sha256": "sha-42",
                "message_truncated": False,
                "raw_ref": raw_ref,
            }
        ],
    )

    result = project_observability_payload(
        payload,
        tool="query_pod_logs",
        max_chars=2600,
        raw_ref="/archive/logs.raw.txt",
    )
    evidence = json.loads(result["summary"])["evidence"][0]

    assert evidence["container"] == "sidecar-cache"
    assert evidence["pod_uid"] == "uid-1"
    assert evidence["identity_basis"] == "pod_uid"
    assert evidence["raw_ref"] == raw_ref
    assert evidence["value_original_length"] == len(message)
    assert evidence["value_truncated"] is False
    assert evidence["attributes"]["retry_budget"] == 0


def test_temporal_pattern_stratification_keeps_rare_tail_without_severity_rules():
    distinct_error_patterns = [
        _record(
            f"fact-pattern-{index}",
            "logging",
            json.dumps(
                {
                    "event": f"failure_{chr(97 + index)}",
                    "level": "error",
                    "message": f"distinct alphabetic failure {chr(97 + index)}",
                    "http_status": 503,
                }
            ),
        )
        for index in range(18)
    ]
    rare_tail = _record(
        "fact-rare-tail",
        "logging",
        json.dumps(
            {
                "event": "termination_snapshot",
                "level": "info",
                "message": "application was serving normally before termination",
                "http_status": 200,
                "unknown_health_epoch": 7,
            }
        ),
    )

    result = project_observability_payload(
        _payload("logging", [*distinct_error_patterns, rare_tail]),
        tool="query_pod_logs",
        max_chars=2200,
        raw_ref="/archive/many-patterns.raw.txt",
    )
    summary = json.loads(result["summary"])

    assert summary["summary_selection"]["omitted"] > 0
    assert summary["summary_selection"]["strategy"] == (
        "information_ranked_pattern_round_robin_budget_scan_no_fault_names"
    )
    tail = next(item for item in summary["evidence"] if item["id"] == "fact-rare-tail")
    assert tail["http_status"] == 200
    assert tail["level"] == "info"
    assert tail["attributes"]["unknown_health_epoch"] == 7
    assert summary["retrieval"]["raw_ref"] == "/archive/many-patterns.raw.txt"
    audit = result["audit"]
    assert audit["semantic_patterns_omitted"] > 0
    assert audit["budget"]["selection_terminated_by"] == "budget_scan_completed"
    assert audit["budget"]["first_rejected"]["reason"] == (
        "candidate_exceeds_remaining_budget"
    )
    assert audit["budget"]["candidates_unattempted"] == 0
    assert audit["omitted_pattern_preview"]
    assert audit["selected_profile_counts"]
    assert audit["omitted_profile_counts"]


def test_trace_time_is_normalized_and_zero_syscall_ids_are_removed():
    record = _record(
        "fact-flow",
        "tracing",
        {
            "timestamp": "2026-08-20 16:30:21",
            "trace_id": "trace-1",
            "request_type": "GET",
            "request_resource": "/health",
            "response_code": 200,
            "syscall_trace_id_request": "0",
        },
        timestamp="2026-08-20 16:30:21",
    )
    payload = _payload(
        "tracing",
        [record],
        telemetry={
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
        },
    )

    result = project_observability_payload(
        payload,
        tool="query_pod_tracing",
        max_chars=2200,
    )
    summary = json.loads(result["summary"])
    evidence = summary["evidence"][0]

    assert evidence["data"]["timestamp"]["utc"] == "2026-08-20T08:30:21Z"
    assert "syscall_trace_id_request" not in evidence["data"]
    assert summary["source_coverage"]["tempo"]["queried_trace_count"] == 2
    assert summary["source_coverage"]["tempo"]["failed_trace_count"] == 1


def test_trace_projection_distinguishes_flow_and_span_and_keeps_normal_http_200():
    trace_id = "0123456789abcdef0123456789abcdef"
    records = [
        _record(
            "fact-flow-200",
            "tracing",
            {
                "timestamp": "2026-08-20 16:30:21",
                "trace_id": trace_id,
                "span_id": "flow-span",
                "direction": "inbound",
                "src_ip": "10.0.0.2",
                "dst_ip": "10.0.0.8",
                "l7_protocol_str": "HTTP",
                "request_type": "GET",
                "request_resource": "/health",
                "response_code": 200,
                "response_status": "Ok",
                "response_duration": 8200,
            },
            fact_type="flow",
            source_system="deepflow",
            timestamp="2026-08-20 16:30:21",
        ),
        _record(
            "fact-span-ok",
            "tracing",
            {
                "timestamp": "2026-08-20T08:30:21Z",
                "trace_id": trace_id,
                "span_id": "tempo-span",
                "service": "api",
                "span_name": "GET /health",
                "span_status": "OK",
                "duration_us": 8400,
                "attributes": {"k8s.pod.uid": "uid-1", "health_epoch": 9},
            },
            fact_type="span",
            source_system="tempo",
            timestamp="2026-08-20T08:30:21Z",
        ),
    ]
    payload = _payload(
        "tracing",
        records,
        flows=[records[0]["value"]],
        spans=[records[1]["value"]],
        telemetry={
            "deepflow": {"coverage": "present", "directness": "direct"},
            "tempo": {
                "coverage": "present",
                "directness": "direct",
                "executed": True,
                "query_meta": {
                    "queried_trace_ids": [trace_id],
                    "successful_lookup_count": 1,
                    "failed_trace_count": 0,
                },
            },
        },
    )

    result = project_observability_payload(
        payload,
        tool="query_pod_tracing",
        max_chars=3000,
        raw_ref="/archive/tracing.raw.txt",
    )
    summary = json.loads(result["summary"])
    evidence = {item["trace_type"]: item for item in summary["evidence"]}

    assert set(evidence) == {"flow", "span"}
    assert evidence["flow"]["data"]["response_code"] == 200
    assert evidence["flow"]["data"]["timestamp"]["utc"] == "2026-08-20T08:30:21Z"
    assert evidence["span"]["data"]["span_status"] == "OK"
    assert evidence["span"]["data"]["attributes"]["health_epoch"] == 9
    assert summary["source_coverage"]["tempo"]["successful_lookup_count"] == 1


def test_metric_budget_prefers_active_direct_facts_over_multiple_zero_phases():
    records = [
        _record(
            f"fact-phase-{phase.lower()}",
            "metrics",
            0,
            attribute="kube_pod_status_phase",
            metadata={"labels": {"container": "kube-state-metrics", "phase": phase}},
            directness="related_context",
            confidence="low",
        )
        for phase in ("Pending", "Succeeded", "Failed", "Unknown")
    ]
    records.extend(
        [
            _record(
                "fact-phase-running",
                "metrics",
                1,
                attribute="kube_pod_status_phase",
                metadata={"labels": {"container": "kube-state-metrics", "phase": "Running"}},
                directness="related_context",
                confidence="low",
            ),
            _record(
                "fact-restarts-active",
                "metrics",
                7,
                attribute="kube_pod_container_status_restarts_total",
                metadata={"labels": {"container": "api"}},
            ),
            _record(
                "fact-waiting-active",
                "metrics",
                1,
                attribute="kube_pod_container_status_waiting_reason",
                metadata={"labels": {"container": "api", "reason": "GenericWaitingState"}},
            ),
            _record(
                "fact-terminated-active",
                "metrics",
                1,
                attribute="kube_pod_container_status_last_terminated_reason",
                metadata={"labels": {"container": "api", "reason": "GenericExitState"}},
            ),
        ]
    )

    result = project_observability_payload(
        _payload("metrics", records),
        tool="execute_pod_promql",
        max_chars=3000,
    )
    selected_ids = {item["id"] for item in json.loads(result["summary"])["evidence"]}

    assert {
        "fact-phase-running",
        "fact-restarts-active",
        "fact-waiting-active",
        "fact-terminated-active",
    } <= selected_ids


def test_trace_budget_gives_flow_and_span_a_first_wave_slot():
    trace_id = "0123456789abcdef0123456789abcdef"
    flows = [
        _record(
            f"fact-flow-{index}",
            "tracing",
            {
                "timestamp": f"2026-08-20 16:30:{index:02d}",
                "trace_id": trace_id,
                "span_id": f"flow-{index}",
                "direction": "inbound",
                "src_ip": "10.0.0.2",
                "dst_ip": "10.0.0.8",
                "l7_protocol_str": "HTTP",
                "request_type": "GET",
                "request_resource": "/work",
                "response_code": 200 if index % 2 == 0 else 500,
                "response_status": "Ok" if index % 2 == 0 else "ServerError",
                "response_duration": 8000 + index,
            },
            fact_type="flow",
            source_system="deepflow",
            timestamp=f"2026-08-20 16:30:{index:02d}",
        )
        for index in range(12)
    ]
    spans = [
        _record(
            f"fact-span-{index}",
            "tracing",
            {
                "timestamp": f"2026-08-20T08:30:{index:02d}Z",
                "trace_id": trace_id,
                "span_id": f"tempo-{index}",
                "service": "api",
                "span_name": "GET /work",
                "span_status": "ERROR",
                "duration_us": 8100 + index,
                "attributes": {"k8s.pod.uid": "uid-1", "attempt": index},
            },
            fact_type="span",
            source_system="tempo",
            directness="related_context",
            confidence="low",
            timestamp=f"2026-08-20T08:30:{index:02d}Z",
        )
        for index in range(3)
    ]

    result = project_observability_payload(
        _payload("tracing", [*flows, *spans], flows=flows, spans=spans),
        tool="query_pod_tracing",
        max_chars=3000,
    )
    evidence = json.loads(result["summary"])["evidence"]
    trace_types = {item["trace_type"] for item in evidence}
    flow_codes = {
        item["data"]["response_code"]
        for item in evidence
        if item["trace_type"] == "flow"
    }

    assert trace_types == {"flow", "span"}
    assert flow_codes == {200, 500}


def test_log_pattern_keeps_head_and_tail_state_progression():
    records = [
        _record(
            f"fact-progress-{value}",
            "logging",
            json.dumps(
                {
                    "event": "allocation_progress",
                    "level": "info",
                    "message": f"allocation advanced allocated_mib={value}",
                    "allocated_mib": value,
                }
            ),
        )
        for value in range(10, 50, 2)
    ]

    result = project_observability_payload(
        _payload("logging", records),
        tool="query_pod_logs",
        max_chars=3000,
    )
    selected_values = {
        item["attributes"]["allocated_mib"]
        for item in json.loads(result["summary"])["evidence"]
    }

    assert {10, 48} <= selected_values


def test_budget_scan_skips_oversized_candidate_and_keeps_later_small_pattern():
    oversized = _record(
        "fact-oversized",
        "logging",
        json.dumps(
            {
                "event": "large_context",
                "level": "info",
                "message": "large structured context",
                "opaque_context": "x" * 5000,
            }
        ),
    )
    small = _record(
        "fact-small",
        "logging",
        json.dumps(
            {
                "event": "small_context",
                "level": "info",
                "message": "small independent observation",
                "state": "present",
            }
        ),
    )

    result = project_observability_payload(
        _payload("logging", [oversized, small]),
        tool="query_pod_logs",
        max_chars=1800,
    )
    selected_ids = {item["id"] for item in json.loads(result["summary"])["evidence"]}

    assert "fact-oversized" not in selected_ids
    assert "fact-small" in selected_ids
    assert result["audit"]["budget"]["rejected_candidates"] >= 1
    assert result["audit"]["budget"]["candidates_unattempted"] == 0


@pytest.mark.parametrize("coverage", ["empty", "absent"])
def test_negative_observation_stays_explicit_and_retrievable(coverage):
    payload = _payload(
        "logging" if coverage == "empty" else "tracing",
        [],
        coverage=coverage,
        fact_ledger={},
        counts={"matched": 0, "retrieved": 0, "normalized": 0, "returned": 0, "dropped": 0},
    )

    result = project_observability_payload(
        payload,
        tool="query_pod_logs" if coverage == "empty" else "query_pod_tracing",
        max_chars=1800,
        raw_ref=f"/archive/{coverage}.raw.txt",
    )
    summary = json.loads(result["summary"])

    assert summary["coverage"] == coverage
    assert summary["negative_observation"] == "query_completed_without_matching_evidence"
    assert summary["evidence"] == []
    assert summary["summary_selection"] == {
        "selected": 0,
        "omitted": 0,
        "strategy": "information_ranked_pattern_round_robin_budget_scan_no_fault_names",
    }
    assert summary["retrieval"]["raw_ref"] == f"/archive/{coverage}.raw.txt"
