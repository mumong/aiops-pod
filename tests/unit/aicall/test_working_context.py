import asyncio
import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages
from app.core.aicall.client import AICall
from app.core.aicall.working_context import WorkingContextMiddleware, summarize_history, summary_chunks, compact_message, message_groups


class SummaryModel:
    def __init__(self):
        self.inputs = []

    async def ainvoke(self, messages, **kwargs):
        self.inputs.append(json.loads(messages[-1].content))
        return AIMessage(content="任务：查 CPU。已发现 node_cpu_seconds_total，目录已读取，下一步仍需数值。")


def test_compaction_probe_counts_repair_schema_at_budget_boundary(tmp_path, monkeypatch):
    from app.core.aicall.client import StructuredContextBudgetError
    from langchain.agents.structured_output import ToolStrategy
    from app.core.workflow.nodes.remediation import RepairDraft
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    client = AICall(model='openai/test', api_key='test')
    schema = ToolStrategy(RepairDraft)
    seen = []
    def guard(request, **kwargs):
        seen.append(request.response_format)
        # Original payload fits without the schema but exceeds with it, as in
        # d550579632504069 (45,396 vs 46,272; effective target 45,744).
        if request.response_format is schema and 'boundary payload' in str(request.messages):
            raise StructuredContextBudgetError('working_context_compaction_required', pre_budget={'context_window':54000})
        return request, {'context_window':54000}
    monkeypatch.setattr(client, '_guard_agent_model_request', guard)
    model = SummaryModel()
    middleware = WorkingContextMiddleware(client, client._create_chat_model(), model, [],
        'system', '修复', 'boundary', 'remediation', lambda **e: None, response_format=schema)
    original = [HumanMessage(content='修复'), HumanMessage(content='boundary payload '*5000)]
    update = asyncio.run(middleware.abefore_model({'messages':original}, None))
    assert update and model.inputs
    replaced = add_messages(original, update['messages'])
    assert asyncio.run(middleware.abefore_model({'messages':replaced}, None)) is None
    assert all(value is schema for value in seen)


def test_material_compaction_retains_recent_original_and_summarizes_older():
    from app.core.aicall.working_context import compact_working_material
    model = SummaryModel()
    material = {'question': '查 CPU', 'working_summary': 'earlier summary',
                'observations': [{'tool_args': {'pod':'old'}, 'result':'OLD ' * 12000},
                                 {'tool_args': {'pod':'new'}, 'result':'LATEST EXACT', 'raw_ref':'/raw/latest'}]}
    compact = asyncio.run(compact_working_material(model, material, window=16000))
    history = ''.join(m['next_history_chunk'] for m in model.inputs)
    assert 'earlier summary' in history and 'OLD ' in history
    assert 'LATEST EXACT' not in history
    retained = json.loads(compact['recent_interactions'][0]['content'])['tool_observation']
    assert retained == material['observations'][-1]
    assert compact['observations'] == []


def test_fanin_compaction_keeps_recent_evidence_with_lane_identity():
    from app.core.aicall.working_context import compact_working_material
    material = {'question': '比较两个Pod', 'parallel_results': [
        {'group_id': 'g1', 'target': {'name':'a'}, 'status':'partial', 'error':'timeout',
         'material': {'working_summary':'a summary', 'observations':[{'result':'a original'}]}},
        {'group_id': 'g2', 'target': {'name':'b'}, 'status':'completed',
         'material': {'working_summary':'b summary', 'observations':[{'result':'b original'}]}}]}
    model = SummaryModel()
    compact = asyncio.run(compact_working_material(model, material, window=54000))
    recent = [json.loads(m['content']) for m in compact['recent_interactions']]
    assert [m['lane_id'] for m in recent] == ['g1','g2']
    assert 'a original' in recent[0]['interaction'][0]['content']
    assert 'b original' in recent[1]['interaction'][0]['content']
    history = ''.join(m['next_history_chunk'] for m in model.inputs)
    assert 'a summary' in history and 'b summary' in history and 'timeout' in history


def test_all_history_chunks_consumed_without_slicing_away_middle():
    model = SummaryModel()
    source = "a" * 15000 + "MIDDLE_IMPORTANT" + "z" * 15000
    asyncio.run(summarize_history(model, "查 CPU", source, window=16000, parallel=False))
    assert ''.join(x['next_history_chunk'] for x in model.inputs) == source
    assert all(x['original_question'] == '查 CPU' for x in model.inputs)
    assert model.inputs[1]['working_summary']


