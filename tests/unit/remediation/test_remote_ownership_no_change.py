"""Ownership facts come from the plan's own cluster; a write kubectl reports as a no-op fails fast.

Live run 9a22d79701c34f2f (center + two edges): the ownerReferences chain of an
edge Pod was looked up on the center, found nothing, and ``kubectl patch replicaset
… (no change)`` was approved, "succeeded" and was watched for 180 seconds. On the
center the same plan is rejected; nothing here depends on the workload kind.
"""

import json

import pytest

from app.core.remediation.ownership import ControllerChain, OwnerLink, managed_write_error
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.preflight import preflight_errors, reports_no_change
from app.core.remediation.recovery import RecoveryConfig
from tests.unit.remediation.test_executor_recovery import _Clock, _factory, _pod
from tests.unit.remediation.test_ownership_chain import DEP, POD, RS, _draft, _runner
from tests.unit.remediation.test_pod_executor import fixture

OBJECTS = {
    "pod/web-7bf9698f49-8xrps": POD,
    "replicaset/web-7bf9698f49": RS,
    "deployment/web": DEP,
}
RS_PATCH = (
    "kubectl patch replicaset web-7bf9698f49 -n ns --type=merge "
    '-p \'{"metadata":{"annotations":{"example.io/network":null}}}\''
)
DEP_PATCH = (
    "kubectl patch deployment web -n ns --type=merge "
    '-p \'{"spec":{"template":{"metadata":{"annotations":{"example.io/network":null}}}}}\''
)


# ---- the chain is resolved on the plan's cluster ------------------------------------


def test_planning_resolves_the_chain_through_the_plans_cluster(monkeypatch):
    """The lookup goes where the dry run goes: the edge, through its runner."""
    from app.core.remediation import preflight
    from app.core.workflow.nodes import remediation as module

    seen = []
    cluster_run = _runner(OBJECTS)

    def runner_for(contract):
        seen.append(contract["clusters"])
        return lambda argv: cluster_run(" ".join(argv))

    monkeypatch.setattr(preflight, "runner_for", runner_for)
    contract = {"namespaces": ["ns"], "pod_names": ["web-7bf9698f49-8xrps"], "clusters": ["edge"]}

    chains = module.RemediationNode()._controller_chains({}, contract)

    chain = chains["ns/web-7bf9698f49-8xrps"]
    assert chain.complete and chain.root.label() == "Deployment/web"
    assert seen == [["edge"]]


def test_planning_node_binds_the_cluster_lookup_to_the_schema(monkeypatch):
    """execute(): chains and the schema's lookup use the plan cluster's runner, not local kubectl."""
    from types import SimpleNamespace

    from app.core.remediation import executor as local
    from app.core.remediation import preflight
    from app.core.workflow.nodes import remediation as module

    monkeypatch.setattr(
        local, "run_local_command", lambda c: pytest.fail(f"local kubectl used: {c}")
    )
    calls = []
    cluster_run = _runner(OBJECTS, calls)
    monkeypatch.setattr(
        preflight, "runner_for", lambda contract: lambda argv: cluster_run(" ".join(argv))
    )
    monkeypatch.setattr(preflight, "is_remote", lambda contract: False)
    node = module.RemediationNode()
    node.ai_call = SimpleNamespace()
    node._prepare_query_tools = lambda: ""
    seen = {}

    def collect(question, prompt, **kw):
        seen["material"], seen["schema"] = json.loads(question), kw["response_schema"]
        return SimpleNamespace(result=json.dumps(_draft(RS_PATCH))), []

    node._call_llm = collect
    node.execute(
        {
            "question": "fix",
            "request_contract": {"clusters": ["edge"]},
            "repair_context": {
                "diagnosis": {
                    "payload": {
                        "group_id": "g1",
                        "groups": [
                            {
                                "target": {
                                    "entities": [
                                        {
                                            "kind": "Pod",
                                            "namespace": "ns",
                                            "name": "web-7bf9698f49-8xrps",
                                        }
                                    ]
                                }
                            }
                        ],
                    }
                }
            },
        }
    )
    facts = seen["material"]["controller_chains"]["ns/web-7bf9698f49-8xrps"]
    assert facts["root"] == "Deployment/web" and facts["complete"] is True
    assert calls[0].startswith("kubectl get pod/web-7bf9698f49-8xrps -n ns")
    with pytest.raises(ValueError, match="Deployment/web"):
        seen["schema"].model_validate(_draft(RS_PATCH))


# ---- an incomplete chain still refuses writes to managed objects ---------------------


def _pod_only():
    return ControllerChain("ns", [OwnerLink("Pod", "web-7bf9698f49-8xrps")], complete=False)


