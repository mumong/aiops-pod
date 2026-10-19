import threading
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.remediation.approval import ApprovalStore
from app.core.remediation.jobs import RepairJobs
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.records import PlanConflict, RecordUnavailable, RepairRecordStore
from tests.unit.remediation.test_pod_executor import fixture


def setup(tmp_path, monkeypatch):
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    jobs.store.save(
        "d",
        "a" * 64,
        None,
        "diagnosis",
        {"groups": [{"group_id": "g1", "analysis": "ONE"}, {"group_id": "g2", "analysis": "TWO"}]},
    )
    monkeypatch.setattr(jobs, "_plan_batch", lambda *args: None)
    return jobs, "a" * 64


def test_idempotent_batch_owner_isolation_revision_only_one_group(tmp_path, monkeypatch):
    jobs, owner = setup(tmp_path, monkeypatch)
    batch = jobs.start(None, owner, "d", "repair")
    assert batch == jobs.start(None, owner, "d", "retry")
    first, second = batch["groups"]
    jobs.store.save(first["job_id"], owner, None, "plan", {"draft": {"answer": "one"}})
    with pytest.raises(RecordUnavailable):
        jobs.detail(first["job_id"], "b" * 64)
    with pytest.raises(PlanConflict):
        jobs.revise(None, owner, first["job_id"], 2, "change")
    new = jobs.revise(None, owner, first["job_id"], 1, "change only g1")
    updated = jobs.batch(batch["batch_id"], owner)
    assert updated["groups"][0]["job_id"] == new["job_id"]
    assert updated["groups"][0]["version"] == 2
    assert updated["groups"][1] == second
    assert jobs.detail(first["job_id"], owner)["status"] == "superseded"
    refreshed = RepairJobs(jobs.store).detail(new["job_id"], owner)
    assert refreshed["feedback"]["text"] == "change only g1"
    assert refreshed["feedback"]["source_version"] == 1
    assert refreshed["feedback"]["target_version"] == 2
    assert refreshed["feedback"]["role"] == "user"
    assert refreshed["history"][0]["plan"]["answer"] == "one"
    assert jobs.detail(second["job_id"], owner)["feedback"] is None
    assert jobs.detail(second["job_id"], owner)["history"] == []
    with pytest.raises(PlanConflict):
        jobs.revise(None, owner, first["job_id"], 1, "stale")


def test_restart_and_immutable_plan_records(tmp_path, monkeypatch):
    jobs, owner = setup(tmp_path, monkeypatch)
    batch = jobs.start(None, owner, "d", "repair")
    restarted = RepairJobs(jobs.store)
    assert restarted.detail(batch["groups"][0]["job_id"], owner)["status"] == "interrupted"
    with pytest.raises(PlanConflict):
        jobs.store.update_payload("d", owner, lambda p: p.clear())
    assert jobs.store.load("d", owner)["payload"]["groups"]


def test_planning_failure_never_enters_execution(tmp_path, monkeypatch):
    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs.start(None, owner, "d", "repair")["groups"][0]
    failure = {"code": "model_connection_interrupted", "message": "模型服务连接中断，方案未生成。"}
    from app.core.workflow.executor import WorkflowExecutor

    monkeypatch.setattr(
        WorkflowExecutor,
        "execute_stream",
        lambda *a, **kw: iter(
            [
                {
                    "type": "final",
                    "repair_record": {"run_id": job["job_id"]},
                    "repair_plan": {"actions": [], "planning_error": failure},
                }
            ]
        ),
    )
    service = SimpleNamespace(
        _build_request_scoped_ai_call=lambda: None, mcp_tools=[], merged_catalog=None
    )
    assert jobs._plan(service, owner, jobs.detail(job["job_id"], owner), "repair") is False
    detail = jobs.detail(job["job_id"], owner)
    assert detail["status"] == "failed"
    assert detail["error_code"] == "model_connection_interrupted"
    assert detail["approval"] is None
    assert detail["status_started_at"] >= detail["created_at"]


