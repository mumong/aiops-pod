import json

import pytest

from app.core.workflow.lane_diagnosis_artifact import (
    LaneArtifactIntegrityError,
    LaneDiagnosisArtifactWriter,
)


def _persist_artifact(
    tmp_path,
    monkeypatch,
    *,
    terminal_status="inconclusive",
    terminal_error=None,
    selected_rca=None,
    claim_validation=None,
    final_projection=None,
):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    writer = LaneDiagnosisArtifactWriter("run-g1")
    diagnostic_status = (
        "diagnosed" if terminal_status == "diagnosed" else "inconclusive"
    )
    artifact = writer.persist(
        group_id="g1",
        parent_group_id="g1",
        presentation_index=0,
        authoritative_entities=[
            {
                "kind": "Pod",
                "namespace": "demo",
                "name": "api",
                "uid": "uid-api",
                "entity_id": "k8s.pod:demo/api:uid-api",
            }
        ],
        snapshot={"contract_version": "aiops.entity-evidence-snapshot.v1"},
        selection_manifest={"rca_input_fact_ids": []},
        rca_input={"fact_ledgers": []},
        rca_attempts=[],
        selected_rca=(
            selected_rca
            if selected_rca is not None
            else {"diagnostic_status": diagnostic_status}
        ),
        claim_validation=(
            claim_validation
            if claim_validation is not None
            else {
                "valid": terminal_status == "diagnosed",
                "reference_valid": terminal_status == "diagnosed",
                "diagnosis_supported": terminal_status == "diagnosed",
                "diagnosis_publishable": terminal_status == "diagnosed",
            }
        ),
        final_projection=(
            final_projection
            if final_projection is not None
            else {
                "terminal_status": terminal_status,
                "diagnostic_status": diagnostic_status,
            }
        ),
        terminal_error=terminal_error or {},
        terminal_status=terminal_status,
    )
    return writer, artifact


def _rebind_artifact(writer, artifact, *, replacements=None, extra_refs=None):
    rebound = json.loads(json.dumps(artifact))
    rebound.pop("artifact_ref", None)
    for name, value in (replacements or {}).items():
        rebound["artifact_refs"][name] = writer.archive.write_json_atomic(
            f"lane_artifacts/g1/{name}.json",
            value,
        )
    rebound["artifact_refs"].update(extra_refs or {})
    rebound["artifact_ref"] = writer.archive.write_json_atomic(
        "lane_artifacts/g1/artifact.json",
        rebound,
    )
    return rebound


def test_lane_artifact_round_trip_verifies_every_hash(tmp_path, monkeypatch):
    writer, artifact = _persist_artifact(tmp_path, monkeypatch)

    loaded = writer.reload_and_verify(artifact)

    assert loaded["snapshot"]["contract_version"] == (
        "aiops.entity-evidence-snapshot.v1"
    )
    assert all(ref["sha256"] for ref in artifact["artifact_refs"].values())
    assert artifact["terminal_status"] == "inconclusive"


def test_lane_artifact_allows_reference_valid_inconclusive_terminal(
    tmp_path,
    monkeypatch,
):
    writer, artifact = _persist_artifact(
        tmp_path,
        monkeypatch,
        terminal_status="inconclusive",
        claim_validation={
            "valid": True,
            "reference_valid": True,
            "diagnosis_supported": False,
            "diagnosis_publishable": False,
        },
    )

    loaded = writer.reload_and_verify(artifact)

    assert loaded["claim_validation"]["reference_valid"] is True
    assert loaded["claim_validation"]["diagnosis_publishable"] is False


def test_lane_artifact_allows_publishable_diagnosis_with_audited_bad_reference(
    tmp_path,
    monkeypatch,
):
    writer, artifact = _persist_artifact(
        tmp_path,
        monkeypatch,
        terminal_status="diagnosed",
        claim_validation={
            "valid": False,
            "reference_valid": False,
            "diagnosis_supported": True,
            "diagnosis_publishable": True,
            "invalid_fact_ids": ["fact-ffffffffffff"],
        },
    )

    loaded = writer.reload_and_verify(artifact)

    assert loaded["artifact"]["terminal_status"] == "diagnosed"
    assert loaded["claim_validation"]["reference_valid"] is False
    assert loaded["claim_validation"]["diagnosis_publishable"] is True


def test_lane_artifact_allows_diagnosis_when_validation_is_explicitly_disabled(
    tmp_path,
    monkeypatch,
):
    writer, artifact = _persist_artifact(
        tmp_path,
        monkeypatch,
        terminal_status="diagnosed",
        selected_rca={
            "diagnostic_status": "diagnosed",
            "root_cause": "model selected root cause",
            "supporting_fact_ids": [],
        },
        claim_validation={
            "enabled": False,
            "skipped": True,
            "valid": None,
        },
    )

    loaded = writer.reload_and_verify(artifact)

    assert loaded["artifact"]["terminal_status"] == "diagnosed"
    assert loaded["claim_validation"]["enabled"] is False


def test_lane_artifact_reload_rejects_digest_mismatch(tmp_path, monkeypatch):
    writer, artifact = _persist_artifact(tmp_path, monkeypatch)
    snapshot_path = artifact["artifact_refs"]["snapshot"]["path"]
    with open(snapshot_path, "w", encoding="utf-8") as handle:
        json.dump({"contract_version": "tampered"}, handle)

    with pytest.raises(LaneArtifactIntegrityError, match="digest mismatch"):
        writer.reload_and_verify(artifact)


