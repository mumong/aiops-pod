"""Opt-in real repair planning test; execution is deferred and guarded."""
import argparse
import json
import threading
import uuid
from pathlib import Path

from app.core.service import get_service
from app.core.workflow.executor import WorkflowExecutor
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.executor import RemediationExecutor
from app.core.remediation.records import RepairRecordStore
from app.core.remediation.group_context import scoped_diagnosis


def forbidden_execution(*args, **kwargs):
    raise AssertionError('Read-only planning verification must never execute a repair')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', required=True)
    parser.add_argument('--diagnosis-run', required=True)
    parser.add_argument('--browser-state', type=Path, required=True)
    parser.add_argument('--group', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    owner = next(c['value'] for c in json.loads(args.browser_state.read_text())['cookies']
                 if c['name'] == 'aiops_query_owner')
    store = RepairRecordStore()
    record = store.load(args.diagnosis_run, owner, 'diagnosis')
    scoped = scoped_diagnosis(record, args.group)
    assert len(scoped['payload']['groups']) == 1
    assert scoped['payload']['diagnosis_result']['key_facts']
    PodRepairExecutor.run = forbidden_execution
    RemediationExecutor.run = forbidden_execution
    service = get_service()
    service.initialize()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'scoped-input.json').write_text(json.dumps(scoped, ensure_ascii=False, indent=2))
    previous = None
    for version, question in enumerate([
        '请基于本组诊断生成修复方案，列出对象、根因、拟执行命令和验证条件。仅规划，本次测试不执行。',
        '仅修改当前组方案：保留原修复目标和变更方向，将修复后的观察窗口改为120秒，并清楚标注尚未执行。仅规划，不执行。',
    ], 1):
        run_id = 'verify-plan-' + uuid.uuid4().hex[:16]
        executor = WorkflowExecutor(holmes_service=service)
        executor.ai_call = service._build_request_scoped_ai_call()
        executor.mcp_tools = service.mcp_tools or []
        overrides = {'query_mode': 'auto', '_query_session_key': (owner, 'verify-' + run_id),
                     '_repair_group_id': args.group, '_defer_repair_execution': True}
        overrides['_plan_run_id' if previous else '_diagnosis_run_id'] = previous or args.diagnosis_run
        events = list(executor.execute_stream(question, run_id, threading.Event(), overrides))
        (args.output / f'v{version}-events.json').write_text(json.dumps(events, ensure_ascii=False, default=str))
        assert not [e for e in events if e.get('type') == 'error'], 'Planner returned an error; inspect events'
        final = next(e for e in events if e.get('type') == 'final')
        plan = final.get('repair_plan') or {}
        assert not plan.get('planning_error'), plan.get('planning_error')
        assert final.get('repair_record'), 'Plan was not persisted'
        saved = store.load(run_id, owner, 'plan')
        assert not saved.get('execution_events'), 'Repair must remain unexecuted'
        (args.output / f'v{version}-final.json').write_text(json.dumps(final, ensure_ascii=False, indent=2))
        print(json.dumps({'version': version, 'run_id': run_id, 'group': args.group,
                          'targets': len(plan.get('targets') or []),
                          'actions': len(plan.get('actions') or []), 'executed': False}), flush=True)
        previous = run_id


if __name__ == '__main__':
    main()
