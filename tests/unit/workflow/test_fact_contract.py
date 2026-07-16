import hashlib
import json

import pytest

from app.core.prompts import ROOT_CAUSE_ANALYZER_PROMPT
from app.core.workflow.fact_contract import (
    bounded_json_dumps,
    compact_fact_ledgers_json,
    extract_fact_ledgers_from_tool_data,
    normalize_case_fact_ledger,
    normalize_fact_ledger,
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
