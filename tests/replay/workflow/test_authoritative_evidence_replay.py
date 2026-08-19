import json
import re
from pathlib import Path

from app.core.skills.models import Layer
from app.core.workflow.entity_evidence_snapshot import (
    build_entity_evidence_snapshot,
)
from app.core.workflow.fact_contract import (
    _canonical_fact_id,
    validate_rca_claims,
)
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.parallel_evidence import ParallelEvidenceNode


FIXTURE_ROOT = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _replay_fixture():
    fixture = json.loads(
        (FIXTURE_ROOT / "generic_authoritative_lane.json").read_text(
            encoding="utf-8"
        )
    )
    entity_id = fixture["authoritative_entity_id"]
    records = []
    for raw in fixture["records"]:
        record = {
            **raw,
            "entity_id": entity_id,
            "entity_kind": "Pod",
            "namespace": fixture["entity"]["namespace"],
            "entity_name": fixture["entity"]["name"],
        }
        record["fact_id"] = _canonical_fact_id(record)
        records.append(record)
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "generic-retained-replay",
        "scope_entity_ids": [entity_id],
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    evidence_analysis = json.dumps({
        "tool_data": [{
            "tool": "generic_source_adapter",
            "semantic_success": True,
            "fact_ledger": ledger,
        }]
    })
    snapshot = build_entity_evidence_snapshot(
        entities=[fixture["entity"]],
        evidence_analysis=evidence_analysis,
        thinking_events=[],
    )
    manifest = snapshot.to_handoff()["selection_manifest"]
    supporting_ids = list(manifest["eligible_support_fact_ids"])
    claim = {
        "diagnostic_status": "diagnosed",
        "root_cause": "Generic evidence-backed source failure",
        "supporting_fact_ids": supporting_ids,
        "hypotheses": [{
            "hypothesis_id": "hyp-replay",
            "entity_id": fixture["model_entity_id"],
            "summary": "Generic evidence-backed source failure",
            "supporting_fact_ids": supporting_ids,
            "confidence": 0.84,
        }],
        "confidence": 0.84,
        "confidence_reason": "Direct canonical records",
    }
    selected_rca = validate_rca_claims(
        claim,
        [ledger],
        authoritative_entity_ids=[entity_id],
    )
    rca_input = {
        "authoritative_entity_ids": [entity_id],
        "selection_manifest": manifest,
        "selected_facts": [
            snapshot.fact_index[fact_id]
            for fact_id in manifest["rca_input_fact_ids"]
        ],
    }
    report = ConclusionFormatterNode().execute({
        "question": "Replay the retained lane",
        "layer": Layer.ABNORMAL,
        "rca_analysis": json.dumps(selected_rca),
        "rca_input_projection": rca_input,
        "thinking_events": [],
    })["conclusion"]
    return {
        "fixture": fixture,
        "snapshot": snapshot,
        "manifest": manifest,
        "selected_rca": selected_rca,
        "report": report,
        "final_fact_ids": set(re.findall(r"fact-[A-Za-z0-9_-]+", report)),
    }


def test_replay_preserves_decisive_facts_through_selected_rca_and_final():
    replay = _replay_fixture()

    eligible = set(replay["manifest"]["eligible_support_fact_ids"])
    assert eligible
    assert replay["selected_rca"]["claim_validation"]["valid"] is True
    assert set(replay["selected_rca"]["supporting_fact_ids"]) <= (
        replay["final_fact_ids"]
    )
    assert eligible <= set(replay["manifest"]["rca_input_fact_ids"])


def test_replay_model_uid_mutation_cannot_change_lane_identity():
    replay = _replay_fixture()
    authoritative = replay["fixture"]["authoritative_entity_id"]

    assert replay["selected_rca"]["hypotheses"][0]["entity_id"] == authoritative
    assert authoritative in replay["report"]
    assert replay["fixture"]["model_entity_id"] not in replay["report"]


