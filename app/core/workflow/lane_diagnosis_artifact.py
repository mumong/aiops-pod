"""Durable authoritative artifact contract for one diagnosis lane."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Literal, Mapping

from pydantic import BaseModel, Field, model_validator

from app.core.context.archive import ContextArchive


LANE_DIAGNOSIS_CONTRACT_VERSION = "aiops.lane-diagnosis-artifact.v2"
_V1_CONTRACT_VERSION = "aiops.lane-diagnosis-artifact.v1"


class LaneArtifactIntegrityError(ValueError):
    """Raised when a persisted lane component cannot be trusted."""


class LaneArtifactRef(BaseModel):
    path: str
    sha256: str = Field(min_length=64, max_length=64)
    bytes: int = Field(ge=0)


class LaneDiagnosisArtifact(BaseModel):
    contract_version: Literal[
        "aiops.lane-diagnosis-artifact.v1",
        "aiops.lane-diagnosis-artifact.v2",
    ] = (
        LANE_DIAGNOSIS_CONTRACT_VERSION
    )
    group_id: str
    parent_group_id: str
    presentation_index: int = Field(ge=0)
    authoritative_entities: list[Dict[str, Any]]
    artifact_refs: Dict[str, LaneArtifactRef]
    terminal_status: Literal["diagnosed", "inconclusive", "error"] | None = None
    diagnostic_status: Literal["diagnosed", "inconclusive"] | None = None
    artifact_ref: LaneArtifactRef | None = None

    @model_validator(mode="after")
    def _require_version_status(self) -> "LaneDiagnosisArtifact":
        if self.contract_version == _V1_CONTRACT_VERSION:
            if self.diagnostic_status is None:
                raise ValueError("v1 lane artifact requires diagnostic_status")
        elif self.terminal_status is None:
            raise ValueError("v2 lane artifact requires terminal_status")
        return self


class LaneDiagnosisArtifactWriter:
    """Persist and integrity-check the complete state of one diagnosis lane."""

    _V1_COMPONENTS = (
        "snapshot",
        "rca_input",
        "rca_attempts",
        "selected_rca",
        "claim_validation",
        "final_projection",
    )
    _V2_COMPONENTS = (
        "snapshot",
        "selection_manifest",
        "rca_input",
        "rca_attempts",
        "selected_rca",
        "claim_validation",
        "final_projection",
        "terminal_error",
    )

    def __init__(self, run_id: str):
        self.archive = ContextArchive(run_id=run_id)

    def persist(
        self,
        *,
        group_id: str,
        parent_group_id: str,
        presentation_index: int,
        authoritative_entities: list[Dict[str, Any]],
        snapshot: Mapping[str, Any],
        selection_manifest: Mapping[str, Any],
        rca_input: Mapping[str, Any],
        rca_attempts: list[Any],
        selected_rca: Mapping[str, Any],
        claim_validation: Mapping[str, Any],
        final_projection: Mapping[str, Any],
        terminal_error: Mapping[str, Any],
        terminal_status: Literal["diagnosed", "inconclusive", "error"],
    ) -> Dict[str, Any]:
        safe_group = self._safe_component(group_id)
        base = f"lane_artifacts/{safe_group}"
        values: Dict[str, Any] = {
            "snapshot": dict(snapshot),
            "selection_manifest": dict(selection_manifest),
            "rca_input": dict(rca_input),
            "rca_attempts": list(rca_attempts),
            "selected_rca": dict(selected_rca),
            "claim_validation": dict(claim_validation),
            "final_projection": dict(final_projection),
            "terminal_error": dict(terminal_error),
        }
        self._validate_cross_component_consistency(
            contract_version=LANE_DIAGNOSIS_CONTRACT_VERSION,
            terminal_status=terminal_status,
            components=values,
        )
        refs = {
            name: self.archive.write_json_atomic(f"{base}/{name}.json", value)
            for name, value in values.items()
        }
        envelope = LaneDiagnosisArtifact(
            group_id=group_id,
            parent_group_id=parent_group_id,
            presentation_index=presentation_index,
            authoritative_entities=authoritative_entities,
            artifact_refs=refs,
            terminal_status=terminal_status,
        )
        envelope_payload = envelope.model_dump(mode="json", exclude_none=True)
        envelope_ref = self.archive.write_json_atomic(
            f"{base}/artifact.json",
            envelope_payload,
        )
        return envelope.model_copy(
            update={"artifact_ref": LaneArtifactRef.model_validate(envelope_ref)}
        ).model_dump(mode="json", exclude_none=True)

    def reload_and_verify(
        self,
        artifact: Mapping[str, Any] | LaneDiagnosisArtifact,
    ) -> Dict[str, Any]:
        try:
            envelope = (
                artifact
                if isinstance(artifact, LaneDiagnosisArtifact)
                else LaneDiagnosisArtifact.model_validate(artifact)
            )
        except Exception as exc:
            raise LaneArtifactIntegrityError(
                f"invalid lane artifact contract: {exc}"
            ) from exc

        if envelope.artifact_ref is not None:
            persisted_envelope = self._read_verified_json(envelope.artifact_ref)
            try:
                persisted_model = LaneDiagnosisArtifact.model_validate(
                    persisted_envelope
                )
            except Exception as exc:
                raise LaneArtifactIntegrityError(
                    f"persisted lane artifact contract mismatch: {exc}"
                ) from exc
            expected = envelope.model_dump(mode="json", exclude={"artifact_ref"})
            actual = persisted_model.model_dump(
                mode="json", exclude={"artifact_ref"}
            )
            if actual != expected:
                raise LaneArtifactIntegrityError("persisted lane artifact mismatch")

        components = (
            self._V1_COMPONENTS
            if envelope.contract_version == _V1_CONTRACT_VERSION
            else self._V2_COMPONENTS
        )
        expected_refs = set(components)
        declared_refs = set(envelope.artifact_refs)
        if declared_refs != expected_refs:
            missing = sorted(expected_refs - declared_refs)
            extra = sorted(declared_refs - expected_refs)
            raise LaneArtifactIntegrityError(
                "lane artifact component refs do not match contract: "
                f"missing={missing}, extra={extra}"
            )
        loaded = {
            name: self._read_verified_json(envelope.artifact_refs[name])
            for name in components
        }
        try:
            self._validate_cross_component_consistency(
                contract_version=envelope.contract_version,
                terminal_status=envelope.terminal_status,
                components=loaded,
            )
        except ValueError as exc:
            raise LaneArtifactIntegrityError(str(exc)) from exc
        loaded["artifact"] = envelope.model_dump(mode="json", exclude_none=True)
        return loaded

    @staticmethod
    def _validate_cross_component_consistency(
        *,
        contract_version: str,
        terminal_status: str | None,
        components: Mapping[str, Any],
    ) -> None:
        """Reject a hash-valid v2 envelope whose terminal signals disagree."""
        if contract_version == _V1_CONTRACT_VERSION:
            return

        named_components: Dict[str, Mapping[str, Any]] = {}
        for name in (
            "selected_rca",
            "claim_validation",
            "final_projection",
            "terminal_error",
        ):
            value = components.get(name)
            if not isinstance(value, Mapping):
                raise ValueError(
                    "lane artifact cross-component mismatch: "
                    f"{name} must be an object"
                )
            named_components[name] = value

        selected_rca = named_components["selected_rca"]
        claim_validation = named_components["claim_validation"]
        final_projection = named_components["final_projection"]
        terminal_error = named_components["terminal_error"]
        expected_diagnostic_status = (
            "diagnosed" if terminal_status == "diagnosed" else "inconclusive"
        )

        selected_status = str(
            selected_rca.get("diagnostic_status") or ""
        ).lower()
        if selected_status and selected_status != expected_diagnostic_status:
            raise ValueError(
                "lane artifact cross-component mismatch: selected_rca "
                f"diagnostic_status={selected_status!r} conflicts with "
                f"terminal_status={terminal_status!r}"
            )

        final_terminal_status = str(
            final_projection.get("terminal_status") or ""
        ).lower()
        if final_terminal_status and final_terminal_status != terminal_status:
            raise ValueError(
                "lane artifact cross-component mismatch: final_projection "
                f"terminal_status={final_terminal_status!r} conflicts with "
                f"terminal_status={terminal_status!r}"
            )
        final_diagnostic_status = str(
            final_projection.get("diagnostic_status") or ""
        ).lower()
        if (
            final_diagnostic_status
            and final_diagnostic_status != expected_diagnostic_status
        ):
            raise ValueError(
                "lane artifact cross-component mismatch: final_projection "
                f"diagnostic_status={final_diagnostic_status!r} conflicts with "
                f"terminal_status={terminal_status!r}"
            )

        reference_valid = claim_validation.get(
            "reference_valid",
            claim_validation.get("valid"),
        )
        diagnosis_publishable = claim_validation.get(
            "diagnosis_publishable",
            claim_validation.get("diagnosis_supported"),
        )
        validation_disabled = claim_validation.get("enabled") is False
        # Artifacts written before the semantic split only carried `valid`.
        # Preserve their diagnosed-path meaning while new artifacts use the
        # explicit publication signal.
        if diagnosis_publishable is None and terminal_status == "diagnosed":
            diagnosis_publishable = reference_valid
        if (
            terminal_status == "diagnosed"
            and not validation_disabled
            and diagnosis_publishable is not True
        ):
            raise ValueError(
                "lane artifact cross-component mismatch: diagnosed terminal "
                "requires claim_validation.diagnosis_publishable=true"
            )
        if (
            terminal_status != "diagnosed"
            and not validation_disabled
            and diagnosis_publishable is True
        ):
            raise ValueError(
                "lane artifact cross-component mismatch: non-diagnosed terminal "
                "cannot publish claim_validation.diagnosis_publishable=true"
            )

        if terminal_status == "error":
            stage = str(terminal_error.get("stage") or "").strip()
            message = str(terminal_error.get("message") or "").strip()
            if not stage or not message:
                raise ValueError(
                    "lane artifact cross-component mismatch: error terminal "
                    "requires terminal_error stage and message"
                )
        elif terminal_error:
            raise ValueError(
                "lane artifact cross-component mismatch: non-error terminal "
                "cannot publish terminal_error"
            )

    def _read_verified_json(self, reference: LaneArtifactRef) -> Any:
        path = Path(reference.path)
        root = self.archive.root.resolve()
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError as exc:
            raise LaneArtifactIntegrityError(
                f"lane artifact file is missing: {path}"
            ) from exc
        if resolved != root and root not in resolved.parents:
            raise LaneArtifactIntegrityError(
                f"lane artifact path is outside archive root: {path}"
            )
        payload = resolved.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != reference.sha256:
            raise LaneArtifactIntegrityError(
                f"lane artifact digest mismatch: {path}"
            )
        if len(payload) != reference.bytes:
            raise LaneArtifactIntegrityError(
                f"lane artifact byte-size mismatch: {path}"
            )
        try:
            return json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LaneArtifactIntegrityError(
                f"lane artifact is not valid JSON: {path}"
            ) from exc

    @staticmethod
    def _safe_component(value: str) -> str:
        safe = "".join(
            character
            if character.isascii() and (character.isalnum() or character in "_.-")
            else "_"
            for character in str(value or "").strip()
        )
        return safe[:120] or "unknown"
