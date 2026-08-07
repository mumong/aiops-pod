from app.core.workflow.group_evidence import aggregate_group_evidence


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
