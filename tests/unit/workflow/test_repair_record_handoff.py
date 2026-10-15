from types import SimpleNamespace

from app.core.query_sessions import QuerySessionStore
from app.core.remediation.records import RepairRecordStore
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.nodes.request_router import RequestRouterNode


def test_repair_handoff_restores_after_session_memory_loss(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_REPAIR_RECORD_ROOT", str(tmp_path))
    monkeypatch.setattr("app.core.query_sessions.query_sessions", QuerySessionStore())
    store = RepairRecordStore(tmp_path)
    store.save(
        "d1",
        "owner",
        "s1",
        "diagnosis",
        {
            "question": "why",
            "report": "original report",
            "request_contract": {"scope": "pod", "namespaces": ["ns"], "pod_names": ["pod"]},
            "groups": [
                {
                    "group_id": "g1",
                    "evidence": [{"raw_ref": "/real/raw", "result_excerpt": "actual error"}],
                }
            ],
        },
    )
    executor = WorkflowExecutor.__new__(WorkflowExecutor)
    captured = {}

    def stream(question, run_id, cancel, overrides):
        captured.update(overrides)
        yield {"type": "run_start"}
        yield {"type": "final"}

    executor._execute_stream = stream
    events = list(
        executor.execute_stream(
            "fix",
            "r1",
            workflow_overrides={"_query_session_key": ("owner", "s1"), "_diagnosis_run_id": "d1"},
        )
    )
    assert captured["_repair_context"]["diagnosis"]["payload"]["report"] == "original report"
    assert captured["_query_session_context"]["turns"][0]["answer"] == "original report"
    assert captured["_repair_entry_requested"] is True
    assert events[0]["session_memory"] == "restored"
    captured.clear()
    events = list(
        executor.execute_stream(
            "fix",
            "r2",
            workflow_overrides={"_query_session_key": ("other", "s1"), "_diagnosis_run_id": "d1"},
        )
    )
    assert events[0]["type"] == "error" and not captured


def test_planning_stream_name_does_not_claim_execution():
    from app.core.workflow.executor import WorkflowExecutor

    executor = object.__new__(WorkflowExecutor)
    assert executor._get_node_display_name("remediation") == "制定 Pod 修复方案"


def test_explicit_repair_entry_routes_without_model_guessing():
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace()
    node._archive_node_input = node._archive_node_output = lambda value: None
    result = node.execute(
        {
            "question": "make a plan",
            "repair_entry_requested": True,
            "repair_context": {
                "diagnosis": {
                    "run_id": "d1",
                    "payload": {
                        "request_contract": {"scope": "namespace", "namespaces": ["demo"]}
                    },
                }
            },
        }
    )
    assert result["request_route"] == "remediation"
    assert result["request_contract"]["namespaces"] == ["demo"]


def test_group_repair_scopes_both_model_context_and_restored_memory(tmp_path, monkeypatch):
    import json

    monkeypatch.setenv("AIOPS_REPAIR_RECORD_ROOT", str(tmp_path))
    monkeypatch.setattr("app.core.query_sessions.query_sessions", QuerySessionStore())
    store = RepairRecordStore(tmp_path)
    store.save(
        "d",
        "owner",
        None,
        "diagnosis",
        {
            "report": "GLOBAL_PRIVATE_REPORT",
            "request_contract": {"scope": "cluster"},
            "groups": [
                {
                    "group_id": "g1",
                    "analysis": "first diagnosis",
                    "target": {"entities": [{"kind": "Pod", "namespace": "ns", "name": "p1"}]},
                },
                {
                    "group_id": "g2",
                    "analysis": "OTHER_GROUP_REPORT",
                    "target": {"entities": [{"kind": "Pod", "namespace": "other", "name": "p2"}]},
                },
            ],
        },
    )
    executor = WorkflowExecutor.__new__(WorkflowExecutor)
    captured = {}

    def stream(question, run_id, cancel, overrides):
        captured.update(overrides)
        yield {"type": "final"}

    executor._execute_stream = stream
    list(
        executor.execute_stream(
            "fix",
            "r",
            workflow_overrides={
                "_query_session_key": ("owner", "unique-group-session"),
                "_diagnosis_run_id": "d",
                "_repair_group_id": "g1",
            },
        )
    )
    material = json.dumps(captured)
    assert "GLOBAL_PRIVATE_REPORT" not in material and "OTHER_GROUP_REPORT" not in material
    memory = captured["_query_session_context"]["turns"][0]
    assert memory["request_contract"]["pod_names"] == ["p1"]
    assert memory["answer"] == "first diagnosis"


def test_real_graph_explicit_repair_never_visits_diagnosis_nodes():
    from app.core.workflow.graph import build_diagnosis_workflow

    graph, nodes = build_diagnosis_workflow(query_mode="auto")
    visited = []

    def forbidden(state):
        raise AssertionError("explicit repair entered a query/diagnosis node")

    for node in nodes:
        node._archive_node_input = node._archive_node_output = lambda value: None
        if node.node_id == "request_router":
            node.ai_call = SimpleNamespace()
        elif node.node_id == "remediation":

            def repair(state):
                visited.append("remediation")
                return {"remediation_draft": {"actions": []}}

            node.execute = repair
        else:
            node.execute = forbidden
    result = graph.invoke(
        {
            "question": "revise only this plan",
            "repair_entry_requested": True,
            "repair_context": {
                "diagnosis": {
                    "payload": {
                        "request_contract": {
                            "scope": "pod",
                            "namespaces": ["demo"],
                            "pod_names": ["p1"],
                        }
                    }
                }
            },
        }
    )
    assert visited == ["remediation"]
    assert result["request_route"] == "remediation"
