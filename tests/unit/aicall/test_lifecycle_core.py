import asyncio
import copy
import json
from pathlib import Path

import pytest

from app.core.context.lifecycle_core import core_from_messages, lifecycle_core, merge_cores
from app.core.workflow.working_material import build_working_material


def snapshot(when='2026-10-12T03:08:04+00:00', uid='u1'):
    return {'contract_version': 'pod-lifecycle.v1', 'status': 'success',
            'observed_at': when, 'scope': {'namespace': 'ns'},
            'next_continue_token': None, 'history_complete': False,
            'pods': [{'namespace': 'ns', 'name': 'pod', 'uid': uid,
                      'phase': 'Running', 'deletion_timestamp': '2026-10-10T09:29:27Z',
                      'conditions': [{'type': 'Ready', 'status': 'False'}],
                      'containers': [{'name': 'app', 'ready': False,
                                      'termination_within_window': False,
                                      'state': {'terminated': {'reason': 'Error', 'exitCode': 137}}}]}]}


def test_old_event_does_not_remove_current_facts():
    raw = snapshot()
    before = copy.deepcopy(raw)
    core = lifecycle_core(raw, '/raw/1')
    pod = core['entities'][0]
    assert pod['deletion_timestamp'] == raw['pods'][0]['deletion_timestamp']
    assert pod['containers'][0]['ready'] is False
    assert pod['containers'][0]['termination_within_window'] is False
    assert pod['conditions'] == {'Ready': {'status': 'False'}}
    assert raw == before


def test_freshest_snapshot_uses_absolute_time_and_replaces_uid():
    newer = lifecycle_core(snapshot('2026-10-12T04:00:00Z', 'new'))
    older = lifecycle_core(snapshot('2026-10-12T11:00:00+08:00', 'old'))
    assert merge_cores(newer, older)['entities'][0]['uid'] == 'new'
    assert merge_cores(newer, newer) == newer


def test_partial_empty_and_failure_do_not_erase_observed_entities():
    original = lifecycle_core(snapshot())
    empty = snapshot('2026-10-12T04:00:00Z')
    empty.update(pods=[], next_continue_token='next')
    assert merge_cores(original, lifecycle_core(empty))['entities'] == original['entities']
    assert lifecycle_core({**snapshot(), 'status': 'error'}) == {}


def test_repeated_model_compaction_cannot_rewrite_core(monkeypatch):
    from app.core.aicall import working_context as wc

    async def misleading(*args, **kwargs):
        return '所有对象均已恢复，只有历史问题'

    monkeypatch.setattr(wc, 'summarize_history', misleading)
    material = {'question': '集群有什么问题', 'observations': [
        {'structured': snapshot(), 'raw_ref': '/raw/1'}]}
    expected = lifecycle_core(snapshot(), '/raw/1')
    for _ in range(3):
        material = asyncio.run(wc.compact_working_material(None, material, window=16000))
        assert material['protected_handoff']['lifecycle_core'] == expected
    assert core_from_messages([{'type': 'human', 'content': json.dumps(material)}]) == expected


def test_node_handoff_keeps_pre_compaction_tool_facts():
    state = {'question': 'q', 'thinking_events': [
        {'type': 'tool_result', 'structured': snapshot(), 'raw_ref': '/raw/1'},
        {'type': 'context_compacted', 'working_summary': '没有异常'}]}
    assert build_working_material(state)['protected_handoff']['lifecycle_core'] == lifecycle_core(snapshot(), '/raw/1')


def test_core_is_not_sent_to_summary_model_or_duplicated(monkeypatch):
    from app.core.aicall import working_context as wc
    seen = []

    async def summary(model, question, history, *args, **kwargs):
        seen.append(history)
        return '摘要'

    monkeypatch.setattr(wc, 'summarize_history', summary)
    raw = snapshot()
    material = build_working_material({'question': 'q', 'thinking_events': [
        {'type': 'tool_result', 'structured': raw, 'result': json.dumps(raw), 'raw_ref': '/raw/1'}]})
    assert material['observations'][0]['result']['facts_in'] == 'protected_handoff.lifecycle_core'
    result = asyncio.run(wc.compact_working_material(None, material, window=16000))
    assert 'deletion_timestamp' not in ''.join(seen)
    assert 'protected_facts_available' in ''.join(seen)
    assert 'observed_entities' in ''.join(seen)
    assert 'deletion_timestamp' not in json.dumps(result['recent_interactions'])
    assert result['protected_handoff']['lifecycle_core']['entities'][0]['deletion_timestamp']


