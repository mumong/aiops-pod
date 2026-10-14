import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.workflow.executor import WorkflowExecutor




























































def test_executor_does_not_propagate_ambient_query_mode_to_nodes(monkeypatch):
    captured = {}

    class _DummyWorkflow:
        def stream(self, initial_state):
            return iter([])

    def _fake_build_workflow(holmes_service, metrics, runbook_catalog, node_config=None, query_mode="auto", **_kw):
        captured["query_mode"] = query_mode
        node = SimpleNamespace(
            node_id="layer",
            set_event_queue=lambda q: None,
        )
        captured["node"] = node
        return _DummyWorkflow(), [node]

    monkeypatch.setattr("app.core.workflow.executor.build_diagnosis_workflow", _fake_build_workflow)

    executor = WorkflowExecutor(
        holmes_service=SimpleNamespace(
            workflow_config={"query_mode": "direct", "nodes": {"layer": True, "conclusion": True}},
            merged_catalog=None,
        )
    )

    list(executor.execute_stream("我的集群有什么问题？"))

    assert captured["query_mode"] == "auto"
    assert getattr(captured["node"], "workflow_config_override", {}).get("query_mode") is None