def test_authoritative_policy_contains_no_fixture_specific_branches():
    fixture = json.loads(
        (FIXTURE_ROOT / "generic_authoritative_lane.json").read_text(
            encoding="utf-8"
        )
    )
    forbidden = {
        fixture["entity"]["namespace"],
        fixture["entity"]["name"],
        fixture["authoritative_entity_id"].rsplit(":", 1)[-1],
        "SourceRejectedOperation",
        "protocol_status\": 531",
    }
    policy_paths = [
        "app/core/workflow/entity_evidence_snapshot.py",
        "app/core/workflow/lane_diagnosis_artifact.py",
        "app/core/workflow/fact_contract.py",
        "app/core/workflow/group_evidence.py",
        "app/core/workflow/nodes/root_cause_analyzer.py",
        "app/core/workflow/nodes/parallel_evidence.py",
        "app/core/workflow/nodes/conclusion_formatter.py",
    ]
    production = "\n".join(
        (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for relative in policy_paths
    )

    assert not {identifier for identifier in forbidden if identifier in production}


def test_replay_gate_preserves_valid_rca_with_context_and_weak_extra_facts():
    """Exercise snapshot -> validation -> Gate without scenario knowledge."""
    entity_id = "k8s.pod:generic-scope/workload:uid-generic"
    base = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "generic-scope",
        "entity_name": "workload",
        "source_system": "generic-source",
        "strength": "strong",
        "evidence_refs": ["archive://generic/source"],
    }
    records = [
        {
            **base,
            "dimension": "kubernetes",
            "fact_type": "configuration",
            "attribute": "container.resources.limit",
            "value": "bounded-value",
            "directness": "direct",
            "confidence": "high",
            "metadata": {"evidence_role": "context"},
        },
        {
            **base,
            "dimension": "logging",
            "fact_type": "log",
            "attribute": "log.message",
            "value": "typed source failure",
            "directness": "direct",
            "confidence": "high",
            "metadata": {"evidence_role": "causal_candidate"},
        },
        {
            **base,
            "dimension": "topology",
            "fact_type": "relationship",
            "attribute": "topology.relationship",
            "value": "related neighbor",
            "directness": "related_context",
            "confidence": "weak",
            "metadata": {"evidence_role": "context"},
        },
    ]
    for record in records:
        record["fact_id"] = _canonical_fact_id(record)
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "generic-gate-replay",
        "scope_entity_ids": [entity_id],
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    evidence_analysis = json.dumps({
        "tool_data": [{"tool": "generic_source_adapter", "fact_ledger": ledger}]
    })
    snapshot = build_entity_evidence_snapshot(
        entities=[{
            "kind": "Pod",
            "namespace": "generic-scope",
            "name": "workload",
        }],
        evidence_analysis=evidence_analysis,
        thinking_events=[],
    ).to_handoff()
    causal_id = records[1]["fact_id"]
    weak_id = records[2]["fact_id"]
    validated = validate_rca_claims(
        {
            "diagnostic_status": "diagnosed",
            "root_cause": "Typed source failure",
            "supporting_fact_ids": [causal_id, weak_id],
            "hypotheses": [{
                "hypothesis_id": "hyp-generic",
                "entity_id": entity_id,
                "summary": "Typed source failure",
                "supporting_fact_ids": [causal_id, weak_id],
                "confidence": 0.86,
            }],
            "confidence": 0.86,
            "confidence_reason": "Direct canonical source record",
        },
        [ledger],
        authoritative_entity_ids=[entity_id],
    )
    gate = ParallelEvidenceNode()._minimum_rca_gate(
        {"entity_evidence_snapshot": snapshot},
        {"rca_analysis": json.dumps(validated)},
    )

    assert snapshot["fact_index"][records[0]["fact_id"]][
        "evidence_role"
    ] == "context"
    assert validated["diagnostic_status"] == "diagnosed"
    assert validated["claim_validation"]["valid"] is False
    assert validated["claim_validation"]["diagnosis_supported"] is True
    assert validated["supporting_fact_ids"] == [causal_id]
    assert gate["verdict"] == "pass"
