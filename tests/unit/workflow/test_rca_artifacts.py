import hashlib
import json

from app.core.skills.models import Layer
from app.core.workflow.entity_evidence_snapshot import build_entity_evidence_snapshot
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode


def _fact(entity_id="k8s.pod:demo/api:uid-a"):
    record = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "logging",
        "fact_type": "log",
        "attribute": "log.message",
        "value": {"message": "source-backed runtime observation"},
        "source_system": "elasticsearch",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["archive://logs/1"],
    }
    canonical = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    record["fact_id"] = (
        "fact-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    )
    return record


def _state(*, eligible=True):
    record = _fact()
    fact_id = record["fact_id"]
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "generic-runtime-observation",
        "scope_entity_ids": [record["entity_id"]],
        "records": [record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    return {
        "question": "What is wrong with this scoped entity?",
        "layer": Layer.L2,
        "layer_handoff": {"diagnosis_scope": "single_group"},
        "evidence_items": [],
        "evidence_analysis": json.dumps({
            "tool_data": [{
                "tool": "query_pod_logs",
                "semantic_success": True,
                "fact_ledger": ledger,
            }]
        }),
        "entity_evidence_snapshot": {
            "contract_version": "aiops.entity-evidence-snapshot.v1",
            "fact_index": {fact_id: record},
            "selection_manifest": {
                "eligible_support_fact_ids": [fact_id] if eligible else [],
                "required_context_fact_ids": [],
                "rca_input_fact_ids": [fact_id] if eligible else [],
                "omitted_fact_ids": [] if eligible else [fact_id],
                "omission_reasons": (
                    {} if eligible else {fact_id: "not_support_eligible"}
                ),
            },
        },
        "thinking_events": [],
    }


def _valid_claim():
    record = _fact()
    return {
        "diagnostic_status": "diagnosed",
        "root_cause": "Evidence-backed candidate",
        "supporting_fact_ids": [record["fact_id"]],
        "hypotheses": [{
            "hypothesis_id": "hyp-1",
            "entity_id": record["entity_id"],
            "summary": "Evidence-backed candidate",
            "supporting_fact_ids": [record["fact_id"]],
            "confidence": 0.86,
        }],
        "causal_chain": {
            "trigger": "Evidence-backed cause",
            "mechanism": "Observed failure mechanism",
            "manifestation": "Scoped entity is abnormal",
        },
        "confidence": 0.86,
        "confidence_reason": "Direct source-backed fact",
    }


def _invalid_claim():
    claim = _valid_claim()
    claim["supporting_fact_ids"] = ["fact-ffffffffffff"]
    claim["hypotheses"][0]["supporting_fact_ids"] = ["fact-ffffffffffff"]
    return claim


def _configured_node(
    tmp_path,
    monkeypatch,
    outputs,
    *,
    validation_enabled=True,
):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    node = RootCauseAnalyzerNode()
    node.workflow_config_override = {
        "rca_validation": {"enabled": validation_enabled},
        "rca_context": {"fact_ledger_enabled": True},
        "rca_structured_output": {"schema": "full"},
    }
    node.current_run_id = "run-g1"
    node.ai_call = object()
    node._save_thinking = lambda state, new_state, thinking_events: None
    remaining = list(outputs)
    calls = []

    def analyze(question, layer, evidence_summary):
        calls.append(evidence_summary)
        return remaining.pop(0), []

    node._analyze_with_llm = analyze
    node.analysis_calls = calls
    return node


def test_rca_validation_disabled_keeps_first_model_result(
    tmp_path,
    monkeypatch,
):
    node = _configured_node(
        tmp_path,
        monkeypatch,
        [_invalid_claim(), _valid_claim()],
        validation_enabled=False,
    )

    result = node.execute(_state())
    rca = json.loads(result["rca_analysis"])

    assert len(node.analysis_calls) == 1
    assert rca["diagnostic_status"] == "diagnosed"
    assert rca["root_cause"] == "Evidence-backed candidate"
    assert rca["claim_validation"] == {
        "enabled": False,
        "skipped": True,
        "valid": None,
        "diagnostic_status": "diagnosed",
        "reasons": [
            "RCA fact binding and publication validation disabled by configuration"
        ],
    }


def test_rca_persists_input_model_output_validated_output_and_claim(
    tmp_path,
    monkeypatch,
):
    node = _configured_node(tmp_path, monkeypatch, [_valid_claim()])

    result = node.execute(_state())

    root = tmp_path / "run-g1"
    assert (root / "node_inputs/rca.input.json").exists()
    assert (root / "node_outputs/rca.attempt-1.model.json").exists()
    assert (root / "node_outputs/rca.attempt-1.validated.json").exists()
    assert (root / "node_outputs/rca.output.json").exists()
    assert (root / "node_outputs/claim_validation.output.json").exists()
    assert json.loads((root / "node_outputs/rca.output.json").read_text()) == (
        json.loads(result["rca_analysis"])
    )


def test_rca_repairs_once_when_invalid_output_has_eligible_support(
    tmp_path,
    monkeypatch,
):
    node = _configured_node(
        tmp_path,
        monkeypatch,
        [_invalid_claim(), _valid_claim()],
    )

    result = node.execute(_state())

    assert json.loads(result["rca_analysis"])["diagnostic_status"] == "diagnosed"
    assert len(node.analysis_calls) == 2
    assert "validation_reasons" in node.analysis_calls[1]


def test_rca_does_not_retry_source_absence_or_retry_more_than_once(
    tmp_path,
    monkeypatch,
):
    missing = _configured_node(
        tmp_path,
        monkeypatch,
        [_invalid_claim(), _valid_claim()],
    )
    missing.execute(_state(eligible=False))
    assert len(missing.analysis_calls) == 1

    twice = _configured_node(
        tmp_path,
        monkeypatch,
        [_invalid_claim(), _invalid_claim(), _valid_claim()],
    )
    result = twice.execute(_state())
    assert json.loads(result["rca_analysis"])["diagnostic_status"] == "inconclusive"
    assert len(twice.analysis_calls) == 2


def test_rca_repair_cannot_replace_a_better_first_attempt():
    first = {
        "diagnostic_status": "inconclusive",
        "phenomenon": "useful first-attempt phenomenon",
        "claim_validation": {
            "diagnosis_publishable": False,
            "valid_supporting_fact_ids": ["fact-a"],
        },
    }
    repaired = {
        "diagnostic_status": "inconclusive",
        "phenomenon": "worse repair",
        "claim_validation": {
            "diagnosis_publishable": False,
            "valid_supporting_fact_ids": [],
        },
    }

    selected = RootCauseAnalyzerNode._select_preferred_rca_result(
        first,
        repaired,
    )

    assert selected["phenomenon"] == "useful first-attempt phenomenon"


def test_single_path_builds_same_authoritative_snapshot_when_not_precomputed(
    tmp_path,
    monkeypatch,
):
    node = _configured_node(tmp_path, monkeypatch, [_valid_claim()])
    state = _state()
    state.pop("entity_evidence_snapshot")

    result = node.execute(state)

    snapshot = result["entity_evidence_snapshot"]
    assert snapshot["contract_version"] == "aiops.entity-evidence-snapshot.v1"
    assert snapshot["selection_manifest"]["eligible_support_fact_ids"]
    assert result["rca_input_projection"]["selection_manifest"] == (
        snapshot["selection_manifest"]
    )


def test_rca_projection_does_not_reexpand_sibling_lane_ledgers():
    target = _fact("k8s.pod:demo/api:uid-a")
    sibling = _fact("k8s.pod:other/worker:uid-b")
    sibling.update({
        "namespace": "other",
        "entity_name": "worker",
        "fact_id": "fact-sibling0001",
    })

    def ledger(case_id, record):
        return {
            "contract_version": "aiops.fact-ledger.v1",
            "case_id": case_id,
            "scope_entity_ids": [record["entity_id"]],
            "records": [record],
            "record_count": 1,
            "truncated": False,
            "source": "mcp_canonical",
            "legacy_contract": False,
        }

    evidence_analysis = {
        "tool_data": [
            {"fact_ledger": ledger("target", target)},
            {"fact_ledger": ledger("sibling", sibling)},
        ]
    }
    snapshot_model = build_entity_evidence_snapshot(
        entities=[{"kind": "Pod", "namespace": "demo", "name": "api"}],
        evidence_analysis=evidence_analysis,
        thinking_events=[],
    )
    assert len(snapshot_model.fact_ledgers) == 1
    assert snapshot_model.fact_ledgers[0].scope_entity_ids == [
        target["entity_id"]
    ]
    assert {
        record.entity_id
        for record in snapshot_model.fact_ledgers[0].records
    } == {target["entity_id"]}
    state = {
        "entity_evidence_snapshot": {
            "contract_version": "aiops.entity-evidence-snapshot.v1",
            "entities": [{"kind": "Pod", "namespace": "demo", "name": "api"}],
            "fact_ledgers": [ledger("target", target)],
            "fact_index": {target["fact_id"]: target},
            "selection_manifest": {
                "eligible_support_fact_ids": [target["fact_id"]],
                "required_context_fact_ids": [],
                "rca_input_fact_ids": [target["fact_id"]],
                "omitted_fact_ids": [],
                "omission_reasons": {},
            },
        }
    }

    projection = RootCauseAnalyzerNode()._build_rca_input_projection(
        state,
        evidence_analysis,
    )

    assert projection["authoritative_entity_ids"] == [target["entity_id"]]
    assert [fact["fact_id"] for fact in projection["selected_facts"]] == [
        target["fact_id"]
    ]
