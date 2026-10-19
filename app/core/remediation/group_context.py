"""Project an existing diagnosis group without sending other groups' bodies.

Grouping is inherited from diagnosis, not inferred from fault-name rules. This
module neither constructs commands nor decides whether a resource is repairable.
"""

from copy import deepcopy

from app.core.remediation.records import RecordUnavailable


def diagnosis_groups(record):
    groups = (record.get("payload") or {}).get("groups") or []
    identifiers = [group.get("group_id") for group in groups]
    if any(not isinstance(gid, str) or not gid for gid in identifiers) or len(
        set(identifiers)
    ) != len(identifiers):
        raise RecordUnavailable("诊断分组标识缺失或重复，请重新生成诊断")
    return [
        {
            "group_id": group["group_id"],
            "target": deepcopy(group.get("target")),
            "summary": _group_summary(group),
        }
        for group in groups
    ] or [
        {
            "group_id": "single",
            "target": None,
            "summary": _group_summary({"analysis": (record.get("payload") or {}).get("report")}),
        }
    ]


# A group whose RCA found nothing to fix (or found it already recovered) gets no job.
SETTLED_OUTCOMES = frozenset({"healthy", "recovered"})


def repairable_groups(record):
    """Groups that still need a repair decision; legacy records count as unresolved."""
    payload = record.get("payload") or {}
    raw_groups = payload.get("groups") or []
    groups = diagnosis_groups(record)
    if not raw_groups:
        # v2 without cases, or a location that handed over nothing to investigate (the
        # healthy / no-target path), found nothing to repair. Older single reports
        # without a stored handoff stay eligible.
        if payload.get("contract_version") == "diagnosis-record.v2":
            return []
        handoff = payload.get("diagnosis_handoff")
        if isinstance(handoff, dict) and not any(
            t.get("status", "investigate") == "investigate"
            for t in handoff.get("targets") or []
            if isinstance(t, dict)
        ):
            return []
        return groups
    return [
        group
        for group, raw in zip(groups, raw_groups, strict=True)
        if str(((raw or {}).get("diagnosis_result") or {}).get("outcome") or "")
        not in SETTLED_OUTCOMES
    ]


def select_groups(groups, contract):
    """Groups the request names (pods, else namespaces); an unscoped request keeps all."""
    contract = contract or {}
    pods = set(contract.get("pod_names") or [])
    namespaces = set(contract.get("namespaces") or [])
    if not pods and not namespaces:
        return list(groups)

    def entities(group):
        return ((group.get("target") or {}).get("entities")) or []

    if pods:
        return [g for g in groups if any(e.get("name") in pods for e in entities(g))]
    return [g for g in groups if any(e.get("namespace") in namespaces for e in entities(g))]


def _group_summary(group):
    """The diagnosis's own one-line cause for this group (historical, not current state)."""
    result = group.get("diagnosis_result") or {}
    for value in (
        result.get("summary"),
        result.get("root_cause"),
        result.get("report"),
        group.get("analysis"),
    ):
        text = str(value or "").strip()
        if text:
            return text[:400]
    return None


def scoped_diagnosis(record, group_id):
    payload = record.get("payload") or {}
    groups = payload.get("groups") or []
    if not groups and group_id == "single":
        return deepcopy(record)
    matches = [g for g in groups if g.get("group_id") == group_id]
    if len(matches) != 1:
        raise RecordUnavailable("指定修复组不存在或不唯一")
    group = deepcopy(matches[0])
    target = group.get("target") or {}
    entities = target.get("entities") or []
    contract = deepcopy(payload.get("request_contract") or {})
    namespaces = sorted({e["namespace"] for e in entities if e.get("namespace")})
    pods = [e["name"] for e in entities if e.get("kind") == "Pod" and e.get("name")]
    if namespaces:
        contract.update(
            namespaces=namespaces, pod_names=pods, scope="pod" if pods else "namespace"
        )
    if payload.get("contract_version") == "diagnosis-record.v2":
        diagnosis = deepcopy(group.get("diagnosis_result") or {})
        report = diagnosis.pop("report", "本组诊断交付不完整；不得据此推测根因。")
        return {
            **{k: deepcopy(v) for k, v in record.items() if k != "payload"},
            "payload": {
                "question": payload.get("question"),
                "request_contract": contract,
                "report": report,
                "diagnosis_result": diagnosis,
                "groups": [
                    {"group_id": group_id, "target": target, "status": group.get("status")}
                ],
                "source_diagnosis_run_id": record.get("run_id"),
                "group_id": group_id,
                "scope_note": "仅本组历史诊断、关键事实、未知条件和引用；生成方案前可自主核实。不是执行授权。",
            },
        }
    # Shared results are discoverable references, not repeated full evidence.
    shared = [
        {
            key: deepcopy(e.get(key))
            for key in (
                "tool_name",
                "tool_args",
                "raw_ref",
                "structured_ref",
                "status",
                "timestamp",
            )
        }
        for e in (payload.get("shared_evidence") or {}).get("evidence", [])
    ]
    return {
        **{k: deepcopy(v) for k, v in record.items() if k != "payload"},
        "payload": {
            "question": payload.get("question"),
            "request_contract": contract,
            "report": group.get("analysis") or "本组诊断见分组证据；不推测未提供的根因。",
            "groups": [group],
            "shared_evidence": {"evidence": shared},
            "source_diagnosis_run_id": record.get("run_id"),
            "group_id": group_id,
            "diagnosis_handoff": deepcopy(group.get("diagnosis_handoff")),
            "scope_note": "仅本组历史诊断和证据；公共证据按引用自主补读，其他组未投递。",
        },
    }
