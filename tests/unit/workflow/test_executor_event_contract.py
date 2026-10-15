"""Characterization test: the full SSE event sequence of WorkflowExecutor.

Drives ``execute_stream`` with scripted fake workflows and compares the
normalized event stream (types, payload keys and stable values) against a
golden file. Volatile values (timestamps, durations, elapsed) are masked.

Regenerate the golden file only for an intentional contract change:
    AIOPS_UPDATE_EXECUTOR_GOLDEN=1 pytest tests/unit/workflow/test_executor_event_contract.py
"""
import json
import os
import re
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.nodes.autonomous_parallel import LaneQueue

GOLDEN = Path(__file__).with_name("golden") / "executor_event_contract.json"
RUN_ID = "contract-run"

_VOLATILE_KEY = re.compile(
    r"(^ts$|ts_ms|timestamp|elapsed|duration|_time$|_ms$|mttr|_at$|duration_seconds)"
)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_TEXT_WITH_TIMINGS = {"answer", "diagnosis_footer"}


def _normalize(value, key=None):
    if key is not None and _VOLATILE_KEY.search(str(key)) and not isinstance(value, (dict, list)):
        return "<volatile>"
    if isinstance(value, dict):
        return {str(k): _normalize(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, float):
        return "<float>"
    if isinstance(value, str) and key in _TEXT_WITH_TIMINGS:
        return _NUMBER.sub("#", value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return repr(type(value).__name__)


# ── fakes ──────────────────────────────────────────────────────────────


class _Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.node_name = f"{node_id}-display"
        self._event_queue = None
        self.cancel_event = None

    def set_event_queue(self, q):
        self._event_queue = q


class _Service:
    merged_catalog = None

    def __init__(self, workflow_config=None):
        self.workflow_config = workflow_config or {"nodes": {}}


class _ScriptedWorkflow:
    """LangGraph stand-in: ``script(ctx)`` is a generator of langgraph events."""

    def __init__(self, nodes, script):
        self.nodes = {node.node_id: node for node in nodes}
        self.script = script
        self.initial_state = None

    @property
    def queue(self):
        return next(iter(self.nodes.values()))._event_queue

    def start(self, node_id, ts=None):
        self.queue.put(("node_lifecycle", {"phase": "start", "node": node_id,
                                           "node_name": f"{node_id}-display", "ts": ts or time.time()}))

    def end(self, node_id, state_update, success=True, error=None):
        payload = {"phase": "end", "node": node_id, "node_name": f"{node_id}-display",
                   "ts": time.time(), "success": success, "state_update": state_update}
        if error is not None:
            payload["error"] = error
        self.queue.put(("node_lifecycle", payload))

    def think(self, data, q=None):
        (q or self.queue).put(("thinking", data))

    def stream(self, initial_state):
        self.initial_state = initial_state
        yield from self.script(self)


@pytest.fixture
def harness(monkeypatch, tmp_path):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path / "archive"))
    monkeypatch.setenv("AIOPS_REPAIR_RECORD_ROOT", str(tmp_path / "records"))
    monkeypatch.delenv("WORKFLOW_STREAM_HEARTBEAT_SECONDS", raising=False)
    monkeypatch.setattr("app.core.workflow.metrics.METRICS_ENABLED", False)
    saved_reports = []
    monkeypatch.setattr(WorkflowExecutor, "_save_report",
                        lambda self, layer, question, answer: saved_reports.append((layer, question)))
    built = {}

    def run(script, node_ids, *, workflow_config=None, overrides=None, consume=None,
            cancel_event=None, question="contract question", records="default"):
        monkeypatch.setenv("AIOPS_REPAIR_RECORD_ROOT", str(tmp_path / "records" / records))
        nodes = [_Node(node_id) for node_id in node_ids]
        workflow = _ScriptedWorkflow(nodes, script)

        def _build(holmes_service, metrics, runbook_catalog, node_config=None, query_mode="auto", **kwargs):
            built.update(node_config=node_config, query_mode=query_mode, kwargs=kwargs)
            return workflow, nodes

        monkeypatch.setattr("app.core.workflow.executor.build_diagnosis_workflow", _build)
        executor = WorkflowExecutor(holmes_service=_Service(workflow_config))
        events = []
        for event in executor.execute_stream(question, run_id=RUN_ID, cancel_event=cancel_event,
                                             workflow_overrides=overrides):
            events.append(event)
            if consume is not None:
                consume(event, workflow)
        return {
            "events": _normalize(events),
            "build": _normalize(built),
            "initial_state_keys": sorted(workflow.initial_state or {}),
            "initial_state": _normalize({k: v for k, v in (workflow.initial_state or {}).items()
                                         if k != "request_time_utc"}),
            "node_run_ids": [getattr(n, "current_run_id", None) for n in nodes],
            "queues_cleared": [n._event_queue is None for n in nodes],
            "saved_reports": [list(r) for r in saved_reports],
        }

    return run


