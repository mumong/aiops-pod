import json

from app.core.workflow.fact_contract import _canonical_fact_id
from app.core.workflow.group_evidence import aggregate_group_evidence
import app.core.workflow.entity_evidence_snapshot as snapshot_module


def _obs_event(tool, dimension, coverage, *, namespace, pod, facts=None, purpose="query"):
    facts = facts or []
    records = []
    for fact in facts:
        records.append({
            "fact_id": fact["fact_id"],
            "entity_id": f"k8s.pod:{namespace}/{pod}:uid",
            "entity_kind": "Pod",
            "namespace": namespace,
            "entity_name": pod,
            "dimension": dimension,
            "fact_type": fact.get("fact_type", "measurement"),
            "attribute": fact.get("attribute", "value"),
            "value": fact["value"],
            "source_system": fact["source_system"],
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
            "evidence_refs": fact.get("evidence_refs", []),
        })
        for optional_key in ("name", "unit", "stats", "metadata"):
            if optional_key in fact:
                records[-1][optional_key] = fact[optional_key]
    return {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": tool,
        "tool_args": {"namespace": namespace, "pod": pod, "purpose": purpose},
        "structured": {
            "status": "query_succeeded",
            "dimension": dimension,
            "coverage": coverage,
            "source_system": {
                "metrics": "prometheus",
                "logging": "elasticsearch",
                "tracing": "deepflow+tempo",
            }.get(dimension, "kubernetes"),
            "entity": {
                "kind": "Pod", "namespace": namespace, "pod": pod,
                "pod_uid": "uid", "pod_ip": "172.16.1.9",
            },
            "purpose": purpose,
            "facts": [],
            "fact_ledger": {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": "query-test",
                "scope_entity_ids": [f"k8s.pod:{namespace}/{pod}:uid"],
                "records": records,
                "record_count": len(records),
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            },
        },
    }


def test_present_fact_is_not_overwritten_by_later_empty_query():
    entity = {"kind": "Pod", "namespace": "aiops-case-09", "name": "workload"}
    events = [
        _obs_event(
            "query_pod_logs", "logging", "present",
            namespace="aiops-case-09", pod="workload", purpose="broad UID query",
            facts=[{
                "fact_id": "fact-log-503",
                "source_system": "elasticsearch",
                "fact_type": "log",
                "attribute": "log.message",
                "value": "dependency unavailable http_status=503",
                "evidence_refs": ["log-ref-503"],
            }],
        ),
        _obs_event(
            "query_pod_logs", "logging", "empty",
            namespace="aiops-case-09", pod="workload", purpose="narrow level query",
        ),
    ]

    result = aggregate_group_evidence([entity], events)
    logging = result["aiops-case-09/workload"]["logging"]

    assert logging["status"] == "present"
    assert logging["query_count"] == 2
    assert logging["present_query_count"] == 1
    assert logging["empty_query_count"] == 1
    assert logging["facts"][0]["fact_id"] == "fact-log-503"
    assert "补充查询未命中" in " ".join(logging["limitations"])


def test_every_entity_has_four_dimensions_and_facts_do_not_cross_entities():
    entities = [
        {"kind": "Pod", "namespace": "aiops-case-06", "name": "crash"},
        {"kind": "Pod", "namespace": "aiops-case-10", "name": "probe"},
    ]
    events = [
        _obs_event(
            "query_pod_tracing", "tracing", "present",
            namespace="aiops-case-06", pod="crash",
            facts=[{
                "fact_id": "fact-c06-flow", "source_system": "deepflow",
                "fact_type": "flow", "attribute": "l7_flow",
                "value": {"request_type": "GET", "request_resource": "/work", "response_code": 500},
                "evidence_refs": ["trace-c06"],
            }],
        ),
        _obs_event(
            "query_pod_tracing", "tracing", "present",
            namespace="aiops-case-10", pod="probe",
            facts=[{
                "fact_id": "fact-c10-flow", "source_system": "deepflow",
                "fact_type": "flow", "attribute": "l7_flow",
                "value": {"request_type": "GET", "request_resource": "/health", "response_code": 500},
                "evidence_refs": ["trace-c10"],
            }],
        ),
    ]

    result = aggregate_group_evidence(entities, events)

    assert set(result["aiops-case-06/crash"]) >= {"kubernetes", "metrics", "logging", "tracing"}
    assert set(result["aiops-case-10/probe"]) >= {"kubernetes", "metrics", "logging", "tracing"}
    assert [f["fact_id"] for f in result["aiops-case-06/crash"]["tracing"]["facts"]] == ["fact-c06-flow"]
    assert [f["fact_id"] for f in result["aiops-case-10/probe"]["tracing"]["facts"]] == ["fact-c10-flow"]