def test_api_contract_and_owner(tmp_path, monkeypatch):
    import app.api.repair_routes as routes

    jobs, owner = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(routes, "repair_jobs", jobs)
    monkeypatch.setattr(routes, "get_service", lambda: None)
    app = FastAPI()
    routes.register_repair_routes(app)
    client = TestClient(app)
    assert client.post("/repair/batches", json={"diagnosis_run_id": "d"}).status_code == 401
    client.cookies.set("aiops_query_owner", owner)
    response = client.post("/repair/batches", json={"diagnosis_run_id": "d"})
    assert response.status_code == 200
    assert len(response.json()["groups"]) == 2
    assert (
        client.post(
            "/repair/batches", json={"diagnosis_run_id": "d", "_defer_repair_execution": False}
        ).status_code
        == 422
    )
    job = response.json()["groups"][0]["job_id"]
    assert (
        client.post(
            f"/repair/jobs/{job}/feedback", json={"version": 1, "feedback": " "}
        ).status_code
        == 422
    )
    client.cookies.set("aiops_query_owner", "b" * 64)
    assert client.get(f"/repair/jobs/{job}").status_code == 404


def test_parallel_planning_does_not_wait_for_approval(tmp_path, monkeypatch):
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    owner = "a" * 64
    jobs.store.save(
        "d", owner, None, "diagnosis", {"groups": [{"group_id": "g1"}, {"group_id": "g2"}]}
    )
    barrier = threading.Barrier(2)
    executed = []
    done = threading.Event()
    release = threading.Event()

    def plan(service, identity, job, question):
        barrier.wait(timeout=3)
        return True

    def execute(service, identity, job):
        executed.append(job["group_id"])
        if len(executed) == 2:
            done.set()
        release.wait(3)

    monkeypatch.setattr(jobs, "_plan", plan)
    monkeypatch.setattr(jobs, "_execute", execute)
    try:
        jobs.start(None, owner, "d", "repair")
        assert done.wait(3)
        assert sorted(executed) == ["g1", "g2"]
    finally:
        release.set()


def test_command_execution_is_serial_even_across_legacy_and_grouped_callers():
    entered = threading.Event()
    release = threading.Event()
    second_entered = threading.Event()
    draft = fixture()[0]
    second = deepcopy(draft)
    second["targets"][0]["pod"] = "different-pod"
    draft["actions"][0]["verify_command"] = ""
    second["actions"][0]["verify_command"] = ""

    def slow(args):
        entered.set()
        assert release.wait(3)
        return "ok"

    def fast(args):
        second_entered.set()
        return "ok"

    first = threading.Thread(
        target=lambda: list(
            PodRepairExecutor(ApprovalStore(), slow).run("one", draft, mode="auto")
        )
    )
    other = threading.Thread(
        target=lambda: list(
            PodRepairExecutor(ApprovalStore(), fast).run("two", second, mode="auto")
        )
    )
    first.start()
    try:
        assert entered.wait(3)
        other.start()
        assert not second_entered.wait(0.15)
    finally:
        release.set()
        first.join(3)
        other.join(3)
    assert second_entered.is_set()


def test_planning_scopes_context_and_defers_execution(tmp_path, monkeypatch):
    import app.core.workflow.executor as module

    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs._new_job("batch", owner, "d", {"group_id": "g1"})
    seen = {}

    class Executor:
        def __init__(self, **kw):
            pass

        def execute_stream(self, question, job_id, cancel, overrides):
            seen.update(overrides)
            yield {
                "type": "final",
                "repair_record": {"run_id": job_id},
                "repair_plan": {"actions": []},
            }

    monkeypatch.setattr(module, "WorkflowExecutor", Executor)
    service = SimpleNamespace(_build_request_scoped_ai_call=lambda: object(), mcp_tools=[])
    assert jobs._plan(service, owner, job, "repair")
    assert seen["_repair_group_id"] == "g1"
    assert seen["query_mode"] == "auto"  # default/full would run the legacy diagnosis graph
    assert seen["_defer_repair_execution"] is True
    assert seen["_query_session_key"] == (owner, "repair-" + job["job_id"])


def test_group_job_reuses_auto_policy_and_records_execution(tmp_path, monkeypatch):
    import app.core.remediation.pod_executor as module

    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs._new_job("batch", owner, "d", {"group_id": "g1"})
    draft = fixture()[0]
    jobs.store.save(job["job_id"], owner, None, "plan", {"draft": draft})
    calls = []
    monkeypatch.setattr(module, "run_argv", lambda argv: calls.append(argv) or "observed")
    jobs._execute(
        SimpleNamespace(workflow_config={"remediation": {"enabled": True, "mode": "auto"}}),
        owner,
        job,
    )
    result = jobs.detail(job["job_id"], owner)
    assert result["status"] == "needs_followup" and result["mode"] == "auto"
    assert len(calls) == 2
    assert result["approval"] is None
    assert len(result["events"]) == 4
    assert job["job_id"] not in jobs.cancellations


