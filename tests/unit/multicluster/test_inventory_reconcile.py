"""Location accounts for every non-nominal Pod (run 51d58579).

edge-89 listed c09 as ``ready: false`` in the model's own tool output, yet no target
named it; edge-88's two Pods were set ``assessed`` and the overview said the cluster
had no anomaly. Code reconciles the inventory and keeps settled targets visible.
"""

import json
from datetime import datetime, timezone

import pytest

from app.core import multicluster
from app.core.workflow.case_report import located_only
from app.core.workflow.case_result import DiagnosisCaseOutput
from app.core.workflow.diagnosis_contract import LocationHandoff
from app.core.workflow.inventory_reconcile import reconcile_inventory, status_facts
from app.core.workflow.pod_detection import PodAssessment
from tests.unit.multicluster.test_scope_routing import CENTER, CONFIG, EDGE88

NOW = datetime(2026, 10, 22, 6, 30, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def multi(tmp_path, monkeypatch):
    path = tmp_path / "clusters.yaml"
    path.write_text(CONFIG)
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(path))
    multicluster.reset()
    yield
    multicluster.reset()


def pod(
    name,
    ns="aiops-case-09",
    phase="Running",
    ready=True,
    state=None,
    last=None,
    node="m1",
    deleting=False,
):
    container = {
        "name": "app",
        "ready": ready,
        "restartCount": 1 if last else 0,
        "state": state or {"running": {}},
    }
    if last:
        container["lastState"] = {"terminated": last}
    meta = {"name": name, "namespace": ns, "uid": f"uid-{name}"}
    if deleting:
        meta["deletionTimestamp"] = "2026-10-22T06:20:00Z"
    return {
        "metadata": meta,
        "spec": {"nodeName": node},
        "status": {
            "phase": phase,
            "conditions": [{"type": "Ready", "status": "True" if ready else "False"}],
            "containerStatuses": [container],
        },
    }


def runner(*pods, calls=None):
    def run(argv):
        if calls is not None:
            calls.append(argv)
        return json.dumps({"items": list(pods)})

    return run


def target(name, ns="aiops-case-09", status="investigate", reason=""):
    return {
        "target_id": name,
        "entity": {"kind": "Pod", "namespace": ns, "name": name},
        "issue": "x",
        "status": status,
        "status_reason": reason,
    }


STATE = {
    "request_contract": {
        "clusters": [EDGE88],
        "cluster_mode": "single",
        "namespaces": [],
        "pod_names": [],
    }
}


def test_unready_pod_the_model_skipped_becomes_an_investigate_target():
    handoff = {
        "targets": [target("other")],
        "coverage": "complete",
        "pod_assessment": {"status": "healthy", "scope": "s", "observed_at": "t", "reason": "r"},
    }
    out, added = reconcile_inventory(
        handoff, STATE, run=runner(pod("workload-c09", ready=False), pod("ok")), now=NOW
    )
    assert added == ["aiops-case-09/workload-c09"]
    extra = out["targets"][-1]
    assert extra["status"] == "investigate" and extra["entity"]["uid"] == "uid-workload-c09"
    assert "Ready=False" in extra["issue"] and "运行但未就绪" in extra["issue"]
    assert out["pod_assessment"]["status"] == "abnormal"
    LocationHandoff.model_validate(out)  # still a valid location contract
    assert handoff["targets"] == [target("other")]  # input untouched


def test_accounted_nominal_succeeded_and_virtual_node_pods_are_left_alone():
    pods = [
        pod("named", ready=False),
        pod("settled", ready=False),
        pod("fine"),
        pod("job", phase="Succeeded", state={"terminated": {"reason": "Completed"}}),
        pod("proxy", phase="Deployed", node=CENTER),  # bound to a configured cluster's Node
    ]
    handoff = {"targets": [target("named"), target("settled", status="deferred", reason="r")]}
    out, added = reconcile_inventory(handoff, STATE, run=runner(*pods), now=NOW)
    assert added == [] and out == handoff


def test_an_assessed_pod_that_is_still_abnormal_is_investigated():
    # Run 73f4a1f5: OOM / liveness Pods "assessed" at location got no evidence or RCA.
    handoff = {
        "targets": [
            target("oom", status="assessed", reason="OOMKilled"),
            target("ok", status="assessed"),
        ]
    }
    out, added = reconcile_inventory(
        handoff, STATE, run=runner(pod("oom", ready=False), pod("ok")), now=NOW
    )
    assert added == ["aiops-case-09/oom"]
    assert [(t["status"], t["status_reason"]) for t in out["targets"]] == [
        ("investigate", ""),
        ("assessed", ""),  # nominal now: the stage's judgement stands
    ]


