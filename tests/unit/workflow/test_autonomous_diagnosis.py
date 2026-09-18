import json
from types import SimpleNamespace

import pytest

from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.request_router import RequestContract
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode
from app.core.context.observation import ObservationProcessor
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisRootCauseNode
from app.core.workflow.nodes.query_answer import QueryConclusionNode
from app.core.aicall.client import StructuredContextBudgetError


def test_legacy_style_prompts_keep_professional_rules_without_old_engine_contracts():
    from app.core.prompts import (
        DEEP_LAYER_PROMPT, DEEP_EVIDENCE_PROMPT, DEEP_RCA_PROMPT,
        DEEP_CONCLUSION_PRESENTATION,
    )
    assert '用户问全集群问题才检查集群范围' in DEEP_LAYER_PROMPT
    assert 'fetch_runbook' in DEEP_LAYER_PROMPT
    assert '执行代码提供的首轮计划' not in DEEP_EVIDENCE_PROMPT
    assert '80%' not in DEEP_EVIDENCE_PROMPT
    assert '最上游可行动条件' in DEEP_RCA_PROMPT
    assert '## 🕵️ 证据内容' in DEEP_CONCLUSION_PRESENTATION
    assert 'QueryAnswer' in DEEP_CONCLUSION_PRESENTATION
    for prompt in (DEEP_LAYER_PROMPT, DEEP_EVIDENCE_PROMPT, DEEP_RCA_PROMPT):
        assert '{layer}' not in prompt
        assert '{evidence_summary}' not in prompt
        assert '{possible_scenarios}' not in prompt


@pytest.mark.parametrize('route,expected', [
    ('focused', ['query_collect', 'conclusion']),
    ('full_diagnosis', ['layer', 'evidence', 'rca', 'conclusion']),
])
def test_model_routes_scoped_task_and_original_question_survives_every_stage(route, expected):
    graph, nodes = build_diagnosis_workflow(query_mode='auto')
    question = '分析 xnet/nginx 的根因，只检查这个 Pod'
    visited, payloads = [], []
    history = {'turns': [{'question': 'xnet 有哪些 Pod', 'scope': 'xnet/nginx'}]}
    observation = {'type': 'tool_result', 'tool_name': 'kubectl_describe',
                   'result': 'Last State: OOMKilled', 'raw_ref': '/raw/describe'}
    for node in nodes:
        node.ai_call = SimpleNamespace()
        if node.node_id == 'request_router':
            def classify(**kw):
                assert json.loads(kw['question'])['history'][0]['scope'] == 'xnet/nginx'
                return RequestContract(route=route, task='diagnose', scope='pod',
                                       namespaces=['xnet'], pod_names=['nginx']), ''
            node.ai_call.call_structured = classify
            continue
        def call(text, prompt, _node=node, **kwargs):
            visited.append(_node.node_id)
            assert question in text
            assert not kwargs.get('stop_checker')
            assert kwargs['skip_remediation_policy']
            if _node.node_id != 'query_collect':
                payload = json.loads(text)
                payloads.append(payload)
                assert payload['question'] == question
                assert payload['request_contract']['pod_names'] == ['nginx']
                if _node.node_id != 'layer':
                    assert any(o['raw_ref'] == '/raw/describe' for o in payload['observations'])
            if _node.node_id in {'rca', 'conclusion'}:
                assert kwargs['force_no_tools']
            if _node.node_id == 'conclusion':
                assert ('证据表至少分别列出' in prompt) == (route == 'full_diagnosis')
                return SimpleNamespace(result=json.dumps({'intent': question, 'scope': 'xnet/nginx',
                    'status': 'partial', 'answer': 'OOMKilled；上游机制待核实', 'missing': ['机制']})), []
            return SimpleNamespace(result='分析草稿，不是事实'), [observation] if _node.node_id in {'layer', 'query_collect'} else []
        node._call_llm = call
    result = graph.invoke({'question': '不得覆盖的旧 question', 'original_question': question,
                           'query_session_context': history})
    assert visited == expected
    assert result['query_session_memory']['turns'][-1]['scope'] == 'xnet/nginx'
    assert all(n.ai_call.query_context_state_compaction for n in nodes if n.node_id in expected)


