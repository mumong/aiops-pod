import json
from copy import deepcopy

import pytest

from app.core.context.observability_projection import _selection_priority, _summary_evidence
from app.core.remediation.agent import _verify_establishes_terminal_success
from app.core.workflow.pod_detection import after_location, assess_delivery


def healthy():
    return {
        "coverage": "complete",
        "targets": [],
        "pod_assessment": {
            "status": "healthy",
            "scope": "ns",
            "observed_at": "2026-10-13T00:00:00Z",
            "recent_signals_reviewed": True,
            "unresolved": [],
            "evidence_refs": ["/raw/1"],
            "reason": "当前状态与近期线索已核实",
        },
    }


def events():
    return [
        {
            "type": "tool_result",
            "status": "success",
            "raw_ref": "/raw/1",
            "result": '{"status":"success","next_continue_token":null}',
        }
    ]


def test_complete_no_pending_skips_deeper_collection():
    result = assess_delivery(healthy(), events())
    assert result["pod_assessment"]["status"] == "healthy"
    assert after_location({"diagnosis_handoff": result}) == "conclusion"


def test_history_limitation_alone_does_not_invalidate_current_health():
    records = events()
    records[0]["result"] = json.dumps(
        {"status": "success", "history_complete": False, "restart_count_in_window": None}
    )
    assert assess_delivery(healthy(), records)["pod_assessment"]["status"] == "healthy"


def test_producer_source_id_is_accepted_but_descriptive_prose_is_not():
    data = healthy()
    data["pod_assessment"]["evidence_refs"] = ["source-1"]
    material = {
        "protected_handoff": {"lifecycle_core": {"sources": {"source-1": {"raw_ref": "/raw/1"}}}}
    }
    assert assess_delivery(data, events(), material)["pod_assessment"]["status"] == "healthy"
    data["pod_assessment"]["evidence_refs"].append("looked at all pods")
    assert assess_delivery(data, events(), material)["pod_assessment"]["status"] == "inconclusive"


@pytest.mark.parametrize(
    "change", ["coverage", "recent", "unresolved", "deferred", "invented_ref", "no_refs"]
)
def test_inconsistent_healthy_becomes_inconclusive(change):
    data = healthy()
    if change == "coverage":
        data["coverage"] = "partial"
    if change == "recent":
        data["pod_assessment"]["recent_signals_reviewed"] = False
    if change == "unresolved":
        data["pod_assessment"]["unresolved"] = ["近期重启尚未解释"]
    if change == "deferred":
        data["targets"] = [{"status": "deferred"}]
    if change == "invented_ref":
        data["pod_assessment"]["evidence_refs"] = ["/invented"]
    if change == "no_refs":
        data["pod_assessment"]["evidence_refs"] = []
    assert assess_delivery(data, events())["pod_assessment"]["status"] == "inconclusive"


@pytest.mark.parametrize(
    "extra",
    [
        {"type": "execution_incomplete"},
        {"type": "tool_result", "status": "failed"},
        {"type": "tool_result", "result": '{"status":"error"}'},
        {"type": "tool_result", "result": '{"next_continue_token":"next"}'},
    ],
)
def test_incomplete_source_never_healthy(extra):
    assert (
        assess_delivery(healthy(), events() + [extra])["pod_assessment"]["status"]
        == "inconclusive"
    )


def test_completed_pagination_does_not_force_extra_diagnosis():
    records = events() + [
        {"type": "tool_result", "result": '{"next_continue_token":"next"}'},
        {"type": "tool_result", "tool_args": {"continue_token": "next"}, "result": "{}"},
    ]
    assert assess_delivery(healthy(), records)["pod_assessment"]["status"] == "healthy"


@pytest.mark.parametrize(
    "issue", ["近10分钟重启，当前Running/Ready", "Running但未Ready", "删除中", "业务失败但Pod就绪"]
)
def test_unresolved_target_remains_investigation(issue):
    data = healthy()
    data["targets"] = [{"status": "investigate", "issue": issue}]
    result = assess_delivery(data, events())
    assert result["pod_assessment"]["status"] == "inconclusive"
    assert after_location({"diagnosis_handoff": result}) == "evidence"
    assert (
        after_location({"diagnosis_handoff": result, "autonomous_groups": [{}, {}]})
        == "parallel_evidence"
    )


def test_recovered_restart_can_be_healthy_after_agent_verifies():
    data = healthy()
    data["targets"] = [{"status": "assessed", "status_reason": "重启已核实，当前恢复，无持续异常"}]
    assert assess_delivery(data, events())["pod_assessment"]["status"] == "healthy"


def test_missing_assessment_never_short_circuits_legacy_input():
    assert (
        after_location({"diagnosis_handoff": {"coverage": "complete", "targets": []}})
        == "evidence"
    )


