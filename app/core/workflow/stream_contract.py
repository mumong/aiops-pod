"""Live stream contract for scoped parallel-evidence tool events."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel

from app.core.workflow.fact_contract import OBSERVABILITY_QUERY_TOOL_DIMENSIONS
from app.core.workflow.schemas import GroupEntity


PARALLEL_EVIDENCE_STREAM_CONTRACT_VERSION = "aiops.parallel-evidence-stream.v1"


class ParallelEvidenceStreamContext(BaseModel):
    """Validated, compact identity attached to a parallel tool event."""

    contract_version: str = PARALLEL_EVIDENCE_STREAM_CONTRACT_VERSION
    group_id: str
    entity: GroupEntity | None = None
    dimension: str
    source_system: str | None = None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _entity_identity(value: Mapping[str, Any]) -> tuple[str, str, str] | None:
    kind = str(value.get("kind") or "Pod").strip()
    namespace = str(value.get("namespace") or "").strip()
    name = str(value.get("name") or value.get("pod") or "").strip()
    if not namespace or not name:
        return None
    return kind.lower(), namespace, name


def _candidate_entities(event: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    structured = _mapping(event.get("structured"))
    candidates = [
        _mapping(structured.get("entity")),
        _mapping(structured.get("primary_entity")),
    ]

    args = _mapping(event.get("tool_args"))
    namespace = str(args.get("namespace") or "").strip()
    name = str(
        args.get("pod")
        or args.get("pod_name")
        or args.get("name")
        or args.get("resource_name")
        or ""
    ).strip()
    if namespace and name:
        candidates.append({
            "kind": args.get("kind") or args.get("resource_kind") or "Pod",
            "namespace": namespace,
            "name": name,
        })
    return [candidate for candidate in candidates if candidate]


def _matching_group_entity(
    event: Mapping[str, Any],
    parallel_context: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    authoritative: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for raw_entity in parallel_context.get("entities") or []:
        entity = _mapping(raw_entity)
        identity = _entity_identity(entity)
        if identity:
            authoritative[identity] = entity

    for candidate in _candidate_entities(event):
        identity = _entity_identity(candidate)
        if identity and identity in authoritative:
            return authoritative[identity]
    return None


def _dimension(event: Mapping[str, Any]) -> str:
    structured = _mapping(event.get("structured"))
    explicit = str(structured.get("dimension") or "").strip().lower()
    if explicit:
        return explicit
    tool_name = str(event.get("tool_name") or "").strip().lower()
    if tool_name in OBSERVABILITY_QUERY_TOOL_DIMENSIONS:
        return OBSERVABILITY_QUERY_TOOL_DIMENSIONS[tool_name]
    if tool_name.startswith(("kubectl_", "kubernetes_")):
        return "kubernetes"
    return "other"


def build_parallel_evidence_stream_context(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Build validated stream identity from authoritative scoped group data."""
    parallel_context = _mapping(event.get("parallel_context"))
    group_id = str(parallel_context.get("group_id") or "").strip()
    if not group_id:
        return {}

    structured = _mapping(event.get("structured"))
    source_system = str(structured.get("source_system") or "").strip() or None
    context = ParallelEvidenceStreamContext(
        group_id=group_id,
        entity=_matching_group_entity(event, parallel_context),
        dimension=_dimension(event),
        source_system=source_system,
    )
    return context.model_dump(exclude_none=True)


def project_parallel_tool_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Project parallel-only fields into the public SSE thinking payload."""
    if not _mapping(event.get("parallel_context")):
        return {}

    projected: dict[str, Any] = {}
    lane_stage = str(event.get("lane_stage") or "").strip()
    if lane_stage:
        projected["lane_stage"] = lane_stage
    if event.get("type") not in {"tool_start", "tool_result"}:
        return projected

    context = build_parallel_evidence_stream_context(event)
    if not context:
        return projected

    projected["evidence_context"] = context
    for key in ("tool_call_id", "tool_sequence"):
        if event.get(key) is not None:
            projected[key] = event.get(key)

    if event.get("type") == "tool_result":
        for key in (
            "semantic_success",
            "result",
            "raw_ref",
            "structured_ref",
            "summary_ref",
        ):
            if event.get(key) is not None:
                projected[key] = event.get(key)
    return projected
