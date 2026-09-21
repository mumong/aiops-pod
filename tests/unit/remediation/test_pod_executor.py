import json
from copy import deepcopy
import threading

from app.core.remediation.approval import ApprovalStore
from app.core.remediation.pod_executor import PodRepairExecutor


def fixture():
    target = {"namespace": "demo", "pod": "api-1", "pod_uid": "p1", "group_id": "g1",
              "owner_kind": "Deployment", "owner_name": "api", "owner_uid": "d1"}
    action = {"id": "a1", "group_id": "g1", "description": "调整资源", "risk": "medium",
              "execute_command": "kubectl set resources deployment/api -n demo --limits=memory=256Mi",
              "verify_command": "kubectl get pod/api-1 -n demo -o json"}
    objects = {
        "pod/api-1": {"metadata": {"name": "api-1", "namespace": "demo", "uid": "p1", "generation": 1,
             "ownerReferences": [{"controller": True, "kind": "Deployment", "name": "api", "uid": "d1"}]}},
        "deployment/api": {"metadata": {"name": "api", "namespace": "demo", "uid": "d1", "generation": 1}},
    }
    writes = []
    def runner(argv):
        if argv[1] == "get":
            return json.dumps(objects[argv[2]])
        writes.append(argv)
        return "configured"
    return {"targets": [target], "actions": [action]}, objects, writes, runner


def test_review_exact_commands_owner_and_single_execution():
    draft, _, writes, runner = fixture()
    store = ApprovalStore()
    events = PodRepairExecutor(store, runner).run("r", draft, owner="alice")
    request = next(events)
    assert request["type"] == "remediation_approval_required" and writes == []
    assert request["payload"]["execute_command"] == draft["actions"][0]["execute_command"]
    assert not store.resolve("r", request["approval_id"], True, owner="bob")
    assert store.resolve("r", request["approval_id"], True, owner="alice")
    draft["actions"][0]["execute_command"] = "rm -rf /tmp/a"
    result = list(events)
    assert len(writes) == 1 and writes[0][1] == "set"
    assert result[-1]["status"] == "needs_followup"
    assert not store.resolve("r", request["approval_id"], True, owner="alice")


def test_generation_change_after_approval_stops_write():
    draft, objects, writes, runner = fixture()
    store = ApprovalStore()
    events = PodRepairExecutor(store, runner).run("r", draft, owner="alice")
    request = next(events)
    objects["deployment/api"]["metadata"]["generation"] = 2
    store.resolve("r", request["approval_id"], True, owner="alice")
    assert list(events)[-1]["status"] == "blocked"
    assert writes == []


def test_auto_still_blocks_out_of_scope_and_hidden_writes():
    for field, command in [("execute_command", "kubectl set resources deployment/other -n demo --limits=memory=256Mi"),
                           ("verify_command", "kubectl rollout restart deployment/api -n demo")]:
        draft, _, writes, runner = fixture()
        draft["actions"][0][field] = command
        result = list(PodRepairExecutor(runner=runner).run("r", draft, mode="auto"))
        assert result[-1]["status"] == "blocked" and writes == []


def test_same_owner_conflict_is_blocked_and_lock_released():
    draft, _, writes, runner = fixture()
    store = ApprovalStore()
    executor = PodRepairExecutor(store, runner)
    first = executor.run("r1", draft, owner="alice")
    request = next(first)
    assert list(executor.run("r2", draft, mode="auto"))[-1]["status"] == "blocked"
    store.resolve("r1", request["approval_id"], False, owner="alice")
    assert list(first)[-1]["status"] == "rejected"
    assert list(executor.run("r3", draft, mode="auto"))[-1]["status"] == "needs_followup"
    assert len(writes) == 1


def test_timeout_and_cancel_do_not_write():
    draft, _, writes, runner = fixture()
    store = ApprovalStore()
    result = list(PodRepairExecutor(store, runner).run("r", draft, owner="alice", timeout=0))
    assert result[-1]["status"] == "timeout" and writes == []
    cancel = threading.Event()
    cancel.set()
    result = list(PodRepairExecutor(store, runner).run("r2", draft, mode="auto", cancel=cancel))
    assert result[-1]["status"] == "cancelled" and writes == []


