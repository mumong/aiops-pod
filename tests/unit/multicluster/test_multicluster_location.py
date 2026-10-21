"""One deep diagnosis over several clusters (spec US6, FR-019)."""

import pytest

from app.core import multicluster
from app.core.workflow.multicluster_location import per_cluster_location
from app.core.workflow.pod_detection import after_location
from tests.unit.multicluster.test_scope_routing import CONFIG, EDGE88, EDGE89


@pytest.fixture
def multi(tmp_path, monkeypatch):
    path = tmp_path / "clusters.yaml"
    path.write_text(CONFIG)
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(path))
    multicluster.reset()
    yield
    multicluster.reset()


STATE = {
    "question": "检查 edge-88 和 edge-89",
    "request_contract": {
        "clusters": [EDGE88, EDGE89],
        "cluster_mode": "multiple",
        "cluster_labels": ["edge-88", "edge-89"],
        "scope": "cluster",
    },
    "thinking_events": [{"type": "old"}],
}


def target(tid, ns, pod, status="investigate"):
    return {
        "target_id": tid,
        "entity": {"kind": "Pod", "namespace": ns, "name": pod, "uid": ""},
        "issue": f"{pod} 异常",
        "status": status,
        "status_reason": "" if status == "investigate" else "ok",
        "evidence_refs": [],
    }


def layer_output(targets, groups, assessment="abnormal"):
    return {
        "diagnosis_handoff": {
            "contract_version": "location-handoff.v1",
            "targets": targets,
            "coverage": "complete",
            "pod_assessment": {
                "status": assessment,
                "scope": "s",
                "observed_at": "t",
                "reason": "r",
            },
        },
        "autonomous_groups": groups,
        "layer_analysis": "分析",
        "thinking_events": [{"type": "old"}, {"type": "new"}],
    }


def fake_runs(outputs):
    seen = []

    def run_one(node, state, cluster):
        seen.append((cluster, state["request_contract"]["clusters"]))
        result = outputs[cluster]
        if isinstance(result, Exception):
            raise result
        return result

    return run_one, seen


REACHABLE = lambda cluster: (True, "")  # noqa: E731


class Node:
    current_run_id = "run1"
    _event_queue = None


def test_each_cluster_located_on_its_own_and_merged(multi):
    run_one, seen = fake_runs(
        {
            EDGE88: layer_output(
                [target("t1", "aiops-case-06", "w1"), target("t2", "aiops-case-08", "w2")],
                [
                    {"group_id": "g1", "target_id": "t1", "question": "q", "entities": []},
                    {"group_id": "g2", "target_id": "t2", "question": "q", "entities": []},
                ],
            ),
            EDGE89: layer_output(
                [target("t1", "aiops-case-06", "w1")],  # same name/namespace, other cluster
                [{"group_id": "g1", "target_id": "t1", "question": "q", "entities": []}],
            ),
        }
    )
    out = per_cluster_location(Node(), STATE, run_one=run_one, probe=REACHABLE)
    assert sorted(seen) == [(EDGE88, [EDGE88]), (EDGE89, [EDGE89])]
    ids = [t["target_id"] for t in out["diagnosis_handoff"]["targets"]]
    assert ids == ["edge-88/t1", "edge-88/t2", "edge-89/t1"]
    groups = out["autonomous_groups"]
    assert [g["group_id"] for g in groups] == ["g1", "g2", "g3"]
    assert [(g["cluster"], g["cluster_label"], g["target_id"]) for g in groups] == [
        (EDGE88, "edge-88", "edge-88/t1"),
        (EDGE88, "edge-88", "edge-88/t2"),
        (EDGE89, "edge-89", "edge-89/t1"),
    ]
    assert "集群 edge-88" in out["layer_analysis"] and "集群 edge-89" in out["layer_analysis"]
    assert out["thinking_events"] == [{"type": "old"}, {"type": "new"}, {"type": "new"}]
    assert after_location({**STATE, **out}) == "parallel_evidence"


def test_one_failing_cluster_does_not_block_the_others(multi):
    run_one, _ = fake_runs(
        {
            EDGE88: layer_output(
                [target("t1", "a", "w1"), target("t2", "a", "w2")],
                [
                    {"group_id": "g1", "target_id": "t1", "question": "q", "entities": []},
                    {"group_id": "g2", "target_id": "t2", "question": "q", "entities": []},
                ],
            ),
            EDGE89: RuntimeError("cluster_unreachable"),
        }
    )
    out = per_cluster_location(Node(), STATE, run_one=run_one, probe=REACHABLE)
    assert len(out["autonomous_groups"]) == 2
    assert out["diagnosis_handoff"]["coverage"] == "partial"
    assert (
        "edge-89" in out["diagnosis_handoff"]["coverage_note"]
        and "不完整" in out["layer_analysis"]
    )
    assert any("edge-89" in w for w in out["warnings"])


def test_a_single_group_narrows_the_run_to_its_cluster(multi):
    run_one, _ = fake_runs(
        {
            EDGE88: layer_output(
                [target("t1", "a", "w1")],
                [{"group_id": "g1", "target_id": "t1", "question": "q", "entities": []}],
            ),
            EDGE89: layer_output([], [], assessment="healthy"),
        }
    )
    out = per_cluster_location(Node(), STATE, run_one=run_one, probe=REACHABLE)
    assert out["request_contract"]["clusters"] == [EDGE88]
    assert out["request_contract"]["cluster_labels"] == ["edge-88"]
    assert after_location({**STATE, **out}) == "evidence"


def test_all_healthy_goes_to_conclusion(multi):
    run_one, _ = fake_runs(
        {EDGE88: layer_output([], [], "healthy"), EDGE89: layer_output([], [], "healthy")}
    )
    out = per_cluster_location(Node(), STATE, run_one=run_one, probe=REACHABLE)
    assert out["autonomous_groups"] == []
    assert after_location({**STATE, **out}) == "conclusion"


