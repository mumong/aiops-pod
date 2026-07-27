import hashlib
import json
import re
from pathlib import Path

import pytest

import app.core.workflow.fact_contract as fact_contract_module
from app.core.prompts import ROOT_CAUSE_ANALYZER_PROMPT
from app.core.workflow.fact_contract import (
    build_kubernetes_lifecycle_fact_ledger,
    build_observability_query_fact_ledger,
    bounded_json_dumps,
    compact_fact_ledgers_json,
    extract_fact_ledgers_from_tool_data,
    normalize_case_fact_ledger,
    normalize_fact_ledger,
    project_final_observability_events,
    select_tool_data_for_rca,
    validate_rca_claims,
)
from app.core.workflow.schemas import FactLedger


MIN_FACT_LEDGER_JSON_CHARS = len('{"fact_ledgers":[]}')
_OPTIONAL_FACT_FIELDS = {
    "namespace",
    "entity_name",
    "strength",
    "unit",
    "timestamp",
    "start",
    "end",
    "metadata",
}
_ROLE_KEY_VARIANTS = [
    "causalRole",
    "causalRoleState",
    "prefixCausalRoleSuffix",
    "PREFIX.CAUSAL/ROLE-SUFFIX",
    "diagnosticRole",
    "diagnosticRoleState",
    "prefixDiagnosticRoleSuffix",
    "PREFIX.DIAGNOSTIC/ROLE-SUFFIX",
]


def _canonical_fact_id(record: dict) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key != "fact_id"
        and (key not in _OPTIONAL_FACT_FIELDS or value not in (None, {}, []))
    }
    payload["evidence_refs"] = sorted({
        str(ref)
        for ref in payload.get("evidence_refs", [])
        if str(ref or "").strip()
    })
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "fact-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def _with_canonical_fact_id(record: dict) -> dict:
    payload = dict(record)
    payload["fact_id"] = _canonical_fact_id(payload)
    return payload


def _fact(
    marker: str,
    entity_id: str,
    *,
    dimension: str = "logging",
    fact_type: str = "log",
    directness: str = "direct",
    confidence: str = "high",
    strength: str = "strong",
    value=None,
):
    return _with_canonical_fact_id({
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": entity_id.rsplit("/", 1)[-1].split(":", 1)[0],
        "dimension": dimension,
        "fact_type": fact_type,
        "attribute": f"{dimension}.observed",
        "value": value if value is not None else {"message": marker},
        "source_system": "test-source",
        "directness": directness,
        "confidence": confidence,
        "strength": strength,
        "evidence_refs": [f"ref:{marker}"],
    })


def _ledger(
    case_id: str,
    entity_id: str,
    records: list[dict],
    *,
    source: str = "mcp_canonical",
    legacy_contract: bool = False,
):
    return {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": case_id,
        "scope_entity_ids": [entity_id],
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": source,
        "legacy_contract": legacy_contract,
    }


def _diagnosed_claim(
    hypotheses: list[dict],
    supporting_fact_ids: list[str],
):
    return {
        "diagnostic_status": "diagnosed",
        "phenomenon": "Two scoped entities are abnormal",
        "root_cause": "Evidence-backed candidate",
        "root_cause_summary": "Evidence-backed candidate",
        "supporting_fact_ids": supporting_fact_ids,
        "contradicting_fact_ids": [],
        "unknowns": [],
        "hypotheses": hypotheses,
        "confidence": 0.86,
        "confidence_reason": "Current-scope direct facts support each hypothesis",
    }


def test_normalize_case_fact_ledger_accepts_canonical_and_rejects_evaluator_records():
    entity_id = "k8s.pod:demo/api:uid-a"
    valid_record = _fact("valid", entity_id)
    payload = _ledger(
        "case-a",
        entity_id,
        [
            valid_record,
            {
                **_fact("root-cause", entity_id),
                "metadata": {"root_cause": "must not reach the agent"},
            },
            {
                **_fact("label", entity_id),
                "metadata": {"label": "evaluator-only"},
            },
        ],
    )

    ledger = normalize_case_fact_ledger({"fact_ledger": payload})

    assert isinstance(ledger, FactLedger)
    assert ledger.source == "mcp_canonical"
    assert ledger.legacy_contract is False
    assert [record.fact_id for record in ledger.records] == [valid_record["fact_id"]]
    assert ledger.record_count == 1
    assert "root_cause" not in ledger.model_dump_json()


def test_normalize_case_fact_ledger_builds_source_only_legacy_records():
    structured = {
        "case_id": "case-legacy",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-a",
        },
        "coverage": {
            "metrics": "present",
            "logs": "present",
            "tracing": "present",
            "topology": "present",
        },
        "dimension_details": {
            "metrics": {
                "highlights": [
                    {
                        "metric": "request_latency_seconds",
                        "max": 1.25,
                        "unit": "s",
                        "evidence_ref": "metrics:latency",
                    }
                ]
            },
            "logs": {
                "samples": [
                    {
                        "timestamp": "2026-07-16T01:00:00Z",
                        "message": "request failed with status 503",
                        "evidence_ref": "logs:target",
                    }
                ]
            },
            "tracing": {
                "flows": [
                    {
                        "src": "10.0.0.1",
                        "dst": "10.0.0.2",
                        "response_code": 503,
                        "evidence_ref": "flows:request",
                    }
                ],
                "spans": [
                    {
                        "trace_id": "trace-a",
                        "name": "GET /resource",
                        "evidence_ref": "traces:span",
                    }
                ],
            },
            "topology": {
                "edges": [
                    {
                        "relationship": "Service --selects--> Pod",
                        "source": "api",
                        "target": "api",
                        "directness": "direct",
                        "confidence": "high",
                        "evidence_refs": ["topology:service-pod"],
                    }
                ]
            },
        },
        "root_cause": "legacy evaluator value",
    }

    ledger = normalize_case_fact_ledger(structured)

    assert ledger is not None
    assert ledger.source == "robusta_legacy_adapter"
    assert ledger.legacy_contract is True
    assert ledger.scope_entity_ids == ["k8s.pod:demo/api:uid-a"]
    assert {"metrics", "logging", "tracing", "topology"} <= {
        record.dimension for record in ledger.records
    }
    assert all(record.evidence_refs for record in ledger.records if record.fact_type != "coverage")
    assert "legacy evaluator value" not in ledger.model_dump_json()


def test_extract_fact_ledgers_preserves_legacy_contract_marker():
    ledger = normalize_case_fact_ledger({
        "case_id": "case-legacy",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-a",
        },
        "coverage": {"logs": "present"},
    })

    extracted = extract_fact_ledgers_from_tool_data([
        {
            "tool": "collect_aiops_case",
            "fact_ledger": ledger.model_dump(mode="json"),
        }
    ])

    assert extracted[0].source == "robusta_legacy_adapter"
    assert extracted[0].legacy_contract is True


def test_normalize_and_compact_preserve_every_scope_entity_identity():
    scope_entity_ids = [
        f"k8s.pod:demo/api-{index:03d}:uid-{index:03d}"
        for index in range(65)
    ]
    payload = _ledger(
        "case-many-entities",
        scope_entity_ids[0],
        [],
    )
    payload["scope_entity_ids"] = scope_entity_ids

    ledger = normalize_fact_ledger(payload)

    assert ledger is not None
    assert ledger.scope_entity_ids == scope_entity_ids
    assert ledger.truncated is False

    compacted = json.loads(
        compact_fact_ledgers_json([ledger], max_chars=12000)
    )
    assert compacted["fact_ledgers"][0]["scope_entity_ids"] == scope_entity_ids

    with pytest.raises(ValueError, match="identity index"):
        compact_fact_ledgers_json([ledger], max_chars=500)


def test_compact_fact_ledgers_json_is_stable_valid_and_bounded():
    ledgers = []
    for case_index in range(2):
        entity_id = f"k8s.pod:demo/api-{case_index}:uid-{case_index}"
        records = [
            _fact(
                f"fact-{case_index:02x}{record_index:010x}",
                entity_id,
                value={"message": f"record-{record_index}-" + ("x" * 180)},
            )
            for record_index in range(30)
        ]
        ledgers.append(FactLedger.model_validate(_ledger(f"case-{case_index}", entity_id, records)))

    first = compact_fact_ledgers_json(ledgers, max_chars=1600)
    second = compact_fact_ledgers_json(ledgers, max_chars=1600)
    parsed = json.loads(first)

    assert first == second
    assert len(first) <= 1600
    assert [item["case_id"] for item in parsed["fact_ledgers"]] == ["case-0", "case-1"]
    assert all(item["truncated"] is True for item in parsed["fact_ledgers"])
    assert all(item["record_count"] == len(item["records"]) for item in parsed["fact_ledgers"])


def test_compact_fact_ledgers_json_skips_oversized_record_and_keeps_later_fact():
    entity_id = "k8s.pod:demo/api:uid-a"
    oversized = _fact(
        "oversized",
        entity_id,
        value={"message": "x" * 5000},
    )
    small = _fact(
        "small",
        entity_id,
        value={"message": "small fact"},
    )
    ledger = FactLedger.model_validate(
        _ledger(
            "case-a",
            entity_id,
            [oversized, small],
        )
    )

    compacted = json.loads(
        compact_fact_ledgers_json([ledger], max_chars=900)
    )

    assert [
        record["fact_id"]
        for record in compacted["fact_ledgers"][0]["records"]
    ] == [small["fact_id"]]


def test_compact_fact_ledgers_revalidates_fact_ids_on_factledger_objects():
    entity_id = "k8s.pod:demo/api:uid-a"
    invalid_record = _fact("invalid-object-id", entity_id)
    invalid_record["fact_id"] = "fact-ffffffffffff"
    ledger = FactLedger.model_validate(
        _ledger(
            "case-object-revalidation",
            entity_id,
            [invalid_record],
        )
    )

    compacted = json.loads(
        compact_fact_ledgers_json([ledger], max_chars=4000)
    )

    assert compacted["fact_ledgers"][0]["case_id"] == (
        "case-object-revalidation"
    )
    assert compacted["fact_ledgers"][0]["scope_entity_ids"] == [entity_id]
    assert compacted["fact_ledgers"][0]["records"] == []
    assert "fact-ffffffffffff" not in json.dumps(compacted)