# ── scenarios ──────────────────────────────────────────────────────────


def _focused(harness):
    def script(wf):
        wf.start("request_router")
        wf.end("request_router", {"request_route": "focused",
                                  "request_contract": {"scope": "pod", "namespaces": ["ns"]}})
        yield {"request_router": {"request_route": "focused"}}
        wf.start("query_collect")
        wf.think({"type": "tool_start", "node": "query_collect", "tool_name": "kubectl_get",
                  "tool_call_id": "c1", "tool_args": {"namespace": "ns"}, "iteration": 1})
        wf.think({"type": "tool_result", "node": "query_collect", "tool_name": "kubectl_get",
                  "tool_call_id": "c1", "status": "success", "result_preview": "pod-a Running",
                  "raw_ref": {"path": "raw/c1.txt"}, "iteration": 1})
        wf.think({"type": "ai_message", "node": "query_collect", "content": "short",
                  "full_content": "full answer text", "iteration": 1})
        wf.end("query_collect", {"query_answer": {"status": "complete", "answer": "pods ok"},
                                 "conclusion": "pods ok", "query_session_memory": {"turns": [1]}})
        yield {"query_collect": {"conclusion": "pods ok"}}

    return harness(script, ["request_router", "query_collect"],
                   overrides={"_query_session_context": {"turns": []}})


def _full_diagnosis(harness):
    def script(wf):
        wf.start("request_router")
        wf.end("request_router", {"request_route": "full_diagnosis",
                                  "request_contract": {"scope": "cluster"}})
        yield {"request_router": {}}
        wf.start("layer")
        wf.think({"type": "ai_message", "node": "layer", "content": "layer thinking"})
        wf.end("layer", {"layer": "L1", "layers": ["L1"], "layer_confidence": 0.75,
                         "layer_reasoning": "pods crash", "layer_analysis": "{\"x\": 1}",
                         "key_entities": [{"kind": "Pod", "name": "a"}],
                         "possible_scenarios": ["oom"]})
        yield {"layer": {}}
        wf.start("evidence")
        wf.end("evidence", {"evidence_analysis": json.dumps({"plan_total": 3, "plan_collected": 2}),
                            "evidence_completeness": 0.5,
                            "diagnosis_handoff": {"targets": [{"id": "t1"}]}})
        yield {"evidence": {}}
        wf.start("rca")
        wf.end("rca", {"root_cause": "memory limit too low", "rca_analysis": "{}",
                       "causal_chain": {"trigger": "load"},
                       "query_draft": "draft text"})
        yield {"rca": {}}
        wf.start("conclusion")
        wf.end("conclusion", {"conclusion": "final report", "conclusion_formatted": "final report",
                              "diagnosis_cases": [{"group_id": "g1", "execution_status": "completed"}],
                              "diagnosis_overview": {"count": 1}})
        yield {"conclusion": {}}

    return harness(script, ["request_router", "layer", "evidence", "rca", "conclusion"],
                   overrides={"_remediation_owner": "owner-1", "_record_session_id": "sess-1"},
                   workflow_config={"nodes": {"layer": True},
                                    "evidence": {"parallel": {"enabled": True, "max": 3}},
                                    "remediation": {"enabled": True}})


def _parallel(harness):
    entities = [{"kind": "Pod", "namespace": "ns", "name": "pod-1"}]

    def script(wf):
        wf.start("layer")
        wf.end("layer", {"layer": "L1", "autonomous_groups": [{"group_id": "g1", "entities": entities},
                                                              {"group_id": "g2", "entities": entities}]})
        yield {"layer": {}}
        # No lifecycle start: the first thinking event must synthesize node_start
        # and finish the still-open previous node.
        lane = LaneQueue(wf.queue, group_id="g1", entities=entities)
        wf.think({"type": "tool_start", "node": "evidence", "tool_name": "kubectl_previous_logs",
                  "tool_call_id": "p1", "tool_args": {"namespace": "ns", "pod_name": "pod-1"}}, lane)
        wf.think({"type": "tool_result", "node": "evidence", "tool_name": "kubectl_previous_logs",
                  "tool_call_id": "p1", "status": "success", "result_preview": "OOMKilled",
                  "tool_args": {"namespace": "ns", "pod_name": "pod-1"}}, lane)
        wf.think({"type": "ai_message", "node": "rca", "content": "lane rca"}, lane)
        wf.end("parallel_evidence", {"autonomous_group_results": [
            {"group_id": "g1", "target": {"group_id": "g1"}, "status": "completed", "error": None,
             "run_id": f"{RUN_ID}-g1"},
            {"group_id": "g2", "target": {"group_id": "g2"}, "status": "partial", "error": "evidence: boom",
             "run_id": f"{RUN_ID}-g2"}]})
        yield {"parallel_evidence": {}}
        # conclusion only reported through langgraph events (no lifecycle):
        yield {"conclusion": {"conclusion": "parallel report"}}

    return harness(script, ["layer", "parallel_evidence", "conclusion"],
                   overrides={"query_mode": "full"})