@pytest.mark.parametrize('node_id', ['query_collect', 'layer', 'evidence'])
@pytest.mark.parametrize('window', [32000, 54000])
def test_reducer_replaces_history_and_next_round_does_not_recompress(tmp_path, monkeypatch, node_id, window):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", str(window))
    client = AICall(model="openai/test", api_key="test")
    client.query_context_state_compaction = True
    model = SummaryModel()
    emitted = []
    middleware = WorkingContextMiddleware(client, client._create_chat_model(), model, [],
                                         'system', '查 CPU', 'replace', node_id,
                                         lambda **e: emitted.append(e))
    original = [HumanMessage(content='查 CPU'),
                AIMessage(content='', tool_calls=[{'id': 't1', 'name': 'get_metric_names', 'args': {}}]),
                ToolMessage(content='huge metric directory ' * 12000, tool_call_id='t1')]
    update = asyncio.run(middleware.abefore_model({'messages': original}, None))
    state = add_messages(original, update['messages'])
    assert len(state) == 2
    assert state[0].content == '查 CPU'
    assert 'huge metric directory' not in str(state)
    assert any(e['type'] == 'context_compacted' for e in emitted)
    calls = len(model.inputs)
    assert asyncio.run(middleware.abefore_model({'messages': state}, None)) is None
    assert len(model.inputs) == calls
    # Subsequent accumulated data can trigger another replacement independently.
    state = add_messages(state, [HumanMessage(content='next huge data ' * 18000)])
    update = asyncio.run(middleware.abefore_model({'messages': state}, None))
    assert len(add_messages(state, update['messages'])) == 2
    assert sum(e['type'] == 'context_compacted' for e in emitted) == 2
    assert len(list((tmp_path/'replace/compactions').glob('*.before.json'))) == 2


def test_summary_failure_does_not_replace_state():
    class Empty:
        async def ainvoke(self, *a, **kw): return SimpleNamespace(content='')
    with pytest.raises(RuntimeError, match='未替换'):
        asyncio.run(summarize_history(Empty(), 'q', 'data'))


def test_parallel_summary_is_bounded_ordered_and_consumes_every_chunk(monkeypatch):
    monkeypatch.setenv('AIOPS_COMPACTION_WORKERS', '3')
    class Model:
        def __init__(self):
            self.inputs, self.active, self.peak = [], 0, 0
        async def ainvoke(self, messages, **kwargs):
            payload = json.loads(messages[-1].content)
            self.inputs.append(payload)
            if payload['mode'] == 'map':
                self.active += 1
                self.peak = max(self.peak, self.active)
                await asyncio.sleep(0.01 * (3 - payload['chunk_index'] % 3))
                self.active -= 1
                return AIMessage(content=f"card-{payload['chunk_index']}")
            return AIMessage(content='merged summary')
    model = Model()
    source = 'old log ' * 12000
    stats = {}
    result = asyncio.run(summarize_history(model, 'Pod OOM', source, window=16000, stats=stats))
    maps = sorted((p for p in model.inputs if p['mode'] == 'map'), key=lambda p:p['chunk_index'])
    assert len(maps) >= 3
    assert ''.join(p['next_history_chunk'] for p in maps) == source
    assert model.peak == 3
    merged = next(p for p in model.inputs if p['mode'] == 'reduce')
    assert merged['next_history_chunk'].index('card-0') < merged['next_history_chunk'].index('card-1')
    assert merged['is_last_chunk'] is True
    assert result == 'merged summary'
    assert stats['calls'] == len(model.inputs)


def test_parallel_failure_cancels_siblings_and_keeps_history(monkeypatch):
    monkeypatch.setenv('AIOPS_COMPACTION_WORKERS', '3')
    cancelled = []
    class Broken:
        async def ainvoke(self, messages, **kwargs):
            p = json.loads(messages[-1].content)
            if p['chunk_index'] == 0:
                await asyncio.sleep(0)
                raise RuntimeError('provider failed')
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled.append(p['chunk_index'])
                raise
    with pytest.raises(RuntimeError, match='provider failed'):
        asyncio.run(summarize_history(Broken(), 'q', 'old log ' * 12000, window=16000))
    assert cancelled


def test_compaction_progress_reports_chunks_and_terminal_state():
    events = []
    asyncio.run(summarize_history(SummaryModel(), 'q', 'a' * 13000,
                                 lambda **e: events.append(e)))
    assert [e['status'] for e in events] == ['running', 'complete']
    assert '1/1' in events[0]['content']
    assert '一份摘要' in events[0]['content']
    # The helper also serves whole-payload callers; don't promise a retained tail here.
    assert '近期完整交互另行保留' not in events[0]['content']


def test_compaction_progress_reports_error_and_cancellation():
    for error, expected in [(RuntimeError('provider failed'), 'error'),
                            (asyncio.CancelledError(), 'cancelled')]:
        events = []
        class Failed:
            async def ainvoke(self, *args, **kwargs):
                raise error
        with pytest.raises(type(error)):
            asyncio.run(summarize_history(Failed(), 'q', 'data', lambda **e: events.append(e)))
        assert events[-1]['status'] == expected