def test_compact_fact_ledgers_prioritizes_direct_diagnostic_fact_over_coverage():
    entity_id = "k8s.pod:demo/api:uid-a"
    coverage_records = [
        _fact(
            f"coverage-{index}",
            entity_id,
            dimension="coverage",
            fact_type="coverage",
            value={"coverage": "present", "noise": "x" * 160},
            directness="related_context",
            confidence="medium",
        )
        for index in range(8)
    ]
    decisive = _fact(
        "decisive-config-log",
        entity_id,
        value={"message": "required config PAYMENT_GATEWAY_TOKEN is missing"},
    )
    ledger = FactLedger.model_validate(
        _ledger("case-priority", entity_id, [*coverage_records, decisive])
    )

    compacted = json.loads(
        compact_fact_ledgers_json([ledger], max_chars=950)
    )
    selected_ids = {
        record["fact_id"]
        for record in compacted["fact_ledgers"][0]["records"]
    }

    assert decisive["fact_id"] in selected_ids


def test_compact_fact_ledgers_prioritizes_direct_fact_globally_across_cases():
    coverage_ledgers = []
    expected_identities = []
    for index in range(12):
        entity_id = f"k8s.pod:demo/api-{index}:uid-{index}"
        coverage = _fact(
            f"coverage-{index}",
            entity_id,
            dimension="coverage",
            fact_type="coverage",
            value={"coverage": "present", "noise": "x" * 900},
            directness="related_context",
            confidence="medium",
        )
        case_id = f"case-coverage-{index}"
        coverage_ledgers.append(
            FactLedger.model_validate(
                _ledger(case_id, entity_id, [coverage])
            )
        )
        expected_identities.append((case_id, entity_id))

    direct_entity_id = "k8s.pod:demo/decisive:uid-direct"
    direct = _fact(
        "direct-config-error",
        direct_entity_id,
        value={"message": "required configuration is missing"},
    )
    direct_case_id = "case-direct"
    ledgers = [
        *coverage_ledgers,
        FactLedger.model_validate(
            _ledger(direct_case_id, direct_entity_id, [direct])
        ),
    ]
    expected_identities.append((direct_case_id, direct_entity_id))

    compacted = json.loads(
        compact_fact_ledgers_json(ledgers, max_chars=4500)
    )

    selected_ids = {
        record["fact_id"]
        for ledger in compacted["fact_ledgers"]
        for record in ledger["records"]
    }
    actual_identities = [
        (ledger["case_id"], ledger["scope_entity_ids"][0])
        for ledger in compacted["fact_ledgers"]
    ]

    assert direct["fact_id"] in selected_ids
    assert actual_identities == expected_identities


def test_compact_fact_ledgers_prefers_canonical_source_over_legacy_peer():
    legacy_entity = "k8s.pod:demo/a-legacy:uid-legacy"
    canonical_entity = "k8s.pod:demo/z-canonical:uid-canonical"
    legacy_fact = _fact(
        "legacy-direct",
        legacy_entity,
        value={"message": "legacy " + ("x" * 500)},
    )
    canonical_fact = _fact(
        "canonical-direct",
        canonical_entity,
        value={"message": "canonical " + ("x" * 500)},
    )
    legacy_ledger = FactLedger.model_validate(
        _ledger(
            "case-legacy-priority",
            legacy_entity,
            [legacy_fact],
            source="robusta_legacy_adapter",
            legacy_contract=True,
        )
    )
    canonical_ledger = FactLedger.model_validate(
        _ledger(
            "case-canonical-priority",
            canonical_entity,
            [canonical_fact],
        )
    )

    compacted = json.loads(
        compact_fact_ledgers_json(
            [legacy_ledger, canonical_ledger],
            max_chars=1500,
        )
    )
    selected_ids = {
        record["fact_id"]
        for ledger in compacted["fact_ledgers"]
        for record in ledger["records"]
    }

    assert canonical_fact["fact_id"] in selected_ids
    assert legacy_fact["fact_id"] not in selected_ids
    assert [
        (ledger["case_id"], ledger["scope_entity_ids"])
        for ledger in compacted["fact_ledgers"]
    ] == [
        ("case-legacy-priority", [legacy_entity]),
        ("case-canonical-priority", [canonical_entity]),
    ]


def test_select_tool_data_for_rca_keeps_every_case_before_supplementary_limit():
    case_items = [
        {
            "tool": "collect_aiops_case",
            "data": f"case summary {index}",
            "fact_ledger": _ledger(
                f"case-{index}",
                f"k8s.pod:demo/api-{index}:uid-{index}",
                [],
            ),
        }
        for index in range(12)
    ]
    supplementary = [
        {"tool": "kubectl_describe", "data": f"supplementary {index}"}
        for index in range(20)
    ]

    selected = select_tool_data_for_rca(
        supplementary + case_items,
        supplementary_limit=3,
    )

    assert [item["fact_ledger"]["case_id"] for item in selected[:12]] == [
        f"case-{index}" for index in range(12)
    ]
    assert [item["data"] for item in selected[12:]] == [
        "supplementary 0",
        "supplementary 1",
        "supplementary 2",
    ]


def test_rca_ledger_selection_excludes_only_marked_replay():
    entity_id = "k8s.pod:demo/api:uid-a"
    first_record = _fact("first", entity_id)
    second_record = _fact("second", entity_id)
    first = {
        "tool": "collect_aiops_case",
        "data": "first",
        "fact_ledger": _ledger(
            "case-a",
            entity_id,
            [first_record],
        ),
    }
    second = {
        "tool": "get_aiops_case",
        "data": "second",
        "fact_ledger": _ledger(
            "case-a",
            entity_id,
            [second_record],
        ),
    }
    replay = {
        **first,
        "data": "replay",
        "deduplicated": True,
    }

    selected = select_tool_data_for_rca([replay, first, second])
    ledgers = extract_fact_ledgers_from_tool_data([replay, first, second])

    assert [item["data"] for item in selected] == ["first", "second"]
    assert [
        ledger.records[0].fact_id for ledger in ledgers
    ] == [first_record["fact_id"], second_record["fact_id"]]


def test_agent_context_nested_fact_ledgers_preserves_every_valid_ledger():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    ledger_a = _ledger(
        "case-nested-a",
        entity_a,
        [_fact("nested-a", entity_a)],
    )
    ledger_b = _ledger(
        "case-nested-b",
        entity_b,
        [_fact("nested-b", entity_b)],
    )
    tool_data = [{
        "tool": "collect_aiops_case",
        "agent_context": json.dumps({
            "fact_ledgers": [ledger_a, ledger_b],
        }),
    }]

    selected = select_tool_data_for_rca(tool_data)
    extracted = extract_fact_ledgers_from_tool_data(tool_data)

    assert [
        item["fact_ledger"]["case_id"]
        for item in selected
    ] == ["case-nested-a", "case-nested-b"]
    assert [ledger.case_id for ledger in extracted] == [
        "case-nested-a",
        "case-nested-b",
    ]


def test_generic_observability_query_context_is_adapted_to_fact_ledger():
    tool_data = [{
        "tool": "query_pod_logs",
        "agent_context": json.dumps({
            "status": "query_succeeded",
            "source_system": "elasticsearch",
            "dimension": "logging",
            "entity": {
                "kind": "Pod",
                "namespace": "demo",
                "pod": "api",
                "pod_uid": "uid-a",
            },
            "coverage": "present",
            "directness": "direct",
            "facts": [{
                "ref": "log-config",
                "source_system": "elasticsearch",
                "dimension": "logging",
                "observed_at": "2026-07-23T08:45:57Z",
                "name": "log.message",
                "value": (
                    "required config PAYMENT_GATEWAY_TOKEN is missing; "
                    "error_code=CONFIG_MISSING"
                ),
                "directness": "direct",
            }],
            "evidence_refs": ["log-config"],
        }, ensure_ascii=False),
    }]

    selected = select_tool_data_for_rca(tool_data)
    extracted = extract_fact_ledgers_from_tool_data(tool_data)

    assert len(selected) == 1
    assert selected[0]["fact_ledger"]["scope_entity_ids"] == [
        "k8s.pod:demo/api:uid-a"
    ]
    assert len(extracted) == 1
    assert extracted[0].source == "robusta_legacy_adapter"
    assert extracted[0].legacy_contract is True
    assert extracted[0].records[0].dimension == "logging"
    assert extracted[0].records[0].fact_type == "log"
    assert extracted[0].records[0].attribute == "log.message"
    assert (
        "required config PAYMENT_GATEWAY_TOKEN is missing"
        in str(extracted[0].records[0].value)
    )
    assert extracted[0].records[0].evidence_refs == ["log-config"]