def test_repair_planning_fan_out_uses_the_diagnosis_lane_limit(tmp_path, monkeypatch):
    # Live 2026-10-19: four repair groups, the 4th waited ~3.5 min because planning
    # read only AIOPS_AUTONOMOUS_PARALLEL_WORKERS (default 3), never the config.
    monkeypatch.delenv("AIOPS_AUTONOMOUS_PARALLEL_WORKERS", raising=False)
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    owner = "a" * 64
    groups = [{"group_id": f"g{i}"} for i in range(1, 5)]
    jobs.store.save("d", owner, None, "diagnosis", {"groups": groups})
    barrier = threading.Barrier(4)
    planned = []
    done = threading.Event()

    def plan(service, identity, job, question):
        barrier.wait(timeout=3)
        planned.append(job["group_id"])
        if len(planned) == 4:
            done.set()
        return False

    monkeypatch.setattr(jobs, "_plan", plan)
    service = SimpleNamespace(workflow_config={"evidence": {"parallel": {"max_workers": 10}}})
    jobs.start(service, owner, "d", "repair")
    assert done.wait(3), "all four groups must plan at the same time"


def _v2(*outcomes):
    return {
        "contract_version": "diagnosis-record.v2",
        "request_contract": {"scope": "cluster"},
        "groups": [
            {
                "group_id": f"g{i}",
                "target": {
                    "target_id": f"t{i}",
                    "entities": [{"kind": "Pod", "namespace": f"ns{i}", "name": f"p{i}"}],
                },
                "status": "completed",
                "diagnosis_result": {"outcome": outcome, "summary": f"s{i}"},
            }
            for i, outcome in enumerate(outcomes, start=1)
        ],
    }


def test_only_unresolved_groups_are_repairable():
    from app.core.remediation.group_context import repairable_groups, select_groups

    record = {"payload": _v2("abnormal", "healthy", "recovered", "inconclusive")}
    assert [g["group_id"] for g in repairable_groups(record)] == ["g1", "g4"]
    assert repairable_groups({"payload": _v2()}) == []  # healthy run: nothing to repair
    groups = repairable_groups(record)
    assert [g["group_id"] for g in select_groups(groups, {"pod_names": ["p4"]})] == ["g4"]
    assert [g["group_id"] for g in select_groups(groups, {"namespaces": ["ns1"]})] == ["g1"]
    assert [g["group_id"] for g in select_groups(groups, {"scope": "cluster"})] == ["g1", "g4"]
    assert select_groups(groups, {"pod_names": ["other"]}) == []


def test_batch_rejects_healthy_diagnosis_and_scopes_to_selected_groups(tmp_path, monkeypatch):
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    owner = "a" * 64
    monkeypatch.setattr(jobs, "_plan_batch", lambda *a, **k: None)
    jobs.store.save("healthy", owner, None, "diagnosis", _v2("healthy"))
    with pytest.raises(PlanConflict, match="未发现需要修复"):
        jobs.start(None, owner, "healthy", "repair")
    jobs.store.save("d", owner, None, "diagnosis", _v2("abnormal", "abnormal", "healthy"))
    scoped = jobs.start(None, owner, "d", "repair", group_ids=["g2"])
    assert [g["group_id"] for g in scoped["groups"]] == ["g2"]
    full = jobs.start(None, owner, "d", "repair")
    assert [g["group_id"] for g in full["groups"]] == ["g1", "g2"]
    assert scoped["batch_id"] != full["batch_id"]
    assert (
        jobs.start(None, owner, "d", "repair", group_ids=["g2"])["batch_id"] == scoped["batch_id"]
    )


def _api(tmp_path, monkeypatch):
    import app.api.repair_routes as routes

    jobs, owner = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(routes, "repair_jobs", jobs)
    monkeypatch.setattr(routes, "get_service", lambda: None)
    app = FastAPI()
    routes.register_repair_routes(app)
    client = TestClient(app)
    client.cookies.set("aiops_query_owner", owner)
    return routes, jobs, owner, client