def test_pending_entity_marks_application_telemetry_not_applicable():
    entity = {"kind": "Pod", "namespace": "aiops-case-01", "name": "pending"}
    events = [
        {
            "type": "tool_result", "status": "success", "semantic_success": True,
            "tool_name": "kubectl_events",
            "tool_args": {"namespace": "aiops-case-01", "resource_name": "pending"},
            "structured": {
                "status": "events_found",
                "selected_events": ["Warning FailedScheduling no nodes matched"],
            },
        },
        {
            **_obs_event(
                "query_pod_tracing", "tracing", "empty",
                namespace="aiops-case-01", pod="pending",
            ),
            "structured": {
                "status": "query_succeeded", "dimension": "tracing",
                "coverage": "empty", "source_system": "deepflow+tempo",
                "entity": {
                    "kind": "Pod", "namespace": "aiops-case-01",
                    "pod": "pending", "pod_ip": None,
                },
                "facts": [],
            },
        },
    ]

    result = aggregate_group_evidence([entity], events, status_keywords=["Pending"])
    dimensions = result["aiops-case-01/pending"]

    assert dimensions["kubernetes"]["status"] == "present"
    assert dimensions["logging"]["status"] == "not_applicable"
    assert dimensions["tracing"]["status"] == "not_applicable"
    assert dimensions["tracing"]["facts"] == []
    assert "容器未启动" in " ".join(dimensions["tracing"]["limitations"])


def test_dimension_states_distinguish_unselected_absent_and_unknown():
    entity = {"kind": "Pod", "namespace": "demo", "name": "workload"}
    no_query = aggregate_group_evidence([entity], [])
    assert no_query["demo/workload"]["metrics"]["status"] == "unselected"

    empty = aggregate_group_evidence([entity], [{
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "execute_pod_promql",
        "tool_args": {"namespace": "demo", "pod": "workload"},
        "structured": {
            "dimension": "metrics",
            "coverage": "empty",
            "entity": {"namespace": "demo", "pod": "workload"},
        },
    }])
    assert empty["demo/workload"]["metrics"]["status"] == "absent"

    partial = aggregate_group_evidence([entity], [{
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "query_pod_logs",
        "tool_args": {"namespace": "demo", "pod": "workload"},
        "structured": {
            "dimension": "logging",
            "coverage": "partial",
            "entity": {"namespace": "demo", "pod": "workload"},
        },
    }])
    assert partial["demo/workload"]["logging"]["status"] == "unknown"


def test_metric_fact_renders_name_unit_and_flat_trend():
    """Ledger-shaped record: metric name in `attribute`, trend in `metadata.stats`."""
    entity = {"kind": "Pod", "namespace": "aiops-case-09", "name": "workload"}
    events = [
        _obs_event(
            "execute_pod_promql", "metrics", "present",
            namespace="aiops-case-09", pod="workload",
            facts=[{
                "fact_id": "fact-metric-restarts",
                "source_system": "prometheus",
                "fact_type": "measurement",
                "attribute": "kube_pod_container_status_restarts_total",
                "value": "0",
                "unit": "count",
                "metadata": {"stats": {"first": 0.0, "min": 0.0, "max": 0.0, "last": 0.0}},
                "evidence_refs": ["metric-ref-restarts"],
            }],
        ),
    ]

    result = aggregate_group_evidence([entity], events)
    facts = result["aiops-case-09/workload"]["metrics"]["facts"]

    assert facts[0]["value"] == "0"
    assert facts[0]["display_value"] == "kube_pod_container_status_restarts_total=0 count（持平）"


