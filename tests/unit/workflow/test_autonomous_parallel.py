import json
import threading
from types import SimpleNamespace

from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode, plan_groups
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode, DiagnosisRootCauseNode
from app.core.workflow.nodes.query_answer import build_working_material


def groups(n=3):
    return [{"group_id": f"g{i}", "question": "为什么重启", "entities": [
        {"kind": "Pod", "namespace": "demo", "name": f"pod-{i}"}]} for i in range(1, n+1)]


def test_three_lanes_overlap_isolate_clients_and_keep_failed_lane(tmp_path, monkeypatch):
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    monkeypatch.setenv('AIOPS_AUTONOMOUS_PARALLEL_WORKERS', '3')
    clients = []
    def make_client():
        client = SimpleNamespace()
        clients.append(client)
        return client
    node = AutonomousParallelNode(SimpleNamespace(_build_request_scoped_ai_call=make_client))
    node.current_run_id = 'parallel-test'
    barrier = threading.Barrier(3)
    seen = []
    def call(self, text, prompt, **kw):
        material = json.loads(text)
        gid = material['group_id']
        assert material['question'] == '检查这三个 Pod 的根因'
        assert material['request_contract']['pod_names'] == [f'pod-{gid[1:]}']
        assert f'demo/pod-{gid[1:]}' in material['task']
        assert 'shared-list' not in text
        assert kw['skip_remediation_policy']
        assert '固定 EvidencePlan' in prompt
        seen.append((gid, self.node_id, id(self.ai_call)))
        if self.node_id == 'evidence':
            barrier.wait(timeout=5)  # Cannot pass if the implementation is serial.
            if gid == 'g2':
                raise RuntimeError('tool/provider failure')
            return SimpleNamespace(result=json.dumps({'analysis': f'{gid} evidence'})), [
                {'type': 'context_compacted', 'working_summary': gid, 'retained_messages': []},
                {'type': 'tool_result', 'tool_name': 'kubectl_describe', 'result': gid, 'raw_ref': f'/{gid}/raw'}]
        assert material['working_summary'] == gid
        assert kw['force_no_tools']
        return SimpleNamespace(result=json.dumps({'summary': f'{gid} RCA uncertain',
            'outcome': 'inconclusive', 'certainty': 'unknown', 'report': f'{gid} report'})), []
    monkeypatch.setattr(DiagnosisEvidenceNode, '_call_llm', call)
    monkeypatch.setattr(DiagnosisRootCauseNode, '_call_llm', call)
    state = {'question': '检查这三个 Pod 的根因', 'autonomous_groups': groups(),
             'thinking_events': [{'type': 'tool_result', 'result': 'shared-list'},
                                 {'type': 'execution_incomplete', 'node': 'layer', 'reason': 'step_limit'}]}
    result = node.execute(state)
    assert len({id(c) for c in clients}) == 3
    assert [r['group_id'] for r in result['autonomous_group_results']] == ['g1', 'g2', 'g3']
    assert [r['status'] for r in result['autonomous_group_results']] == ['completed', 'partial', 'completed']
    assert len({client for gid, stage, client in seen if gid == 'g1'}) == 1
    material = build_working_material({**state, **result})
    assert material['working_summary'] is None  # No sibling's compaction may reset the parent.
    assert material['observations'][0]['result'] == 'shared-list'
    assert len(material['parallel_results']) == 3
    assert material['execution_incomplete']
    assert (tmp_path/'parallel-test/parallel/results.json').exists()


def test_invalid_contract_continues_serially_without_model_reextraction():
    node = SimpleNamespace(ai_call=SimpleNamespace(call_structured=lambda **kw: (_ for _ in ()).throw(AssertionError('no model'))))
    assert plan_groups(node, {'question':'q'})['autonomous_groups'] == []
    result = plan_groups(node, {'question':'q', 'diagnosis_handoff': {'targets': 'invalid'}})
    assert result['autonomous_groups'] == []
    assert result['warnings']


def test_dictionary_tool_pairs_remain_atomic():
    from app.core.aicall.working_context import message_groups, partition_recent
    messages = [{'type':'ai','tool_calls':[{'id':'one'}],'content':''},
                {'type':'tool','tool_call_id':'one','content':'latest result'}]
    old, recent = partition_recent(message_groups(messages), 54000)
    assert not old
    assert recent == [messages]


def test_auto_graph_routes_multiple_targets_to_lanes_then_conclusion():
    from app.core.workflow.graph import build_diagnosis_workflow
    graph, nodes = build_diagnosis_workflow(query_mode='auto')
    visited = []
    for node in nodes:
        def execute(state, name=node.node_id):
            visited.append(name)
            if name == 'request_router': return {'request_route':'full_diagnosis'}
            if name == 'layer': return {'autonomous_groups':groups(2)}
            if name == 'parallel_evidence': return {'autonomous_group_results':[{'group_id':'g1'}, {'group_id':'g2'}]}
            if name == 'conclusion':
                assert len(state['autonomous_group_results']) == 2
                return {'conclusion':'两组结果'}
            raise AssertionError('Unexpected serial or legacy stage')
        node.execute = execute
    result = graph.invoke({'question':'两个Pod根因'})
    assert visited == ['request_router','layer','parallel_evidence','conclusion']
    assert result['conclusion'] == '两组结果'


def test_tls_model_failure_stops_branch_before_rca_and_propagates_to_parent(monkeypatch):
    import httpx
    import pytest
    from openai import InternalServerError
    from app.core.aicall.errors import ModelStreamInterrupted, raise_on_model_disconnect
    failure = InternalServerError('utls: TLS handshake: EOF', response=httpx.Response(
        500, request=httpx.Request('POST', 'https://model.invalid/v1/chat/completions')), body={})
    node = AutonomousParallelNode(SimpleNamespace(_build_request_scoped_ai_call=lambda: SimpleNamespace()))
    parent_cancel = threading.Event()
    node.current_run_id = 'tls-failure-test'
    node.cancel_event = parent_cancel
    node.ai_call = None
    def fail(*args, **kwargs):
        raise failure
    def forbidden(*args, **kwargs):
        raise AssertionError('RCA must not run after a fatal model connection failure')
    monkeypatch.setattr(DiagnosisEvidenceNode, '_call_llm', fail)
    monkeypatch.setattr(DiagnosisRootCauseNode, '_call_llm', forbidden)
    with pytest.raises(ModelStreamInterrupted, match='LLM API 服务连接中断'):
        node.execute({'question': '检查Pod', 'autonomous_groups': groups(1)})
    assert not parent_cancel.is_set()  # Model failure is not a user cancellation.
    assert node.cancel_event.is_set()
    # A tool-originated text exception is not classified as a model disconnect.
    raise_on_model_disconnect(RuntimeError('tool TLS handshake: EOF'))
