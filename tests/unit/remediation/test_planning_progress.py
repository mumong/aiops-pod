"""A repair job shows how its plan is being made: tool calls, results and reasoning.

The planning run already streams the same thinking events as a diagnosis lane; the job
loop used to keep only node start/complete, so the workspace showed a bare "planning"
for minutes.
"""

from types import SimpleNamespace

from app.core.remediation.progress import PlanningProgress
from tests.unit.remediation.test_jobs import setup


def _thinking(kind, **fields):
    return {"type": "thinking", "thinking_type": kind, "node": "remediation", **fields}


def test_progress_pairs_tool_calls_with_results_and_keeps_reasoning():
    progress = PlanningProgress(clock=lambda: 100.0)
    assert progress.add(_thinking("ai_reasoning", content="先读 Deployment"))
    assert progress.add(
        _thinking(
            "tool_start",
            tool_name="kubectl_get_yaml",
            tool_call_id="c1",
            tool_args={"kind": "deployment", "name": "workload", "namespace": "ns"},
        )
    )
    assert progress.add(
        _thinking(
            "tool_result",
            tool_name="kubectl_get_yaml",
            tool_call_id="c1",
            status="success",
            result_preview="apiVersion: apps/v1\nkind: Deployment",
            duration_seconds=0.4,
        )
    )
    snap = progress.snapshot()
    assert snap["reasoning"] == "先读 Deployment"
    assert snap["tools"] == [
        {
            "id": "c1",
            "name": "kubectl_get_yaml",
            "args": '{"kind": "deployment", "name": "workload", "namespace": "ns"}',
            "status": "success",
            "preview": "apiVersion: apps/v1\nkind: Deployment",
            "duration_seconds": 0.4,
        }
    ]


def test_failed_and_semantically_empty_results_are_errors_and_text_is_bounded():
    progress = PlanningProgress(clock=lambda: 0.0)
    progress.add(_thinking("tool_start", tool_name="t", tool_call_id="a"))
    progress.add(
        _thinking(
            "tool_result",
            tool_name="t",
            tool_call_id="a",
            status="success",
            semantic_success=False,
            result_preview="x" * 5000,
        )
    )
    progress.add(_thinking("ai_reasoning", content="r" * 50000))
    snap = progress.snapshot()
    assert snap["tools"][0]["status"] == "error"
    assert len(snap["tools"][0]["preview"]) <= PlanningProgress.PREVIEW_CHARS + 1
    assert len(snap["reasoning"]) <= PlanningProgress.REASONING_CHARS + 1


def test_reasoning_alone_flushes_at_most_every_interval():
    now = [0.0]
    progress = PlanningProgress(clock=lambda: now[0])
    assert progress.add(_thinking("ai_reasoning", content="a"))  # first write
    assert not progress.add(_thinking("ai_reasoning", content="b"))
    now[0] = PlanningProgress.FLUSH_SECONDS + 0.1
    assert progress.add(_thinking("ai_reasoning", content="c"))
    assert not progress.add({"type": "heartbeat"})


def test_planning_job_records_its_progress(tmp_path, monkeypatch):
    import app.core.workflow.executor as module

    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs._new_job("batch", owner, "d", {"group_id": "g1"})

    class Executor:
        def __init__(self, **kw):
            pass

        def execute_stream(self, question, job_id, cancel, overrides):
            yield _thinking("tool_start", tool_name="kubectl_describe", tool_call_id="c1")
            yield _thinking(
                "tool_result",
                tool_name="kubectl_describe",
                tool_call_id="c1",
                status="success",
                result_preview="Name: p",
            )
            yield {
                "type": "final",
                "repair_record": {"run_id": job_id},
                "repair_plan": {"actions": []},
            }

    monkeypatch.setattr(module, "WorkflowExecutor", Executor)
    service = SimpleNamespace(_build_request_scoped_ai_call=lambda: object(), mcp_tools=[])
    assert jobs._plan(service, owner, job, "repair")
    detail = jobs.detail(job["job_id"], owner)
    assert detail["planning_progress"]["tools"][0]["name"] == "kubectl_describe"
    assert detail["planning_progress"]["tools"][0]["status"] == "success"
