"""Protected identity, provenance and selected source facts across summarization.

These records describe acquisitions, not verified diagnoses or mandatory tasks.
Long tool bodies and model prose deliberately remain outside this contract.
"""
import copy
import json


def protected_handoff(material):
    protected = copy.deepcopy(material.get("protected_handoff") or {})
    from app.core.context.lifecycle_core import core_from_material
    core = core_from_material(material)
    if core:
        protected['lifecycle_core'] = core
    acquired = acquisition_refs(material)
    if acquired:
        protected["evidence_receipts"] = merge_receipts(
            [*(protected.get("evidence_receipts") or []), *acquired])
    lanes = []
    for lane in material.get("parallel_results") or []:
        data = lane.get("material") or {}
        receipts = acquisition_refs(data)
        # Shared acquisitions retain their existing ownership; a branch does
        # not become the owner merely because it inherited the observation.
        lanes.append({
            **{k: copy.deepcopy(lane[k]) for k in (
                "group_id", "target", "run_id", "status", "error", "started_at", "completed_at"
            ) if k in lane},
            "evidence_receipts": receipts,
            "execution_incomplete": copy.deepcopy(data.get("execution_incomplete") or []),
        })
    if lanes:
        protected["groups"] = lanes
    for key in ("diagnosis_target", "shared_runbooks"):
        if material.get(key):
            protected[key] = copy.deepcopy(material[key])
    return protected


def acquisition_refs(material):
    receipts = [*((material.get("protected_handoff") or {}).get("evidence_receipts") or []),
                *(material.get("evidence_receipts") or [])]
    for observation in material.get("observations") or []:
        if observation.get("raw_ref"):
            receipts.append({k: observation[k] for k in (
                "tool_name", "raw_ref", "structured_ref", "status", "semantic_success", "timestamp"
            ) if k in observation})
    return merge_receipts(receipts)


def merge_receipts(items):
    indexed, unaddressed = {}, []
    for item in items:
        if item.get("raw_ref"):
            ref = item["raw_ref"]
            indexed[ref] = {**indexed.get(ref, {}), **{k: v for k, v in item.items() if v is not None}}
        else:
            unaddressed.append(item)
    return unique([*indexed.values(), *unaddressed])


def unique(items):
    result, seen = [], set()
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False, default=str)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(item))
    return result


def handoff_from_messages(messages):
    """Recover explicit contracts only, never infer ownership from model prose."""
    result = {}
    for message in messages:
        data = message if isinstance(message, dict) else message.model_dump()
        if data.get("type", data.get("role")) not in {"human", "user"}:
            continue
        content = data.get("content")
        if not isinstance(content, str):
            continue
        try:
            payload = json.loads(content)
        except (ValueError, RecursionError):
            continue
        if isinstance(payload, dict):
            result.update(protected_handoff(payload))
    from app.core.context.lifecycle_core import core_from_messages
    core = core_from_messages(messages)
    if core:
        result['lifecycle_core'] = core
    return result


def shared_runbook_projection(observation, shared_refs):
    """Replace inherited full text only when a real archive address exists.

    New branch reads, failed fetches and unarchived results stay untouched.
    This neither fetches nor blocks a subsequent autonomous read.
    """
    ref = observation.get("raw_ref")
    if (observation.get("tool_name") != "fetch_runbook" or not ref
            or ref not in shared_refs or observation.get("status") != "success"
            or observation.get("semantic_success") is False):
        return observation
    return {**observation, "result": {
        "shared_reference": ref,
        "runbook_id": (observation.get("tool_args") or {}).get("runbook_id"),
        "note": "定位阶段已读取，相关应用要点见共享定位分析；这不是手册全文。可自主重新读取手册或归档，不要求重复读取。",
    }}


def project_shared_messages(messages, shared_refs):
    result = copy.deepcopy(messages)
    for message in result:
        if not isinstance(message, dict):
            continue
        extras = {**(message.get("provenance") or {}), **(message.get("additional_kwargs") or {})}
        if (message.get("type", message.get("role")) == "tool"
                and message.get("name") == "fetch_runbook"
                and extras.get("aiops_raw_ref") in shared_refs
                and extras.get("aiops_semantic_success") is not False):
            message["content"] = json.dumps({
                "shared_reference": extras["aiops_raw_ref"],
                "note": "已读共享手册；按需自主补读，当前仅传递引用。",
            }, ensure_ascii=False)
    return result
