import os
import sys
import time
import types
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.service import HolmesService
from app.core.skills.models import EvidenceItem, EvidenceLevel
from app.core.workflow.executor import WorkflowExecutor


def _install_fake_langfuse(monkeypatch):
    calls = {"sessions": []}

    @contextmanager
    def _propagate_attributes(**kwargs):
        calls["sessions"].append(kwargs.get("session_id"))
        yield

    fake_langfuse = types.ModuleType("langfuse")
    fake_langfuse.propagate_attributes = _propagate_attributes
    monkeypatch.setitem(sys.modules, "langfuse", fake_langfuse)
    return calls


class _DummyNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.node_name = node_id
        self._event_queue = None

    def set_event_queue(self, q):
        self._event_queue = q


class _DummyWorkflow:
    def __init__(self, nodes):
        self._nodes = {node.node_id: node for node in nodes}

    def _run_node(self, node_id, sleep_seconds, state_update):
        node = self._nodes[node_id]
        event_queue = node._event_queue

        event_queue.put((
            "node_lifecycle",
            {
                "phase": "start",
                "node": node.node_id,
                "node_name": node.node_name,
                "ts": time.time(),
            },
        ))
        time.sleep(sleep_seconds)
        event_queue.put((
            "node_lifecycle",
            {
                "phase": "end",
                "node": node.node_id,
                "node_name": node.node_name,
                "ts": time.time(),
                "success": True,
                "state_update": state_update,
            },
        ))
        return state_update

    def stream(self, initial_state):
        yield {"rca": self._run_node("rca", 0.02, {
            "root_cause": "simulated-rca",
            "rca_analysis": "{}",
        })}
        yield {"conclusion": self._run_node("conclusion", 0.03, {
            "conclusion": "simulated conclusion",
            "conclusion_formatted": "simulated conclusion",
        })}


class _DummyLogListener:
    def get_runbook_summary(self):
        return {"matched": False, "runbook_ids": []}

    def get_tool_calls(self):
        return []

    def detach(self):
        return None


class _DummyHolmesService:
    merged_catalog = None
    workflow_config = {"nodes": {"layer": False, "evidence": False, "rca": True, "conclusion": True}}


def test_executor_tracks_non_streaming_final_node_duration(monkeypatch):
    nodes = [_DummyNode("rca"), _DummyNode("conclusion")]

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full": (
            _DummyWorkflow(nodes),
            nodes,
        ),
    )
    monkeypatch.setattr(
        "app.core.workflow.executor.create_log_listener",
        lambda: _DummyLogListener(),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("timing test"))
    final_event = next(event for event in events if event.get("type") == "final")
    node_metrics = final_event["metrics"]["nodes"]

    assert 15 <= node_metrics["rca"]["duration_ms"] <= 40
    assert node_metrics["conclusion"]["duration_ms"] >= 25
    assert node_metrics["conclusion"]["duration_ms"] > node_metrics["rca"]["duration_ms"]


def test_executor_propagates_langfuse_session_at_workflow_boundary(monkeypatch):
    langfuse_calls = _install_fake_langfuse(monkeypatch)
    nodes = [_DummyNode("rca"), _DummyNode("conclusion")]

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full": (
            _DummyWorkflow(nodes),
            nodes,
        ),
    )
    monkeypatch.setattr(
        "app.core.workflow.executor.create_log_listener",
        lambda: _DummyLogListener(),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("timing test", run_id="workflow-session-1"))

    assert any(event.get("type") == "run_start" for event in events)
    assert langfuse_calls["sessions"] == ["workflow-session-1"]


