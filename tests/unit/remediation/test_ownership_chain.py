"""Writes go to the top of the ownerReferences chain, whatever the workload kind.

Live 2026-10-19 (job fb639f92ad5c4a32): the plan patched the ReplicaSet's template; the
Deployment rewrote it, the command "succeeded", recovery timed out.
"""

import json

import pytest

from app.core.remediation.ownership import (
    ControllerChain,
    OwnerLink,
    chains_for_targets,
    managed_write_error,
    resolve_controller_chain,
)

POD = {
    "metadata": {
        "name": "web-7bf9698f49-8xrps",
        "uid": "pod-uid",
        "ownerReferences": [
            {
                "apiVersion": "apps/v1",
                "kind": "ReplicaSet",
                "name": "web-7bf9698f49",
                "uid": "rs-uid",
                "controller": True,
            }
        ],
    }
}
RS = {
    "metadata": {
        "name": "web-7bf9698f49",
        "uid": "rs-uid",
        "ownerReferences": [
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "name": "web",
                "uid": "dep-uid",
                "controller": True,
            }
        ],
    }
}
DEP = {"metadata": {"name": "web", "uid": "dep-uid"}}


def _runner(objects, calls=None):
    def run(command):
        if calls is not None:
            calls.append(command)
        for key, obj in objects.items():
            if key in command:
                return json.dumps(obj)
        raise RuntimeError("Error from server (NotFound): not found")

    return run


def test_chain_walks_pod_replicaset_deployment_with_read_only_gets():
    calls = []
    chain = resolve_controller_chain(
        "ns",
        "web-7bf9698f49-8xrps",
        _runner(
            {
                "pod/web-7bf9698f49-8xrps": POD,
                "replicaset/web-7bf9698f49": RS,
                "deployment/web": DEP,
            },
            calls,
        ),
    )
    assert [link.label() for link in chain.links] == [
        "Pod/web-7bf9698f49-8xrps",
        "ReplicaSet/web-7bf9698f49",
        "Deployment/web",
    ]
    assert chain.root.label() == "Deployment/web" and chain.complete
    assert all(c.startswith("kubectl get ") and "-o json" in c for c in calls)
    assert chain.managed_by("replicaset", "web-7bf9698f49").label() == "Deployment/web"
    assert chain.managed_by("rs", "web-7bf9698f49").label() == "Deployment/web"
    assert chain.managed_by("deployment", "web") is None  # the root is nobody's member


def test_bare_pod_has_no_root_and_lookup_failure_is_incomplete_not_fatal():
    bare = resolve_controller_chain(
        "ns", "solo", _runner({"pod/solo": {"metadata": {"name": "solo", "uid": "u"}}})
    )
    assert bare.root is None and bare.complete and bare.pod.uid == "u"
    missing = resolve_controller_chain("ns", "gone", _runner({}))
    assert missing.links[0].name == "gone" and not missing.complete
    partial = resolve_controller_chain(
        "ns", "web-7bf9698f49-8xrps", _runner({"pod/web-7bf9698f49-8xrps": POD})
    )
    assert [l.kind for l in partial.links] == ["Pod", "ReplicaSet"] and not partial.complete


def test_cronjob_job_chain_is_the_same_rule():
    pod = {
        "metadata": {
            "name": "run-1-abc",
            "ownerReferences": [
                {"apiVersion": "batch/v1", "kind": "Job", "name": "run-1", "controller": True}
            ],
        }
    }
    job = {
        "metadata": {
            "name": "run-1",
            "ownerReferences": [
                {
                    "apiVersion": "batch/v1",
                    "kind": "CronJob",
                    "name": "nightly",
                    "controller": True,
                }
            ],
        }
    }
    chain = resolve_controller_chain(
        "ns",
        "run-1-abc",
        _runner(
            {
                "pod/run-1-abc": pod,
                "job/run-1": job,
                "cronjob/nightly": {"metadata": {"name": "nightly"}},
            }
        ),
    )
    assert managed_write_error(
        'kubectl patch job run-1 -n ns -p \'{"spec":{"suspend":true}}\'', chain
    ).startswith("job/run-1 由 CronJob/nightly 管理")
    assert (
        managed_write_error(
            'kubectl patch cronjob nightly -n ns -p \'{"spec":{"suspend":true}}\'', chain
        )
        == ""
    )