def test_verified_owner_cannot_escape_original_user_scope():
    draft, _, writes, runner = fixture()
    result = list(PodRepairExecutor(runner=runner).run(
        "r", draft, mode="auto", request_contract={"namespaces": ["other"]}))
    assert result[-1]["status"] == "blocked" and writes == []


def test_failed_command_is_visible_with_group_stage_and_no_more_actions():
    draft, _, writes, runner = fixture()
    def fail(argv):
        if argv[1] == 'set':
            writes.append(argv)
            raise RuntimeError('request timed out; outcome unknown')
        return runner(argv)
    events = list(PodRepairExecutor(runner=fail).run('failure', draft, mode='auto'))
    result = next(e for e in events if e['type'] == 'remediation_tool_result')
    assert (result['group_id'], result['action_id'], result['stage'], result['status']) == ('g1', 'a1', 'execute', 'failed')
    assert 'outcome unknown' in result['result_preview']
    assert events[-1]['status'] == 'failed' and len(writes) == 1


def test_cancel_during_approval_is_not_reported_as_timeout():
    draft, _, writes, runner = fixture()
    cancel = threading.Event()
    stream = PodRepairExecutor(ApprovalStore(), runner).run('cancel', draft, owner='alice', cancel=cancel)
    assert next(stream)['type'] == 'remediation_approval_required'
    cancel.set()
    assert list(stream)[-1]['status'] == 'cancelled'
    assert not writes


def test_local_runner_uses_projected_serviceaccount_without_exposing_token(monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace
    from app.core.remediation.pod_executor import run_argv
    monkeypatch.delenv('KUBECONFIG', raising=False)
    monkeypatch.setenv('KUBERNETES_SERVICE_HOST', '10.0.0.1')
    monkeypatch.setenv('KUBERNETES_SERVICE_PORT', '443')
    original = Path.is_file
    monkeypatch.setattr(Path, 'is_file', lambda p: True if str(p).endswith('/serviceaccount/token') else original(p))
    def execute(args, **kwargs):
        config = json.loads(Path(kwargs['env']['KUBECONFIG']).read_text())
        assert config['users'][0]['user'] == {'tokenFile': '/var/run/secrets/kubernetes.io/serviceaccount/token'}
        assert config['clusters'][0]['cluster']['server'] == 'https://10.0.0.1:443'
        assert kwargs['timeout'] == 60
        assert all('--token' not in arg for arg in args)
        return SimpleNamespace(returncode=0, stdout='ok')
    monkeypatch.setattr('app.core.remediation.pod_executor.subprocess.run', execute)
    assert run_argv(['kubectl', 'get', 'pod/demo', '-n', 'demo']) == 'ok'


def test_two_groups_keep_separate_targets_commands_and_approvals():
    draft, objects, writes, _ = fixture()
    second = json.loads(json.dumps(draft).replace('api-1', 'worker-1').replace('deployment/api', 'deployment/worker'))
    second['targets'][0].update(group_id='g2', owner_name='worker', pod_uid='p2', owner_uid='d2')
    second['actions'][0].update(group_id='g2', id='a2')
    objects['pod/worker-1'] = deepcopy(objects['pod/api-1'])
    objects['pod/worker-1']['metadata'].update(name='worker-1', uid='p2', ownerReferences=[
        {'controller': True, 'kind': 'Deployment', 'name': 'worker', 'uid': 'd2'}])
    objects['deployment/worker'] = {'metadata': {'name': 'worker', 'namespace': 'demo', 'uid': 'd2', 'generation': 1}}
    draft['targets'] += second['targets']
    draft['actions'] += second['actions']
    def runner(argv):
        if argv[1] == 'get':
            return json.dumps(objects[argv[2]])
        writes.append(argv)
        return 'configured'
    store = ApprovalStore()
    stream = PodRepairExecutor(store, runner).run('groups', draft, owner='alice')
    seen = []
    for event in stream:
        if event['type'] == 'remediation_approval_required':
            seen.append((event['group_id'], event['payload']['target']['pod']))
            store.resolve('groups', event['approval_id'], True, owner='alice')
    assert seen == [('g1', 'api-1'), ('g2', 'worker-1')]
    assert [args[3] for args in writes] == ['deployment/api', 'deployment/worker']
