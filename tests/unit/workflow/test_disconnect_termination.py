"""Fatal transport failures must never become successful partial workflow runs."""
import queue
import threading
import time
from types import SimpleNamespace

import pytest

from app.core.aicall.errors import ModelStreamInterrupted
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode, DiagnosisRootCauseNode


@pytest.mark.parametrize('failed_stage', ['layer', 'evidence', 'rca', 'conclusion', 'query_collect', 'remediation'])
def test_graph_stops_at_failed_stage(failed_stage):
    graph, nodes = build_diagnosis_workflow(query_mode='auto')
    visited = []
    route = {'query_collect': 'focused', 'remediation': 'remediation'}.get(failed_stage, 'full_diagnosis')
    for node in nodes:
        def execute(state, name=node.node_id):
            visited.append(name)
            if name == failed_stage:
                raise ModelStreamInterrupted('LLM API 服务连接中断，本次运行已终止。')
            return {'request_route': route} if name == 'request_router' else {}
        node.execute = execute
    with pytest.raises(ModelStreamInterrupted):
        graph.invoke({'question': '测试'})
    assert visited[-1] == failed_stage


def test_parallel_disconnect_stops_peers_and_never_runs_rca(monkeypatch, tmp_path):
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    monkeypatch.setenv('AIOPS_AUTONOMOUS_PARALLEL_WORKERS', '2')
    node = AutonomousParallelNode(SimpleNamespace(_build_request_scoped_ai_call=lambda: SimpleNamespace(_push=lambda *a, **k: None)))
    parent = threading.Event()
    node.cancel_event = parent
    node.current_run_id = 'disconnect-parallel'
    node.set_event_queue(queue.Queue())
    barrier = threading.Barrier(2)
    peer_stopped = threading.Event()

    def evidence(self, state):
        barrier.wait(timeout=3)
        if state['diagnosis_target']['group_id'] == 'g1':
            raise ModelStreamInterrupted('LLM API 服务连接中断')
        assert self.cancel_event.wait(timeout=3)
        peer_stopped.set()
        return {}

    monkeypatch.setattr(DiagnosisEvidenceNode, 'execute', evidence)
    monkeypatch.setattr(DiagnosisRootCauseNode, 'execute', lambda *a: pytest.fail('RCA must not start'))
    groups = [{'group_id': f'g{i}', 'question': 'q', 'entities': [
        {'kind': 'Pod', 'namespace': 'test', 'name': f'p{i}'}]} for i in [1, 2]]
    with pytest.raises(ModelStreamInterrupted):
        node.execute({'question': 'q', 'autonomous_groups': groups})
    assert peer_stopped.wait(timeout=3)
    assert not parent.is_set()  # Must emit error, not silently report user cancellation.


def test_executor_emits_error_without_final_or_downstream(monkeypatch):
    from app.core.workflow.executor import WorkflowExecutor
    from tests.unit.workflow.test_executor_timing import _DummyHolmesService
    graph, nodes = build_diagnosis_workflow(query_mode='auto')
    visited = []
    for node in nodes:
        def execute(state, name=node.node_id):
            visited.append(name)
            if name == 'request_router':
                return {'request_route': 'full_diagnosis'}
            if name == 'layer':
                raise ModelStreamInterrupted('LLM API 服务连接中断，本次运行已终止。')
            pytest.fail('No downstream node after disconnect')
        node.execute = execute
    monkeypatch.setattr('app.core.workflow.executor.build_diagnosis_workflow', lambda *a, **k: (graph, nodes))
    events = list(WorkflowExecutor(holmes_service=_DummyHolmesService()).execute_stream('测试'))
    assert visited == ['request_router', 'layer']
    assert len([e for e in events if e['type'] == 'error']) == 1
    assert not any(e['type'] == 'final' for e in events)


def test_client_disconnect_releases_worker(monkeypatch):
    """Closing the stream early must not leave a producer blocked on a full queue."""
    from app.core.workflow.executor import WorkflowExecutor
    from tests.unit.workflow.test_executor_timing import _DummyHolmesService
    graph, nodes = build_diagnosis_workflow(query_mode='auto')
    producer_done = threading.Event()

    for node in nodes:
        def execute(state, name=node.node_id, node=node):
            if name == 'request_router':
                return {'request_route': 'full_diagnosis'}
            try:
                for i in range(2000):  # far more than the old 500-slot queue
                    if node.cancel_event.is_set():
                        break
                    node._event_queue.put(('thinking', {'type': 'ai_token', 'node': name, 'content': str(i)}))
                    time.sleep(0.002)
            finally:
                producer_done.set()
            return {}
        node.execute = execute

    monkeypatch.setattr('app.core.workflow.executor.build_diagnosis_workflow', lambda *a, **k: (graph, nodes))
    cancel = threading.Event()
    stream = WorkflowExecutor(holmes_service=_DummyHolmesService()).execute_stream('测试', cancel_event=cancel)
    for event in stream:  # read until the producer is streaming tokens
        if event.get('type') == 'thinking':
            break
    stream.close()  # client disconnect -> GeneratorExit inside the generator

    assert producer_done.wait(timeout=5)
    assert cancel.is_set()