def test_deep_handoff_uses_replaced_working_context_not_old_observations():
    node = DiagnosisEvidenceNode()
    node.ai_call = SimpleNamespace()
    seen = {}
    def call(text, *args, **kwargs):
        seen.update(json.loads(text))
        return SimpleNamespace(result='继续分析'), []
    node._call_llm = call
    node.execute({'original_question': '查 xnet', 'thinking_events': [
        {'type': 'tool_result', 'result': 'OLD_HUGE'},
        {'type': 'context_compacted', 'working_summary': '已检查 xnet', 'retained_messages': []},
        {'type': 'tool_result', 'result': '最新观测'},
    ]})
    assert 'OLD_HUGE' not in json.dumps(seen)
    assert seen['working_summary'] == '已检查 xnet'
    assert node.ai_call.working_context_original_question == '查 xnet'


@pytest.mark.parametrize('node_id', ['query_collect', 'layer', 'evidence'])
def test_heavy_table_summary_does_not_select_only_abnormal_objects(tmp_path, node_id):
    processor = ObservationProcessor(archive_root=str(tmp_path))
    rows = 'NAMESPACE NAME READY STATUS RESTARTS AGE\n' + ''.join(
        f'xnet healthy-{i} 1/1 Running 0 10d\n' for i in range(300)) + 'other bad 0/1 Pending 0 1d\n'
    result = processor.process(run_id='scope', node_id=node_id, sequence=1,
                               tool_name='kubectl_get_by_kind_in_cluster', raw_content=rows, preserve_raw=True)
    assert 'healthy-0' in result['summary']
    assert result['structured']['selection_policy'] == 'source_order_not_health_filtered'


@pytest.mark.parametrize('node_class', [DiagnosisRootCauseNode, QueryConclusionNode])
def test_tool_free_nodes_compact_oversized_material_instead_of_truncating(node_class, monkeypatch):
    node = node_class()
    model = SimpleNamespace(bind=lambda **kw: object())
    node.ai_call = SimpleNamespace(_create_chat_model=lambda **kw: model, _push=lambda *a, **kw: None)
    calls, summaries = [], []
    async def summarize(model, question, material, *args, **kwargs):
        summaries.append((question, material))
        return '已查 Pod 当前状态，尚缺上游原因；/raw/describe'
    monkeypatch.setattr('app.core.aicall.working_context.summarize_history', summarize)
    def call(text, *args, **kwargs):
        calls.append(json.loads(text))
        assert kwargs['force_no_tools']
        if len(calls) == 1:
            raise StructuredContextBudgetError('working_context_compaction_required')
        return SimpleNamespace(result='证据不足以确认上游原因'), []
    node._call_llm = call
    output = node.execute({'original_question': '为什么 xnet/nginx 重启？',
        'request_contract': {'route': 'full_diagnosis', 'pod_names': ['nginx']},
        'request_time_utc': '2026-09-18T02:00:00Z',
        'thinking_events': [{'type': 'tool_result', 'result': '完整待压缩证据', 'raw_ref': '/raw/describe'}]})
    assert summaries[0][0] == '为什么 xnet/nginx 重启？'
    assert '完整待压缩证据' not in summaries[0][1]
    assert '完整待压缩证据' in json.dumps(calls[1]['recent_interactions'], ensure_ascii=False)
    assert calls[1]['question'] == summaries[0][0]
    assert calls[1]['request_contract']['route'] == 'full_diagnosis'
    assert calls[1]['request_time_utc'] == '2026-09-18T02:00:00Z'
    assert calls[1]['working_summary'].endswith('/raw/describe')
    assert calls[1]['observations'] == []
    assert output
