#!/usr/bin/env python3
"""Reset only the four remediation fixtures; never executes an Agent repair."""
import argparse
import subprocess
import sys
import time

from manage_cases import ROOT, catalog, clean, command, deploy
from verify_observability import evaluate_status_gate, resolve_workload_pods, run_kubectl_json

CASE_IDS = ('c04', 'c06', 'c09', 'c11')


def selected_cases():
    cases = catalog()
    selected = [cases[key] for key in CASE_IDS]
    for key, case in zip(CASE_IDS, selected):
        if case['namespace'] != 'aiops-case-' + key[1:] or case['variant']:
            raise ValueError('Case namespace does not match the fixed remediation suite')
    return selected


def status(cases):
    for case in cases:
        print('\n' + case['id'] + ' / ' + case['namespace'], flush=True)
        command(['kubectl', '-n', case['namespace'], 'get', 'pods'], timeout=20)


def wait_for_faults(cases, timeout):
    deadline = time.monotonic() + timeout
    while True:
        pending = []
        for case in cases:
            pods = resolve_workload_pods(case)
            matched = False
            for identity, pod in pods:
                events = run_kubectl_json(['-n', case['namespace'], 'get', 'events',
                                          '--field-selector', 'involvedObject.uid=' + identity.uid])
                matched, _ = evaluate_status_gate(pod, events.get('items', []), case['status_gate'])
                if matched:
                    break
            if not matched:
                pending.append(case['id'])
        if not pending:
            print('PASS: c04 / c06 / c09 / c11 预期异常状态均已出现。', flush=True)
            return
        if time.monotonic() >= deadline:
            status(cases)
            raise RuntimeError('异常未按期出现：' + ', '.join(pending))
        print('等待异常成立：' + ', '.join(pending), flush=True)
        time.sleep(min(5, max(0, deadline - time.monotonic())))


def reset(cases, timeout):
    # Validate manifests before deleting the old fixtures.
    for case in cases:
        command(['kubectl', 'kustomize', str(ROOT / case['directory'])], capture=True, timeout=30)
    for case in cases:
        print('清理 ' + case['namespace'], flush=True)
        clean(case)  # Reuses targeted c11 finalizer removal; unknown finalizers are retained.
    for case in cases:
        deploy(case)
    c11 = next(c for c in cases if c['id'] == 'c11')
    ns = c11['namespace']
    command(['kubectl', '-n', ns, 'wait', '--for=condition=Ready', 'pod/workload',
             f'--timeout={timeout}s'], timeout=timeout + 10)
    deadline = time.monotonic() + timeout
    while True:
        logs = command(['kubectl', '-n', ns, 'logs', 'pod/workload', '--tail=30'], capture=True, timeout=20)
        if '"event":"http_request"' in logs:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('c11 未产生业务请求，尚未触发删除，请检查 traffic-driver')
        time.sleep(2)
    command(['kubectl', '-n', ns, 'delete', 'pod/workload', '--wait=false'], timeout=20)
    wait_for_faults(cases, timeout)
    status(cases)


def main(argv=None):
    parser = argparse.ArgumentParser(description='专属修复 Case：c04、c06、c09、c11。reset 会删除这四个命名空间内的全部资源并重新部署。')
    parser.add_argument('action', choices=('reset', 'clean', 'status'))
    parser.add_argument('--timeout', type=int, default=180, help='就绪、流量和异常检查各阶段的超时秒数；默认 180')
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error('--timeout 必须大于 0')
    cases = selected_cases()
    context = command(['kubectl', 'config', 'current-context'], capture=True, timeout=20).strip()
    print('集群：' + context + '\n范围：' + ', '.join(c['namespace'] for c in cases), flush=True)
    if args.action == 'reset':
        reset(cases, args.timeout)
    elif args.action == 'clean':
        for case in cases:
            clean(case)
    else:
        status(cases)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('失败：' + str(exc) + '；已完成的操作不会自动回滚，可排查后重新运行 reset。', file=sys.stderr)
        sys.exit(1)
