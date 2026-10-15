"""Explicit consumer projections; persistent state is not model context."""

from copy import deepcopy

from app.core.workflow.diagnosis_contract import scoped_handoff
from app.core.workflow.working_material import build_working_material


def location_seed(handoff):
    """Only selected targets; never rediscover anomalies from source Pod phase."""
    handoff = handoff or {}
    targets = []
    for target in handoff.get("targets") or []:
        refs = list(target.get("evidence_refs") or [])
        # Compatibility with persisted diagnosis-handoff.v1 location records.
        for fact in target.get("facts") or []:
            refs.extend(fact.get("evidence_refs") or [])
        targets.append(
            {
                k: deepcopy(target[k])
                for k in ("target_id", "entity", "issue", "status", "status_reason")
                if k in target
            }
        )
        targets[-1]["evidence_refs"] = list(dict.fromkeys(refs))
    return {
        "contract_version": "location-handoff.v1",
        "targets": targets,
        "coverage": handoff.get("coverage", "unknown"),
        "coverage_note": handoff.get("coverage_note", ""),
    }


def branch_state(state, group):
    """New worker inherits identity and source handles, not parent history."""
    local = {
        key: deepcopy(state[key])
        for key in (
            "original_question",
            "request_time_utc",
            "run_id",
            "request_contract",
            "diagnosis_context_policy",
        )
        if key in state
    }
    local["original_question"] = state.get("original_question") or state.get("question", "")
    local["question"] = group.get("question", "")
    local["diagnosis_target"] = deepcopy(group)
    local["diagnosis_target"].setdefault("target_id", group["group_id"])
    if state.get("diagnosis_handoff") and group.get("target_id"):
        local["diagnosis_handoff"] = location_seed(
            scoped_handoff(state["diagnosis_handoff"], group["target_id"])
        )
    else:
        # Historical groups already have assigned entities; do not extract new
        # targets from prose or inherit the parent's unbounded tool history.
        local["diagnosis_handoff"] = location_seed(
            {
                "targets": [
                    {
                        "target_id": group.get("target_id") or group["group_id"],
                        "entity": entity,
                        "issue": group.get("question", ""),
                        "status": "investigate",
                    }
                    for entity in group.get("entities") or []
                ]
            }
        )
    local["thinking_events"] = []
    local["diagnosis_events_start"] = 0
    local["autonomous_groups"] = []
    local["autonomous_group_results"] = []
    return local


def stage_material(state, stage):
    """Location can inspect the fleet; evidence/RCA see only their work stream.

    Non-core text and own tool results remain available to ordinary compaction.
    No lifecycle reconstruction or sibling histories enter protected handoff.
    """
    if stage == "layer":
        return build_working_material({**state, "diagnosis_context_policy": "identity.v1"})
    events = (state.get("thinking_events") or [])[state.get("diagnosis_events_start", 0) :]
    local = {
        **state,
        "thinking_events": events,
        "diagnosis_context_policy": "identity.v1",
        "autonomous_group_results": [],
        "autonomous_groups": [],
        "query_session_context": None,
    }
    if stage == "evidence":
        local["query_draft"] = ""
    material = build_working_material(local)
    protected = {
        "context_policy": "stage.v1",
        "diagnosis_handoff": location_seed(state.get("diagnosis_handoff")),
    }
    if stage == "rca" and state.get("diagnosis_evidence_handoff"):
        protected["evidence_handoff"] = deepcopy(state["diagnosis_evidence_handoff"])
    return {
        "question": state.get("original_question") or state.get("question", ""),
        "task": state.get("question", ""),
        "group_id": (state.get("diagnosis_target") or {}).get("group_id"),
        "request_contract": deepcopy(state.get("request_contract")),
        "request_time_utc": material["request_time_utc"],
        "protected_handoff": protected,
        "shared_runbooks": deepcopy(state.get("shared_runbooks") or []),
        "analysis_draft": material.get("analysis_draft", ""),
        "working_summary": material.get("working_summary"),
        "recent_interactions": material.get("recent_interactions") or [],
        "observations": material.get("observations") or [],
        "execution_incomplete": material.get("execution_incomplete") or [],
    }