def test_metric_fact_humanizes_bytes_and_shows_rising_trend():
    """facts-shaped record: metric name in `name`, trend in top-level `stats`."""
    entity = {"kind": "Pod", "namespace": "aiops-case-10", "name": "workload"}
    events = [
        _obs_event(
            "execute_pod_promql", "metrics", "present",
            namespace="aiops-case-10", pod="workload",
            facts=[{
                "fact_id": "fact-metric-memory",
                "source_system": "prometheus",
                "fact_type": "measurement",
                "name": "container_memory_working_set_bytes",
                "value": "15421440",
                "unit": "bytes",
                "stats": {"first": 10485760.0, "min": 10485760.0, "max": 15421440.0, "last": 15421440.0},
                "evidence_refs": ["metric-ref-memory"],
            }],
        ),
    ]

    result = aggregate_group_evidence([entity], events)
    rendered = result["aiops-case-10/workload"]["metrics"]["facts"][0]["display_value"]

    assert rendered.startswith("container_memory_working_set_bytes=15421440 bytes")
    assert "≈14.7 MiB" in rendered
    assert "上升 10485760 → 15421440" in rendered


def test_identical_metric_rows_from_repeat_queries_collapse():
    entity = {"kind": "Pod", "namespace": "aiops-case-10", "name": "workload"}
    metric_fact = {
        "source_system": "prometheus",
        "fact_type": "measurement",
        "attribute": "container_memory_working_set_bytes",
        "value": "15421440",
        "unit": "bytes",
        "metadata": {"stats": {"first": 15421440.0, "min": 15421440.0, "max": 15421440.0, "last": 15421440.0}},
    }
    events = [
        _obs_event(
            "execute_pod_promql", "metrics", "present",
            namespace="aiops-case-10", pod="workload",
            facts=[{**metric_fact, "fact_id": "fact-mem-a", "evidence_refs": ["ref-a"]}],
        ),
        _obs_event(
            "execute_pod_promql", "metrics", "present",
            namespace="aiops-case-10", pod="workload",
            facts=[{**metric_fact, "fact_id": "fact-mem-b", "evidence_refs": ["ref-b"]}],
        ),
    ]

    result = aggregate_group_evidence([entity], events)
    facts = result["aiops-case-10/workload"]["metrics"]["facts"]

    assert len(facts) == 1
    assert facts[0]["fact_id"] == "fact-mem-a"


def test_non_metric_fact_rendering_is_unchanged_by_metric_branch():
    """Logging record with generic `attribute` must not become 'log.message=...'."""
    entity = {"kind": "Pod", "namespace": "aiops-case-09", "name": "workload"}
    events = [
        _obs_event(
            "query_pod_logs", "logging", "present",
            namespace="aiops-case-09", pod="workload",
            facts=[{
                "fact_id": "fact-log-503",
                "source_system": "elasticsearch",
                "fact_type": "log",
                "attribute": "log.message",
                "value": "dependency unavailable http_status=503",
                "evidence_refs": ["log-ref-503"],
            }],
        ),
    ]

    result = aggregate_group_evidence([entity], events)
    rendered = result["aiops-case-09/workload"]["logging"]["facts"][0]["value"]

    assert rendered == "dependency unavailable http_status=503"


def test_event_target_accepts_pod_name_and_primary_entity_contracts():
    entity = {"kind": "Pod", "namespace": "aiops-case-09", "name": "workload"}
    by_tool_args = _obs_event(
        "query_pod_logs", "logging", "present",
        namespace="aiops-case-09", pod="workload",
        facts=[{
            "fact_id": "fact-pod-name", "source_system": "elasticsearch",
            "value": "dependency unavailable", "evidence_refs": ["log-ref"],
        }],
    )
    by_tool_args["tool_args"] = {
        "namespace": "aiops-case-09", "pod_name": "workload",
    }
    by_tool_args["structured"].pop("entity")

    by_primary_entity = _obs_event(
        "query_pod_tracing", "tracing", "present",
        namespace="aiops-case-09", pod="workload",
        facts=[{
            "fact_id": "fact-primary-entity", "source_system": "deepflow",
            "value": {"request_type": "GET", "request_resource": "/work", "response_code": 503},
            "evidence_refs": ["trace-ref"],
        }],
    )
    structured = by_primary_entity["structured"]
    structured["primary_entity"] = structured.pop("entity")
    by_primary_entity["tool_args"] = {}

    result = aggregate_group_evidence([entity], [by_tool_args, by_primary_entity])
    dimensions = result["aiops-case-09/workload"]

    assert dimensions["logging"]["facts"][0]["fact_id"] == "fact-pod-name"
    assert dimensions["tracing"]["facts"][0]["fact_id"] == "fact-primary-entity"


