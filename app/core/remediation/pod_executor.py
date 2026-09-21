"""Execute a reviewed Pod plan with exact scope, fresh identity and no LLM writes."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time

from app.core.remediation.approval import approval_store
from app.core.remediation.policy import CommandPolicy, validate_target_command

_lock = threading.Lock()
_busy: set[tuple[str, str, str]] = set()
_NAME = re.compile(r"[a-z0-9](?:[-a-z0-9.]*[a-z0-9])?\Z")


def run_argv(args):
    # kubectl does not automatically use client-go's in-cluster config here.
    # Use only this Pod's projected ServiceAccount, never host/admin credentials.
    token = Path('/var/run/secrets/kubernetes.io/serviceaccount/token')
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix='aiops-kube-') as directory:
        if not env.get('KUBECONFIG') and env.get('KUBERNETES_SERVICE_HOST') and token.is_file():
            host = env['KUBERNETES_SERVICE_HOST']
            if ':' in host and not host.startswith('['):
                host = '[' + host + ']'
            config = {'apiVersion': 'v1', 'kind': 'Config',
                'clusters': [{'name': 'in-cluster', 'cluster': {
                    'server': 'https://' + host + ':' + env.get('KUBERNETES_SERVICE_PORT', '443'),
                    'certificate-authority': str(token.parent / 'ca.crt')}}],
                'users': [{'name': 'serviceaccount', 'user': {'tokenFile': str(token)}}],
                'contexts': [{'name': 'repair', 'context': {'cluster': 'in-cluster', 'user': 'serviceaccount'}}],
                'current-context': 'repair'}
            path = Path(directory) / 'config'
            path.write_text(json.dumps(config))
            path.chmod(0o600)
            env['KUBECONFIG'] = str(path)
        result = subprocess.run(args, capture_output=True, text=True, timeout=60, check=False, env=env)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "kubectl failed")[:3000])
    return result.stdout


def verified_objects(target, runner):
    """Walk the actual controlling owner chain; reject invented owner identities."""
    ns, name = target["namespace"], target["pod"]
    if not _NAME.fullmatch(ns) or not _NAME.fullmatch(name):
        raise ValueError("无效 Pod 名称或命名空间")
    kind, expected_uid = "pod", target["pod_uid"]
    found = {}
    for _ in range(5):
        obj = json.loads(runner(["kubectl", "get", f"{kind}/{name}", "-n", ns, "-o", "json", "--request-timeout=15s"]))
        meta = obj["metadata"]
        if not expected_uid or meta.get("uid") != expected_uid or meta.get("name") != name or meta.get("namespace") != ns:
            raise ValueError("Pod/控制器身份已变化，需重新诊断和审批")
        found[(ns, kind, name)] = (meta["uid"], str(meta.get("generation", "")))
        owners = [o for o in meta.get("ownerReferences", []) if o.get("controller") is True]
        if not owners:
            break
        if len(owners) != 1:
            raise ValueError("控制器归属不明确")
        owner = owners[0]
        kind, name, expected_uid = owner["kind"].lower(), owner["name"], owner["uid"]
        if kind not in {"replicaset", "deployment", "statefulset", "daemonset"} or not _NAME.fullmatch(name):
            break
    if target.get("owner_name"):
        owner_key = (ns, target.get("owner_kind", "").lower(), target["owner_name"])
        if owner_key not in found or found[owner_key][0] != target.get("owner_uid"):
            raise ValueError("建议中的控制器未经实际 ownerReferences 证实")
    return found


class PodRepairExecutor:
    def __init__(self, store=approval_store, runner=run_argv):
        self.store, self.runner = store, runner

    def run(self, run_id, draft, *, owner="", mode="review", timeout=600, cancel=None, policy=None,
            request_contract=None):
        draft = deepcopy(draft)
        policy = policy or CommandPolicy()
        finish = lambda status, reason: {"type": "remediation_finished", "run_id": run_id,
                                         "status": status, "reason": reason}
        if not draft or not draft.get("actions"):
            yield finish("skipped", "没有可安全执行的结构化修复动作")
            return
        if mode != "auto" and not owner:
            yield finish("blocked", "人工修复需要会话归属，请从前端会话发起")
            return
        reserved = set()
        pending = None
        try:
            targets = {t["group_id"]: t for t in draft["targets"]}
            if len(targets) != len(draft["targets"]):
                raise ValueError("重复诊断组标识")
            prepared = []
            for action in draft["actions"]:
                target = targets[action["group_id"]]
                contract = request_contract or {}
                if ((contract.get("namespaces") and target["namespace"] not in contract["namespaces"])
                        or (contract.get("pod_names") and target["pod"] not in contract["pod_names"])):
                    raise ValueError("修复目标超出用户请求范围")
                objects = verified_objects(target, self.runner)
                stages = []
                for stage in ("dry_run", "execute", "verify"):
                    command = action.get(stage + "_command")
                    if not command:
                        continue
                    argv, operation = validate_target_command(command, objects, policy)
                    if stage == "dry_run" and "--dry-run=server" not in argv:
                        raise ValueError("预演命令必须显式 --dry-run=server")
                    if stage == "verify" and operation not in {"get", "describe", "logs", "top", "rollout_status"}:
                        raise ValueError("验证命令必须只读")
                    stages.append((stage, command, argv))
                if not any(s[0] == "execute" for s in stages) or not any(s[0] == "verify" for s in stages):
                    raise ValueError("动作必须具备执行与验证命令")
                prepared.append((action, target, objects, stages))
            # Hold all scopes across approval + execution; another request must
            # not approve a conflicting change to the same controller in parallel.
            scopes = {key for _, _, objects, _ in prepared for key in objects}
            with _lock:
                if scopes & _busy:
                    raise ValueError("目标已有待审或执行中的修复，请等待完成")
                _busy.update(scopes)
                reserved = scopes
            for action, target, original, stages in prepared:
                if cancel and cancel.is_set():
                    yield finish("cancelled", "请求已取消，未继续执行")
                    return
                if mode != "auto":
                    request = self.store.create_request(run_id, "action", action["description"],
                        {"target": target, **action}, timeout_seconds=timeout, owner=owner)
                    pending = request.approval_id
                    yield {"type": "remediation_approval_required", "run_id": run_id,
                           "approval_id": pending, "approval_kind": "action", "title": request.title,
                           "payload": request.payload, "expires_at": request.expires_at, "server_time": time.time(),
                           "group_id": action["group_id"]}
                    decision = None
                    while time.time() < request.expires_at and not (cancel and cancel.is_set()):
                        decision = self.store.poll_decision(run_id, pending)
                        if decision is not None:
                            break
                        yield {"type": "heartbeat", "run_id": run_id, "stage": "remediation_approval"}
                        time.sleep(0.2)
                    self.store.close(run_id, pending)
                    pending = None
                    if cancel and cancel.is_set():
                        yield finish("cancelled", "请求已取消，未继续执行；此前已执行动作不会自动回滚")
                        return
                    if decision is None or not decision.approved:
                        yield finish("rejected" if decision else "timeout", "修复未获有效批准，未执行")
                        return
                # Generation detects controller spec changes during review;
                # Pod UID detects recreation. Neither relies on LLM confidence.
                if verified_objects(target, self.runner) != original:
                    raise ValueError("审批期间对象配置已变化，请重新制定方案")
                for stage, command, argv in stages:
                    if cancel and cancel.is_set():
                        yield finish("cancelled", "请求取消；已执行动作不会自动回滚")
                        return
                    validate_target_command(command, original, policy)
                    yield {"type": "remediation_tool_start", "run_id": run_id,
                           "group_id": action["group_id"], "action_id": action["id"],
                           "stage": stage, "command": command, "status": "running"}
                    try:
                        output = self.runner(argv)
                    except Exception as exc:
                        yield {"type": "remediation_tool_result", "run_id": run_id,
                               "group_id": action["group_id"], "action_id": action["id"],
                               "stage": stage, "command": command, "status": "failed",
                               "result_preview": str(exc)[:6000], "result_truncated": len(str(exc)) > 6000}
                        yield finish("failed", "修复命令或验证失败；已尝试的写操作可能生效，请复查状态，未自动回滚")
                        return
                    yield {"type": "remediation_tool_result", "run_id": run_id,
                           "group_id": action["group_id"], "action_id": action["id"],
                           "stage": stage, "command": command, "status": "success",
                           "result_preview": str(output)[:6000], "result_truncated": len(str(output)) > 6000}
            yield finish("needs_followup", "已执行批准的命令并返回验证结果；命令成功不等于 Pod 根因已消除，请复查状态")
        except Exception as exc:
            yield finish("blocked", str(exc))
        finally:
            if pending:
                self.store.close(run_id, pending)
            with _lock:
                _busy.difference_update(reserved)
