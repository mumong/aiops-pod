"""Deletion facts from the lifecycle tool survive the core projection (attention Pods)."""

from app.core.context import lifecycle_core


def _payload(**extra):
    return {
        "contract_version": "pod-lifecycle.v1",
        "status": "success",
        "observed_at": "2026-10-16T11:29:19+00:00",
        "pods": [{
            "namespace": "aiops-case-11", "name": "workload", "uid": "u1", "phase": "Running",
            "deletion_timestamp": "2026-10-16T11:10:19Z", "conditions": [], "containers": [], **extra,
        }],
    }


def test_finalizers_grace_and_terminating_seconds_are_kept():
    core = lifecycle_core.lifecycle_core(_payload(finalizers=["aiops.lab/hold"], deletion_grace_period_seconds=0, terminating_seconds=1140))
    entity = core["entities"][0]
    assert entity["finalizers"] == ["aiops.lab/hold"]
    assert entity["deletion_grace_period_seconds"] == 0
    assert entity["terminating_seconds"] == 1140
    assert lifecycle_core._nominal(entity) is False


def test_empty_finalizers_are_not_emitted():
    core = lifecycle_core.lifecycle_core(_payload(finalizers=[], terminating_seconds=None))
    assert "finalizers" not in core["entities"][0] and "terminating_seconds" not in core["entities"][0]