class _FakeRemediationRun:
    calls = []

    def __init__(self, *args, **kwargs):
        type(self).calls.append(("init", sorted(kwargs)))

    def run(self, *args, **kwargs):
        type(self).calls.append(("run", sorted(kwargs)))
        yield {"type": "remediation_started", "run_id": kwargs.get("run_id") or args[0]}
        yield {"type": "remediation_approval_required", "action_id": "a1", "command": "kubectl patch x"}
        yield {"type": "remediation_finished", "status": "approved", "run_id": RUN_ID}


def _remediation_report_script(wf):
    wf.start("conclusion")
    wf.end("conclusion", {"conclusion_formatted": "report with plan", "layer": "L2"})
    yield {"conclusion": {}}


def _remediation(harness, monkeypatch, executor_name):
    _FakeRemediationRun.calls = []
    plan = SimpleNamespace(remediation_available=True, fix_type="patch", risk_level="low",
                           requires_human_approval=True, issue_groups=[], basis=["b"],
                           actions=[SimpleNamespace(id="a1", type="kubectl_patch")],
                           stop_conditions=[])
    monkeypatch.setattr("app.core.workflow.executor.extract_remediation_plan", lambda report: plan)
    monkeypatch.setattr("app.core.workflow.executor.RemediationExecutor", _FakeRemediationRun)
    monkeypatch.setattr("app.core.workflow.executor.RemediationAgentExecutor", _FakeRemediationRun)
    result = harness(_remediation_report_script, ["conclusion"],
                     workflow_config={"remediation": {"enabled": True, "executor": executor_name,
                                                      "mode": "auto", "approval_timeout_seconds": "7"}})
    result["remediation_calls"] = _FakeRemediationRun.calls
    return result


def _remediation_invalid_plan(harness, monkeypatch):
    def _raise(report):
        raise ValueError("unsafe remediation command")
    monkeypatch.setattr("app.core.workflow.executor.extract_remediation_plan", _raise)
    return harness(_remediation_report_script, ["conclusion"],
                   workflow_config={"remediation": {"enabled": True}})


def _remediation_missing_actions(harness):
    def script(wf):
        wf.start("conclusion")
        wf.end("conclusion", {"conclusion_formatted": "run kubectl delete pod web-1 now"})
        yield {"conclusion": {}}
    return harness(script, ["conclusion"], workflow_config={"remediation": {"enabled": True}})


def _pod_remediation(harness, monkeypatch, records="pod"):
    import app.core.remediation.pod_executor as pod_executor
    calls = []

    class _FakePod:
        def run(self, run_id, draft, **kwargs):
            calls.append({"run_id": run_id, "draft": draft, "owner": kwargs["owner"], "mode": kwargs["mode"],
                          "timeout": kwargs["timeout"], "has_record_store": kwargs["record_store"] is not None,
                          "request_contract": kwargs["request_contract"]})
            yield {"type": "remediation_approval_required", "run_id": run_id, "action": "patch"}
            yield {"type": "remediation_finished", "run_id": run_id, "status": "done"}

    monkeypatch.setattr(pod_executor, "PodRepairExecutor", _FakePod)

    def script(wf):
        wf.start("request_router")
        wf.end("request_router", {"request_route": "remediation", "request_contract": {"scope": "pod"}})
        yield {"request_router": {}}
        wf.start("remediation")
        wf.end("remediation", {"remediation_draft": {"actions": [{"id": "x"}]}, "conclusion": "plan ready"})
        yield {"remediation": {}}

    result = harness(script, ["request_router", "remediation"],
                     overrides={"_remediation_owner": "owner-2", "_record_session_id": "sess-2",
                                "_repair_group_id": "g9", "_repair_context": {"diagnosis": {"run_id": "d1"}},
                                "_repair_entry_requested": True},
                     workflow_config={"remediation": {"enabled": True, "mode": "review",
                                                      "approval_timeout_seconds": 30}},
                     records=records)
    result["pod_calls"] = _normalize(calls)
    return result


