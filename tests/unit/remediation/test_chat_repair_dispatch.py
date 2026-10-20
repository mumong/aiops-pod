"""A chat repair request after a grouped diagnosis is the same per-group batch as the button.

Live 2026-10-19 (run d09fc5c84ff54eb8): "修复刚刚的问题" after a 4-group diagnosis gave
the whole 61k-char record to ONE planning agent (5 slow rounds, an HTTP 400, then a
fallback plan that invented a Secret value). The button path plans each group in its
own agent, in parallel, with per-group approval. Both entries now share that path.
"""

from types import SimpleNamespace

from app.core.workflow.nodes.remediation import RemediationNode


def _record(*outcomes, scoped=False):
    payload = {
        "contract_version": "diagnosis-record.v2",
        "groups": [
            {
                "group_id": f"g{i}",
                "target": {
                    "target_id": f"t{i}",
                    "entities": [{"kind": "Pod", "namespace": f"ns{i}", "name": f"p{i}"}],
                },
                "diagnosis_result": {"outcome": outcome, "summary": f"cause {i}"},
            }
            for i, outcome in enumerate(outcomes, start=1)
        ],
    }
    if scoped:
        payload["group_id"] = "g1"
    return {"run_id": "diag-1", "kind": "diagnosis", "payload": payload}


def _node():
    node = RemediationNode()
    node.ai_call = SimpleNamespace()
    node._call_llm = lambda *a, **k: (_ for _ in ()).throw(AssertionError("no single agent"))
    return node


def _state(record, contract):
    return {
        "question": "修复刚刚的问题",
        "request_contract": contract,
        "repair_context": {"diagnosis": record},
    }


def test_grouped_diagnosis_dispatches_unresolved_groups_without_a_planning_agent():
    out = _node().execute(_state(_record("abnormal", "healthy", "abnormal"), {"scope": "cluster"}))
    dispatch = out["remediation_dispatch"]
    assert dispatch == {"diagnosis_run_id": "diag-1", "group_ids": ["g1", "g3"]}
    assert out["remediation_draft"] is None and out["request_route"] == "remediation"
    assert "异常组 1" in out["conclusion"] and "异常组 3" in out["conclusion"]


def test_request_naming_one_pod_dispatches_only_its_group():
    out = _node().execute(_state(_record("abnormal", "abnormal"), {"pod_names": ["p2"]}))
    assert out["remediation_dispatch"]["group_ids"] == ["g2"]


def test_healthy_diagnosis_answers_directly_without_planning():
    out = _node().execute(_state(_record("healthy", "recovered"), {"scope": "cluster"}))
    assert out["remediation_dispatch"]["group_ids"] == []
    assert "未发现需要修复" in out["conclusion"]


def test_no_dispatch_for_job_scoped_records_or_unmatched_targets():
    node = RemediationNode()
    assert node._group_dispatch(_state(_record("abnormal", scoped=True), {})) is None
    assert node._group_dispatch(_state(_record("abnormal"), {"pod_names": ["other"]})) is None
    assert node._group_dispatch({"repair_context": {}}) is None
    with_plan = _state(_record("abnormal"), {})
    with_plan["repair_context"]["previous_plan"] = {"run_id": "p"}
    assert node._group_dispatch(with_plan) is None


def test_executor_starts_the_dispatched_or_requested_batch(monkeypatch):
    from app.core.remediation import jobs as jobs_module
    from app.core.remediation.records import PlanConflict
    from app.core.workflow.executor import WorkflowExecutor

    started = []

    def start(service, owner, diagnosis_id, question, group_ids=None):
        started.append((owner, diagnosis_id, group_ids))
        if diagnosis_id == "healthy":
            raise PlanConflict("该诊断未发现需要修复的异常组，无需生成修复方案")
        return {
            "batch_id": f"batch-{diagnosis_id}",
            "groups": [{"group_id": "g1", "job_id": "j1", "status": "queued", "x": 1}],
        }

    monkeypatch.setattr(jobs_module.repair_jobs, "start", start)
    executor = WorkflowExecutor(holmes_service=None)
    owner = {"_remediation_owner": "o" * 64}
    dispatched = {"remediation_dispatch": {"diagnosis_run_id": "d1", "group_ids": ["g1"]}}
    batch, note = executor._start_repair_batch("修复", dispatched, owner, None)
    assert batch["batch_id"] == "batch-d1" and batch["groups"][0] == {
        "group_id": "g1",
        "job_id": "j1",
        "status": "queued",
        "target": None,
    }
    assert started[-1] == ("o" * 64, "d1", ["g1"]) and note == ""
    nothing = {"remediation_dispatch": {"diagnosis_run_id": "d1", "group_ids": []}}
    assert executor._start_repair_batch("修复", nothing, owner, None) == (None, "")
    auto = {**owner, "_auto_repair_plan": True}
    record = {"run_id": "healthy", "kind": "diagnosis"}
    batch, note = executor._start_repair_batch("诊断", {}, auto, record)
    assert batch is None and "未发现需要修复" in note
    assert executor._start_repair_batch("诊断", {}, owner, record) == (None, "")
    assert "session_id" in executor._start_repair_batch("修复", dispatched, {}, None)[1]


def test_auto_mode_starts_the_batch_after_a_web_diagnosis_without_a_click(monkeypatch, tmp_path):
    """Boss (2026-10-20): in auto mode a diagnosis should plan, approve and run by itself;
    a person is only needed when a command is blocked. The button stays for review mode."""
    from types import SimpleNamespace

    import app.core.remediation.jobs as jobs_module
    from app.core.remediation.settings import RepairSettings
    from app.core.workflow.executor import WorkflowExecutor

    monkeypatch.setattr(
        "app.core.remediation.settings.repair_settings", RepairSettings(path=tmp_path / "s.json")
    )
    started = []
    monkeypatch.setattr(
        jobs_module.repair_jobs,
        "start",
        lambda service, owner, diagnosis_id, question, group_ids=None: started.append(diagnosis_id)
        or {"batch_id": f"batch-{diagnosis_id}", "groups": []},
    )
    monkeypatch.setattr(WorkflowExecutor, "_record_repairable", staticmethod(lambda r: True))
    record = {"run_id": "d1", "kind": "diagnosis"}
    owner = {"_remediation_owner": "o" * 64}

    def executor(mode):
        service = SimpleNamespace(
            workflow_config={"remediation": {"enabled": True, "mode": mode}},
            mcp_tools=[],
            merged_catalog=None,
        )
        return WorkflowExecutor(holmes_service=service)

    batch, note = executor("auto")._start_repair_batch("诊断", {}, owner, record)
    assert batch["batch_id"] == "batch-d1" and started == ["d1"] and note == ""
    assert executor("review")._start_repair_batch("诊断", {}, owner, record) == (None, "")
    healthy = {"run_id": "h", "kind": "diagnosis"}
    monkeypatch.setattr(WorkflowExecutor, "_record_repairable", staticmethod(lambda r: False))
    assert executor("auto")._start_repair_batch("诊断", {}, owner, healthy) == (None, "")
    assert started == ["d1"]
