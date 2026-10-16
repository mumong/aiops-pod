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
