import hashlib
import json

import pytest
from pydantic import ValidationError

from app.core.workflow.fact_contract import (
    normalize_fact_ledger,
)
from app.core.workflow.schemas import FactRecord


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


def test_fact_record_preserves_nonblank_source_system():
    entity_id = "k8s.pod:demo/api:uid-a"
    payload = _fact("source-preserved", entity_id)
    payload["source_system"] = "kubernetes"

    record = FactRecord.model_validate(payload)

    assert record.source_system == "kubernetes"


def test_fact_record_strips_nonblank_source_system():
    entity_id = "k8s.pod:demo/api:uid-a"
    payload = _fact("source-stripped", entity_id)
    payload["source_system"] = "  kubernetes  "

    record = FactRecord.model_validate(payload)

    assert record.source_system == "kubernetes"


def test_fact_record_rejects_whitespace_only_source_system():
    entity_id = "k8s.pod:demo/api:uid-a"
    payload = _fact("source-blank", entity_id)
    payload["source_system"] = "   "

    with pytest.raises(
        ValidationError,
        match="source_system must not be blank",
    ):
        FactRecord.model_validate(payload)


def test_normalize_fact_ledger_keeps_id_built_from_stripped_source():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("source-canonical-after-strip", entity_id)
    record["source_system"] = "  kubernetes  "
    record["fact_id"] = _canonical_fact_id({
        **record,
        "source_system": "kubernetes",
    })

    ledger = normalize_fact_ledger(
        _ledger(
            "case-source-canonical-after-strip",
            entity_id,
            [record],
            source="robusta_legacy_adapter",
            legacy_contract=True,
        )
    )

    assert ledger is not None
    assert ledger.record_count == 1
    assert ledger.records[0].fact_id == record["fact_id"]
    assert ledger.records[0].source_system == "kubernetes"


def test_normalize_fact_ledger_drops_id_built_from_unstripped_source():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = _fact("source-canonical-before-strip", entity_id)
    record["source_system"] = "  kubernetes  "
    record["fact_id"] = _canonical_fact_id(record)

    ledger = normalize_fact_ledger(
        _ledger(
            "case-source-canonical-before-strip",
            entity_id,
            [record],
            source="robusta_legacy_adapter",
            legacy_contract=True,
        )
    )

    assert ledger is not None
    assert ledger.records == []
    assert ledger.record_count == 0


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