def test_case_titles_name_the_cluster():
    from types import SimpleNamespace

    from app.core.workflow.case_report import conclude_cases

    group = {
        "group_id": "g1",
        "target_id": "edge-88/t1",
        "cluster_label": "edge-88",
        "entities": [{"namespace": "a", "name": "w1"}],
    }
    state = {
        "question": "q",
        "autonomous_groups": [group],
        "autonomous_group_results": [
            {
                "group_id": "g1",
                "status": "completed",
                "case_result": {
                    "group_id": "g1",
                    "target": group,
                    "summary": "s",
                    "report": "r",
                    "execution_status": "completed",
                    "outcome": "abnormal",
                    "certainty": "supported",
                    "key_facts": [],
                    "unresolved": [],
                    "runbook_refs": [],
                    "result_ref": "x",
                },
            }
        ],
    }
    node = SimpleNamespace(
        _call_llm=lambda *a, **k: (SimpleNamespace(result='{"overview":"o"}'), []),
        _archive_node_input=lambda _: None,
        _archive_node_output=lambda _: None,
    )
    out = conclude_cases(node, state)
    assert "## edge-88 · 异常组 1 · a/w1" in out["conclusion"]


def test_router_allows_deep_diagnosis_over_several_clusters_but_not_repair(multi):
    from types import SimpleNamespace

    from app.core.workflow.nodes.request_router import RequestRouterNode

    def route(values):
        node = RequestRouterNode()
        node.ai_call = SimpleNamespace(call_structured=lambda **k: (k["schema"](**values), ""))
        return node.execute({"question": "检查 edge-88 和 edge-89"})

    deep = route(
        {
            "route": "full_diagnosis",
            "task": "diagnose",
            "scope": "cluster",
            "cluster_mode": "multiple",
            "clusters": ["edge-88", "edge-89"],
        }
    )
    assert deep["request_route"] == "full_diagnosis"
    repair = route(
        {
            "route": "remediation",
            "task": "repair",
            "scope": "cluster",
            "cluster_mode": "multiple",
            "clusters": ["edge-88", "edge-89"],
        }
    )
    assert repair["request_route"] == "clarify" and "一个集群" in repair["conclusion"]


def test_lane_state_built_by_branch_state_binds_the_group_cluster(multi):
    from app.core.workflow.stage_material import branch_state

    group = {
        "group_id": "g2",
        "target_id": "edge-89/t1",
        "cluster": EDGE89,
        "cluster_label": "edge-89",
        "question": "q",
        "entities": [],
    }
    local = branch_state(STATE, group)
    assert multicluster.run_clusters(local) == [EDGE89]


def test_unreachable_cluster_is_not_located_and_reported(multi):
    run_one, seen = fake_runs(
        {
            EDGE88: layer_output(
                [target("t1", "a", "w1"), target("t2", "a", "w2")],
                [
                    {"group_id": "g1", "target_id": "t1", "question": "q", "entities": []},
                    {"group_id": "g2", "target_id": "t2", "question": "q", "entities": []},
                ],
            ),
            EDGE89: layer_output(
                [], [], "healthy"
            ),  # would look "healthy" if it ran with failing tools
        }
    )
    out = per_cluster_location(
        Node(), STATE, run_one=run_one, probe=lambda c: (c != EDGE89, "cluster_unreachable")
    )
    assert [c for c, _ in seen] == [EDGE88]
    assert out["cluster_failures"] == ["edge-89：集群当前不可达（cluster_unreachable），未能检查"]
    assert out["diagnosis_handoff"]["coverage"] == "partial"


def test_sub_runs_are_told_which_cluster_they_locate(multi):
    run_one, _ = fake_runs(
        {EDGE88: layer_output([], [], "healthy"), EDGE89: layer_output([], [], "healthy")}
    )
    questions = []

    def spy(node, state, cluster):
        questions.append(state["question"])
        return run_one(node, state, cluster)

    per_cluster_location(Node(), STATE, run_one=spy, probe=lambda c: (True, ""))
    assert any("本次只定位集群 edge-88" in q for q in questions)
    assert any("本次只定位集群 edge-89" in q for q in questions)


def test_report_states_unfinished_clusters_in_code_not_by_the_model():
    from types import SimpleNamespace

    from app.core.workflow.case_report import conclude_cases

    group = {
        "group_id": "g1",
        "target_id": "edge-88/t1",
        "cluster_label": "edge-88",
        "entities": [{"namespace": "a", "name": "w1"}],
    }
    state = {
        "question": "q",
        "cluster_failures": ["edge-89：集群当前不可达（cluster_unreachable），未能检查"],
        "autonomous_groups": [group],
        "autonomous_group_results": [
            {
                "group_id": "g1",
                "status": "completed",
                "case_result": {
                    "group_id": "g1",
                    "target": group,
                    "summary": "s",
                    "report": "r",
                    "execution_status": "completed",
                    "outcome": "abnormal",
                    "certainty": "supported",
                    "key_facts": [],
                    "unresolved": [],
                    "runbook_refs": [],
                    "result_ref": "x",
                },
            }
        ],
    }
    node = SimpleNamespace(
        _call_llm=lambda *a, **k: (SimpleNamespace(result='{"overview":"edge-89 无异常"}'), []),
        _archive_node_input=lambda _: None,
        _archive_node_output=lambda _: None,
    )
    out = conclude_cases(node, state)
    assert (
        "未完成检查的集群：edge-89：集群当前不可达（cluster_unreachable），未能检查"
        in out["conclusion"]
    )
