import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.workflow.executor import WorkflowExecutor


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
        lambda holmes_service, metrics, runbook_catalog, node_config: (
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