def test_json_approval_resolves_only_the_jobs_pending_request(tmp_path, monkeypatch):
    from app.core.remediation.approval import approval_store

    routes, jobs, owner, client = _api(tmp_path, monkeypatch)
    job = client.post("/repair/batches", json={"diagnosis_run_id": "d"}).json()["groups"][0]
    job_id = job["job_id"]
    request = approval_store.create_request(
        job_id, "action", "patch", {"id": "a1"}, timeout_seconds=60, owner=owner
    )
    jobs._update(
        job_id, owner, status="awaiting_approval", approval={"approval_id": request.approval_id}
    )
    url = f"/repair/jobs/{job_id}/approve"
    wrong = client.post(url, json={"approval_id": "other", "approved": True})
    assert wrong.status_code == 409
    ok = client.post(
        url, json={"approval_id": request.approval_id, "approved": True, "reviewer": "api-user"}
    )
    assert ok.status_code == 200 and ok.json()["job_id"] == job_id
    assert approval_store.decision_status(job_id, request.approval_id, owner) == "approved"
    batch = client.get("/repair/batches/batch-d").json()
    assert batch["groups"][0]["pending_approval_id"] == request.approval_id


def test_batch_events_stream_until_every_job_is_terminal(tmp_path, monkeypatch):
    routes, jobs, owner, client = _api(tmp_path, monkeypatch)
    monkeypatch.setattr(routes, "BATCH_EVENT_POLL_SECONDS", 0.01)
    groups = client.post("/repair/batches", json={"diagnosis_run_id": "d"}).json()["groups"]
    for group in groups:
        jobs._update(group["job_id"], owner, status="recovered")
    with client.stream("GET", "/repair/batches/batch-d/events") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    assert "event: batch" in body and "event: end" in body
    assert '"status": "recovered"' in body


def test_location_without_targets_is_not_repairable():
    from app.core.remediation.group_context import repairable_groups

    no_target = {
        "payload": {
            "diagnosis_handoff": {"targets": [], "pod_assessment": {"status": "inconclusive"}}
        }
    }
    assert repairable_groups(no_target) == []
    pending = {"payload": {"diagnosis_handoff": {"targets": [{"status": "investigate"}]}}}
    assert [g["group_id"] for g in repairable_groups(pending)] == ["single"]
    legacy = {"payload": {"report": "old"}}
    assert [g["group_id"] for g in repairable_groups(legacy)] == ["single"]


def test_api_principal_reaches_its_batches_and_is_the_default_reviewer(tmp_path, monkeypatch):
    import app.api.repair_routes as routes
    from app.api.identity import principal_owner
    from app.core.remediation.approval import approval_store

    monkeypatch.setenv("AIOPS_API_TOKENS", "a2a=tok-a2a")
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    owner = principal_owner("a2a")
    jobs.store.save("d", owner, None, "diagnosis", {"groups": [{"group_id": "g1"}]})
    monkeypatch.setattr(jobs, "_plan_batch", lambda *args: None)
    monkeypatch.setattr(routes, "repair_jobs", jobs)
    monkeypatch.setattr(routes, "get_service", lambda: None)
    audit = []
    monkeypatch.setattr(
        "app.core.remediation.audit.audit_event", lambda kind, **f: audit.append(f)
    )
    app = FastAPI()
    routes.register_repair_routes(app)
    client = TestClient(app)
    auth = {"Authorization": "Bearer tok-a2a"}
    assert client.post("/repair/batches", json={"diagnosis_run_id": "d"}).status_code == 401
    job_id = client.post("/repair/batches", json={"diagnosis_run_id": "d"}, headers=auth).json()[
        "groups"
    ][0]["job_id"]
    request = approval_store.create_request(job_id, "action", "t", {}, owner=owner)
    jobs._update(
        job_id, owner, status="awaiting_approval", approval={"approval_id": request.approval_id}
    )
    ok = client.post(
        f"/repair/jobs/{job_id}/approve",
        json={"approval_id": request.approval_id, "approved": True},
        headers=auth,
    )
    assert ok.status_code == 200
    assert audit[-1]["reviewer"] == "a2a" and audit[-1]["principal"] == "a2a"
    bad = client.get("/repair/batches/batch-d", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401
