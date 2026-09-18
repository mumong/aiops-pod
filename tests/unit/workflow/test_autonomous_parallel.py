import json
import threading
from types import SimpleNamespace

from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode, PodTargets, PodTarget, plan_groups
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
        gid = material['diagnosis_target']['group_id']
        assert material['original_question'] == '检查这三个 Pod 的根因'
        assert material['request_contract']['pod_names'] == [f'pod-{gid[1:]}']
        assert f'demo/pod-{gid[1:]}' in material['question']
        assert kw['skip_remediation_policy']
        assert '固定 EvidencePlan' in prompt
        seen.append((gid, self.node_id, id(self.ai_call)))
        if self.node_id == 'evidence':
            barrier.wait(timeout=5)  # Cannot pass if the implementation is serial.
            if gid == 'g2':
                raise RuntimeError('tool/provider failure')
            return SimpleNamespace(result=f'{gid} evidence'), [
                {'type': 'context_compacted', 'working_summary': gid, 'retained_messages': []},
                {'type': 'tool_result', 'tool_name': 'kubectl_describe', 'result': gid, 'raw_ref': f'/{gid}/raw'}]
        assert material['working_summary'] == gid
        assert kw['force_no_tools']
        return SimpleNamespace(result=f'{gid} RCA uncertain'), []
    monkeypatch.setattr(DiagnosisEvidenceNode, '_call_llm', call)
    monkeypatch.setattr(DiagnosisRootCauseNode, '_call_llm', call)
    state = {'question': '检查这三个 Pod 的根因', 'autonomous_groups': groups(),
             'thinking_events': [{'type': 'tool_result', 'result': 'shared-list'}]}
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


def test_planner_deduplicates_targets_and_failure_continues_serially():
    plan = PodTargets(targets=[PodTarget(namespace='demo', name='pod', question='重启')]*2)
    node = SimpleNamespace(ai_call=SimpleNamespace(call_structured=lambda **kw: (plan,'')))
    assert len(plan_groups(node, {'question':'q'})['autonomous_groups']) == 1
    node.ai_call.call_structured = lambda **kw: (None, 'bad')
    result = plan_groups(node, {'question':'q'})
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
