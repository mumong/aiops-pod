"""Opt-in real-cluster acceptance, isolated namespace; no business resources.

Creates fixtures and intentionally leaves them for inspection/explicit cleanup.
Approves only reviewed commands for the named fixtures, never global auto mode.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', required=True)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--reuse-fixtures', action='store_true', help='Reuse only this script\'s labeled test namespace')
    parser.add_argument('--resume-session', help='Resume an interrupted test batch using its private session.json')
    args = parser.parse_args()
    ns = args.namespace
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    def kube(*argv):
        return subprocess.check_output(['kubectl', *argv], text=True)
    existing = kube('get', 'ns', ns, '--ignore-not-found', '-o', 'json')
    if args.reuse_fixtures:
        assert json.loads(existing)['metadata']['labels'].get('purpose') == 'grouped-repair-acceptance'
    else:
        assert not existing, 'fixture namespace must not exist'
    image = 'xnet.registry.io:8443/observability/python:3-alpine'
    script = ('import os,sys,http.server; '
              'p=os.getenv("APP_CONFIG_PATH"); '
              'print("APP_CONFIG_PATH is required" if not p else "config="+p,flush=True); '
              'sys.exit(1) if not p else None; '
              'http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler,port=8080)')
    items = [{'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {
        'name': ns, 'labels': {'purpose': 'grouped-repair-acceptance'}}}]
    for name in ('env-case', 'readiness-case'):
        container = {'name': 'app', 'image': image, 'command': ['python', '-u', '-c', script],
                     'env': [{'name': 'APP_CONF_PATH' if name == 'env-case' else 'APP_CONFIG_PATH', 'value': '/etc/hosts'}],
                     'readinessProbe': {'httpGet': {'path': '/', 'port': 9090 if name == 'readiness-case' else 8080}, 'periodSeconds': 2},
                     'resources': {'requests': {'cpu': '10m', 'memory': '16Mi'}, 'limits': {'cpu': '100m', 'memory': '64Mi'}}}
        items.append({'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': name, 'namespace': ns},
                      'spec': {'replicas': 1, 'selector': {'matchLabels': {'app': name}},
                               'template': {'metadata': {'labels': {'app': name}},
                                            'spec': {'terminationGracePeriodSeconds': 1, 'containers': [container]}}}})
    items.append({'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'finalizer-case', 'namespace': ns,
                  'finalizers': ['aiops.lab/hold'], 'annotations': {'test-cleanup': 'no external resources or outstanding cleanup'}},
                  'spec': {'terminationGracePeriodSeconds': 1, 'containers': [{'name': 'app', 'image': image,
                      'command': ['python', '-m', 'http.server', '8080']}]}})
    if not args.reuse_fixtures:
        subprocess.run(['kubectl', 'apply', '-f', '-'], input=json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': items}), text=True, check=True)
        kube('delete', 'pod', 'finalizer-case', '-n', ns, '--wait=false')
    client = requests.Session()
    trusted = ('隔离验收基线：env-case 必需环境变量名 APP_CONFIG_PATH，原 APP_CONF_PATH 的值 /etc/hosts 正确且该文件存在；'
               'readiness-case 应用 HTTP 监听 8080，健康请求 / 返回 200；finalizer-case 的 aiops.lab/hold 是测试标记，'
               '无外部资源或未完成清理任务，可以定点移除。仅处理本命名空间三个测试对象。')
    question = f'深入诊断命名空间 {ns} 的异常 Pod，按异常对象并发分组分析，不执行修复。' + trusted
    if args.resume_session:
        saved = json.loads(Path(args.resume_session).read_text())
        client.cookies.set('aiops_query_owner', saved['cookie'])
        final = {'run_id': saved['batch_id'].removeprefix('batch-'), 'repair_record': {'kind': 'diagnosis'}}
    else:
        final = None
        with client.get(args.api+'/ask', params={'q': question, 'format': 'sse', 'session_id': 'grouped-live-'+ns}, stream=True, timeout=(10, 600)) as response:
            response.raise_for_status()
            identity = out/'session.json'
            identity.touch(mode=0o600)
            identity.write_text(json.dumps({'cookie': client.cookies.get('aiops_query_owner')}))
            event_type = None
            with (out/'diagnosis.jsonl').open('w') as log:
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('event: '):
                        event_type = line[7:]
                    if not line.startswith('data: '):
                        continue
                    event = json.loads(line[6:])
                    event.setdefault('type', event_type)
                    log.write(json.dumps(event, ensure_ascii=False)+'\n')
                    if event.get('type') in ('run_start', 'node_start', 'final', 'error'):
                        print(event.get('type'), event.get('run_id'), event.get('node'), flush=True)
                    if event.get('type') == 'final':
                        final = event
    assert final and (final.get('repair_record') or {}).get('kind') == 'diagnosis'
    def request(method, path, **kw):
        response = client.request(method, args.api+path, timeout=20, **kw)
        response.raise_for_status()
        return response.json()
    batch = request('POST', '/repair/batches', json={'diagnosis_run_id': final['run_id'], 'question': '生成各组修复方案。'+trusted})
    assert len(batch['groups']) == 3, batch
    assert request('POST', '/repair/batches', json={'diagnosis_run_id': final['run_id']})['batch_id'] == batch['batch_id']
    print('BATCH', batch['batch_id'], flush=True)
    if args.resume_session:
        for group in batch['groups']:
            if group['status'] in ('interrupted', 'failed', 'cancelled'):
                request('POST', '/repair/jobs/'+group['job_id']+'/feedback', json={
                    'version': group['version'], 'feedback': '继续根据本组诊断生成修复方案。'+trusted})
    # Persist only test-session identity privately for follow-up browser/API tests.
    identity = out/'session.json'
    identity.touch(mode=0o600)
    identity.write_text(json.dumps({'cookie': client.cookies.get('aiops_query_owner'), 'batch_id': batch['batch_id']}))
    deadline = time.monotonic()+480
    revised = False
    approved = set()
    last = None
    while time.monotonic() < deadline:
        batch = request('GET', '/repair/batches/'+batch['batch_id'])
        status = [(g['group_id'], g['status'], g['version']) for g in batch['groups']]
        if status != last:
            print('STATUS', status, flush=True)
            last = status
        jobs = [request('GET', '/repair/jobs/'+g['job_id']) for g in batch['groups']]
        for job in jobs:
            (out/(job['job_id']+'.json')).write_text(json.dumps(job, ensure_ascii=False, indent=2))
        if not revised and all(j['status'] == 'awaiting_approval' for j in jobs):
            chosen = jobs[0]
            old_ids = [g['job_id'] for g in batch['groups']]
            request('POST', '/repair/jobs/'+chosen['job_id']+'/feedback', json={
                'version': chosen['version'], 'feedback': '保持修复对象和已核实变更不变，补充明确的恢复验收条件。'+trusted})
            updated = request('GET', '/repair/batches/'+batch['batch_id'])
            assert [g['job_id'] for g in updated['groups']][1:] == old_ids[1:]
            assert request('GET', '/repair/jobs/'+chosen['job_id'])['status'] == 'superseded'
            revised = True
            continue
        if revised:
            for job in jobs:
                approval = job.get('approval')
                if not approval or approval['approval_id'] in approved:
                    continue
                action = approval['payload']
                command = action['execute_command']
                words = shlex.split(command)
                assert words[0] == 'kubectl' and any(verb in words for verb in ('patch', 'set')), command
                assert ns in words and any(name in command for name in ('env-case', 'readiness-case', 'finalizer-case')), command
                assert not any(token in words for token in (';', '&&', '|', 'delete', '--all')), command
                for field in ('dry_run_command', 'verify_command'):
                    extra = action.get(field)
                    if extra:
                        argv = shlex.split(extra)
                        assert argv[0] == 'kubectl' and any(verb in argv for verb in ('get', 'wait', 'rollout')), extra
                        assert ns in argv and not any(token in argv for token in (';', '&&', '|', 'delete', '--all', 'undo', 'restart')), extra
                response = client.post(args.api+'/remediation/approve', data={
                    'run_id': job['job_id'], 'approval_id': approval['approval_id'], 'approved': 'true'}, timeout=15)
                response.raise_for_status()
                approved.add(approval['approval_id'])
                print('APPROVED', job['group_id'], command, flush=True)
        if all(j['status'] not in ('queued', 'planning', 'planned', 'awaiting_approval', 'executing') for j in jobs):
            assert revised and all(j['status'] == 'needs_followup' for j in jobs), status
            break
        time.sleep(2)
    else:
        raise AssertionError('repair timeout')
    for name in ('env-case', 'readiness-case'):
        print(kube('rollout', 'status', 'deployment/'+name, '-n', ns, '--timeout=90s'), flush=True)
        code = kube('exec', 'deployment/'+name, '-n', ns, '--', 'python', '-c',
                    'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8080/",timeout=5).status)')
        assert code.strip() == '200', (name, code)
    assert not kube('get', 'pod', 'finalizer-case', '-n', ns, '--ignore-not-found')
    print('LIVE_GROUPED_REPAIR_PASSED', flush=True)


if __name__ == '__main__':
    main()
