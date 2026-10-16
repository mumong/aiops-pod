"""RepairDraft rejects commands that name a different controller than the verified owner."""

import pytest

from app.core.remediation.policy import named_resources
from app.core.workflow.nodes.remediation import RepairDraft


def _draft(command):
    return {
        "intent": "fix", "scope": "pod", "status": "answered", "answer": "plan",
        "targets": [{"namespace": "aiops-case-09", "pod": "workload-5487445f9-k4648", "group_id": "single",
                     "owner_kind": "Deployment", "owner_name": "workload", "owner_uid": "d1"}],
        "actions": [{"id": "a1", "group_id": "single", "description": "fix probe", "risk": "low",
                     "execute_command": command, "rollback_advice": "revert"}],
        "assessments": [{"group_id": "single", "status": "ready", "reason": "ok"}],
    }


def test_named_resources_parses_both_forms():
    assert named_resources("kubectl patch deployment workload -n ns -p '{}'") == [("deployment", "workload")]
    assert named_resources("kubectl patch deploy/workload -n ns --type=json -p '[]'") == [("deployment", "workload")]
    assert named_resources("kubectl set env deployment/api -n ns A=b") == [("deployment", "api")]
    assert named_resources("kubectl get pods -n ns") == []


def test_replicaset_name_passed_as_deployment_is_rejected():
    with pytest.raises(ValueError) as info:
        RepairDraft.model_validate(_draft(
            "kubectl patch deployment workload-5487445f9 -n aiops-case-09 --type=json -p '[]'"))
    assert "Deployment/workload" in str(info.value)


def test_verified_owner_and_pod_commands_pass():
    RepairDraft.model_validate(_draft("kubectl patch deployment/workload -n aiops-case-09 --type=json -p '[]'"))
    RepairDraft.model_validate(_draft("kubectl patch pod/workload-5487445f9-k4648 -n aiops-case-09 --type=merge -p '{}'"))


def test_targets_without_assessments_are_rejected():
    draft = _draft("kubectl patch deployment/workload -n aiops-case-09 --type=json -p '[]'")
    draft["assessments"] = []
    draft["actions"] = []
    with pytest.raises(ValueError) as info:
        RepairDraft.model_validate(draft)
    assert "assessments" in str(info.value)


def test_kubectl_write_in_prose_without_actions_is_rejected():
    draft = _draft("kubectl patch deployment/workload -n aiops-case-09 --type=json -p '[]'")
    draft["actions"] = []
    draft["assessments"] = [{"group_id": "single", "status": "needs_input", "reason": "x"}]
    draft["answer"] = "修复步骤：\n```bash\nkubectl patch deployment workload -n aiops-case-06 -p '{}'\n```"
    with pytest.raises(ValueError) as info:
        RepairDraft.model_validate(draft)
    assert "actions 为空" in str(info.value)
    # Read-only commands in prose are explanation, not an unsubmitted plan.
    draft["answer"] = "可用 `kubectl describe pod x` 复查；\nkubectl get pods -n demo"
    RepairDraft.model_validate(draft)
