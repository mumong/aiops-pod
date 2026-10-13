from copy import deepcopy
from types import SimpleNamespace
import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.remediation.jobs import RepairJobs
from app.core.remediation.records import RepairRecordStore, RecordUnavailable, PlanConflict
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.approval import ApprovalStore
from tests.unit.remediation.test_pod_executor import fixture


def setup(tmp_path, monkeypatch):
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    jobs.store.save('d', 'a'*64, None, 'diagnosis', {'groups': [
        {'group_id': 'g1', 'analysis': 'ONE'}, {'group_id': 'g2', 'analysis': 'TWO'}]})
    monkeypatch.setattr(jobs, '_plan_batch', lambda *args: None)
    return jobs, 'a'*64


def test_idempotent_batch_owner_isolation_revision_only_one_group(tmp_path, monkeypatch):
    jobs, owner = setup(tmp_path, monkeypatch)
    batch = jobs.start(None, owner, 'd', 'repair')
    assert batch == jobs.start(None, owner, 'd', 'retry')
    first, second = batch['groups']
    jobs.store.save(first['job_id'], owner, None, 'plan', {'draft': {'answer': 'one'}})
    with pytest.raises(RecordUnavailable):
        jobs.detail(first['job_id'], 'b'*64)
    with pytest.raises(PlanConflict):
        jobs.revise(None, owner, first['job_id'], 2, 'change')
    new = jobs.revise(None, owner, first['job_id'], 1, 'change only g1')
    updated = jobs.batch(batch['batch_id'], owner)
    assert updated['groups'][0]['job_id'] == new['job_id']
    assert updated['groups'][0]['version'] == 2
    assert updated['groups'][1] == second
    assert jobs.detail(first['job_id'], owner)['status'] == 'superseded'
    refreshed = RepairJobs(jobs.store).detail(new['job_id'], owner)
    assert refreshed['feedback']['text'] == 'change only g1'
    assert refreshed['feedback']['source_version'] == 1
    assert refreshed['feedback']['target_version'] == 2
    assert refreshed['feedback']['role'] == 'user'
    assert refreshed['history'][0]['plan']['answer'] == 'one'
    assert jobs.detail(second['job_id'], owner)['feedback'] is None
    assert jobs.detail(second['job_id'], owner)['history'] == []
    with pytest.raises(PlanConflict):
        jobs.revise(None, owner, first['job_id'], 1, 'stale')


def test_restart_and_immutable_plan_records(tmp_path, monkeypatch):
    jobs, owner = setup(tmp_path, monkeypatch)
    batch = jobs.start(None, owner, 'd', 'repair')
    restarted = RepairJobs(jobs.store)
    assert restarted.detail(batch['groups'][0]['job_id'], owner)['status'] == 'interrupted'
    with pytest.raises(PlanConflict):
        jobs.store.update_payload('d', owner, lambda p: p.clear())
    assert jobs.store.load('d', owner)['payload']['groups']


def test_planning_failure_never_enters_execution(tmp_path, monkeypatch):
    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs.start(None, owner, 'd', 'repair')['groups'][0]
    failure = {'code': 'model_connection_interrupted', 'message': '模型服务连接中断，方案未生成。'}
    from app.core.workflow.executor import WorkflowExecutor
    monkeypatch.setattr(WorkflowExecutor, 'execute_stream', lambda *a, **kw: iter([
        {'type': 'final', 'repair_record': {'run_id': job['job_id']},
         'repair_plan': {'actions': [], 'planning_error': failure}}]))
    service = SimpleNamespace(_build_request_scoped_ai_call=lambda: None, mcp_tools=[], merged_catalog=None)
    assert jobs._plan(service, owner, jobs.detail(job['job_id'], owner), 'repair') is False
    detail = jobs.detail(job['job_id'], owner)
    assert detail['status'] == 'failed'
    assert detail['error_code'] == 'model_connection_interrupted'
    assert detail['approval'] is None
    assert detail['status_started_at'] >= detail['created_at']