@pytest.fixture
def chain():
    return ControllerChain(
        "ns",
        [
            OwnerLink("Pod", "web-7bf9698f49-8xrps", "pod-uid"),
            OwnerLink("ReplicaSet", "web-7bf9698f49", "rs-uid"),
            OwnerLink("Deployment", "web", "dep-uid"),
        ],
    )


def test_managed_member_write_is_rejected_root_and_reads_are_not(chain):
    patch = 'kubectl patch replicaset web-7bf9698f49 -n ns --type=json -p=\'[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["a"]}]\''
    error = managed_write_error(patch, chain)
    assert (
        "replicaset/web-7bf9698f49 由 Deployment/web 管理" in error and "Deployment/web" in error
    )
    assert managed_write_error("kubectl set image rs/web-7bf9698f49 app=x -n ns", chain) != ""
    assert (
        managed_write_error(patch.replace("replicaset web-7bf9698f49", "deployment web"), chain)
        == ""
    )
    assert managed_write_error("kubectl get rs/web-7bf9698f49 -n ns -o yaml", chain) == ""
    assert managed_write_error("kubectl rollout status deployment/web -n ns", chain) == ""
    assert (
        managed_write_error("kubectl patch rs other -n ns -p '{}'", chain) == ""
    )  # not in this chain
    assert managed_write_error(patch, None) == ""


def test_chains_for_targets_reads_each_pod_once():
    calls = []
    targets = [
        {
            "entities": [
                {"kind": "Pod", "namespace": "ns", "name": "web-7bf9698f49-8xrps"},
                {"kind": "Service", "namespace": "ns", "name": "web"},
            ]
        },
        {"entities": [{"kind": "Pod", "namespace": "ns", "name": "web-7bf9698f49-8xrps"}]},
    ]
    chains = chains_for_targets(
        targets,
        _runner(
            {
                "pod/web-7bf9698f49-8xrps": POD,
                "replicaset/web-7bf9698f49": RS,
                "deployment/web": DEP,
            },
            calls,
        ),
    )
    assert list(chains) == ["ns/web-7bf9698f49-8xrps"] and len(calls) == 3


# ---- RepairDraft binding -------------------------------------------------------------


def _draft(command, **target_overrides):
    return {
        "intent": "fix",
        "scope": "ns",
        "status": "answered",
        "answer": "plan",
        "targets": [
            {
                "namespace": "ns",
                "pod": "web-7bf9698f49-8xrps",
                "group_id": "g1",
                **target_overrides,
            }
        ],
        "actions": [
            {
                "id": "a1",
                "group_id": "g1",
                "description": "d",
                "risk": "low",
                "execute_command": command,
                "rollback_advice": "r",
            }
        ],
    }


def test_bound_draft_rejects_replicaset_write_and_names_the_deployment(chain):
    from app.core.workflow.nodes.remediation import RepairDraft

    bound = RepairDraft.with_controller_chains({"ns/web-7bf9698f49-8xrps": chain})
    assert bound.__name__ == "RepairDraft" and RepairDraft.controller_chains == {}
    with pytest.raises(ValueError, match="Deployment/web"):
        bound.model_validate(
            _draft(
                'kubectl patch replicaset web-7bf9698f49 -n ns --type=json -p=\'[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["a"]}]\''
            )
        )
    ok = bound.model_validate(
        _draft(
            'kubectl patch deployment web -n ns --type=json -p=\'[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["a"]}]\''
        )
    )
    assert ok.actions[0].execute_command.startswith("kubectl patch deployment web")


