import queue
from types import SimpleNamespace

from langchain_core.messages import AIMessageChunk

from app.core.aicall.client import AICall
from app.core.aicall.model_streaming import VisibleChatOpenAI
from app.core.workflow.nodes.autonomous_parallel import LaneQueue
from app.core.workflow.stream_contract import project_parallel_tool_event


def test_gateway_reasoning_delta_survives_sdk_and_keeps_tool_calls():
    model = VisibleChatOpenAI(model='test', api_key='test')
    raw = {'choices': [{'index':0, 'delta': {'role':'assistant', 'reasoning_content':'下一步核对日志',
        'tool_calls':[{'index':0, 'id':'call-1','type':'function','function':{'name':'logs','arguments':'{}'}}]}, 'finish_reason':None}]}
    result = model._convert_chunk_to_generation_chunk(raw, AIMessageChunk, {})
    assert result.message.additional_kwargs['reasoning_content'] == '下一步核对日志'
    assert result.message.tool_calls[0]['name'] == 'logs'
    # Reasoning is its own channel; the answer channel stays clean.
    assert AICall._extract_reasoning_text(result.message) == '下一步核对日志'
    assert AICall._extract_visible_ai_text(result.message) == ''


def test_regular_text_and_full_message_reasoning_remain_visible():
    model = VisibleChatOpenAI(model='test', api_key='test')
    result = model._create_chat_result({'choices':[{'index':0,'message':{'role':'assistant',
        'content':'已确认未就绪', 'reasoning_content':'检查就绪条件'}, 'finish_reason':'stop'}]})
    message = result.generations[0].message
    assert AICall._extract_visible_ai_text(message) == '已确认未就绪'
    assert AICall._extract_reasoning_text(message) == '检查就绪条件'
    blocks = SimpleNamespace(content=[
        {'type':'reasoning', 'summary':[{'type':'summary_text','text':'可见摘要'}], 'encrypted_content':'opaque'},
        {'type':'text','text':'正文'}])
    assert AICall._extract_visible_ai_text(blocks) == '正文'
    assert AICall._extract_reasoning_text(blocks) == '可见摘要'


def test_parallel_text_is_scoped_and_streamed_not_dropped():
    output = queue.Queue()
    scoped = LaneQueue(output, group_id='g2', entities=[{'kind':'Pod','namespace':'ns','name':'p'}])
    scoped.put_nowait(('thinking', {'type':'ai_token','node':'evidence','content':'准备查询日志'}))
    _, event = output.get_nowait()
    assert event['node'] == 'parallel_evidence'
    assert event['content'] == '准备查询日志'
    projected = project_parallel_tool_event(event)
    assert projected['parallel_group_id'] == 'g2'
    assert projected['lane_stage'] == 'evidence'