def test_kubernetes_fact_ledger_preserves_resource_limit_and_canonical_fields():
    entity = {"kind": "Pod", "namespace": "aiops-case-08", "name": "workload"}
    event = {
        "type": "tool_result",
        "status": "success",
        "semantic_success": True,
        "tool_name": "kubectl_describe",
        "tool_args": {
            "kind": "pod",
            "namespace": "aiops-case-08",
            "name": "workload",
        },
        "structured": {
            "dimension": "kubernetes",
            "status": "pod_described",
            "selected_events": ["Back-off restarting failed container"],
            "fact_ledger": {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": "kubernetes-lifecycle-test",
                "scope_entity_ids": ["k8s.pod:aiops-case-08/workload:uid"],
                "records": [{
                    "fact_id": "fact-resource-limit-memory",
                    "entity_id": "k8s.pod:aiops-case-08/workload:uid",
                    "entity_kind": "Pod",
                    "namespace": "aiops-case-08",
                    "entity_name": "workload",
                    "dimension": "kubernetes",
                    "fact_type": "configuration",
                    "attribute": "container.resource_limit.memory",
                    "value": {"container": "app", "value": "64Mi"},
                    "unit": "kubernetes_quantity",
                    "source_system": "kubernetes",
                    "directness": "direct",
                    "confidence": "high",
                    "strength": "strong",
                    "evidence_refs": ["structured://describe"],
                    "metadata": {"source_path": "spec.containers[0].resources.limits.memory"},
                    "schema_extension": {"type_url": "example.dev/k8s-resource/v1"},
                }],
                "record_count": 1,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            },
        },
    }

    result = aggregate_group_evidence([entity], [event])
    facts = result["aiops-case-08/workload"]["kubernetes"]["facts"]

    assert [fact["fact_id"] for fact in facts] == ["fact-resource-limit-memory"]
    assert facts[0]["attribute"] == "container.resource_limit.memory"
    assert facts[0]["value"] == {"container": "app", "value": "64Mi"}
    assert facts[0]["metadata"]["source_path"].endswith("limits.memory")
    assert facts[0]["schema_extension"]["type_url"] == "example.dev/k8s-resource/v1"
    assert facts[0]["display_value"].startswith("container.resource_limit.memory=")
    assert "64Mi" in facts[0]["display_value"]


def test_metric_projection_preserves_labels_timestamp_and_unknown_extensions():
    entity = {"kind": "Pod", "namespace": "aiops-case-08", "name": "workload"}
    event = _obs_event(
        "execute_pod_promql",
        "metrics",
        "present",
        namespace="aiops-case-08",
        pod="workload",
        facts=[{
            "fact_id": "fact-terminated-reason",
            "source_system": "prometheus",
            "fact_type": "measurement",
            "attribute": "kube_pod_container_status_last_terminated_reason",
            "value": "1",
            "unit": "unitless",
            "metadata": {
                "labels": {
                    "namespace": "aiops-case-08",
                    "pod": "workload",
                    "container": "app",
                    "reason": "OOMKilled",
                },
                "stats": {"first": 1.0, "min": 1.0, "max": 1.0, "last": 1.0},
            },
            "evidence_refs": ["metric://terminated-reason"],
        }],
    )
    record = event["structured"]["fact_ledger"]["records"][0]
    record["timestamp"] = "2026-08-14T08:00:00Z"
    record["schema_extension"] = {"type_url": "example.dev/prom-series/v2"}

    result = aggregate_group_evidence([entity], [event])
    fact = result["aiops-case-08/workload"]["metrics"]["facts"][0]

    assert fact["metadata"]["labels"]["reason"] == "OOMKilled"
    assert fact["timestamp"] == "2026-08-14T08:00:00Z"
    assert fact["schema_extension"]["type_url"] == "example.dev/prom-series/v2"
    assert "reason=OOMKilled" in fact["display_value"]


def test_zero_valued_categorical_metric_is_a_negative_observation():
    record = {
        "dimension": "metrics",
        "fact_type": "measurement",
        "attribute": "kube_pod_status_reason",
        "value": "0",
        "metadata": {
            "labels": {
                "namespace": "demo",
                "pod": "workload",
                "reason": "NodeLost",
            },
        },
        "directness": "direct",
        "confidence": "high",
    }

    assert snapshot_module.classify_fact_evidence_role(record) == (
        "negative_observation"
    )


def test_explicit_context_role_is_not_overridden_by_generic_event_heuristic():
    record = {
        "dimension": "kubernetes",
        "fact_type": "event",
        "attribute": "event.message",
        "value": {
            "type": "Warning",
            "reason": "Failed",
            "message": "source reported a failure",
        },
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "metadata": {"evidence_role": "context"},
    }

    assert snapshot_module.classify_fact_evidence_role(record) == "context"


