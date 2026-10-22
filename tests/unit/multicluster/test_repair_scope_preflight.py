"""Group repairs run on their own cluster, and commands are dry-run before approval.

Run 9062db56: a two-cluster diagnosis's groups were repaired with the diagnosis's
two-cluster scope; the executor treated "not one cluster" as local, so every
command ran on the center (edge-89 namespaces not found; the center's own
aiops-case-08 was changed instead of edge-88's). One plan also used an unknown
kubectl flag that nothing checked before approval.
"""

import pytest

from aiops_edge.kubectl_args import classify
from app.core import multicluster
from app.core.remediation.approval import ApprovalStore
from app.core.remediation.group_context import scoped_diagnosis
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.preflight import dry_run_argv, preflight_errors
from app.core.workflow.nodes.remediation import RepairAction, RepairDraft
from tests.unit.multicluster.test_executor_remote import (  # noqa: F401
    POLICY,
    FakeJobs,
    multi,
    runner_with,
)
from tests.unit.multicluster.test_scope_routing import EDGE88
from tests.unit.remediation.test_pod_executor import fixture

EDGE89 = "vc-dluw0jousipr6h5co2bwpyqk2"


def diagnosis_record():
    def group(gid, cluster, label, ns):
        return {
            "group_id": gid,
            "status": "completed",
            "target": {
                "group_id": gid,
                "cluster": cluster,
                "cluster_label": label,
                "entities": [{"kind": "Pod", "namespace": ns, "name": "workload"}],
            },
            "diagnosis_result": {"summary": "s", "report": "r"},
        }

    return {
        "run_id": "diag",
        "kind": "diagnosis",
        "payload": {
            "contract_version": "diagnosis-record.v2",
            "question": "q",
            "request_contract": {
                "scope": "cluster",
                "clusters": [EDGE88, EDGE89],
                "cluster_labels": ["edge-88", "edge-89"],
                "cluster_mode": "multiple",
            },
            "groups": [
                group("g1", EDGE88, "edge-88", "aiops-case-08"),
                group("g3", EDGE89, "edge-89", "aiops-case-04"),
            ],
        },
    }


def test_group_repair_is_scoped_to_the_groups_own_cluster():
    contract = scoped_diagnosis(diagnosis_record(), "g3")["payload"]["request_contract"]
    assert contract["clusters"] == [EDGE89] and contract["cluster_labels"] == ["edge-89"]
    assert contract["cluster_mode"] == "single" and contract["namespaces"] == ["aiops-case-04"]


def test_executor_refuses_a_repair_without_exactly_one_cluster(multi):  # noqa: F811
    draft, _, _, _ = fixture()
    calls, jobs = [], FakeJobs()
    events = list(
        PodRepairExecutor(ApprovalStore(), runner_with(calls), remote_jobs=jobs).run(
            "r",
            draft,
            owner="alice",
            mode="auto",
            policy=POLICY,
            request_contract={"namespaces": ["demo"], "clusters": [EDGE88, EDGE89]},
        )
    )
    assert (
        events[-1]["status"] == "blocked" and events[-1]["error_code"] == "cluster_scope_ambiguous"
    )
    assert "edge-88" in events[-1]["reason"] and calls == [] and jobs.runs == []


def test_single_cluster_mode_is_unaffected():
    multicluster.reset()
    assert multicluster.job_scope_error({"namespaces": ["demo"]}) is None


def test_dry_run_form_only_for_kubectl_writes():
    assert dry_run_argv("kubectl set env deployment/workload -n ns FAILURE_MODE-") == [
        "kubectl",
        "set",
        "env",
        "deployment/workload",
        "-n",
        "ns",
        "FAILURE_MODE-",
        "--dry-run=client",
    ]
    for command in (
        "kubectl get pods -n ns",
        "kubectl exec -n ns p -- ls",
        "kubectl delete pod p --dry-run=server",
        "rm -rf /",
        "kubectl patch deploy x -p '{",
    ):
        assert dry_run_argv(command) is None, command


def test_preflight_reports_kubectl_errors_and_skips_subcommands_without_dry_run():
    def run(argv):
        if "--remove=env/FAILURE_MODE" in argv:
            raise RuntimeError("error: unknown flag: --remove")
        if "aiops-case-04" in argv:
            raise RuntimeError(
                'Error from server (NotFound): namespaces "aiops-case-04" not found'
            )
        if "uncordon" in argv:
            raise RuntimeError("error: unknown flag: --dry-run")
        return "deployment.apps/workload (dry run)"

    actions = [
        RepairAction(
            id="a1",
            group_id="g",
            description="d",
            risk="low",
            rollback_advice="r",
            execute_command="kubectl set env deployment/workload -n aiops-case-10 --remove=env/FAILURE_MODE",
        ),
        RepairAction(
            id="a2",
            group_id="g",
            description="d",
            risk="low",
            rollback_advice="r",
            execute_command="kubectl patch deployment workload -n aiops-case-04 -p '{}'",
        ),
        RepairAction(
            id="a3",
            group_id="g",
            description="d",
            risk="low",
            rollback_advice="r",
            execute_command="kubectl set env deployment/workload -n aiops-case-10 FAILURE_MODE-",
        ),
        RepairAction(
            id="a4",
            group_id="g",
            description="d",
            risk="low",
            rollback_advice="r",
            execute_command="kubectl uncordon node1",
        ),
    ]
    errors = preflight_errors(actions, run)
    assert len(errors) == 2
    assert errors[0].startswith("a1:") and "unknown flag: --remove" in errors[0]
    assert errors[1].startswith("a2:") and "not found" in errors[1]


def test_planning_schema_sends_a_failed_dry_run_back_to_the_model():
    schema = RepairDraft.with_preflight(
        lambda actions: ["a1: `kubectl x` → error: unknown flag: --remove"]
    )
    data = {
        "intent": "repair",
        "scope": "s",
        "status": "answered",
        "answer": "a",
        "targets": [{"namespace": "ns", "pod": "p", "group_id": "g"}],
        "actions": [
            {
                "id": "a1",
                "group_id": "g",
                "description": "d",
                "risk": "low",
                "execute_command": "kubectl x",
                "rollback_advice": "r",
            }
        ],
    }
    with pytest.raises(ValueError, match="命令预检未通过.*unknown flag: --remove"):
        schema.model_validate(data)
    assert schema.__name__ == "RepairDraft"
    RepairDraft.model_validate(data)  # stored drafts are re-read without any cluster call


def test_client_dry_run_is_a_read_on_remote_clusters():
    assert classify(["kubectl", "set", "env", "deploy/x", "A-", "--dry-run=client"]) == (
        "read",
        None,
    )
    assert classify(["kubectl", "set", "env", "deploy/x", "A-", "--dry-run=server"]) == (
        "write",
        None,
    )
    assert classify(["kubectl", "set", "env", "deploy/x", "A-"]) == ("write", None)