def test_recent_restart_waiting_and_deleting_pods_are_named_with_raw_facts():
    recent = {"reason": "OOMKilled", "exitCode": 137, "finishedAt": "2026-10-22T06:25:00Z"}
    old = {"reason": "Error", "exitCode": 1, "finishedAt": "2026-10-20T06:25:00Z"}
    assert "OOMKilled" in "".join(status_facts(pod("a", last=recent), NOW))
    assert status_facts(pod("b", last=old), NOW) == []  # outside the 10-minute window
    waiting = status_facts(
        pod("c", ready=False, state={"waiting": {"reason": "CrashLoopBackOff"}}), NOW
    )
    assert any("CrashLoopBackOff" in fact for fact in waiting)
    assert any("删除中" in fact for fact in status_facts(pod("d", deleting=True), NOW))


def test_scope_follows_the_contract_and_a_named_pod_is_not_reconciled():
    calls = []
    scoped = {"request_contract": {**STATE["request_contract"], "namespaces": ["a", "b"]}}
    reconcile_inventory({"targets": []}, scoped, run=runner(calls=calls), now=NOW)
    assert calls == [
        ["get", "pods", "-o", "json", "-n", "a"],
        ["get", "pods", "-o", "json", "-n", "b"],
    ]
    named = {"request_contract": {**STATE["request_contract"], "pod_names": ["p"]}}
    assert reconcile_inventory({"targets": []}, named, run=runner(pod("x", ready=False))) == (
        {"targets": []},
        [],
    )


def test_unreadable_inventory_leaves_the_handoff_unchanged():
    def broken(argv):
        raise RuntimeError("cluster_unreachable")

    handoff = {"targets": [target("t")]}
    assert reconcile_inventory(handoff, STATE, run=broken) == (handoff, [])


def test_default_runner_never_uses_ambient_kubeconfig(monkeypatch):
    # Unit tests and local runs have no in-cluster ServiceAccount: no kubectl at all.
    monkeypatch.delenv("KUBERNETES_SERVICE_HOST", raising=False)
    local = {"request_contract": {"clusters": [CENTER], "cluster_mode": "single"}}
    import app.core.remediation.pod_executor as executor

    monkeypatch.setattr(executor, "run_argv", lambda *a, **k: pytest.fail("kubectl was called"))
    assert reconcile_inventory({"targets": []}, local) == ({"targets": []}, [])


def test_settled_targets_stay_in_the_overview_with_their_cluster():
    state = {
        "request_contract": {"cluster_labels": ["edge-88", "edge-89"]},
        "diagnosis_handoff": {
            "targets": [
                {
                    **target(
                        "edge-88/c08", ns="aiops-case-08", status="assessed", reason="判为测试场景"
                    ),
                    "entity": {"kind": "Pod", "namespace": "aiops-case-08", "name": "w-08"},
                },
                {
                    **target("edge-89/c04"),
                    "entity": {"kind": "Pod", "namespace": "n", "name": "w"},
                },
            ]
        },
    }
    assert located_only(state) == ["edge-88 aiops-case-08/w-08（定位判断：判为测试场景）"]


def test_single_text_answers_for_list_fields_are_accepted():
    # Live: "unresolved: Input should be a valid list" cost a structured retry.
    assert PodAssessment(
        scope="s", observed_at="t", reason="r", unresolved="待核实"
    ).unresolved == ["待核实"]
    case = DiagnosisCaseOutput(
        outcome="abnormal",
        summary="s",
        certainty="supported",
        report="r",
        unresolved="u",
        runbook_refs="",
    )
    assert case.unresolved == ["u"] and case.runbook_refs == []
    with pytest.raises(ValueError):
        PodAssessment(scope="s", observed_at="t", reason="r", unresolved={"a": 1})


def test_object_lists_sent_as_json_text_are_accepted():
    facts = [{"statement": "Ready=False", "evidence_refs": ["/a/raw.txt"]}]
    case = DiagnosisCaseOutput(
        outcome="abnormal",
        summary="s",
        certainty="supported",
        report="r",
        key_facts=json.dumps(facts),
    )
    assert case.key_facts[0].statement == "Ready=False"
    with pytest.raises(ValueError):
        DiagnosisCaseOutput(
            outcome="abnormal", summary="s", certainty="supported", report="r", key_facts="x"
        )


def test_missing_target_id_is_the_entity_identity():
    handoff = LocationHandoff.model_validate(
        {
            "targets": [
                {"entity": {"kind": "Pod", "namespace": "ns", "name": "w"}, "issue": "x"},
                {"target_id": "kept", "entity": {"kind": "Pod", "name": "v"}, "issue": "y"},
            ]
        }
    )
    assert [t.target_id for t in handoff.targets] == ["ns-w", "kept"]
    with pytest.raises(ValueError):
        LocationHandoff.model_validate({"targets": [{"entity": {"kind": "Pod"}, "issue": "x"}]})


def test_unknown_target_status_errs_toward_investigation():
    handoff = LocationHandoff.model_validate(
        {
            "targets": [
                {
                    "target_id": "t",
                    "entity": {"kind": "Pod", "name": "w"},
                    "issue": "x",
                    "status": "abnormal",
                }
            ]
        }
    )
    assert handoff.targets[0].status == "investigate"
