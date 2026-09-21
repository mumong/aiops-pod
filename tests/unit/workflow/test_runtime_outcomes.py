from app.core.workflow.stream_contract import workflow_outcome, project_query_tool_event
from app.core.workflow.metrics import WorkflowMetrics


def test_partial_is_not_success_and_clarification_is_not_failure():
    assert workflow_outcome({'query_answer': {'status': 'answered'}}) == 'success'
    assert workflow_outcome({'query_answer': {'status': 'clarify'}}) == 'success'
    assert workflow_outcome({'query_answer': {'status': 'partial'}}) == 'partial'
    assert workflow_outcome({'thinking_events': [{'type': 'execution_incomplete', 'reason': 'step_limit'}]}) == 'partial'
    assert workflow_outcome({'autonomous_group_results': [{'status': 'partial'}]}) == 'partial'
    assert workflow_outcome({'request_error': {'code': 'model_timeout'}}) == 'error'


def test_regular_tool_projection_preserves_semantic_failure():
    event = project_query_tool_event({'type': 'tool_result', 'status': 'error',
        'semantic_success': False, 'transport_status': 'success',
        'structured': {'status': 'query_rejected', 'coverage': 'error'},
        'result': '{"status":"query_rejected","coverage":"error"}'})
    assert event['semantic_success'] is False
    assert event['transport_status'] == 'success'


def test_metrics_count_semantic_failure_and_keep_lanes_separate():
    metrics = WorkflowMetrics(run_id='test')
    metrics.rebuild_runtime_counts([
        {'type': 'tool_result', 'node': 'evidence', 'lane_id': 'g1', 'tool_call_id': 'same',
         'status': 'success', 'semantic_success': False},
        {'type': 'tool_result', 'node': 'evidence', 'lane_id': 'g2', 'tool_call_id': 'same',
         'status': 'success', 'semantic_success': True},
    ])
    assert metrics.total_tool_calls == 2
    assert metrics.failed_tool_calls == 1
    assert metrics.successful_tool_calls == 1


def test_acquisition_receipts_survive_compaction_and_keep_lane_identity():
    import asyncio
    from types import SimpleNamespace
    from app.core.workflow.nodes.query_answer import build_working_material
    from app.core.aicall.working_context import compact_working_material
    events = [
        {'type':'tool_result','tool_name':'query_pod_tracing','tool_args':{'namespace':'n','pod':'p'},
         'status':'success','semantic_success':True,'structured':{'coverage':'present'},'raw_ref':'/trace','lane_id':'g1'},
        {'type':'tool_result','tool_name':'fetch_runbook','tool_args':{'runbook_id':'oom.md'},'status':'success'},
        {'type':'context_compacted','working_summary':'Only status survived','retained_messages':[]},
    ]
    material = build_working_material({'question':'why?','thinking_events':events})
    assert not material['observations']
    class Model:
        async def ainvoke(self,*a,**k):return SimpleNamespace(content='summary')
    compact=asyncio.run(compact_working_material(Model(),material,window=54000))
    assert compact['evidence_receipts']==material['evidence_receipts']
    assert compact['evidence_receipts'][0]['raw_ref']=='/trace'
    assert compact['evidence_receipts'][0]['group_id']=='g1'
    assert compact['evidence_receipts'][1]['runbook_id']=='oom.md'
