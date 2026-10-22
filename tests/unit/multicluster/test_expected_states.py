"""Operator-declared expected states (Boss 2026-10-22, run e43e8298).

xnet-management runs leader election: one replica Ready, standbys 0/1 Running.
A declared standby is excluded only when live data matches the declaration.
"""

import json

import pytest

from app.core import multicluster
from app.core.workflow.expected_states import apply_expected_states
from tests.unit.multicluster.test_scope_routing import CENTER, CONFIG, EDGE88

RULE = {
    "cluster": "center",
    "namespace": "xnet",
    "workload": "Deployment/xnet-management",
    "reason": "主备选举，同一时间只有 1 个副本 Ready",
    "healthy_when": {"ready_replicas_min": 1},
}
STATE = {"request_contract": {"clusters": [CENTER], "cluster_mode": "single"}}


@pytest.fixture(autouse=True)
def multi(tmp_path, monkeypatch):
    path = tmp_path / "clusters.yaml"
    path.write_text(CONFIG)
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(path))
    multicluster.reset()
    yield
    multicluster.reset()


def target(name, namespace="xnet"):
    return {
        "target_id": name,
        "entity": {"kind": "Pod", "namespace": namespace, "name": name},
        "issue": "Running 但未 Ready",
        "status": "investigate",
    }


def handoff(*targets):
    return {
        "targets": list(targets),
        "pod_assessment": {"status": "abnormal", "scope": "s", "observed_at": "t", "reason": "r"},
    }


def cluster(ready=1, waiting=False, rs_owner="xnet-management"):
    state = {"waiting": {"reason": "CrashLoopBackOff"}} if waiting else {"running": {}}
    objects = {
        ("pod",): {
            "metadata": {
                "ownerReferences": [
                    {"kind": "ReplicaSet", "name": "xnet-management-c59b67d75", "controller": True}
                ]
            },
            "status": {"phase": "Running", "containerStatuses": [{"state": state}]},
        },
        ("replicaset",): {
            "metadata": {
                "ownerReferences": [{"kind": "Deployment", "name": rs_owner, "controller": True}]
            }
        },
        ("deployment",): {"spec": {"replicas": 3}, "status": {"readyReplicas": ready}},
    }
    calls = []

    def run(argv):
        calls.append(argv)
        return json.dumps(objects[(argv[1],)])

    run.calls = calls
    return run


def test_satisfied_declaration_excludes_and_names_the_pod():
    out, excluded = apply_expected_states(handoff(target("m6h2f")), STATE, cluster(), [RULE])
    assert out["targets"][0]["status"] == "excluded"
    assert "1/3 Ready" in out["targets"][0]["status_reason"]
    assert excluded == [
        "center xnet/m6h2f（主备选举，同一时间只有 1 个副本 Ready；Deployment/xnet-management 1/3 Ready）"
    ]
    # Nothing left to diagnose: the location result becomes healthy, with the reason.
    assert out["pod_assessment"]["status"] == "healthy"
    assert "运维声明" in out["pod_assessment"]["reason"]


@pytest.mark.parametrize(
    "run",
    [
        cluster(ready=0),  # no replica serves: really abnormal
        cluster(waiting=True),  # a standby that crashes is not "only unready"
        cluster(rs_owner="other"),  # a different workload in the same namespace
    ],
)
def test_unmet_declaration_keeps_the_investigation(run):
    out, excluded = apply_expected_states(handoff(target("m6h2f")), STATE, run, [RULE])
    assert out["targets"][0]["status"] == "investigate" and excluded == []
    assert out["pod_assessment"]["status"] == "abnormal"


def test_declaration_is_bound_to_its_cluster_and_namespace():
    edge = {"request_contract": {"clusters": [EDGE88], "cluster_mode": "single"}}
    run = cluster()
    out, excluded = apply_expected_states(handoff(target("m6h2f")), edge, run, [RULE])
    assert excluded == [] and run.calls == []
    out, excluded = apply_expected_states(handoff(target("x", "other")), STATE, run, [RULE])
    assert excluded == [] and run.calls == []


def test_unverifiable_target_is_never_excluded():
    def broken(argv):
        raise RuntimeError("cluster_unreachable")

    out, excluded = apply_expected_states(handoff(target("m6h2f")), STATE, broken, [RULE])
    assert out["targets"][0]["status"] == "investigate" and excluded == []


def test_other_abnormal_targets_keep_the_assessment():
    out, excluded = apply_expected_states(
        handoff(target("m6h2f"), target("web", "shop")), STATE, cluster(), [RULE]
    )
    assert [t["status"] for t in out["targets"]] == ["excluded", "investigate"]
    assert out["pod_assessment"]["status"] == "abnormal" and len(excluded) == 1


def test_declarations_are_read_from_the_clusters_config(tmp_path, monkeypatch):
    from app.core.workflow.expected_states import declarations

    path = tmp_path / "c.yaml"
    path.write_text(
        CONFIG + "expected_states:\n  - " + json.dumps(RULE, ensure_ascii=False) + "\n"
    )
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(path))
    assert declarations() == [RULE]


def test_default_runner_calls_kubectl_on_the_target_cluster(monkeypatch):
    """Live 13.0.14: run_argv takes the full argv; without "kubectl" nothing was verified."""
    from app.core.remediation import pod_executor

    seen = []
    fake = cluster()

    def run_argv(argv, cluster=None):
        seen.append((argv[0], cluster))
        return fake(argv[1:])

    monkeypatch.setattr(pod_executor, "run_argv", run_argv)
    out, excluded = apply_expected_states(handoff(target("m6h2f")), STATE, items=[RULE])
    assert len(excluded) == 1 and set(seen) == {("kubectl", CENTER)}