@pytest.mark.parametrize("terminal_status", ["diagnosed", "inconclusive", "error"])
def test_lane_artifact_v2_terminal_states_persist_complete_component_set(
    tmp_path,
    monkeypatch,
    terminal_status,
):
    terminal_error = (
        {"stage": "lane_execution", "message": "worker exploded"}
        if terminal_status == "error"
        else {}
    )
    writer, artifact = _persist_artifact(
        tmp_path,
        monkeypatch,
        terminal_status=terminal_status,
        terminal_error=terminal_error,
    )

    expected_components = {
        "snapshot",
        "selection_manifest",
        "rca_input",
        "rca_attempts",
        "selected_rca",
        "claim_validation",
        "final_projection",
        "terminal_error",
    }
    assert artifact["contract_version"] == "aiops.lane-diagnosis-artifact.v2"
    assert artifact["terminal_status"] == terminal_status
    assert set(artifact["artifact_refs"]) == expected_components
    assert all(ref["sha256"] and ref["bytes"] > 0 for ref in artifact["artifact_refs"].values())

    loaded = writer.reload_and_verify(artifact)

    assert expected_components <= set(loaded)
    assert loaded["terminal_error"] == terminal_error
    expected_diagnostic_status = (
        "diagnosed" if terminal_status == "diagnosed" else "inconclusive"
    )
    assert loaded["selected_rca"]["diagnostic_status"] == (
        expected_diagnostic_status
    )
    assert loaded["claim_validation"]["valid"] is (
        terminal_status == "diagnosed"
    )
    assert loaded["final_projection"]["terminal_status"] == terminal_status


@pytest.mark.parametrize("boundary", ["persist", "reload"])
def test_lane_artifact_error_terminal_rejects_diagnosed_publication_signals(
    tmp_path,
    monkeypatch,
    boundary,
):
    contradictory = {
        "selected_rca": {"diagnostic_status": "diagnosed"},
        "claim_validation": {"valid": True},
        "final_projection": {
            "terminal_status": "error",
            "diagnostic_status": "diagnosed",
        },
    }
    terminal_error = {"stage": "rca", "message": "worker exploded"}

    if boundary == "persist":
        with pytest.raises(ValueError, match="cross-component"):
            _persist_artifact(
                tmp_path,
                monkeypatch,
                terminal_status="error",
                terminal_error=terminal_error,
                **contradictory,
            )
        return

    writer, artifact = _persist_artifact(
        tmp_path,
        monkeypatch,
        terminal_status="error",
        terminal_error=terminal_error,
    )
    artifact = _rebind_artifact(
        writer,
        artifact,
        replacements=contradictory,
    )

    with pytest.raises(LaneArtifactIntegrityError, match="cross-component"):
        writer.reload_and_verify(artifact)


def test_lane_artifact_terminal_reload_rejects_ninth_component_ref(
    tmp_path,
    monkeypatch,
):
    writer, artifact = _persist_artifact(tmp_path, monkeypatch)
    artifact = _rebind_artifact(
        writer,
        artifact,
        extra_refs={
            "rogue": {
                "path": "/etc/hosts",
                "sha256": "0" * 64,
                "bytes": 1,
            },
        },
    )

    with pytest.raises(LaneArtifactIntegrityError, match="component refs"):
        writer.reload_and_verify(artifact)


def test_lane_artifact_terminal_reload_rejects_byte_size_mismatch(
    tmp_path,
    monkeypatch,
):
    writer, artifact = _persist_artifact(tmp_path, monkeypatch)
    artifact_without_envelope = json.loads(json.dumps(artifact))
    artifact_without_envelope.pop("artifact_ref")
    artifact_without_envelope["artifact_refs"]["snapshot"]["bytes"] += 1

    with pytest.raises(LaneArtifactIntegrityError, match="byte-size mismatch"):
        writer.reload_and_verify(artifact_without_envelope)


def test_lane_artifact_backward_reloads_v1_archive(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    writer = LaneDiagnosisArtifactWriter("run-v1")
    components = {
        "snapshot": {"contract_version": "aiops.entity-evidence-snapshot.v1"},
        "rca_input": {"fact_ledgers": []},
        "rca_attempts": [],
        "selected_rca": {"diagnostic_status": "inconclusive"},
        "claim_validation": {"valid": False},
        "final_projection": {"diagnostic_status": "inconclusive"},
    }
    refs = {
        name: writer.archive.write_json_atomic(
            f"lane_artifacts/g1-v1/{name}.json",
            value,
        )
        for name, value in components.items()
    }
    envelope = {
        "contract_version": "aiops.lane-diagnosis-artifact.v1",
        "group_id": "g1",
        "parent_group_id": "g1",
        "presentation_index": 0,
        "authoritative_entities": [],
        "artifact_refs": refs,
        "diagnostic_status": "inconclusive",
    }
    envelope["artifact_ref"] = writer.archive.write_json_atomic(
        "lane_artifacts/g1-v1/artifact.json",
        envelope,
    )

    loaded = writer.reload_and_verify(envelope)

    assert loaded["artifact"]["contract_version"] == (
        "aiops.lane-diagnosis-artifact.v1"
    )
    assert loaded["selected_rca"]["diagnostic_status"] == "inconclusive"