def _langgraph_only(harness):
    """Nodes without lifecycle events: completion inferred from the next event."""
    def script(wf):
        yield {"layer": {"layer": "L3", "layers": ["L3"], "layer_confidence": 0.5}}
        wf.think({"type": "iteration_start", "node": "evidence", "iteration": 2})
        yield {"evidence": {"evidence_analysis": "{}"}}
        yield {"rca": {"root_cause": "disk full", "rca_analysis": "{}"}}

    return harness(script, ["layer", "evidence", "rca"], overrides={"query_mode": "direct"})


def _node_error(harness):
    def script(wf):
        wf.start("layer")
        wf.think({"type": "ai_message", "node": "layer", "content": "about to fail"})
        wf.end("layer", {}, success=False, error="boom")
        raise RuntimeError("boom")
        yield  # pragma: no cover

    return harness(script, ["layer", "evidence"])


def _heartbeat(harness, monkeypatch):
    monkeypatch.setenv("WORKFLOW_STREAM_HEARTBEAT_SECONDS", "0.02")
    released = threading.Event()

    def script(wf):
        wf.start("rca")
        assert released.wait(timeout=5)
        wf.end("rca", {"root_cause": "rc", "query_draft": "draft"})
        yield {"rca": {}}

    def consume(event, wf):
        if event["type"] == "heartbeat":
            released.set()

    return harness(script, ["rca"], consume=consume)


def _cancel(harness):
    cancel = threading.Event()
    worker_exit = threading.Event()

    def script(wf):
        wf.start("evidence")
        wf.think({"type": "ai_message", "node": "evidence", "content": "working"})
        try:
            node = wf.nodes["evidence"]
            assert node.cancel_event.wait(timeout=5)
            wf.end("evidence", {"evidence_analysis": "late"})
            yield {"evidence": {}}
        finally:
            worker_exit.set()

    def consume(event, wf):
        if event["type"] == "thinking":
            cancel.set()

    result = harness(script, ["evidence", "rca"], consume=consume, cancel_event=cancel)
    result["worker_exited"] = worker_exit.wait(timeout=5)
    result["cancel_set"] = cancel.is_set()
    return result


def _collect(harness, monkeypatch):
    out = {}
    out["focused"] = _focused(harness)
    out["full_diagnosis"] = _full_diagnosis(harness)
    out["parallel"] = _parallel(harness)
    out["remediation_deterministic"] = _remediation(harness, monkeypatch, "deterministic")
    out["remediation_react"] = _remediation(harness, monkeypatch, "react")
    out["remediation_invalid_plan"] = _remediation_invalid_plan(harness, monkeypatch)
    out["remediation_missing_actions"] = _remediation_missing_actions(harness)
    out["remediation_pod"] = _pod_remediation(harness, monkeypatch)
    out["remediation_pod_record_conflict"] = _pod_remediation(harness, monkeypatch)
    out["langgraph_only"] = _langgraph_only(harness)
    out["node_error"] = _node_error(harness)
    out["heartbeat"] = _heartbeat(harness, monkeypatch)
    out["cancel"] = _cancel(harness)
    return json.loads(json.dumps(out, ensure_ascii=False, sort_keys=False))


def test_executor_event_contract_matches_golden(harness, monkeypatch):
    actual = _collect(harness, monkeypatch)
    if os.getenv("AIOPS_UPDATE_EXECUTOR_GOLDEN") == "1":
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(actual, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for scenario in expected:
        exp, act = expected[scenario], actual[scenario]
        # Compare event-by-event first for a readable failure, then everything.
        assert [e["type"] for e in act["events"]] == [e["type"] for e in exp["events"]], scenario
        for index, (a, e) in enumerate(zip(act["events"], exp["events"])):
            assert list(a) == list(e), (scenario, index, "key order")
            assert a == e, (scenario, index)
        assert act == exp, scenario
    assert sorted(actual) == sorted(expected)


def test_heartbeat_names_the_running_stage_not_a_lingering_finished_one():
    """Live run 2e1e601acab74d13: text heartbeats said '问题定位' during parallel lanes."""
    import threading
    from types import SimpleNamespace
    from app.core.workflow.executor import _StreamTranslator

    t = object.__new__(_StreamTranslator)
    t.heartbeat_interval_s, t.last_event_ts, t.seq, t.run_id = 1, 0, 0, "r"
    t.current_nodes = {"layer", "parallel_evidence"}
    t.completed_nodes = {"layer"}
    t.node_start_times = {"layer": 1.0, "parallel_evidence": 2.0}
    t.executor = SimpleNamespace(_get_node_display_name=lambda n: {"parallel_evidence": "分组并发诊断"}.get(n, n))
    alive = threading.Thread(target=lambda: None)
    alive.is_alive = lambda: True
    [event] = list(t._maybe_heartbeat(alive))
    assert event["node"] == "parallel_evidence" and event["node_name"] == "分组并发诊断"