def test_bound_draft_fills_owner_identity_from_the_cluster_not_the_model(chain):
    from app.core.workflow.nodes.remediation import RepairDraft

    bound = RepairDraft.with_controller_chains({"ns/web-7bf9698f49-8xrps": chain})
    draft = bound.model_validate(
        _draft(
            "kubectl get pod/web-7bf9698f49-8xrps -n ns",
            owner_kind="ReplicaSet",
            owner_name="web-7bf9698f49",
        )
    )
    target = draft.targets[0]
    assert (target.owner_kind, target.owner_name, target.owner_uid, target.pod_uid) == (
        "Deployment",
        "web",
        "dep-uid",
        "pod-uid",
    )
    # The model's guess of the controller is replaced, so the owner-consistency check
    # now compares against the Deployment: a different deployment name is still rejected.
    with pytest.raises(ValueError, match="控制器"):
        bound.model_validate(_draft("kubectl patch deployment web-7bf9698f49 -n ns -p '{}'"))
    # Unbound schema: nothing is enforced or filled.
    plain = RepairDraft.model_validate(
        _draft(
            "kubectl get pod/web-7bf9698f49-8xrps -n ns",
            owner_kind="ReplicaSet",
            owner_name="web-7bf9698f49",
        )
    )
    assert plain.targets[0].owner_kind == "ReplicaSet"


def test_planning_node_injects_chain_facts_and_binds_the_schema(monkeypatch):
    from types import SimpleNamespace

    from app.core.workflow.nodes import remediation as module

    node = module.RemediationNode()
    node.ai_call = SimpleNamespace()
    node._prepare_query_tools = lambda: ""
    chain = ControllerChain(
        "ns", [OwnerLink("Pod", "p1", "u"), OwnerLink("Deployment", "web", "d")]
    )
    monkeypatch.setattr(module, "chains_for_targets", lambda targets, runner: {"ns/p1": chain})
    seen = {}

    def collect(question, prompt, **kw):
        seen["material"] = json.loads(question)
        seen["schema"] = kw["response_schema"]
        return SimpleNamespace(
            result=json.dumps(
                {
                    "intent": "r",
                    "scope": "p1",
                    "status": "answered",
                    "answer": "x",
                    "targets": [],
                    "actions": [],
                }
            )
        ), []

    node._call_llm = collect
    node.execute(
        {
            "question": "fix",
            "repair_context": {
                "diagnosis": {
                    "payload": {
                        "group_id": "g1",
                        "groups": [
                            {
                                "target": {
                                    "entities": [{"kind": "Pod", "namespace": "ns", "name": "p1"}]
                                }
                            }
                        ],
                    }
                }
            },
        }
    )
    assert seen["material"]["controller_chains"] == {"ns/p1": chain.to_dict()}
    assert (
        seen["schema"].controller_chains == {"ns/p1": chain}
        and seen["schema"].__name__ == "RepairDraft"
    )


def test_planning_node_resolves_chains_from_the_request_without_a_diagnosis(monkeypatch):
    """The node runs on its own too ("修复 ns/p1"): its targets come from the request."""

    from app.core.workflow.nodes import remediation as module

    node = module.RemediationNode()
    seen = {}

    def chains(targets, runner):
        seen["targets"] = targets
        return {}

    monkeypatch.setattr(module, "chains_for_targets", chains)
    node._controller_chains({}, {"namespaces": ["ns"], "pod_names": ["p1", "p2"], "scope": "pod"})
    assert seen["targets"] == [
        {
            "entities": [
                {"kind": "Pod", "namespace": "ns", "name": "p1"},
                {"kind": "Pod", "namespace": "ns", "name": "p2"},
            ]
        }
    ]
    seen.clear()
    node._controller_chains({}, {"namespaces": ["a", "b"], "pod_names": ["p1"]})
    assert "targets" not in seen  # ambiguous namespace: nothing guessed