def test_validate_rca_claims_accepts_one_supported_hypothesis_per_entity():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    fact_a = _fact("entity-a", entity_a)
    fact_b = _fact("entity-b", entity_b)
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-a", entity_a, [fact_a])
        ),
        FactLedger.model_validate(
            _ledger("case-b", entity_b, [fact_b])
        ),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_a,
                "summary": "Candidate for entity A",
                "supporting_fact_ids": [fact_a["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            },
            {
                "hypothesis_id": "hyp-b",
                "entity_id": entity_b,
                "summary": "Candidate for entity B",
                "supporting_fact_ids": [fact_b["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.84,
            },
        ],
        [fact_a["fact_id"], fact_b["fact_id"]],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "diagnosed"
    assert result["claim_validation"]["valid"] is True
    assert result["claim_validation"]["invalid_fact_ids"] == []
    assert {item["entity_id"] for item in result["hypotheses"]} == {entity_a, entity_b}


def test_a024_validate_rca_claims_reconciles_entity_logging_limitations():
    entity_with_logs = "k8s.pod:demo/orders-api-abc123def0-x1y2z:uid-a"
    entity_without_logs = "k8s.pod:demo/worker-api-abc123def0-z9y8x:uid-b"
    log_fact = _fact(
        "allocated memory",
        entity_with_logs,
        value={"message": "allocated memory", "allocated_mib": 62},
    )
    lifecycle_fact = _fact(
        "recent restart",
        entity_without_logs,
        dimension="kubernetes",
        fact_type="state",
        value={"status": "Running", "restart_count": 4},
    )
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-with-logs", entity_with_logs, [log_fact])
        ),
        FactLedger.model_validate(
            _ledger(
                "case-without-logs",
                entity_without_logs,
                [lifecycle_fact],
            )
        ),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-with-logs",
                "entity_id": entity_with_logs,
                "summary": "Memory allocation candidate",
                "supporting_fact_ids": [log_fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [
                    "orders-api 没有当前日志 Fact；"
                    "缺少 resource limits 和连续内存时序。"
                ],
                "confidence": 0.88,
            },
            {
                "hypothesis_id": "hyp-without-logs",
                "entity_id": entity_without_logs,
                "summary": "Restart candidate",
                "supporting_fact_ids": [lifecycle_fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": ["worker-api 没有日志，无法引用日志原文。"],
                "confidence": 0.82,
            },
        ],
        [log_fact["fact_id"], lifecycle_fact["fact_id"]],
    )
    claim.update({
        "evidence_analysis": [
            {
                "evidence_id": log_fact["fact_id"],
                "raw_data": "allocated_mib=62",
                "interpretation": (
                    "这是 orders-api 同一 Pod 的直接日志，"
                    "明确给出 allocated_mib=62。"
                    "该 Pod 没有可用日志 Fact，无法引用日志原文。"
                ),
            },
            {
                "evidence_id": lifecycle_fact["fact_id"],
                "raw_data": "restart_count=4",
                "interpretation": (
                    "worker-api 没有可用日志 Fact，"
                    "仍需补采应用日志。"
                ),
            },
        ],
        "unknowns": [
            "orders-api 没有当前日志 Fact；"
            "不能为该 Pod 提供日志 message 原文。",
            "orders-api 未提供应用日志或 OOM 时间点；"
            "worker-api 没有当前日志 Fact；"
            "节点压力未知。"
        ],
        "limitations": (
            "orders-api 缺少日志、资源规格及连续内存时序；"
            "worker-api 缺少日志；"
            "敏感配置来源未采集。"
        ),
    })

    result = validate_rca_claims(claim, ledgers)
    serialized = json.dumps(result, ensure_ascii=False)

    assert "orders-api 没有当前日志 Fact" not in serialized
    assert "orders-api 未提供应用日志" not in serialized
    assert "不能为该 Pod 提供日志 message 原文" not in serialized
    assert "该 Pod 没有。" not in serialized
    assert "该 Pod 没有可用日志 Fact" not in result["evidence_analysis"][0][
        "interpretation"
    ]
    assert "同一 Pod 的直接日志，明确给出 allocated_mib=62" in result[
        "evidence_analysis"
    ][0]["interpretation"]
    assert "worker-api 没有当前日志 Fact" in serialized
    assert "worker-api 缺少日志" in serialized
    assert "worker-api 没有可用日志 Fact" in serialized
    assert "resource limits" in serialized
    assert "连续内存时序" in serialized
    assert "OOM 时间点" in serialized
    assert "节点压力未知" in serialized
    assert "敏感配置来源未采集" in serialized


def test_a026_mixed_entity_generic_log_denial_keeps_only_unlogged_entity():
    entity_with_logs = "k8s.pod:demo/orders-api-abc123def0-x1y2z:uid-a"
    entity_without_logs = "k8s.pod:demo/worker-api-abc123def0-z9y8x:uid-b"
    log_fact = _fact(
        "allocated memory",
        entity_with_logs,
        value={"message": "allocated memory", "allocated_mib": 62},
    )
    lifecycle_fact = _fact(
        "recent restart",
        entity_without_logs,
        dimension="kubernetes",
        fact_type="state",
        value={"status": "Running", "restart_count": 4},
    )
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-with-logs", entity_with_logs, [log_fact])
        ),
        FactLedger.model_validate(
            _ledger(
                "case-without-logs",
                entity_without_logs,
                [lifecycle_fact],
            )
        ),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-with-logs",
                "entity_id": entity_with_logs,
                "summary": "Memory allocation candidate",
                "supporting_fact_ids": [log_fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            },
            {
                "hypothesis_id": "hyp-without-logs",
                "entity_id": entity_without_logs,
                "summary": "Restart candidate",
                "supporting_fact_ids": [lifecycle_fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.82,
            },
        ],
        [log_fact["fact_id"], lifecycle_fact["fact_id"]],
    )
    claim["limitations"] = (
        "orders-api 和 worker-api 都缺少日志；节点压力未知。"
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["limitations"] == "worker-api 缺少日志；节点压力未知。"


def test_a026_specific_log_window_and_field_gaps_remain_verbatim():
    entity_with_logs = "k8s.pod:demo/orders-api-abc123def0-x1y2z:uid-a"
    log_fact = _fact(
        "allocated memory",
        entity_with_logs,
        value={"message": "allocated memory", "allocated_mib": 62},
    )
    ledger = FactLedger.model_validate(
        _ledger("case-with-logs", entity_with_logs, [log_fact])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-with-logs",
                "entity_id": entity_with_logs,
                "summary": "Memory allocation candidate",
                "supporting_fact_ids": [log_fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        [log_fact["fact_id"]],
    )
    limitations = (
        "orders-api 缺少 OOM 前日志，不能确定终止前最后一次分配；"
        "orders-api 缺少日志中的时间戳；"
        "orders-api 日志缺少字段 request_id；"
        "orders-api 缺少最近一次退出前日志窗口。"
    )
    claim["limitations"] = limitations

    result = validate_rca_claims(claim, [ledger])

    assert result["limitations"] == limitations


def _a027_logging_gap_claim(*, include_unlogged_entity: bool = False):
    entity_with_logs = "k8s.pod:demo/orders-api-abc123def0-x1y2z:uid-a"
    log_fact = _fact(
        "allocated memory",
        entity_with_logs,
        value={"message": "allocated memory", "allocated_mib": 62},
    )
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-with-logs", entity_with_logs, [log_fact])
        )
    ]
    hypotheses = [
        {
            "hypothesis_id": "hyp-with-logs",
            "entity_id": entity_with_logs,
            "summary": "Memory allocation candidate",
            "supporting_fact_ids": [log_fact["fact_id"]],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "confidence": 0.88,
        }
    ]
    supporting_fact_ids = [log_fact["fact_id"]]

    if include_unlogged_entity:
        entity_without_logs = (
            "k8s.pod:demo/worker-api-abc123def0-z9y8x:uid-b"
        )
        lifecycle_fact = _fact(
            "recent restart",
            entity_without_logs,
            dimension="kubernetes",
            fact_type="state",
            value={"status": "Running", "restart_count": 4},
        )
        ledgers.append(
            FactLedger.model_validate(
                _ledger(
                    "case-without-logs",
                    entity_without_logs,
                    [lifecycle_fact],
                )
            )
        )
        hypotheses.append({
            "hypothesis_id": "hyp-without-logs",
            "entity_id": entity_without_logs,
            "summary": "Restart candidate",
            "supporting_fact_ids": [lifecycle_fact["fact_id"]],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "confidence": 0.82,
        })
        supporting_fact_ids.append(lifecycle_fact["fact_id"])

    return (
        _diagnosed_claim(hypotheses, supporting_fact_ids),
        ledgers,
    )


def test_a027_same_clause_generic_denial_keeps_timestamp_gap():
    claim, ledgers = _a027_logging_gap_claim()
    claim["limitations"] = "orders-api 缺少日志和日志中的时间戳。"

    result = validate_rca_claims(claim, ledgers)

    assert result["limitations"] == "orders-api 缺少日志中的时间戳。"


