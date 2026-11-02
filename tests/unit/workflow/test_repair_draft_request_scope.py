"""A target outside the user's request goes back to the model while it can still fix it.

Run fe4fff51ed7846db (c09): the plan named the Deployment but left targets[].pod empty;
only the executor checked the request scope, so the job ended blocked with a bare
"修复目标超出用户请求范围" and the model never saw why.
"""

import pytest

from app.core.remediation.policy import request_scope_error
from app.core.workflow.nodes.remediation import RepairDraft

CONTRACT = {"namespaces": ["aiops-case-09"], "pod_names": ["workload-5487445f9-k4648"]}


def _draft(pod="workload-5487445f9-k4648", namespace="aiops-case-09"):
    return {
        "intent": "fix",
        "scope": "pod",
        "status": "answered",
        "answer": "plan",
        "targets": [{"namespace": namespace, "pod": pod, "group_id": "single"}],
        "actions": [
            {
                "id": "a1",
                "group_id": "single",
                "description": "fix probe",
                "risk": "low",
                "execute_command": f"kubectl rollout restart deployment/workload -n {namespace}",
                "rollback_advice": "none",
            }
        ],
        "assessments": [{"group_id": "single", "status": "ready", "reason": "ok"}],
    }


def test_empty_pod_names_the_requested_pod_and_the_next_step():
    with pytest.raises(ValueError) as info:
        RepairDraft.with_request_scope(CONTRACT).model_validate(_draft(pod=""))
    text = str(info.value)
    assert "pod 为空" in text and "workload-5487445f9-k4648" in text
    assert "尚未执行" in text and "重新提交" in text


def test_other_pod_and_other_namespace_say_which_value_is_out_of_scope():
    with pytest.raises(ValueError) as info:
        RepairDraft.with_request_scope(CONTRACT).model_validate(_draft(pod="other-pod"))
    assert "other-pod" in str(info.value) and "workload-5487445f9-k4648" in str(info.value)
    with pytest.raises(ValueError) as info:
        RepairDraft.with_request_scope(CONTRACT).model_validate(_draft(namespace="demo"))
    assert "demo" in str(info.value) and "aiops-case-09" in str(info.value)


def test_in_scope_target_and_unbound_schema_pass():
    RepairDraft.with_request_scope(CONTRACT).model_validate(_draft())
    RepairDraft.with_request_scope({}).model_validate(_draft(pod="anything"))
    RepairDraft.model_validate(_draft(pod=""))


def test_scope_refusal_comes_before_the_cluster_dry_run():
    calls = []
    schema = RepairDraft.with_preflight(
        lambda actions: calls.append(actions) or []
    ).with_request_scope(CONTRACT)
    with pytest.raises(ValueError):
        schema.model_validate(_draft(pod=""))
    assert calls == []


def test_same_rule_as_the_executor():
    assert request_scope_error("aiops-case-09", "workload-5487445f9-k4648", CONTRACT) is None
    assert request_scope_error("x", "y", None) is None
    assert request_scope_error("aiops-case-09", "", {"namespaces": ["aiops-case-09"]}) is None
    assert request_scope_error("aiops-case-09", "", CONTRACT)
