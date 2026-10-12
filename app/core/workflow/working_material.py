"""Pure projections for shared evidence and the latest working context."""

from datetime import datetime, timezone
from app.core.context.handoff import shared_runbook_projection, project_shared_messages


def evidence_receipts(events):
    """Small acquisition inventory, never a semantic proof or diagnosis gate."""
    receipts = {}
    dimensions = {
        "execute_pod_promql": "metrics",
        "query_pod_logs": "logging",
        "query_pod_tracing": "tracing",
        "query_pod_topology": "topology",
        "fetch_runbook": "runbook",
    }
    for event in events:
        name = event.get("tool_name")
        if event.get("type") != "tool_result" or name not in dimensions:
            continue
        args = event.get("tool_args") or {}
        structured = event.get("structured") or {}
        item = {
            "tool": name,
            "dimension": dimensions[name],
            "namespace": args.get("namespace"),
            "pod": args.get("pod"),
            "runbook_id": args.get("runbook_id"),
            "status": event.get("status"),
            "semantic_success": event.get("semantic_success"),
            "coverage": structured.get("coverage"),
            "raw_ref": event.get("raw_ref"),
            "group_id": event.get("lane_id"),
            "observed_at": event.get("timestamp"),
        }
        # Keep latest reference per acquisition outcome, not the full result or
        # an ever-growing duplicate of every query. Failures and empties differ.
        key = tuple(
            item[k]
            for k in ("tool", "namespace", "pod", "runbook_id", "status", "coverage", "group_id")
        )
        receipts[key] = {k: v for k, v in item.items() if v is not None}
    return list(receipts.values())


def build_working_material(state):
    """Carry the user task and only the latest working evidence representation."""
    events = [e for e in state.get("thinking_events") or [] if not e.get("lane_id")]
    last_compaction = next(
        (
            i
            for i in range(len(events) - 1, -1, -1)
            if events[i].get("type") == "context_compacted"
        ),
        -1,
    )
    shared = state.get("shared_runbooks") or []
    shared_refs = {item["raw_ref"] for item in shared if item.get("raw_ref")}
    from app.core.context.lifecycle_core import core_from_material, observation_reference, material_without_core
    protected = dict(events[last_compaction].get('protected_handoff') or {}) if last_compaction >= 0 else {}
    if state.get('diagnosis_handoff') is not None:
        protected['diagnosis_handoff'] = state['diagnosis_handoff']
    light = (state.get('diagnosis_context_policy') == 'identity.v1'
             or (state.get('diagnosis_handoff') or {}).get('contract_version') == 'location-handoff.v1')
    legacy_core = protected.pop('lifecycle_core', None) if light else None
    if light:
        protected['context_policy'] = 'identity.v1'
    core = {} if light else core_from_material({'protected_handoff': protected,
                              'observations': [e for e in events if e.get('type') == 'tool_result'],
                              'parallel_results': state.get('autonomous_group_results') or []})
    if core:
        protected['lifecycle_core'] = core
    return {
        "question": state.get("question", "")
        if state.get("diagnosis_target")
        else state.get("original_question") or state.get("question", ""),
        "original_question": state.get("original_question") or state.get("question", ""),
        "original_request_contract": state.get("original_request_contract"),
        "shared_location_notes": state.get("shared_location_notes"),
        "shared_runbooks": shared,
        "protected_handoff": protected,
        **({"previous_lifecycle_context": legacy_core} if legacy_core else {}),
        "request_contract": state.get("request_contract"),
        "diagnosis_target": state.get("diagnosis_target"),
        "parallel_inventory": state.get("autonomous_groups") or [],
        "parallel_results": material_without_core({
            "parallel_results": state.get("autonomous_group_results") or []})["parallel_results"],
        "request_time_utc": state.get("request_time_utc")
        or datetime.now(timezone.utc).isoformat(),
        "analysis_draft": state.get("query_draft", ""),
        "evidence_receipts": evidence_receipts(state.get("thinking_events") or []),
        "working_summary": events[last_compaction].get("working_summary")
        if last_compaction >= 0
        else None,
        "recent_interactions": project_shared_messages(events[last_compaction].get("retained_messages", []), shared_refs)
        if last_compaction >= 0
        else [],
        "session_history": state.get("query_session_context") if last_compaction < 0 else None,
        "execution_incomplete": [
            f"{event['lane_id']}: {event.get('reason')}"
            if event.get("lane_id")
            else event.get("reason")
            for event in state.get("thinking_events") or []
            if event.get("type") == "execution_incomplete"
        ],
        "observations": [
            shared_runbook_projection((lambda o: o if light else observation_reference(o))({
                key: event.get(key)
                for key in (
                    "tool_name",
                    "tool_args",
                    "status",
                    "semantic_success",
                    "result",
                    "raw_ref",
                    "structured_ref",
                    "timestamp",
                )
            }), shared_refs)
            for event in events[last_compaction + 1 :]
            if event.get("type") == "tool_result"
        ],
    }