def test_parallel_fanin_deduplicates_entities_without_mutating_lanes():
    core = lifecycle_core(snapshot())
    lanes = [{'group_id': 'g1', 'material': {'protected_handoff': {'lifecycle_core': core}}},
             {'group_id': 'g2', 'material': {'protected_handoff': {'lifecycle_core': core}}}]
    original = copy.deepcopy(lanes)
    result = build_working_material({'question': 'q', 'autonomous_group_results': lanes})
    assert len(result['protected_handoff']['lifecycle_core']['entities']) == 1
    assert 'lifecycle_core' not in json.dumps(result['parallel_results'])
    assert lanes == original


def test_selected_records_are_preserved_without_fabricating_full_entities():
    packet = {'contract_version': 'evidence-records.v1', 'status': 'success', 'coverage': 'partial',
              'record_unit': 'pod', 'source_metadata': {'scope': {'namespace': 'ns'},
              'observed_at': '2026-10-12T04:00:00Z', 'coverage': 'partial'},
              'input_rows': 1, 'matched_rows': 1, 'unknown_filter_rows': 0,
              'executed_query': {'fields': ['ready']}, 'result_type': 'records',
              'columns': ['pod', 'ready'], 'rows': [{'pod': 'pod', 'ready': False}]}
    core = lifecycle_core(packet)
    assert core['entities'] == []
    assert next(iter(core['record_sets'].values()))['packet'] == packet
    newer = copy.deepcopy(packet)
    newer['source_metadata']['observed_at'] = '2026-10-12T05:00:00Z'
    newer['rows'][0]['ready'] = True
    result = merge_cores(lifecycle_core(newer), core)
    assert len(result['record_sets']) == 1
    assert next(iter(result['record_sets'].values()))['packet'] == newer


@pytest.mark.parametrize('node', ['layer', 'evidence', 'query_collect'])
def test_diagnosis_projection_preserves_archive_and_query_compatibility(tmp_path, node):
    from app.core.context.observation import ObservationProcessor
    raw = json.dumps(snapshot())
    result = ObservationProcessor(archive_root=str(tmp_path)).process('test', node, 1, 'query_pod_lifecycle', raw)
    assert Path(result['raw_ref']).read_text() == raw
    assert result['structured']['pods'] == snapshot()['pods']
    if node == 'query_collect':
        assert result['summary'] == raw
    else:
        assert json.loads(result['summary'])['contract_version'] == 'pod-lifecycle-core.v1'
        assert core_from_messages([{'type': 'tool', 'content': result['summary'],
            'additional_kwargs': {'aiops_raw_ref': result['raw_ref']}}]) == lifecycle_core(result['structured'], result['raw_ref'])


def test_oversized_protected_core_fails_without_replacing_original(tmp_path, monkeypatch):
    from langchain_core.messages import AIMessage, HumanMessage

    from app.core.aicall import working_context as wc
    from app.core.aicall.client import AICall, StructuredContextBudgetError
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    client = AICall(model='openai/test', api_key='test')
    async def summary(*args, **kwargs):
        return AIMessage(content='压缩后仍有核心事实')
    from types import SimpleNamespace
    middleware = wc.WorkingContextMiddleware(client, client._create_chat_model(),
        SimpleNamespace(ainvoke=summary), [], 'system', 'q', 'overflow', 'layer', lambda **e: None)
    def fail_probe(messages):
        raise StructuredContextBudgetError('working_context_compaction_required', pre_budget={'context_window': 16000})
    monkeypatch.setattr(middleware, 'probe', fail_probe)
    original = [HumanMessage(content=json.dumps({'protected_handoff': {'lifecycle_core': lifecycle_core(snapshot())}}))]
    before = copy.deepcopy(original)
    with pytest.raises(StructuredContextBudgetError):
        asyncio.run(middleware.abefore_model({'messages': original}, None))
    assert original == before