def test_a027_same_clause_generic_denial_keeps_field_gap():
    claim, ledgers = _a027_logging_gap_claim()
    claim["limitations"] = (
        "orders-api 没有日志，且日志缺少字段 request_id。"
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["limitations"] == "orders-api 日志缺少字段 request_id。"


def test_a027_log_before_marker_mixed_denial_keeps_unlogged_entity():
    claim, ledgers = _a027_logging_gap_claim(include_unlogged_entity=True)
    claim["limitations"] = "orders-api 和 worker-api 的日志均不可用。"

    result = validate_rca_claims(claim, ledgers)

    assert result["limitations"] == "worker-api 的日志不可用。"


def test_validate_rca_claims_downgrades_unknown_fact_reference():
    entity_id = "k8s.pod:demo/api:uid-a"
    valid_record = _fact("valid", entity_id)
    ledger = FactLedger.model_validate(
        _ledger("case-a", entity_id, [valid_record])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_id,
                "summary": "Unsupported candidate",
                "supporting_fact_ids": ["fact-ffffffffffff"],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        ["fact-ffffffffffff"],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "inconclusive"
    assert result["supporting_fact_ids"] == []
    assert result["claim_validation"]["invalid_fact_ids"] == ["fact-ffffffffffff"]
    assert result["confidence"] < 0.5


def test_validate_rca_claims_downgrades_cross_entity_reference():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    fact_a = _fact("entity-a", entity_a)
    fact_b = _fact("entity-b", entity_b)
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-a", entity_a, [fact_a])
        ),
        FactLedger.model_validate(
            _ledger("case-b", entity_b, [fact_b])
        ),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_a,
                "summary": "Cross-entity candidate",
                "supporting_fact_ids": [fact_b["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            },
            {
                "hypothesis_id": "hyp-b",
                "entity_id": entity_b,
                "summary": "Entity B candidate",
                "supporting_fact_ids": [fact_b["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            },
        ],
        [fact_b["fact_id"]],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "inconclusive"
    assert fact_b["fact_id"] in result["claim_validation"]["invalid_fact_ids"]
    assert any("cross-entity" in reason for reason in result["claim_validation"]["reasons"])


def test_validate_rca_claims_accepts_explicit_direct_topology_link_to_scope():
    entity_id = "k8s.pod:demo/api:uid-a"
    service_id = "k8s.service:demo/api"
    topology_record = _fact(
            "service-selects-pod",
            service_id,
            dimension="topology",
            fact_type="relationship",
            directness="direct",
            confidence="high",
            value={
                "source_entity_id": service_id,
                "target_entity_id": entity_id,
                "relationship": "selects",
            },
        )
    topology_record.update({
        "entity_kind": "Service",
        "entity_name": "api",
    })
    topology_record["fact_id"] = _canonical_fact_id(topology_record)
    ledger = FactLedger.model_validate(
        _ledger("case-a", entity_id, [topology_record])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_id,
                "summary": "Scoped relationship candidate",
                "supporting_fact_ids": [topology_record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        [topology_record["fact_id"]],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "diagnosed"
    assert result["supporting_fact_ids"] == [topology_record["fact_id"]]
    assert result["claim_validation"]["valid"] is True


def test_validate_rca_claims_downgrades_weak_related_context_only_support():
    entity_id = "k8s.pod:demo/api:uid-a"
    weak_record = _fact(
        "weak-context",
        entity_id,
        dimension="topology",
        fact_type="relationship",
        directness="related_context",
        confidence="weak",
    )
    ledger = FactLedger.model_validate(_ledger("case-a", entity_id, [weak_record]))
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_id,
                "summary": "Weak-context candidate",
                "supporting_fact_ids": [weak_record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        [weak_record["fact_id"]],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "inconclusive"
    assert result["supporting_fact_ids"] == []
    assert any("weak" in reason for reason in result["claim_validation"]["reasons"])


def test_validate_rca_claims_downgrades_direct_low_confidence_only_support():
    entity_id = "k8s.pod:demo/api:uid-a"
    low_confidence_record = _fact(
        "direct-low",
        entity_id,
        directness="direct",
        confidence="low",
    )
    ledger = FactLedger.model_validate(
        _ledger("case-a", entity_id, [low_confidence_record])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_id,
                "summary": "Low-confidence candidate",
                "supporting_fact_ids": [low_confidence_record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.7,
            }
        ],
        [low_confidence_record["fact_id"]],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "inconclusive"
    assert result["supporting_fact_ids"] == []
    assert any(
        "low-confidence" in reason
        for reason in result["claim_validation"]["reasons"]
    )


def test_validate_rca_claims_requires_support_and_hypothesis_for_each_entity():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    fact_a = _fact("entity-a", entity_a)
    fact_b = _fact("entity-b", entity_b)
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-a", entity_a, [fact_a])
        ),
        FactLedger.model_validate(
            _ledger("case-b", entity_b, [fact_b])
        ),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_a,
                "summary": "Entity A candidate without support",
                "supporting_fact_ids": [],
                "contradicting_fact_ids": [],
                "unknowns": ["No direct supporting fact"],
                "confidence": 0.4,
            }
        ],
        [],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "inconclusive"
    assert result["supporting_fact_ids"] == []
    assert any(
        "required entity" in reason or "missing hypothesis" in reason
        for reason in result["claim_validation"]["reasons"]
    )
    assert any("no valid supporting facts" in reason for reason in result["claim_validation"]["reasons"])


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "rootCause",
        "rootCauseState",
        "ROOT.CAUSE",
        "root/cause",
        "root:cause",
        "root...__///cause",
        "expectedRemediation",
        "expectedRemediationPlan",
        "GROUND.TRUTH",
        "groundTruthLabel",
        "diagnosisReason",
        "preFailureBehavior",
        "requestDriver",
        "LaBeL",
        "labels",
        "evaluator.answer",
        *_ROLE_KEY_VARIANTS,
    ],
)
def test_normalize_fact_ledger_rejects_nested_evaluator_key_variants(
    forbidden_key,
):
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("nested-evaluator", entity_id)
    record["value"] = {
        "outer": [
            {
                "inner": {
                    forbidden_key: "must not reach the agent",
                }
            }
        ]
    }
    record["fact_id"] = _canonical_fact_id(record)

    ledger = normalize_fact_ledger(
        _ledger("case-evaluator", entity_id, [record])
    )

    assert ledger is not None
    assert ledger.records == []


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "rootCause",
        "rootCauseState",
        "ROOT.CAUSE",
        "root/cause",
        "root:cause",
        "root...__///cause",
        "expectedRemediation",
        "expectedRemediationPlan",
        "GROUND.TRUTH",
        "groundTruthLabel",
        "diagnosisReason",
        "preFailureBehavior",
        "requestDriver",
        "LaBeL",
        "labels",
        "evaluator.answer",
        *_ROLE_KEY_VARIANTS,
    ],
)
def test_legacy_adapter_rejects_nested_evaluator_key_variants(forbidden_key):
    structured = {
        "case_id": "case-legacy-evaluator",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-a",
        },
        "coverage": {"metrics": "present"},
        "dimension_details": {
            "metrics": {
                "highlights": [
                    {
                        "metric": "request_latency_seconds",
                        "samples": [
                            {
                                "value": 1.25,
                                forbidden_key: "must not reach the agent",
                            }
                        ],
                        "evidence_ref": "metrics:latency",
                    }
                ]
            }
        },
    }

    ledger = normalize_case_fact_ledger(structured)

    assert ledger is not None
    assert all(record.fact_type == "coverage" for record in ledger.records)
    assert "must not reach the agent" not in ledger.model_dump_json()


def test_normalize_fact_ledger_rejects_forbidden_attribute_and_metadata_families():
    entity_id = "k8s.pod:demo/api:uid-a"
    forbidden_attribute = _fact("forbidden-attribute", entity_id)
    forbidden_attribute["attribute"] = "diagnosisReason"
    forbidden_attribute["fact_id"] = _canonical_fact_id(forbidden_attribute)
    forbidden_metadata = _fact("forbidden-metadata", entity_id)
    forbidden_metadata["metadata"] = {
        "nested": [
            {"preFailureBehavior": "must not reach the agent"},
            {"requestDriver": "must not reach the agent"},
        ]
    }
    forbidden_metadata["fact_id"] = _canonical_fact_id(forbidden_metadata)

    ledger = normalize_fact_ledger(
        _ledger(
            "case-forbidden-contract-fields",
            entity_id,
            [forbidden_attribute, forbidden_metadata],
        )
    )

    assert ledger is not None
    assert ledger.records == []


@pytest.mark.parametrize("forbidden_key", _ROLE_KEY_VARIANTS)
def test_normalize_fact_ledger_rejects_role_family_attributes_and_metadata(
    forbidden_key,
):
    entity_id = "k8s.pod:demo/api:uid-a"
    forbidden_attribute = _fact("forbidden-role-attribute", entity_id)
    forbidden_attribute["attribute"] = forbidden_key
    forbidden_attribute["fact_id"] = _canonical_fact_id(forbidden_attribute)
    forbidden_metadata = _fact("forbidden-role-metadata", entity_id)
    forbidden_metadata["metadata"] = {
        "outer": [{"inner": {forbidden_key: "must not reach the agent"}}]
    }
    forbidden_metadata["fact_id"] = _canonical_fact_id(forbidden_metadata)

    ledger = normalize_fact_ledger(
        _ledger(
            "case-forbidden-role-contract-fields",
            entity_id,
            [forbidden_attribute, forbidden_metadata],
        )
    )

    assert ledger is not None
    assert ledger.records == []


def test_normalize_fact_ledger_preserves_source_text_with_causal_words():
    entity_id = "k8s.pod:demo/api:uid-a"
    message = (
        "request driver logged a root cause label, causal role, and diagnostic "
        "role in ordinary source text"
    )
    record = _fact(
        "ordinary-source-text",
        entity_id,
        value={"message": message},
    )

    ledger = normalize_fact_ledger(
        _ledger("case-source-text", entity_id, [record])
    )

    assert ledger is not None
    assert [item.fact_id for item in ledger.records] == [record["fact_id"]]
    assert ledger.records[0].value["message"] == message


def test_bounded_context_projection_strips_all_nested_evaluator_variants():
    payload = {
        "safe": {"value": 1},
        "nested": [
            {"ROOT.CAUSE": "secret-dot"},
            {"rootCauseState": "secret-root-cause-state"},
            {"expected/remediation": "secret-slash"},
            {"expectedRemediationPlan": "secret-remediation-plan"},
            {"ground:truth": "secret-colon"},
            {"groundTruthLabel": "secret-ground-truth-label"},
            {"diagnosisReason": "secret-diagnosis"},
            {"preFailureBehavior": "secret-pre-failure"},
            {"requestDriver": "secret-request-driver"},
            {"LaBeL": "secret-label"},
            {"labels": "secret-labels"},
            {"evaluator...answer": "secret-evaluator"},
        ],
    }

    rendered = bounded_json_dumps(payload, max_chars=12000)
    parsed = json.loads(rendered)

    assert parsed["safe"] == {"value": 1}
    assert all(not item for item in parsed["nested"])
    assert "secret-" not in rendered


def test_bounded_context_projection_strips_role_key_families():
    payload = {
        "safe": {"message": "causal role and diagnostic role are source text"},
        "nested": [
            {"outer": [{"inner": {key: f"secret-{index}"}}]}
            for index, key in enumerate(_ROLE_KEY_VARIANTS)
        ],
    }

    rendered = bounded_json_dumps(payload, max_chars=12000)
    parsed = json.loads(rendered)

    assert parsed["safe"]["message"] == (
        "causal role and diagnostic role are source text"
    )
    assert all(item == {"outer": [{"inner": {}}]} for item in parsed["nested"])
    assert "secret-" not in rendered


def test_bounded_json_dumps_supports_readable_json_within_same_hard_budget():
    payload = {
        "case_target_coverage": {
            "total": 1,
            "collected": 1,
            "rate": 1.0,
        },
        "diagnostic_sufficiency_summary": {
            "score": 0.5,
            "status": "partial",
        },
    }

    rendered = bounded_json_dumps(
        payload,
        max_chars=400,
        indent=2,
    )

    assert len(rendered) <= 400
    assert '"rate": 1.0' in rendered
    assert '"score": 0.5' in rendered
    assert "\n  " in rendered
    assert json.loads(rendered) == payload


def test_normalize_fact_ledger_accepts_valid_canonical_id_and_sorts_refs():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("sorted-refs", entity_id)
    record["evidence_refs"] = ["ref:z", "ref:a", "ref:z"]
    record["fact_id"] = _canonical_fact_id(record)

    ledger = normalize_fact_ledger(_ledger("case-valid-id", entity_id, [record]))

    assert ledger is not None
    assert [item.fact_id for item in ledger.records] == [record["fact_id"]]
    assert ledger.records[0].evidence_refs == ["ref:a", "ref:z"]


def test_normalize_fact_ledger_preserves_complete_canonical_evidence_refs():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("complete-refs", entity_id)
    record["evidence_refs"] = [
        f"ref:{index:02d}"
        for index in range(40)
    ]
    record["fact_id"] = _canonical_fact_id(record)

    ledger = normalize_fact_ledger(
        _ledger("case-complete-refs", entity_id, [record])
    )

    assert ledger is not None
    assert ledger.records[0].fact_id == record["fact_id"]
    assert ledger.records[0].evidence_refs == record["evidence_refs"]


def test_normalize_fact_ledger_rejects_mismatched_canonical_id():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("mismatched", entity_id)
    record["fact_id"] = "fact-000000000000"

    ledger = normalize_fact_ledger(
        _ledger("case-mismatched-id", entity_id, [record])
    )

    assert ledger is not None
    assert ledger.records == []


