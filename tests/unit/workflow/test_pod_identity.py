"""Model selects targets; code binds their identity (live run 77253475e72f4adf: 4 Pod targets
delivered with namespace='' -> no parallel lanes)."""

from types import SimpleNamespace

from app.core.workflow import pod_identity
from app.core.workflow.pod_identity import complete_pod_namespaces

LISTING = "\n".join(
    [
        "aiops-case-04\tworkload-6584f97c76-wxr8h\tuid-04",
        "aiops-case-11\tworkload\tuid-11",
        "aiops-case-12\tworkload\tuid-12",
        "admin\tfpga-operator\tuid-x",
    ]
)


def test_fills_by_uid_and_by_unique_name_only():
    entities = [
        {"kind": "Pod", "namespace": "", "name": "workload-6584f97c76-wxr8h", "uid": "uid-04"},
        {"kind": "Pod", "namespace": "", "name": "workload", "uid": "uid-11"},  # uid wins
        {"kind": "Pod", "namespace": "", "name": "workload"},  # ambiguous name
        {"kind": "Pod", "namespace": "", "name": "fpga-operator"},  # unique name
        {"kind": "Pod", "namespace": "keep", "name": "x", "uid": "uid-x"},  # untouched
        {"kind": "Node", "namespace": "", "name": "node2"},  # not a Pod
    ]
    calls = []
    filled = complete_pod_namespaces(entities, runner=lambda argv: calls.append(argv) or LISTING)
    assert filled == 3 and len(calls) == 1
    assert [e["namespace"] for e in entities] == [
        "aiops-case-04",
        "aiops-case-11",
        "",
        "admin",
        "keep",
        "",
    ]
    assert calls[0][:4] == ["kubectl", "get", "pods", "-A"]


def test_no_lookup_when_nothing_is_missing_and_failures_are_tolerated():
    complete = [{"kind": "Pod", "namespace": "a", "name": "p"}]
    assert (
        complete_pod_namespaces(
            complete, runner=lambda argv: (_ for _ in ()).throw(AssertionError)
        )
        == 0
    )

    def broken(argv):
        raise RuntimeError("forbidden")

    assert (
        complete_pod_namespaces([{"kind": "Pod", "namespace": "", "uid": "u"}], runner=broken) == 0
    )


def test_plan_groups_fans_out_when_namespaces_are_completed(monkeypatch, tmp_path):
    from app.core.workflow.nodes.autonomous_parallel import plan_groups

    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setattr(pod_identity, "_default_runner", lambda argv: LISTING)
    targets = [
        {
            "target_id": f"t{i}",
            "issue": "x",
            "status": "investigate",
            "status_reason": "",
            "evidence_refs": [],
            "entity": {"kind": "Pod", "namespace": "", "name": name, "uid": uid},
        }
        for i, (name, uid) in enumerate(
            [("workload-6584f97c76-wxr8h", "uid-04"), ("workload", "uid-11")]
        )
    ]
    handoff = {
        "contract_version": "location-handoff.v1",
        "targets": targets,
        "coverage": "complete",
        "coverage_note": "",
    }
    node = SimpleNamespace(current_run_id="r1", ai_call=None, node_id="layer")
    result = plan_groups(node, {"question": "q", "diagnosis_handoff": handoff})
    assert [g["entities"][0]["namespace"] for g in result["autonomous_groups"]] == [
        "aiops-case-04",
        "aiops-case-11",
    ]
    assert result["diagnosis_handoff"]["targets"][0]["entity"]["namespace"] == "aiops-case-04"
    assert handoff["targets"][0]["entity"]["namespace"] == ""  # caller's dict is not mutated