def test_api_contract_and_owner(tmp_path, monkeypatch):
    import app.api.repair_routes as routes
    jobs, owner = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(routes, 'repair_jobs', jobs)
    monkeypatch.setattr(routes, 'get_service', lambda: None)
    app = FastAPI()
    routes.register_repair_routes(app)
    client = TestClient(app)
    assert client.post('/repair/batches', json={'diagnosis_run_id': 'd'}).status_code == 401
    client.cookies.set('aiops_query_owner', owner)
    response = client.post('/repair/batches', json={'diagnosis_run_id': 'd'})
    assert response.status_code == 200
    assert len(response.json()['groups']) == 2
    assert client.post('/repair/batches', json={'diagnosis_run_id': 'd', '_defer_repair_execution': False}).status_code == 422
    job = response.json()['groups'][0]['job_id']
    assert client.post(f'/repair/jobs/{job}/feedback', json={'version': 1, 'feedback': ' '}).status_code == 422
    client.cookies.set('aiops_query_owner', 'b'*64)
    assert client.get(f'/repair/jobs/{job}').status_code == 404


def test_parallel_planning_does_not_wait_for_approval(tmp_path, monkeypatch):
    jobs = RepairJobs(RepairRecordStore(tmp_path))
    owner = 'a'*64
    jobs.store.save('d', owner, None, 'diagnosis', {'groups': [{'group_id': 'g1'}, {'group_id': 'g2'}]})
    barrier = threading.Barrier(2)
    executed = []
    done = threading.Event()
    release = threading.Event()
    def plan(service, identity, job, question):
        barrier.wait(timeout=3)
        return True
    def execute(service, identity, job):
        executed.append(job['group_id'])
        if len(executed) == 2:
            done.set()
        release.wait(3)
    monkeypatch.setattr(jobs, '_plan', plan)
    monkeypatch.setattr(jobs, '_execute', execute)
    try:
        jobs.start(None, owner, 'd', 'repair')
        assert done.wait(3)
        assert sorted(executed) == ['g1', 'g2']
    finally:
        release.set()


def test_command_execution_is_serial_even_across_legacy_and_grouped_callers():
    entered = threading.Event()
    release = threading.Event()
    second_entered = threading.Event()
    draft = fixture()[0]
    second = deepcopy(draft)
    second['targets'][0]['pod'] = 'different-pod'
    draft['actions'][0]['verify_command'] = ''
    second['actions'][0]['verify_command'] = ''
    def slow(args):
        entered.set()
        assert release.wait(3)
        return 'ok'
    def fast(args):
        second_entered.set()
        return 'ok'
    first = threading.Thread(target=lambda: list(PodRepairExecutor(ApprovalStore(), slow).run('one', draft, mode='auto')))
    other = threading.Thread(target=lambda: list(PodRepairExecutor(ApprovalStore(), fast).run('two', second, mode='auto')))
    first.start()
    try:
        assert entered.wait(3)
        other.start()
        assert not second_entered.wait(.15)
    finally:
        release.set()
        first.join(3)
        other.join(3)
    assert second_entered.is_set()


def test_planning_scopes_context_and_defers_execution(tmp_path, monkeypatch):
    import app.core.workflow.executor as module
    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs._new_job('batch', owner, 'd', {'group_id': 'g1'})
    seen = {}
    class Executor:
        def __init__(self, **kw):
            pass
        def execute_stream(self, question, job_id, cancel, overrides):
            seen.update(overrides)
            yield {'type': 'final', 'repair_record': {'run_id': job_id}, 'repair_plan': {'actions': []}}
    monkeypatch.setattr(module, 'WorkflowExecutor', Executor)
    service = SimpleNamespace(_build_request_scoped_ai_call=lambda: object(), mcp_tools=[])
    assert jobs._plan(service, owner, job, 'repair')
    assert seen['_repair_group_id'] == 'g1'
    assert seen['query_mode'] == 'auto'  # default/full would run the legacy diagnosis graph
    assert seen['_defer_repair_execution'] is True
    assert seen['_query_session_key'] == (owner, 'repair-' + job['job_id'])


def test_group_job_reuses_auto_policy_and_records_execution(tmp_path, monkeypatch):
    import app.core.remediation.pod_executor as module
    jobs, owner = setup(tmp_path, monkeypatch)
    job = jobs._new_job('batch', owner, 'd', {'group_id': 'g1'})
    draft = fixture()[0]
    jobs.store.save(job['job_id'], owner, None, 'plan', {'draft': draft})
    calls = []
    monkeypatch.setattr(module, 'run_argv', lambda argv: calls.append(argv) or 'observed')
    jobs._execute(SimpleNamespace(workflow_config={'remediation': {'enabled': True, 'mode': 'auto'}}), owner, job)
    result = jobs.detail(job['job_id'], owner)
    assert result['status'] == 'needs_followup' and result['mode'] == 'auto'
    assert len(calls) == 2
    assert result['approval'] is None
    assert len(result['events']) == 4
    assert job['job_id'] not in jobs.cancellations
