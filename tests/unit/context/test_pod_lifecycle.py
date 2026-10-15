"""Paginated source facts must reach the model without lossy re-summary."""

import json

from app.core.context.lifecycle_core import INVENTORY_VERSION, inventory_view, lifecycle_core
from app.core.context.observation import ObservationProcessor
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode, DiagnosisStageNode
from app.core.workflow.nodes.query_answer import QueryCollectNode


def _pod(index, namespace="ns", **overrides):
    container = {
        "name": "app",
        "role": "app",
        "ready": True,
        "restart_count_total": 0,
        "state": {"running": {}},
        "last_state": {},
        "termination_within_window": False,
        "restart_count_in_window": None,
    }
    container.update(overrides.pop("container", {}))
    pod = {
        "namespace": namespace,
        "name": f"p{index}",
        "uid": f"uid{index}",
        "node": "node1",
        "phase": "Running",
        "conditions": [{"type": "Ready", "status": "True"}],
        "containers": [container],
    }
    pod.update(overrides)
    return pod


def _list_payload(pods, **extra):
    return {
        "contract_version": "pod-lifecycle.v1",
        "status": "success",
        "coverage": "present",
        "observed_at": "2026-10-15T08:00:00Z",
        "scope": {"namespace": None, "pod": None},
        "returned_count": len(pods),
        "pods": pods,
        **extra,
    }


def test_lifecycle_preserves_large_page_and_recent_termination(tmp_path):
    pods = [
        _pod(
            i,
            container={
                "last_state": {"terminated": {"reason": "OOMKilled", "exitCode": 137}},
                "termination_within_window": True,
            },
        )
        for i in range(50)
    ]
    data = _list_payload(pods, coverage="partial", next_continue_token="opaque")
    raw = json.dumps(data)
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=1000,
        summarizer=lambda *a: "should never replace facts",
    )
    result = processor.process(
        run_id="lifecycle",
        node_id="layer",
        sequence=1,
        tool_name="query_pod_lifecycle",
        raw_content=raw,
    )
    summary = json.loads(result["summary"])
    # Every recently terminated Pod is an attention entity: all 50 stay in full.
    assert [e["name"] for e in summary["entities"]] == [p["name"] for p in pods]
    assert summary["entities"][0]["containers"][0]["last_state"] == {
        "terminated": {"reason": "OOMKilled", "exitCode": 137}
    }
    assert next(iter(summary["sources"].values()))["next_continue_token"] == "opaque"
    assert result["structured"]["pods"] == data["pods"]
    assert result["semantic_success"] is True
    assert result["processor"] == "pod_lifecycle+core"
    assert "query_pod_lifecycle" in DiagnosisStageNode.READ_TOOLS
    assert "query_pod_lifecycle" in DiagnosisEvidenceNode.READ_TOOLS
    assert "query_pod_lifecycle" in QueryCollectNode.READ_TOOLS


def test_cluster_inventory_shows_attention_pods_in_full_and_nominal_pods_as_roster(tmp_path):
    pods = [_pod(i, namespace=f"ns{i % 3}") for i in range(68)]
    pods += [
        _pod(
            100,
            namespace="bad",
            phase="Pending",
            conditions=[{"type": "Ready", "status": "False"}],
            container={"ready": False, "state": {"waiting": {"reason": "ImagePullBackOff"}}},
        ),
        _pod(
            101,
            namespace="bad",
            container={
                "ready": False,
                "state": {"waiting": {"reason": "CrashLoopBackOff"}},
                "last_state": {"terminated": {"reason": "Error", "exitCode": 1}},
                "termination_within_window": True,
                "restart_count_in_window": 3,
            },
        ),
        _pod(102, namespace="bad", deletion_timestamp="2026-10-15T07:59:00Z"),
        _pod(
            103,
            namespace="jobs",
            phase="Succeeded",
            conditions=[{"type": "Ready", "status": "False"}],
            container={
                "ready": False,
                "state": {"terminated": {"reason": "Completed", "exitCode": 0}},
            },
        ),
    ]
    raw = json.dumps(_list_payload(pods))
    processor = ObservationProcessor(archive_root=str(tmp_path), summarizer=lambda *a: "never")
    result = processor.process(
        run_id="inventory",
        node_id="layer",
        sequence=1,
        tool_name="query_pod_lifecycle",
        raw_content=raw,
    )
    summary = json.loads(result["summary"])
    assert result["processor"] == "pod_lifecycle+inventory"
    assert summary["contract_version"] == INVENTORY_VERSION
    assert [e["name"] for e in summary["entities"]] == ["p100", "p101", "p102"]
    assert summary["attention_count"] == 3 and summary["nominal_count"] == 69
    assert summary["nominal_roster"]["jobs"] == ["p103"]
    assert sum(len(v) for v in summary["nominal_roster"].values()) == 69
    assert summary["entities"][1]["containers"][0]["state"] == {
        "waiting": {"reason": "CrashLoopBackOff"}
    }
    # The roster is an order of magnitude smaller than the full core, and the archive keeps everything.
    assert len(result["summary"]) < len(raw) / 4
    assert len(result["structured"]["pods"]) == 72


def test_inventory_view_keeps_single_pod_scope_and_small_nominal_sets_unchanged():
    single = lifecycle_core(
        {**_list_payload([_pod(1)]), "scope": {"namespace": "ns", "pod": "p1"}}
    )
    assert inventory_view(single) is single
    small = lifecycle_core(_list_payload([_pod(i) for i in range(3)]))
    assert inventory_view(small) is small
    # Nominal needs Ready=True; a Running Pod with a not-ready container is attention.
    mixed = lifecycle_core(
        _list_payload([_pod(i) for i in range(4)] + [_pod(9, container={"ready": False})])
    )
    view = inventory_view(mixed)
    assert [e["name"] for e in view["entities"]] == ["p9"] and view["nominal_count"] == 4


def test_lifecycle_errors_are_not_successful_empty_data(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path))
    for raw in ['{"status":"error","coverage":"unknown","error":"Forbidden"}', "not json"]:
        result = processor.process(
            run_id="bad",
            node_id="layer",
            sequence=1,
            tool_name="query_pod_lifecycle",
            raw_content=raw,
        )
        assert result["semantic_success"] is False
        assert result["summary"] == raw