def test_executor_assigns_same_run_id_to_all_four_nodes_without_ai_call(monkeypatch):
    nodes = [_DummyNode("layer"), _DummyNode("evidence"), _DummyNode("rca"), _DummyNode("conclusion")]

    class _NoopWorkflow:
        def stream(self, initial_state):
            return iter([])

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full": (
            _NoopWorkflow(),
            nodes,
        ),
    )
    monkeypatch.setattr(
        "app.core.workflow.executor.create_log_listener",
        lambda: _DummyLogListener(),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    list(executor.execute_stream("timing test", run_id="workflow-session-4"))

    assert [getattr(node, "current_run_id", None) for node in nodes] == [
        "workflow-session-4",
        "workflow-session-4",
        "workflow-session-4",
        "workflow-session-4",
    ]


def test_executor_assigns_same_run_id_and_ai_call_to_all_four_nodes(monkeypatch):
    nodes = [_DummyNode("layer"), _DummyNode("evidence"), _DummyNode("rca"), _DummyNode("conclusion")]

    class _NoopWorkflow:
        def stream(self, initial_state):
            return iter([])

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full": (
            _NoopWorkflow(),
            nodes,
        ),
    )
    monkeypatch.setattr(
        "app.core.workflow.executor.create_log_listener",
        lambda: _DummyLogListener(),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    executor.ai_call = object()
    executor.mcp_tools = ["tool-a"]
    list(executor.execute_stream("timing test", run_id="workflow-session-5"))

    assert [getattr(node, "current_run_id", None) for node in nodes] == [
        "workflow-session-5",
        "workflow-session-5",
        "workflow-session-5",
        "workflow-session-5",
    ]
    assert all(getattr(node, "ai_call", None) is executor.ai_call for node in nodes)
    assert all(getattr(node, "tools", None) == ["tool-a"] for node in nodes)


def test_executor_langfuse_session_scope_preserves_original_exception(monkeypatch):
    _install_fake_langfuse(monkeypatch)
    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())

    with pytest.raises(ValueError, match="workflow failed"):
        with executor._langfuse_session_scope("workflow-session-error"):
            raise ValueError("workflow failed")


def test_executor_evidence_snapshot_is_json_serializable():
    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    snapshot = executor._extract_state_snapshot(
        {
            "evidence_completeness": 0.5,
            "evidence_analysis": '{"plan_total":2,"plan_collected":1}',
            "evidence_items": [
                EvidenceItem(
                    id="e1",
                    description="pod yaml",
                    level=EvidenceLevel.CRITICAL,
                    collected=True,
                    value="ok",
                    source="thinking_match",
                ),
                EvidenceItem(
                    id="e2",
                    description="pod events",
                    level=EvidenceLevel.IMPORTANT,
                    collected=False,
                    source="planned",
                ),
            ],
        },
        "evidence",
    )

    assert snapshot["evidence_count"] == 2
    assert snapshot["collected_count"] == 1
    assert snapshot["evidence_items"][0]["id"] == "e1"
    assert snapshot["evidence_items"][0]["level"] == "critical"
    assert snapshot["evidence_items"][1]["collected"] is False

    import json
    json.dumps(snapshot, ensure_ascii=False)


class _SlowNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.node_name = f"{node_id}-name"
        self._event_queue = None

    def set_event_queue(self, q):
        self._event_queue = q


class _SlowWorkflow:
    def __init__(self, node):
        self._node = node

    def stream(self, initial_state):
        self._node._event_queue.put((
            "node_lifecycle",
            {
                "phase": "start",
                "node": self._node.node_id,
                "node_name": self._node.node_name,
                "ts": time.time(),
            },
        ))
        time.sleep(0.45)
        self._node._event_queue.put((
            "node_lifecycle",
            {
                "phase": "end",
                "node": self._node.node_id,
                "node_name": self._node.node_name,
                "ts": time.time(),
                "success": True,
                "state_update": {
                    "conclusion": "done",
                    "conclusion_formatted": "done",
                },
            },
        ))
        yield {"conclusion": {"conclusion": "done"}}


def test_executor_emits_heartbeat_when_workflow_is_idle(monkeypatch):
    node = _SlowNode("conclusion")

    monkeypatch.setenv("WORKFLOW_STREAM_HEARTBEAT_SECONDS", "0.02")
    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full": (
            _SlowWorkflow(node),
            [node],
        ),
    )
    monkeypatch.setattr(
        "app.core.workflow.executor.create_log_listener",
        lambda: _DummyLogListener(),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("heartbeat test"))

    heartbeat = next(event for event in events if event.get("type") == "heartbeat")
    assert heartbeat["node"] == "conclusion"
    assert heartbeat["node_name"] == "汇总总结"


def test_workflow_to_text_renders_heartbeat_lines():
    class _Executor:
        def execute_stream(self, question, cancel_event=None, workflow_overrides=None):
            yield {"type": "run_start", "run_id": "hbtest"}
            yield {"type": "node_start", "node": "conclusion", "node_name": "汇总总结"}
            yield {"type": "heartbeat", "node": "conclusion", "node_name": "汇总总结"}
            yield {"type": "final", "answer": "done", "metrics": {}, "elapsed_seconds": 1.0}

    service = HolmesService()
    output = "".join(service._workflow_to_text(_Executor(), "heartbeat test"))

    assert "仍在处理" in output
    assert "汇总总结" in output