def test_incomplete_chain_reads_the_written_objects_own_owner():
    error = managed_write_error(RS_PATCH, _pod_only(), _runner(OBJECTS))
    assert "replicaset/web-7bf9698f49" in error and "Deployment/web" in error
    # The top controller has no owner: the write is where the controller writes.
    assert managed_write_error(DEP_PATCH, _pod_only(), _runner(OBJECTS)) == ""
    # Unreadable object: no claim either way (the dry run reports NotFound).
    assert managed_write_error(RS_PATCH, _pod_only(), _runner({})) == ""
    # Reads are never looked up.
    calls = []
    assert (
        managed_write_error(
            "kubectl get rs web-7bf9698f49 -n ns", _pod_only(), _runner(OBJECTS, calls)
        )
        == ""
    )
    assert calls == []


def test_complete_chain_needs_no_extra_lookup():
    chain = ControllerChain(
        "ns",
        [
            OwnerLink("Pod", "web-7bf9698f49-8xrps"),
            OwnerLink("ReplicaSet", "web-7bf9698f49"),
            OwnerLink("Deployment", "web"),
        ],
    )
    calls = []
    assert "Deployment/web" in managed_write_error(RS_PATCH, chain, _runner(OBJECTS, calls))
    assert managed_write_error(DEP_PATCH, chain, _runner(OBJECTS, calls)) == ""
    assert calls == []


def test_bound_schema_with_incomplete_chain_rejects_the_managed_write():
    from app.core.workflow.nodes.remediation import RepairDraft

    bound = RepairDraft.with_controller_chains(
        {"ns/web-7bf9698f49-8xrps": _pod_only()}, _runner(OBJECTS)
    )
    with pytest.raises(ValueError, match="Deployment/web"):
        bound.model_validate(_draft(RS_PATCH))
    assert bound.model_validate(_draft(DEP_PATCH)).actions[0].execute_command == DEP_PATCH


# ---- kubectl's "no change" verdict ---------------------------------------------------


@pytest.mark.parametrize(
    "output, expected",
    [
        ("replicaset.apps/web-7bf9698f49 patched (no change)\n", True),
        ("deployment.apps/web patched (no change) (server dry run)", True),
        ("deployment.apps/web unchanged", True),
        ("deployment.apps/web unchanged (server dry run)", True),
        ("deployment.apps/web patched", False),
        ("deployment.apps/web patched (server dry run)", False),
        ("deployment.apps/web configured (server dry run)", False),
        ("deployment.apps/a unchanged\ndeployment.apps/b configured", False),
        ("", False),  # silence is not evidence of a no-op
        ("Warning: --record is deprecated\ndeployment.apps/web patched (no change)", True),
    ],
)
def test_reports_no_change(output, expected):
    assert reports_no_change(output) is expected


def test_preflight_rejects_a_write_the_server_would_not_apply():
    from types import SimpleNamespace

    action = SimpleNamespace(
        id="a1", execute_command=RS_PATCH, dry_run_command="", verify_command=""
    )
    seen = []

    def run(argv):
        seen.append(argv)
        return "replicaset.apps/web-7bf9698f49 patched (no change) (server dry run)"

    errors = preflight_errors([action], run)
    assert "--dry-run=server" in seen[0]
    assert len(errors) == 1 and "不会改变任何对象" in errors[0] and "a1" in errors[0]
    assert (
        preflight_errors([action], lambda argv: "replicaset.apps/x patched (server dry run)") == []
    )


# ---- execution: every write a no-op -> no recovery wait --------------------------------


def _run(write_output):
    draft, _, _, _ = fixture()
    clock = _Clock()
    watched = []

    def runner(argv):
        if argv[1] == "get":
            watched.append(argv)
            return _pod(ready=False, waiting="ContainerCreating")
        return write_output

    events = list(
        PodRepairExecutor(runner=runner).run(
            "noop",
            draft,
            mode="auto",
            recovery=RecoveryConfig(timeout_seconds=60, poll_seconds=5, settle_seconds=0),
            watch_factory=_factory(clock),
        )
    )
    return events, clock


def test_a_no_op_write_finishes_failed_without_waiting_for_recovery():
    events, clock = _run("deployment.apps/api patched (no change)")
    final = events[-1]
    assert final["status"] == "failed" and final["error_code"] == "no_change"
    assert "没有改变任何对象" in final["reason"] and "kubectl set resources" in final["reason"]
    assert not [e for e in events if e["type"] == "remediation_recovery"]
    assert clock.now == 0  # no polling at all


def test_a_real_change_still_goes_to_the_recovery_watch():
    events, _ = _run("deployment.apps/api resource requirements updated")
    assert [e for e in events if e["type"] == "remediation_recovery"]
    assert events[-1]["status"] == "not_recovered"