def test_direct_strong_warning_event_without_explicit_role_is_causal_candidate():
    record = {
        "dimension": "kubernetes",
        "fact_type": "event",
        "attribute": "event.message",
        "value": {
            "type": "Warning",
            "reason": "Failed",
            "message": "source reported a failure",
        },
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "metadata": {},
    }

    assert snapshot_module.classify_fact_evidence_role(record) == (
        "causal_candidate"
    )


def test_top_level_explicit_role_survives_reclassification():
    record = {
        "dimension": "kubernetes",
        "fact_type": "configuration",
        "attribute": "container.resources.limits.memory",
        "value": "64Mi",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_role": "context",
        "metadata": {"evidence_role": "causal_candidate"},
    }

    assert snapshot_module.classify_fact_evidence_role(record) == "context"


def test_snapshot_manifest_retains_causal_and_direct_dimension_facts():
    entity_id = "k8s.pod:demo/workload:uid-workload"
    records = []
    fact_specs = [
        (
            "kubernetes",
            "event",
            "event.message",
            {"type": "Warning", "reason": "Failed", "message": "failure"},
        ),
        ("metrics", "measurement", "resource.value", 91),
        ("logging", "log", "log.message", "runtime failure"),
        (
            "tracing",
            "span",
            "application_span",
            {"status_code": "ERROR", "http_status": 500},
        ),
    ]
    for dimension, fact_type, attribute, value in fact_specs:
        record = {
            "entity_id": entity_id,
            "entity_kind": "Pod",
            "namespace": "demo",
            "entity_name": "workload",
            "dimension": dimension,
            "fact_type": fact_type,
            "attribute": attribute,
            "value": value,
            "source_system": dimension,
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
            "evidence_refs": [f"archive://{dimension}"],
        }
        record["fact_id"] = _canonical_fact_id(record)
        records.append(record)
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "generic-four-dimension-ledger",
        "scope_entity_ids": [entity_id],
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }

    snapshot = snapshot_module.build_entity_evidence_snapshot(
        entities=[{"kind": "Pod", "namespace": "demo", "name": "workload"}],
        evidence_analysis=json.dumps({"tool_data": [{"fact_ledger": ledger}]}),
        thinking_events=[],
    )
    manifest = snapshot.to_handoff()["selection_manifest"]

    assert set(manifest["eligible_support_fact_ids"]) <= set(
        manifest["rca_input_fact_ids"]
    )
    assert set(manifest["required_context_fact_ids"]) <= set(
        manifest["rca_input_fact_ids"]
    )
    assert set(manifest["rca_input_fact_ids"]).isdisjoint(
        manifest["omitted_fact_ids"]
    )
    selected_dimensions = {
        snapshot.fact_index[fact_id]["dimension"]
        for fact_id in manifest["rca_input_fact_ids"]
    }
    assert selected_dimensions == {"kubernetes", "metrics", "logging", "tracing"}


def test_authoritative_snapshot_preserves_valid_unknown_record_extensions():
    entity_id = "k8s.pod:demo/workload:uid-workload"
    record = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "workload",
        "dimension": "metrics",
        "fact_type": "measurement",
        "attribute": "container_memory_working_set_bytes",
        "value": "67108864",
        "unit": "bytes",
        "source_system": "prometheus",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["prometheus://query/memory"],
    }
    record["fact_id"] = _canonical_fact_id(record)
    record["schema_extension"] = {
        "type_url": "example.dev/prom-series/v2",
        "identity_fields": ["namespace", "pod", "container", "uid"],
    }
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "future-compatible-ledger",
        "scope_entity_ids": [entity_id],
        "records": [record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }

    snapshot = snapshot_module.build_entity_evidence_snapshot(
        entities=[{"kind": "Pod", "namespace": "demo", "name": "workload"}],
        evidence_analysis=json.dumps({
            "tool_data": [{
                "tool": "execute_pod_promql",
                "status": "success",
                "fact_ledger": ledger,
            }],
        }),
        thinking_events=[],
    )
    fact = snapshot.dimension_evidence_by_entity[
        "demo/workload"
    ]["metrics"]["facts"][0]

    assert fact["schema_extension"]["type_url"] == (
        "example.dev/prom-series/v2"
    )
    assert fact["schema_extension"]["identity_fields"][-1] == "uid"