def test_validate_rca_claims_rejects_cross_ledger_fact_id_collision():
    entity_id = "k8s.pod:demo/api:uid-a"
    collision_id = "fact-collision0001"
    first = _fact("collision-a", entity_id)
    second = _fact("collision-b", entity_id)
    first["fact_id"] = collision_id
    second["fact_id"] = collision_id
    ledgers = [
        FactLedger.model_validate(_ledger("case-a", entity_id, [first])),
        FactLedger.model_validate(_ledger("case-b", entity_id, [second])),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-collision",
                "entity_id": entity_id,
                "summary": "Collision must not authorize a diagnosis",
                "supporting_fact_ids": [collision_id],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        [collision_id],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "inconclusive"
    assert collision_id in result["claim_validation"]["invalid_fact_ids"]
    assert any(
        "collision" in reason
        for reason in result["claim_validation"]["reasons"]
    )


def test_validate_rca_claims_infers_entity_for_published_hypothesis_shape():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("published-shape", entity_id)
    ledger = FactLedger.model_validate(
        _ledger("case-published-shape", entity_id, [record])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-published",
                "summary": "Published contract omits entity_id",
                "supporting_fact_ids": [record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.86,
            }
        ],
        [record["fact_id"]],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "diagnosed"
    assert result["hypotheses"][0]["entity_id"] == entity_id


def test_validate_rca_claims_allows_multiple_supported_hypotheses_for_entity():
    entity_id = "k8s.pod:demo/api:uid-a"
    first = _fact("candidate-a", entity_id)
    second = _fact("candidate-b", entity_id)
    ledger = FactLedger.model_validate(
        _ledger("case-multiple", entity_id, [first, second])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_id,
                "summary": "First independently supported candidate",
                "supporting_fact_ids": [first["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.82,
            },
            {
                "hypothesis_id": "hyp-b",
                "entity_id": entity_id,
                "summary": "Second independently supported candidate",
                "supporting_fact_ids": [second["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.78,
            },
        ],
        [first["fact_id"], second["fact_id"]],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "diagnosed"
    assert len(result["hypotheses"]) == 2
    assert all(item["entity_id"] == entity_id for item in result["hypotheses"])


def test_validate_rca_claims_downgrades_when_any_hypothesis_is_invalid():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("valid-candidate", entity_id)
    ledger = FactLedger.model_validate(
        _ledger("case-invalid-extra", entity_id, [record])
    )
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-valid",
                "entity_id": entity_id,
                "summary": "Validated candidate",
                "supporting_fact_ids": [record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.84,
            },
            {
                "hypothesis_id": "hyp-invalid",
                "summary": "Unvalidated candidate",
                "supporting_fact_ids": ["fact-ffffffffffff"],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.7,
            },
        ],
        [record["fact_id"], "fact-ffffffffffff"],
    )

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "inconclusive"
    assert result["claim_validation"]["valid"] is False
    assert "fact-ffffffffffff" in result["claim_validation"]["invalid_fact_ids"]


def test_validate_rca_claims_rejects_ambiguous_inferred_entity():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    fact_a = _fact("ambiguous-a", entity_a)
    fact_b = _fact("ambiguous-b", entity_b)
    ledgers = [
        FactLedger.model_validate(_ledger("case-a", entity_a, [fact_a])),
        FactLedger.model_validate(_ledger("case-b", entity_b, [fact_b])),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-ambiguous",
                "summary": "References facts from two entities",
                "supporting_fact_ids": [
                    fact_a["fact_id"],
                    fact_b["fact_id"],
                ],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        [fact_a["fact_id"], fact_b["fact_id"]],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "inconclusive"
    assert any(
        "ambiguous" in reason
        for reason in result["claim_validation"]["reasons"]
    )


def test_validate_rca_claims_requires_supported_hypothesis_for_every_pod():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    fact_a = _fact("covered-a", entity_a)
    fact_b = _fact("uncovered-b", entity_b)
    ledgers = [
        FactLedger.model_validate(_ledger("case-a", entity_a, [fact_a])),
        FactLedger.model_validate(_ledger("case-b", entity_b, [fact_b])),
    ]
    claim = _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_a,
                "summary": "Only the first Pod is covered",
                "supporting_fact_ids": [fact_a["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.84,
            }
        ],
        [fact_a["fact_id"]],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "inconclusive"
    assert any(
        entity_b in reason and "required entity" in reason
        for reason in result["claim_validation"]["reasons"]
    )


def _topology_record(marker, attached_entity_id, value):
    record = _fact(
        marker,
        attached_entity_id,
        dimension="topology",
        fact_type="relationship",
        directness="direct",
        confidence="high",
        value=value,
    )
    record["entity_kind"] = "TopologyEdge"
    record["fact_id"] = _canonical_fact_id(record)
    return record


def _single_fact_claim(entity_id, record):
    return _diagnosed_claim(
        [
            {
                "hypothesis_id": "hyp-topology",
                "entity_id": entity_id,
                "summary": "Topology-backed candidate",
                "supporting_fact_ids": [record["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        [record["fact_id"]],
    )


def test_validate_rca_claims_rejects_forged_topology_note():
    entity_id = "k8s.pod:demo/api:uid-a"
    service_id = "k8s.service:demo/api"
    record = _topology_record(
        "forged-note",
        service_id,
        {
            "relationship": "unrelated",
            "notes": f"free-form mention of {entity_id}",
        },
    )
    ledger = FactLedger.model_validate(
        _ledger("case-forged-note", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "inconclusive"
    assert record["fact_id"] in result["claim_validation"]["invalid_fact_ids"]


def test_validate_rca_claims_rejects_topology_with_wrong_typed_endpoints():
    entity_id = "k8s.pod:demo/api:uid-a"
    service_id = "k8s.service:demo/api"
    record = _topology_record(
        "wrong-endpoints",
        service_id,
        {
            "source_entity_id": service_id,
            "target_entity_id": "k8s.pod:demo/other:uid-b",
            "relationship": "selects",
        },
    )
    ledger = FactLedger.model_validate(
        _ledger("case-wrong-endpoints", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "inconclusive"


@pytest.mark.parametrize(
    "topology_value",
    [
        {
            "target_entity_id": "k8s.pod:demo/api:uid-a",
            "relationship": "selects",
        },
        {
            "source_entity_id": "k8s.pod:demo/api:uid-a",
            "relationship": "owned_by",
        },
        {
            "source_entity_id": "k8s.service:demo/api",
            "target_entity_id": "k8s.pod:demo/api:uid-a",
        },
        {
            "source": {
                "entity_id": "k8s.service:demo/api",
                "kind": "ConfigMap",
            },
            "target": {
                "entity_id": "k8s.pod:demo/api:uid-a",
                "kind": "Pod",
            },
            "relation": "selects",
        },
    ],
)
def test_validate_rca_claims_rejects_incomplete_or_malformed_typed_topology(
    topology_value,
):
    entity_id = "k8s.pod:demo/api:uid-a"
    service_id = "k8s.service:demo/api"
    record = _topology_record(
        "incomplete-topology",
        service_id,
        topology_value,
    )
    ledger = FactLedger.model_validate(
        _ledger("case-incomplete-topology", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "inconclusive"
    assert record["fact_id"] in result["claim_validation"]["invalid_fact_ids"]


def test_validate_rca_claims_accepts_reversed_typed_topology_endpoints():
    entity_id = "k8s.pod:demo/api:uid-a"
    owner_id = "k8s.replicaset:demo/api-rs"
    record = _topology_record(
        "reversed-endpoints",
        owner_id,
        {
            "source_entity_id": entity_id,
            "target_entity_id": owner_id,
            "relationship": "owned_by",
        },
    )
    ledger = FactLedger.model_validate(
        _ledger("case-reversed-endpoints", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "diagnosed"


def test_validate_rca_claims_accepts_canonical_typed_topology_shape():
    entity_id = "k8s.pod:demo/api:uid-a"
    service_id = "k8s.service:demo/api"
    record = _topology_record(
        "canonical-endpoints",
        service_id,
        {
            "source": {"entity_id": service_id, "kind": "Service"},
            "target": {"entity_id": entity_id, "kind": "Pod"},
            "relation": "selects",
        },
    )
    ledger = FactLedger.model_validate(
        _ledger("case-canonical-endpoints", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "diagnosed"


def test_validate_rca_claims_downgrades_derived_medium_strong_support():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact(
        "derived-medium-strong",
        entity_id,
        directness="derived",
        confidence="medium",
        strength="strong",
    )
    ledger = FactLedger.model_validate(
        _ledger("case-derived-medium", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "inconclusive"
    assert result["supporting_fact_ids"] == []


def test_validate_rca_claims_downgrades_coverage_only_support():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact(
        "coverage-only",
        entity_id,
        dimension="coverage",
        fact_type="coverage",
        directness="direct",
        confidence="high",
    )
    ledger = FactLedger.model_validate(
        _ledger("case-coverage-only", entity_id, [record])
    )

    result = validate_rca_claims(
        _single_fact_claim(entity_id, record),
        [ledger],
    )

    assert result["diagnostic_status"] == "inconclusive"


def test_compact_fact_ledgers_json_rejects_impossible_minimum_budget():
    with pytest.raises(ValueError, match="minimum"):
        compact_fact_ledgers_json(
            [],
            max_chars=MIN_FACT_LEDGER_JSON_CHARS - 1,
        )


def test_compact_fact_ledgers_json_accepts_exact_minimum_boundary():
    rendered = compact_fact_ledgers_json(
        [],
        max_chars=MIN_FACT_LEDGER_JSON_CHARS,
    )

    assert rendered == '{"fact_ledgers":[]}'
    assert len(rendered) == MIN_FACT_LEDGER_JSON_CHARS


def test_compact_fact_ledgers_json_retains_identity_index_for_many_cases():
    ledgers = [
        FactLedger.model_validate(
            _ledger(
                f"case-{index:03d}",
                f"k8s.pod:demo/api-{index:03d}:uid-{index:03d}",
                [],
            )
        )
        for index in range(65)
    ]

    first = compact_fact_ledgers_json(ledgers, max_chars=12000)
    second = compact_fact_ledgers_json(ledgers, max_chars=12000)
    parsed = json.loads(first)

    assert first == second
    assert len(first) <= 12000
    assert parsed["fact_ledgers"] == []
    assert parsed["omitted_case_count"] == 65
    assert [item["case_id"] for item in parsed["case_index"]] == [
        f"case-{index:03d}" for index in range(65)
    ]
    assert all(item["ledger_ref"] for item in parsed["case_index"])


def test_persisted_aiops_context_is_adapted_before_other_representations():
    structured_context = {
        "case_id": "case-persisted",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "demo",
            "name": "api",
            "uid": "uid-a",
        },
        "coverage": {"logs": "present"},
        "dimension_details": {
            "logs": {
                "samples": [
                    {
                        "message": "request returned status 503",
                        "evidence_ref": "logs:target",
                    }
                ]
            }
        },
    }
    selected = select_tool_data_for_rca([
        {
            "tool": "collect_aiops_case",
            "data": "RAW REPRESENTATION",
            "agent_facts": "TEXT FACT REPRESENTATION",
            "agent_context": json.dumps(structured_context),
        }
    ])
    ledgers = extract_fact_ledgers_from_tool_data(selected)

    assert len(ledgers) == 1
    assert ledgers[0].source == "robusta_legacy_adapter"
    assert selected[0]["fact_ledger"]["case_id"] == "case-persisted"


def test_rca_prompt_matches_generic_fact_support_threshold():
    assert "direct 且 confidence=medium/high" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "direct 或 high-confidence" not in ROOT_CAUSE_ANALYZER_PROMPT
    assert "有工具证据且有分析结论，至少 0.8" not in ROOT_CAUSE_ANALYZER_PROMPT
    assert "必须且只能有一个 hypothesis" not in ROOT_CAUSE_ANALYZER_PROMPT
    assert "每个当前 scope entity 必须恰好有一个 hypothesis" not in ROOT_CAUSE_ANALYZER_PROMPT
    assert "必须恰好有一个 hypothesis" not in ROOT_CAUSE_ANALYZER_PROMPT
    assert "每个 required abnormal Pod 必须至少有一个通过引用校验的 hypothesis" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "同一 entity 允许有多个独立 hypothesis" in ROOT_CAUSE_ANALYZER_PROMPT
    assert "`entity_id` 可省略，但只能由引用事实唯一推断" in ROOT_CAUSE_ANALYZER_PROMPT
    assert '"entity_id": "当前 Fact Ledger scope 中的 entity_id"' not in ROOT_CAUSE_ANALYZER_PROMPT
    assert "strength=critical/strong" not in ROOT_CAUSE_ANALYZER_PROMPT


def test_kubernetes_lifecycle_adapter_preserves_last_reason_and_exit_code():
    ledger = build_kubernetes_lifecycle_fact_ledger({
        "name": "api-abc",
        "namespace": "demo",
        "status": "Running",
        "containers": [
            {
                "name": "business-api",
                "state": "Waiting",
                "last_state": "Terminated",
                "reason": "OOMKilled",
                "exit_code": "137",
                "restart_count": "42",
            }
        ],
        "evidence_refs": [
            "/archive/kubectl-describe.raw",
            "/archive/kubectl-describe.summary",
        ],
    })

    assert ledger is not None
    records = {record.attribute: record for record in ledger.records}
    assert records["container.last_terminated_reason"].value == {
        "container": "business-api",
        "reason": "OOMKilled",
    }
    assert records["container.last_exit_code"].value == {
        "container": "business-api",
        "exit_code": 137,
    }
    assert records["container.restart_count"].value == {
        "container": "business-api",
        "restart_count": 42,
    }
    assert all(
        record.source_system == "kubernetes"
        for record in records.values()
    )
    assert all(
        "/archive/kubectl-describe.raw" in record.evidence_refs
        for record in records.values()
    )


def test_topology_query_fact_adapter_adds_canonical_typed_endpoints():
    ledger = build_observability_query_fact_ledger({
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-api",
        },
        "coverage": "present",
        "directness": "direct",
        "facts": [
            {
                "ref": "topology-owned-by",
                "source_system": "kubernetes",
                "name": "kubernetes.relationship",
                "relation": "owned_by",
                "value": {
                    "relation": "owned_by",
                    "relationship": "Pod --owned_by--> ReplicaSet",
                    "source": {
                        "kind": "Pod",
                        "namespace": "demo",
                        "name": "api",
                        "uid": "uid-api",
                    },
                    "target": {
                        "kind": "ReplicaSet",
                        "namespace": "demo",
                        "name": "api-rs",
                        "uid": "uid-rs",
                    },
                    "source_field": "metadata.ownerReferences",
                },
                "directness": "direct",
                "confidence": "high",
            }
        ],
    })

    assert ledger is not None
    assert ledger.scope_entity_ids == ["k8s.pod:demo/api:uid-api"]
    record = ledger.records[0]
    assert record.fact_type == "relationship"
    assert record.attribute == "kubernetes.relationship"
    assert record.value["source"]["entity_id"] == (
        "k8s.pod:demo/api:uid-api"
    )
    assert record.value["target"]["entity_id"] == (
        "k8s.replicaset:demo/api-rs:uid-rs"
    )
    assert record.value["source_field"] == "metadata.ownerReferences"
    assert record.evidence_refs == ["topology-owned-by"]


def test_topology_adapter_keeps_same_named_edges_separate_by_complete_identity():
    ledger = build_observability_query_fact_ledger({
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-demo-api",
        },
        "coverage": "present",
        "directness": "direct",
        "facts": [],
        "edges": [
            {
                "relationship": "Pod --calls--> Service",
                "source": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-demo-api",
                },
                "target": {
                    "kind": "Service",
                    "namespace": "demo",
                    "name": "backend",
                    "uid": "uid-demo-backend",
                },
                "source_field": "demo.calls",
                "source_system": "kubernetes",
                "directness": "direct",
                "confidence": "high",
                "evidence_refs": ["edge-demo"],
            },
            {
                "relationship": "Pod --calls--> Service",
                "source": {
                    "kind": "Pod",
                    "namespace": "other",
                    "name": "api",
                    "uid": "uid-other-api",
                },
                "target": {
                    "kind": "Service",
                    "namespace": "other",
                    "name": "backend",
                    "uid": "uid-other-backend",
                },
                "source_field": "other.calls",
                "source_system": "kubernetes",
                "directness": "direct",
                "confidence": "low",
                "evidence_refs": ["edge-other"],
            },
        ],
    })

    assert ledger is not None
    relationships = [
        record
        for record in ledger.records
        if record.fact_type == "relationship"
    ]
    assert len(relationships) == 2
    by_source_id = {
        record.value["source"]["entity_id"]: record
        for record in relationships
    }
    demo = by_source_id["k8s.pod:demo/api:uid-demo-api"]
    other = by_source_id["k8s.pod:other/api:uid-other-api"]
    assert demo.value["target"]["entity_id"] == (
        "k8s.service:demo/backend:uid-demo-backend"
    )
    assert demo.value["source_field"] == "demo.calls"
    assert demo.confidence == "high"
    assert demo.evidence_refs == ["edge-demo"]
    assert other.value["target"]["entity_id"] == (
        "k8s.service:other/backend:uid-other-backend"
    )
    assert other.value["source_field"] == "other.calls"
    assert other.confidence == "low"
    assert other.evidence_refs == ["edge-other"]


def test_topology_adapter_drops_unmatched_edge_without_source_confidence():
    structured = {
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-api",
        },
        "coverage": "present",
        "directness": "direct",
        "facts": [],
        "entities": [
            {
                "kind": "Pod",
                "namespace": "demo",
                "name": "api",
                "uid": "uid-api",
            }
        ],
        "edges": [
            {
                "relationship": "Pod --calls--> Service",
                "source": {
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-api",
                },
                "target": {
                    "kind": "Service",
                    "namespace": "demo",
                    "name": "backend",
                    "uid": "uid-backend",
                },
                "source_system": "kubernetes",
                "directness": "direct",
                "evidence_refs": ["edge-unscored"],
            }
        ],
        "evidence_refs": ["topology-snapshot"],
    }
    original = json.loads(json.dumps(structured))

    ledger = build_observability_query_fact_ledger(structured)

    assert ledger is not None
    assert [
        record
        for record in ledger.records
        if record.fact_type == "relationship"
    ] == []
    assert not any(
        "edge-unscored" in record.evidence_refs
        for record in ledger.records
    )
    assert structured == original


def test_topology_adapter_matches_explicit_entity_ids_for_edge_confidence():
    ledger = build_observability_query_fact_ledger({
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-api",
        },
        "coverage": "present",
        "directness": "direct",
        "facts": [
            {
                "ref": "fact-ref",
                "source_system": "kubernetes",
                "dimension": "topology",
                "name": "topology.relationship.observed",
                "value": {
                    "relationship": "Pod --calls--> Service",
                    "source": {
                        "entity_id": "k8s.pod:demo/api:uid-api",
                        "kind": "Pod",
                        "namespace": "demo",
                        "name": "api-alias",
                        "uid": "uid-api",
                    },
                    "target": {
                        "entity_id": (
                            "k8s.service:demo/backend:uid-backend"
                        ),
                        "kind": "Service",
                        "namespace": "demo",
                        "name": "backend-alias",
                        "uid": "uid-backend",
                    },
                },
                "directness": "direct",
            }
        ],
        "edges": [
            {
                "relationship": "Pod --calls--> Service",
                "source": {
                    "entity_id": "k8s.pod:demo/api:uid-api",
                    "kind": "Pod",
                    "namespace": "demo",
                    "name": "api",
                    "uid": "uid-api",
                },
                "target": {
                    "entity_id": (
                        "k8s.service:demo/backend:uid-backend"
                    ),
                    "kind": "Service",
                    "namespace": "demo",
                    "name": "backend",
                    "uid": "uid-backend",
                },
                "source_field": "network.destination",
                "source_system": "kubernetes",
                "directness": "direct",
                "confidence": "high",
                "evidence_refs": ["edge-ref"],
            }
        ],
    })

    assert ledger is not None
    relationships = [
        record
        for record in ledger.records
        if record.fact_type == "relationship"
    ]
    assert len(relationships) == 1
    relationship = relationships[0]
    assert relationship.attribute == "topology.relationship.observed"
    assert relationship.value["source_field"] == "network.destination"
    assert relationship.confidence == "high"
    assert set(relationship.evidence_refs) == {"fact-ref", "edge-ref"}


def _topology_candidate_fact(
    *,
    namespace="demo",
    source_uid="uid-api",
    target_uid="uid-backend",
    evidence_ref="fact-ref",
):
    return {
        "ref": evidence_ref,
        "source_system": "kubernetes",
        "dimension": "topology",
        "name": "topology.relationship.observed",
        "value": {
            "relationship": "Pod --calls--> Service",
            "source": {
                "entity_id": (
                    f"k8s.pod:{namespace}/api:{source_uid}"
                ),
                "kind": "Pod",
                "namespace": namespace,
                "name": "api",
                "uid": source_uid,
            },
            "target": {
                "entity_id": (
                    f"k8s.service:{namespace}/backend:{target_uid}"
                ),
                "kind": "Service",
                "namespace": namespace,
                "name": "backend",
                "uid": target_uid,
            },
        },
        "directness": "direct",
    }


def _topology_candidate_edge(
    source_field,
    evidence_ref,
    *,
    confidence=None,
    namespace="demo",
    source_uid="uid-api",
    target_uid="uid-backend",
):
    edge = {
        "relationship": "Pod --calls--> Service",
        "source": {
            "entity_id": f"k8s.pod:{namespace}/api:{source_uid}",
            "kind": "Pod",
            "namespace": namespace,
            "name": "api",
            "uid": source_uid,
        },
        "target": {
            "entity_id": (
                f"k8s.service:{namespace}/backend:{target_uid}"
            ),
            "kind": "Service",
            "namespace": namespace,
            "name": "backend",
            "uid": target_uid,
        },
        "source_field": source_field,
        "source_system": "kubernetes",
        "directness": "direct",
        "evidence_refs": [evidence_ref],
    }
    if confidence is not None:
        edge["confidence"] = confidence
    return edge


def _topology_candidate_payload(edges, *, facts=None):
    return {
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-api",
        },
        "coverage": "present",
        "directness": "direct",
        "facts": facts or [_topology_candidate_fact()],
        "edges": edges,
    }


def _topology_relationship_records(ledger):
    return [
        record
        for record in ledger.records
        if record.fact_type == "relationship"
    ]


def test_topology_candidate_selection_ignores_unscored_exact_edge_first():
    unscored = _topology_candidate_edge(
        "unscored.destination",
        "edge-unscored-first",
    )
    scored = _topology_candidate_edge(
        "scored.destination",
        "edge-scored-second",
        confidence="high",
    )

    ledger = build_observability_query_fact_ledger(
        _topology_candidate_payload([unscored, scored])
    )

    assert ledger is not None
    relationships = _topology_relationship_records(ledger)
    assert len(relationships) == 1
    relationship = relationships[0]
    assert relationship.value["source_field"] == "scored.destination"
    assert relationship.confidence == "high"
    assert set(relationship.evidence_refs) == {
        "fact-ref",
        "edge-scored-second",
    }
    assert "edge-unscored-first" not in relationship.evidence_refs


def test_topology_candidate_selection_is_identical_under_input_reversal():
    unscored = _topology_candidate_edge(
        "unscored.destination",
        "edge-unscored",
    )
    scored = _topology_candidate_edge(
        "scored.destination",
        "edge-scored",
        confidence="high",
    )

    first = build_observability_query_fact_ledger(
        _topology_candidate_payload([unscored, scored])
    )
    reversed_order = build_observability_query_fact_ledger(
        _topology_candidate_payload([scored, unscored])
    )

    assert first is not None
    assert reversed_order is not None
    first_relationship = _topology_relationship_records(first)
    reversed_relationship = _topology_relationship_records(
        reversed_order
    )
    assert len(first_relationship) == 1
    assert len(reversed_relationship) == 1
    assert first_relationship[0].model_dump(
        mode="json",
        exclude_none=True,
    ) == reversed_relationship[0].model_dump(
        mode="json",
        exclude_none=True,
    )
    assert first_relationship[0].fact_id == (
        reversed_relationship[0].fact_id
    )


def test_topology_candidate_selection_ranks_scored_duplicates_without_leakage():
    zeta = _topology_candidate_edge(
        "zeta.destination",
        "edge-zeta",
        confidence="high",
    )
    alpha = _topology_candidate_edge(
        "alpha.destination",
        "edge-alpha",
        confidence="high",
    )
    other = _topology_candidate_edge(
        "other.destination",
        "edge-other",
        confidence="medium",
        namespace="other",
        source_uid="uid-other-api",
        target_uid="uid-other-backend",
    )
    facts = [
        _topology_candidate_fact(evidence_ref="fact-demo"),
        _topology_candidate_fact(
            namespace="other",
            source_uid="uid-other-api",
            target_uid="uid-other-backend",
            evidence_ref="fact-other",
        ),
    ]

    first = build_observability_query_fact_ledger(
        _topology_candidate_payload(
            [zeta, other, alpha],
            facts=facts,
        )
    )
    reversed_order = build_observability_query_fact_ledger(
        _topology_candidate_payload(
            [alpha, other, zeta],
            facts=facts,
        )
    )

    assert first is not None
    assert reversed_order is not None

    def by_source_id(ledger):
        return {
            record.value["source"]["entity_id"]: record
            for record in _topology_relationship_records(ledger)
        }

    first_records = by_source_id(first)
    reversed_records = by_source_id(reversed_order)
    assert {
        key: record.model_dump(mode="json", exclude_none=True)
        for key, record in first_records.items()
    } == {
        key: record.model_dump(mode="json", exclude_none=True)
        for key, record in reversed_records.items()
    }

    demo = first_records["k8s.pod:demo/api:uid-api"]
    assert demo.value["source_field"] == "alpha.destination"
    assert demo.confidence == "high"
    assert set(demo.evidence_refs) == {"fact-demo", "edge-alpha"}
    assert "edge-zeta" not in demo.evidence_refs
    assert "edge-other" not in demo.evidence_refs

    other_record = first_records[
        "k8s.pod:other/api:uid-other-api"
    ]
    assert other_record.value["source_field"] == "other.destination"
    assert other_record.confidence == "medium"
    assert set(other_record.evidence_refs) == {
        "fact-other",
        "edge-other",
    }
    assert "edge-alpha" not in other_record.evidence_refs
    assert "edge-zeta" not in other_record.evidence_refs


def test_deployed_topology_reconstructs_primary_identity_and_typed_endpoints():
    structured = {
        "ok": True,
        "status": "query_succeeded",
        "source_system": "kubernetes",
        "dimension": "topology",
        "entity": {
            "kind": "Pod",
            "entity_id": "e:pod",
            "pod_ip": "172.16.1.20",
        },
        "purpose": "确认目标 Pod 的控制器、Service、节点和容器关系",
        "coverage": "present",
        "directness": "direct",
        "query": {
            "scope": {
                "kind": "Pod",
                "namespace": "demo",
                "pod": "api-abc",
            }
        },
        "facts": [
            {
                "ref": "topology-owned-by",
                "source_system": "kubernetes",
                "name": "kubernetes.relationship",
                "relation": "owned_by",
                "value": {
                    "relation": "owned_by",
                    "relationship": "Pod --owned_by--> ReplicaSet",
                    "source": "e:pod",
                    "target": "e:rs",
                    "source_field": "metadata.ownerReferences",
                },
                "directness": "direct",
                "confidence": "high",
            }
        ],
        "entities": [
            {
                "entity_id": "e:pod",
                "kind": "Pod",
                "namespace": "demo",
                "name": "api-abc",
                "uid": "uid-api",
                "source_system": "kubernetes",
            },
            {
                "entity_id": "e:rs",
                "kind": "ReplicaSet",
                "namespace": "demo",
                "name": "api-rs",
                "uid": "uid-rs",
                "source_system": "kubernetes",
            },
        ],
        "edges": [
            {
                "relation": "owned_by",
                "source": "e:pod",
                "target": "e:rs",
                "source_system": "kubernetes",
                "evidence_ref": "topology-owned-by",
            }
        ],
        "topology_summary": {
            "entity_count": 2,
            "edge_count": 1,
            "relations": {"owned_by": 1},
        },
        "evidence_refs": ["topology-owned-by"],
    }

    ledger = build_observability_query_fact_ledger(structured)

    assert ledger is not None
    assert ledger.scope_entity_ids == ["k8s.pod:demo/api-abc:uid-api"]
    relationships = _topology_relationship_records(ledger)
    assert len(relationships) == 1
    assert relationships[0].value == {
        "relation": "owned_by",
        "relationship": "Pod --owned_by--> ReplicaSet",
        "source": {
            "entity_id": "e:pod",
            "kind": "Pod",
            "name": "api-abc",
            "namespace": "demo",
            "source_system": "kubernetes",
            "uid": "uid-api",
        },
        "target": {
            "entity_id": "e:rs",
            "kind": "ReplicaSet",
            "name": "api-rs",
            "namespace": "demo",
            "source_system": "kubernetes",
            "uid": "uid-rs",
        },
        "source_field": "metadata.ownerReferences",
    }
    assert relationships[0].evidence_refs == ["topology-owned-by"]


def test_partial_observability_ledger_preserves_fact_and_limitation():
    ledger = build_observability_query_fact_ledger({
        "status": "query_partial",
        "source_system": "prometheus",
        "dimension": "metrics",
        "entity": {
            "kind": "Pod",
            "namespace": "demo",
            "pod": "api",
            "pod_uid": "uid-api",
        },
        "coverage": "partial",
        "directness": "direct",
        "facts": [
            {
                "ref": "metric-partial-memory",
                "source_system": "prometheus",
                "dimension": "metrics",
                "name": "container_memory_working_set_bytes",
                "value": 70168576,
                "unit": "bytes",
                "directness": "direct",
            }
        ],
        "limitations": ["Prometheus returned only the newest shard"],
        "evidence_refs": ["metric-partial-memory"],
    })

    assert ledger is not None
    records = {record.attribute: record for record in ledger.records}
    assert records["container_memory_working_set_bytes"].value == 70168576
    assert records["container_memory_working_set_bytes"].source_system == (
        "prometheus"
    )
    assert records["metrics.coverage"].fact_type == "coverage"
    assert records["metrics.coverage"].value == {
        "coverage": "partial",
        "limitations": ["Prometheus returned only the newest shard"],
    }
    assert records["metrics.coverage"].evidence_refs == [
        "metric-partial-memory"
    ]


def test_final_projection_requires_explicit_success_and_explicit_retry_intent():
    def event(
        event_id,
        *,
        semantic_success_marker,
        purpose_marker,
        status,
        coverage,
    ):
        item = {
            "id": event_id,
            "type": "tool_result",
            "status": "success",
            "tool_name": "execute_pod_promql",
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
            },
            "structured": {
                "status": status,
                "source_system": "prometheus",
                "dimension": "metrics",
                "entity": {"namespace": "demo", "pod": "api"},
                "coverage": coverage,
                "facts": [],
            },
        }
        if semantic_success_marker != "missing":
            item["semantic_success"] = semantic_success_marker
        if purpose_marker != "missing":
            item["tool_args"]["purpose"] = purpose_marker
            item["structured"]["purpose"] = purpose_marker
        return item

    events = [
        event(
            "explicit-rejection",
            semantic_success_marker=False,
            purpose_marker="确认内存趋势",
            status="query_rejected",
            coverage="error",
        ),
        event(
            "transport-only-success",
            semantic_success_marker="missing",
            purpose_marker="确认内存趋势",
            status="query_succeeded",
            coverage="present",
        ),
        event(
            "malformed-partial",
            semantic_success_marker=True,
            purpose_marker="确认内存趋势",
            status="query_partial",
            coverage="partial",
        ),
        event(
            "unidentified-rejection",
            semantic_success_marker=False,
            purpose_marker="missing",
            status="query_rejected",
            coverage="error",
        ),
        event(
            "unidentified-success",
            semantic_success_marker=True,
            purpose_marker="missing",
            status="query_succeeded",
            coverage="present",
        ),
    ]

    projected = project_final_observability_events(events)

    assert [item["id"] for item in projected] == [
        "explicit-rejection",
    ]


def test_a029_compact_a028_ledgers_is_fair_bounded_and_order_independent():
    archive = (
        Path(__file__).resolve().parents[3]
        / "agent-loop/tasks/T007/attempts/A028/artifacts/context_archive/"
        "node_outputs/evidence.output.json"
    )
    evidence_output = json.loads(archive.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_output["snapshot"]["evidence_analysis"])
    ledgers = [
        item["fact_ledger"]
        for item in evidence["tool_data"]
        if item.get("fact_ledger")
    ]

    forward = compact_fact_ledgers_json(ledgers, max_chars=24000)
    reverse = compact_fact_ledgers_json(
        list(reversed(ledgers)),
        max_chars=24000,
    )
    compacted = json.loads(forward)
    records = [
        record
        for ledger in compacted["fact_ledgers"]
        for record in ledger["records"]
    ]

    def value_text(record):
        value = record.get("value")
        return value if isinstance(value, str) else json.dumps(
            value,
            ensure_ascii=False,
        )

    assert len(ledgers) == 10
    assert len(forward) <= 24000
    assert forward == reverse
    assert {
        int(match)
        for record in records
        if record.get("dimension") == "logging"
        for match in re.findall(
            r'"allocated_mib"\s*:\s*(60|62)',
            value_text(record),
        )
    } == {60, 62}
    assert any(
        record.get("source_system") == "tempo"
        and record.get("attribute") == "application_span"
        for record in records
    )
    for workload in ("trace-oom-api", "trace-config-api"):
        assert any(
            workload in str(record.get("entity_name") or "")
            and record.get("source_system") == "kubernetes"
            and record.get("directness") == "direct"
            and record.get("confidence") == "high"
            and "ReplicaSet --owned_by--> Deployment" in value_text(record)
            and record.get("evidence_refs")
            for record in records
        )
    assert any(
        record.get("dimension") == "kubernetes"
        and record.get("attribute") == "container.last_terminated_reason"
        and "OOMKilled" in value_text(record)
        for record in records
    )


def test_a029_validate_rca_claims_corrects_unique_long_fact_id_prefix_everywhere():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("unique-prefix", entity_id)
    full_id = record["fact_id"]
    prefix = full_id[:-1]
    ledger = FactLedger.model_validate(
        _ledger("case-unique-prefix", entity_id, [record])
    )
    claim = _diagnosed_claim(
        [{
            "hypothesis_id": "hyp-unique-prefix",
            "entity_id": entity_id,
            "summary": "Unique long prefix should resolve",
            "supporting_fact_ids": [prefix],
            "contradicting_fact_ids": [],
            "unknowns": [
                f"unknown supporting fact reference: {prefix}",
            ],
            "confidence": 0.9,
        }],
        [prefix],
    )
    claim.update({
        "evidence_inventory": [{
            "id": prefix,
            "source": "test-source",
            "content": "Direct fact",
            "reliability": "high",
        }],
        "evidence_analysis": [{
            "evidence_id": prefix,
            "raw_data": "observed",
            "interpretation": (
                f"unknown top-level fact reference: {prefix}"
            ),
        }],
        "unknowns": [
            f"unknown top-level fact reference: {prefix}",
            "one or more fact references failed validation",
        ],
        "confidence_reason": (
            f"unknown supporting fact reference: {prefix}; "
            f"unknown top-level fact reference: {prefix}; "
            "one or more fact references failed validation"
        ),
        "limitations": (
            "Fact-reference validation did not support a diagnosed result."
        ),
    })

    result = validate_rca_claims(claim, [ledger])

    assert result["diagnostic_status"] == "diagnosed"
    assert result["claim_validation"]["valid"] is True
    assert result["supporting_fact_ids"] == [full_id]
    assert result["hypotheses"][0]["supporting_fact_ids"] == [full_id]
    assert result["evidence_inventory"][0]["id"] == full_id
    assert result["evidence_analysis"][0]["evidence_id"] == full_id
    serialized = json.dumps(result, ensure_ascii=False)
    assert "unknown supporting fact reference" not in serialized
    assert "unknown top-level fact reference" not in serialized
    assert "Fact-reference validation did not support" not in serialized
    assert result["confidence_reason"] == (
        "Fact references normalized against the current ledger."
    )


@pytest.mark.parametrize(
    "reference",
    [
        "fact-abc123",
        "fact-abcdef12345",
        "fact-ffffffffffff",
    ],
)
def test_a029_fact_id_prefix_rejects_short_ambiguous_and_unknown(
    monkeypatch,
    reference,
):
    entity_id = "k8s.pod:demo/api:uid-a"
    first = _fact("ambiguous-prefix-a", entity_id)
    second = _fact("ambiguous-prefix-b", entity_id)
    first["fact_id"] = "fact-abcdef12345a"
    second["fact_id"] = "fact-abcdef12345b"
    monkeypatch.setattr(
        fact_contract_module,
        "_canonical_fact_id",
        lambda record: str(
            getattr(record, "fact_id", None)
            or (record.get("fact_id") if isinstance(record, dict) else "")
        ),
    )
    ledgers = [
        FactLedger.model_validate(
            _ledger("case-prefix-a", entity_id, [first])
        ),
        FactLedger.model_validate(
            _ledger("case-prefix-b", entity_id, [second])
        ),
    ]
    claim = _diagnosed_claim(
        [{
            "hypothesis_id": "hyp-invalid-prefix",
            "entity_id": entity_id,
            "summary": "Invalid prefix must remain rejected",
            "supporting_fact_ids": [reference],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "confidence": 0.9,
        }],
        [reference],
    )

    result = validate_rca_claims(claim, ledgers)

    assert result["diagnostic_status"] == "inconclusive"
    assert reference in result["claim_validation"]["invalid_fact_ids"]


def test_a029_rca_reconciles_logging_and_exact_trace_denials_only():
    entity_id = "k8s.pod:demo/orders-api-abc123def0-x1y2z:uid-a"
    trace_id = "0123456789abcdef0123456789abcdef"
    other_trace_id = "fedcba9876543210fedcba9876543210"

    def record(marker, source_system, fact_type, attribute, value):
        return _with_canonical_fact_id({
            "entity_id": entity_id,
            "entity_kind": "Pod",
            "namespace": "demo",
            "entity_name": "orders-api-abc123def0-x1y2z",
            "dimension": (
                "logging" if fact_type == "log" else "tracing"
            ),
            "fact_type": fact_type,
            "attribute": attribute,
            "value": value,
            "source_system": source_system,
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
            "evidence_refs": [f"ref:{marker}"],
        })

    log_fact = record(
        "log",
        "elasticsearch",
        "log",
        "log.message",
        {"message": "allocated memory", "allocated_mib": 62},
    )
    flow_fact = record(
        "flow",
        "deepflow",
        "flow",
        "l7_flow",
        {"trace_id": trace_id, "request_resource": "/orders"},
    )
    span_fact = record(
        "span",
        "tempo",
        "span",
        "application_span",
        {"trace_id": trace_id, "name": "GET /orders"},
    )
    ledger = FactLedger.model_validate(
        _ledger(
            "case-reconcile",
            entity_id,
            [log_fact, flow_fact, span_fact],
        )
    )
    claim = _diagnosed_claim(
        [{
            "hypothesis_id": "hyp-reconcile",
            "entity_id": entity_id,
            "summary": "Direct facts support the entity",
            "supporting_fact_ids": [
                log_fact["fact_id"],
                flow_fact["fact_id"],
                span_fact["fact_id"],
            ],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "confidence": 0.9,
        }],
        [
            log_fact["fact_id"],
            flow_fact["fact_id"],
            span_fact["fact_id"],
        ],
    )
    claim.update({
        "unknowns": [
            "没有 orders-api 的有效日志事实；"
            "该查询 ledger 为空且 truncated。",
            (
                f'未提供与 DeepFlow trace_id="{trace_id}" '
                "完全匹配的 Tempo span。"
            ),
            (
                f'未提供与 DeepFlow trace_id="{other_trace_id}" '
                "完全匹配的 Tempo span。"
            ),
            "orders-api 日志中的时间戳未知。",
        ],
        "evidence_analysis": [{
            "evidence_id": flow_fact["fact_id"],
            "raw_data": f"trace_id={trace_id}",
            "interpretation": (
                f"当前没有同 trace_id={trace_id} 的 Tempo span 事实；"
                "当前采样不能证明完整端到端调用链。"
            ),
        }],
    })

    result = validate_rca_claims(claim, [ledger])
    serialized = json.dumps(result, ensure_ascii=False)

    assert "有效日志事实" not in serialized
    assert "ledger 为空且 truncated" not in serialized
    assert f'trace_id="{trace_id}"' not in serialized
    assert any(
        other_trace_id in item
        for item in result["unknowns"]
    )
    assert "日志中的时间戳未知" in serialized
    assert "当前采样不能证明完整端到端调用链" in serialized
