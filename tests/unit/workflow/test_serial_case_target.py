"""Serial RCA keeps a valid report when location handed over more than one target."""

from app.core.workflow.case_result import bind_case_result
from app.core.workflow.nodes.autonomous_diagnosis import serial_case_target


def _target(tid, kind, name, status="investigate", namespace="ns"):
    return {
        "target_id": tid,
        "status": status,
        "entity": {"kind": kind, "namespace": namespace, "name": name, "uid": tid + "-uid"},
    }


def test_pod_plus_owner_deployment_form_one_serial_case():
    handoff = {
        "targets": [
            _target("pod-1", "Pod", "web-abc"),
            _target("deploy-1", "Deployment", "web", namespace=""),
        ]
    }
    target = serial_case_target(handoff)
    assert target["group_id"] == "single" and target["target_id"] == "pod-1+deploy-1"
    assert [e["kind"] for e in target["entities"]] == ["Pod", "Deployment"]
    case = bind_case_result(
        {"outcome": "abnormal", "summary": "s", "certainty": "confirmed", "report": "r"},
        group_id="single",
        target=target,
        result_ref="/x/result.json",
    )
    assert case["execution_status"] == "completed" and case["target"] == target


def test_deferred_targets_are_left_out_unless_nothing_else_remains():
    handoff = {"targets": [_target("a", "Pod", "a"), _target("b", "Pod", "b", status="deferred")]}
    assert serial_case_target(handoff)["target_id"] == "a"
    only_deferred = {"targets": [_target("b", "Pod", "b", status="deferred")]}
    assert serial_case_target(only_deferred)["target_id"] == "b"
    assert serial_case_target({"targets": []}) is None and serial_case_target(None) is None