def test_real_langgraph_persists_replacement_across_tool_rounds(tmp_path, monkeypatch):
    from langchain.agents import create_agent
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.tools import tool
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    monkeypatch.setenv('MODEL_CONTEXT_WINDOW', '32000')
    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs): return self
    @tool
    def directory() -> str:
        """Return a large directory."""
        return 'directory item ' * 8000
    model = Model(responses=[
        AIMessage(content='', tool_calls=[{'name': 'directory', 'args': {}, 'id': 'one'}]),
        AIMessage(content='', tool_calls=[{'name': 'directory', 'args': {}, 'id': 'two'}]),
        AIMessage(content='done'),
    ])
    client = AICall(model='openai/test', api_key='test')
    client.query_context_state_compaction = True
    events = []
    middleware = WorkingContextMiddleware(client, model, SummaryModel(), [directory], 'system',
                                         '查 CPU', 'graph', 'query_collect', lambda **e: events.append(e))
    agent = create_agent(model, tools=[directory], system_prompt='system', middleware=[middleware])
    state = asyncio.run(agent.ainvoke({'messages': [HumanMessage(content='查 CPU')]}))
    assert sum(e['type'] == 'context_compacted' for e in events) == 2
    assert len(state['messages']) == 3  # original intent, new summary, final answer
    assert state['messages'][-1].content == 'done'
    assert 'directory item' not in str(state['messages'])


def test_aicall_stream_handles_noop_and_replacement_updates(tmp_path, monkeypatch):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.tools import tool
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    monkeypatch.setenv('MODEL_CONTEXT_WINDOW', '32000')
    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs): return self
    @tool
    def directory() -> str:
        """Return a large directory."""
        return 'directory item ' * 8000
    model = Model(responses=[AIMessage(content='', tool_calls=[
        {'name': 'directory', 'args': {}, 'id': 'one'}]), AIMessage(content='finished')])
    summary_model = FakeMessagesListChatModel(responses=[AIMessage(content='目录已采集，原任务查 CPU。')])
    client = AICall(model='openai/test', api_key='test')
    client.query_context_state_compaction = True
    client.query_raw_passthrough = True
    monkeypatch.setattr(client, '_create_chat_model', lambda **kw: summary_model if kw.get('node_id') == 'context_compaction' else model)
    result, events = client.call('system', '查 CPU', tools=[directory], max_steps=20,
                                 run_id='stream', node_id='query_collect')
    assert result.result == 'finished'
    assert any(e['type'] == 'context_compacted' for e in events)
    assert not any(e['type'] == 'execution_incomplete' for e in events)


def test_54k_keeps_recent_parallel_tool_exchange_verbatim(tmp_path, monkeypatch):
    monkeypatch.setenv('AIOPS_CONTEXT_ARCHIVE_ROOT', str(tmp_path))
    monkeypatch.setenv('MODEL_CONTEXT_WINDOW', '54000')
    client = AICall(model='openai/test', api_key='test')
    client.query_context_state_compaction = True
    model = SummaryModel()
    events = []
    middleware = WorkingContextMiddleware(client, client._create_chat_model(), model, [],
        'system', '查 CPU', 'recent', 'query_collect', lambda **e: events.append(e))
    recent = [AIMessage(content='', tool_calls=[
        {'id': 'cpu', 'name': 'metrics', 'args': {'q': 'cpu'}},
        {'id': 'mem', 'name': 'metrics', 'args': {'q': 'memory'}}]),
        ToolMessage(content='CPU rate: 0.137 cores at time T', tool_call_id='cpu'),
        ToolMessage(content='memory working_set: 123456 bytes', tool_call_id='mem')]
    original = [HumanMessage(content='查 CPU'), HumanMessage(content='old data ' * 18000), *recent]
    result = asyncio.run(middleware.abefore_model({'messages': original}, None))
    state = add_messages(original, result['messages'])
    assert [m.content for m in state[-3:]] == [m.content for m in recent]
    assert [m.tool_call_id for m in state[-2:]] == ['cpu', 'mem']
    assert '0.137' not in ''.join(x['next_history_chunk'] for x in model.inputs)
    event = next(e for e in events if e['type'] == 'context_compacted')
    assert event['retained_messages'][-2]['content'] == recent[-2].content
    assert asyncio.run(middleware.abefore_model({'messages': state}, None)) is None


def test_summary_packing_preserves_units_and_uses_one_call_at_54k():
    sections = ['a' * 12000 + '\n', 'b' * 14000 + '\n', '中文事实' * 2000 + '\n']
    chunks, _ = summary_chunks('q', ''.join(sections), window=54000, sections=sections)
    assert chunks == [''.join(sections)]
    chunks, _ = summary_chunks('q', ''.join(sections), window=24000, sections=sections)
    assert ''.join(chunks) == ''.join(sections)


def test_incomplete_tool_exchange_is_not_silently_split():
    with pytest.raises(RuntimeError, match='尚不完整'):
        message_groups([AIMessage(content='', tool_calls=[{'id': 'a', 'name': 'metrics', 'args': {}}])])


def test_compact_envelope_removes_telemetry_not_facts():
    message = AIMessage(content='fact', response_metadata={'usage': {'total': 999}})
    assert compact_message(message)['content'] == 'fact'
    assert 'response_metadata' not in compact_message(message)