def test_zero_and_nonzero_have_equal_priority_and_identity_labels_survive():
    fact = {
        "metric": "up",
        "value": 0,
        "labels": {"instance": "a", "job": "b", "node": "n", "service": "s"},
    }
    assert _selection_priority(fact) == _selection_priority({**fact, "value": 1})
    assert _summary_evidence(deepcopy(fact), compact=True)["labels"] == fact["labels"]


@pytest.mark.parametrize(
    "text", ["Running 1/1", "Ready=True Running", "successfully rolled out", "old log Error"]
)
def test_plain_text_is_not_machine_verified_recovery(text):
    assert not _verify_establishes_terminal_success(
        "kubectl rollout status deployment/x", text, False
    )


def test_verified_healthy_check_is_reported_without_a_model_call():
    # Live 2026-10-19 (run 7e55538bc3c648d7): after location the conclusion model took
    # 39 s to restate a check the code had already verified.
    from app.core.workflow.nodes import query_answer

    node = query_answer.QueryConclusionNode()
    node._archive_node_input = lambda payload: None
    node._archive_node_output = lambda output: None
    node._call_llm = lambda *a, **k: (_ for _ in ()).throw(AssertionError("model called"))
    assessment = {
        "status": "healthy",
        "scope": "全集群 Pod（108 个容器）",
        "observed_at": "2026-10-19T09:58:08Z",
        "recent_signals_reviewed": True,
        "unresolved": [],
        "evidence_refs": ["/archive/tools/001.raw.txt"],
        "reason": "全部 Running 且 Ready，近 10 分钟无终止或重启",
    }
    out = node.execute(
        {
            "question": "我的集群有什么问题",
            "request_time_utc": "fixed",
            "request_contract": {"route": "full_diagnosis", "scope": "cluster"},
            "diagnosis_handoff": {
                "pod_assessment": assessment,
                "targets": [],
                "coverage": "complete",
            },
        }
    )
    answer = out["query_answer"]
    assert (
        answer["status"] == "answered" and answer["evidence_refs"] == assessment["evidence_refs"]
    )
    for text in (
        "未发现 Pod 异常",
        "全集群 Pod（108 个容器）",
        "2026-10-19T09:58:08Z",
        "全部 Running",
    ):
        assert text in out["conclusion"]


# ---- live 2026-10-19 (runs 805ff1d4, 9d9f3ecf): a fully Running/Ready cluster stayed
# inconclusive because of the guard's own notices and a superseded first page ----------


def _lifecycle(ref, result, args=None, **extra):
    return {
        "type": "tool_result",
        "tool_name": "query_pod_lifecycle",
        "tool_args": args or {"record_type": "pod"},
        "status": "success",
        "raw_ref": ref,
        "result": json.dumps(result),
        **extra,
    }


def test_repeat_notices_and_idle_finish_do_not_downgrade_health():
    records = events() + [
        {
            "type": "tool_result",
            "tool_name": "query_pod_lifecycle",
            "status": "error",
            "deduplicated": True,
            "result": "【重复调用，结果未变化】",
        },
        {"type": "loop_finished", "reason": "idle_round"},
    ]
    assert assess_delivery(healthy(), records)["pod_assessment"]["status"] == "healthy"


def test_page_superseded_by_a_complete_query_of_the_same_scope_is_not_a_gap():
    first = _lifecycle(
        "/raw/a", {"status": "success", "pagination": {"next_continue_token": "t1"}}
    )
    complete = _lifecycle(
        "/raw/1",
        {"status": "success", "groups": [{"phase": "Running", "count": 108}]},
        args={"record_type": "pod", "group_by": "phase"},
    )
    assert assess_delivery(healthy(), [first, complete])["pod_assessment"]["status"] == "healthy"
    other_scope = _lifecycle("/raw/1", {"status": "success"}, args={"namespace": "other"})
    assert (
        assess_delivery(healthy(), [first, other_scope])["pod_assessment"]["status"]
        == "inconclusive"
    )


def test_uncited_health_uses_the_successful_inventory_reads():
    data = healthy()
    data["pod_assessment"]["evidence_refs"] = []
    records = [_lifecycle("/raw/inv", {"status": "success"})]
    result = assess_delivery(data, records)["pod_assessment"]
    assert result["status"] == "healthy" and result["evidence_refs"] == ["/raw/inv"]


def test_unrelated_failed_query_is_noted_once_inventory_is_complete():
    records = [
        _lifecycle("/raw/1", {"status": "success"}),
        {
            "type": "tool_result",
            "tool_name": "kubernetes_tabular_query",
            "status": "error",
            "result": "Command failed (exit 1)",
        },
    ]
    result = assess_delivery(healthy(), records)["pod_assessment"]
    assert result["status"] == "healthy" and "kubernetes_tabular_query" in result["reason"]
    failed_inventory = [_lifecycle("/raw/1", {"status": "error"}, status="error")]
    assert (
        assess_delivery(healthy(), failed_inventory)["pod_assessment"]["status"] == "inconclusive"
    )
