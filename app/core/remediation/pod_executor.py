"""Execute agent-selected Kubernetes commands with approval and real results."""

import json
import os
import subprocess
import tempfile
import threading
import time
from copy import deepcopy
from pathlib import Path

from aiops_edge.jobs_client import RemoteResultUnknown
from app.core.remediation.approval import approval_store
from app.core.remediation.audit import audit_event
from app.core.remediation.execution_guard import RepairCommandDenied, check_repair_execution
from app.core.remediation.policy import active_policy, check_command, validate_target_command
from app.core.remediation.recovery import RecoveryConfig, RecoveryWatch
from app.core.workflow.group_runner import group_display_name

_lock = threading.Lock()
_command_lock = threading.Lock()
COMMAND_TIMEOUT_SECONDS = int(os.getenv("AIOPS_REPAIR_COMMAND_TIMEOUT", "60"))
_busy: set[tuple[str, str, str]] = set()


def _run_remote(args, env):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"命令执行超时（{COMMAND_TIMEOUT_SECONDS} 秒），结果未知：命令可能已部分生效，请复查资源状态"
        ) from exc
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "kubectl failed")[:3000])
    return result.stdout


def run_argv(args, cluster=None):
    # A remote cluster (multi-cluster deployments) is reached through the kubectl
    # shim and the edge runner; no credentials of that cluster exist here.
    from app.core import multicluster

    remote_env = multicluster.kubectl_env(cluster)
    if remote_env is not None:
        return _run_remote(args, remote_env)
    # kubectl does not automatically use client-go's in-cluster config here.
    # Use only this Pod's projected ServiceAccount, never host/admin credentials.
    token = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="aiops-kube-") as directory:
        if not env.get("KUBECONFIG") and env.get("KUBERNETES_SERVICE_HOST") and token.is_file():
            host = env["KUBERNETES_SERVICE_HOST"]
            if ":" in host and not host.startswith("["):
                host = "[" + host + "]"
            config = {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {
                        "name": "in-cluster",
                        "cluster": {
                            "server": "https://"
                            + host
                            + ":"
                            + env.get("KUBERNETES_SERVICE_PORT", "443"),
                            "certificate-authority": str(token.parent / "ca.crt"),
                        },
                    }
                ],
                "users": [{"name": "serviceaccount", "user": {"tokenFile": str(token)}}],
                "contexts": [
                    {
                        "name": "repair",
                        "context": {"cluster": "in-cluster", "user": "serviceaccount"},
                    }
                ],
                "current-context": "repair",
            }
            path = Path(directory) / "config"
            path.write_text(json.dumps(config))
            path.chmod(0o600)
            env["KUBECONFIG"] = str(path)
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"命令执行超时（{COMMAND_TIMEOUT_SECONDS} 秒），结果未知：命令可能已部分生效，请复查资源状态"
            ) from exc
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "kubectl failed")[:3000])
    return result.stdout


REMOTE_WAIT_SECONDS = int(os.getenv("AIOPS_REMOTE_WAIT_SECONDS", "600"))


class PodRepairExecutor:
    def __init__(self, store=approval_store, runner=run_argv, remote_jobs=None):
        self.store, self.runner = store, runner
        # Multi-cluster: execute stages on an edge cluster run as edge runner jobs.
        self.remote_jobs = remote_jobs

    def run(
        self,
        run_id,
        draft,
        *,
        owner="",
        mode="review",
        timeout=600,
        cancel=None,
        policy=None,
        request_contract=None,
        record_store=None,
        recovery: RecoveryConfig | None = None,
        max_duration=0,
        watch_factory=None,
    ):
        """``recovery`` enables the status-only recovery watch after the commands;
        ``max_duration`` (seconds, 0 = off) bounds the whole execution so a stuck
        approval or a long action never leaves the job open-ended."""
        draft = deepcopy(draft)
        policy = policy or active_policy()
        started_at = time.time()
        max_duration = int(max_duration or 0)
        from app.core import multicluster

        remote = multicluster.job_cluster(request_contract)
        cluster_label = (
            multicluster.labels([remote.name])[0]
            if remote
            else multicluster.job_label(request_contract)
        )
        if remote is not None:
            # Reads (dry run, verify, recovery) reach the edge through the kubectl shim.
            read = lambda argv: self.runner(argv, cluster=remote.name)  # noqa: E731
            jobs = self.remote_jobs
            if jobs is None:
                from aiops_edge.jobs_client import RemoteJobs

                jobs = RemoteJobs.from_config()
        else:
            read, jobs = self.runner, None

        def finish(status, reason, error_code=None, **extra):
            event = {
                "type": "remediation_finished",
                "run_id": run_id,
                "status": status,
                "reason": reason,
                "elapsed_seconds": int(time.time() - started_at),
                **extra,
            }
            if error_code:
                event["error_code"] = error_code
            if record_store:
                record_store.transition(run_id, owner, status, event)
            return event

        if draft and draft.get("planning_error"):
            yield finish("failed", draft["planning_error"]["message"])
            return
        scope_error = multicluster.job_scope_error(request_contract)
        if scope_error and draft and draft.get("actions"):
            yield finish("blocked", scope_error, error_code="cluster_scope_ambiguous")
            return
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
                if (
                    contract.get("namespaces")
                    and target["namespace"] not in contract["namespaces"]
                ) or (contract.get("pod_names") and target["pod"] not in contract["pod_names"]):
                    raise ValueError("修复目标超出用户请求范围")
                # Group locks avoid simultaneous approved plans. They do not
                # prescribe evidence collection or infer allowed resource types.
                objects = {(target["namespace"], "pod", target["pod"])}
                stages = []
                for stage in ("dry_run", "execute", "verify"):
                    command = action.get(stage + "_command")
                    if not command:
                        continue
                    try:
                        # One rule engine for verbs, flags, kinds and in-container
                        # executables; every refusal names its rule.
                        argv, operation = validate_target_command(command, objects, policy)
                        check_repair_execution(argv, policy)
                    except RepairCommandDenied as exc:
                        rule = getattr(exc, "rule", "") or "policy"
                        audit_event(
                            "command_denied",
                            run_id=run_id,
                            group_id=action["group_id"],
                            action_id=action["id"],
                            stage=stage,
                            rule=rule,
                            command=command,
                            reason=str(exc),
                        )
                        yield {
                            "type": "remediation_tool_result",
                            "run_id": run_id,
                            "group_id": action["group_id"],
                            "action_id": action["id"],
                            "stage": stage,
                            "command": command,
                            "status": "failed",
                            "error_code": "repair_command_denied",
                            "rule": rule,
                            "execution_skipped": True,
                            "result_preview": str(exc),
                            "result_truncated": False,
                        }
                        yield finish(
                            "blocked",
                            f"命中高危命令规则 {rule}：{exc}；本计划尚未执行任何命令，请调整方案后重新提交",
                            "repair_command_denied",
                        )
                        return
                    stages.append((stage, command, argv))
                if not any(s[0] == "execute" for s in stages):
                    raise ValueError("动作必须具备执行命令")
                prepared.append((action, target, objects, stages))
            # Hold declared Pod scopes across approval + execution. This avoids
            # duplicate plans for that Pod, not all cross-resource conflicts.
            scopes = {key for _, _, objects, _ in prepared for key in objects}
            with _lock:
                if scopes & _busy:
                    raise ValueError("目标已有待审或执行中的修复，请等待完成")
                _busy.update(scopes)
                reserved = scopes
            # Baseline for the recovery judgement: the target's state before any command.
            watch = None
            before = {}
            watched = []
            if recovery is not None:
                watch = (watch_factory or RecoveryWatch)(read, recovery)
                for _, target, _, _ in prepared:
                    if target["group_id"] in before:
                        continue
                    watched.append(target)
                    try:
                        before[target["group_id"]] = watch.observe(target)
                    except Exception as exc:
                        before[target["group_id"]] = {"exists": None, "error": str(exc)[:200]}
            total_actions, done_actions = len(prepared), 0
            approved_any = False
            verify_failures = []
            for action, target, original, stages in prepared:
                approval_marker = "auto"
                # approval_required commands always wait for a person, also in auto mode.
                high_risk = [
                    f"{command}：{verdict.reason}"
                    for _, command, _ in stages
                    for verdict in [check_command(command, policy)]
                    if verdict.requires_approval
                ]
                if max_duration and time.time() - started_at > max_duration:
                    yield finish(
                        "timeout",
                        f"整体执行时限 {max_duration} 秒已到：已完成 {done_actions}/{total_actions} 个动作，"
                        "未开始后续动作；已执行动作不会自动回滚",
                        "execution_deadline",
                    )
                    return
                if record_store and not record_store.current(run_id, owner):
                    yield finish("superseded", "方案已被修改请求替代，旧审批不可继续执行")
                    return
                if cancel and cancel.is_set():
                    yield finish("cancelled", "请求已取消，未继续执行")
                    return
                if mode != "auto" or high_risk:
                    if record_store and not record_store.transition(
                        run_id, owner, "awaiting_approval"
                    ):
                        yield finish("superseded", "方案已被修改请求替代")
                        return
                    request = self.store.create_request(
                        run_id,
                        "action",
                        action["description"],
                        {
                            "target": target,
                            **action,
                            "high_risk": high_risk,
                            **({"cluster": cluster_label} if cluster_label else {}),
                        },
                        timeout_seconds=timeout,
                        owner=owner,
                    )
                    pending = request.approval_id
                    yield {
                        "type": "remediation_approval_required",
                        "run_id": run_id,
                        "approval_id": pending,
                        "approval_kind": "action",
                        "title": request.title,
                        "payload": request.payload,
                        "expires_at": request.expires_at,
                        "server_time": time.time(),
                        "group_id": action["group_id"],
                        "high_risk": high_risk,
                        **({"cluster": cluster_label} if cluster_label else {}),
                    }
                    decision = None
                    while time.time() < request.expires_at and not (cancel and cancel.is_set()):
                        if record_store and not record_store.current(run_id, owner):
                            yield finish("superseded", "方案已被修改请求替代，旧审批已失效")
                            return
                        decision = self.store.poll_decision(run_id, pending)
                        if decision is not None:
                            break
                        yield {
                            "type": "heartbeat",
                            "run_id": run_id,
                            "stage": "remediation_approval",
                        }
                        time.sleep(0.2)
                    self.store.close(run_id, pending)
                    pending = None
                    if cancel and cancel.is_set():
                        yield finish(
                            "cancelled", "请求已取消，未继续执行；此前已执行动作不会自动回滚"
                        )
                        return
                    if decision is None or not decision.approved:
                        yield finish(
                            "rejected" if decision else "timeout",
                            "用户拒绝了该动作，未执行"
                            if decision
                            else f"审批超时（{int(timeout)} 秒内未批准），未执行",
                        )
                        return
                    approval_marker = request.approval_id
                if remote is not None:
                    # Approved (or auto) but the edge must be reachable before anything runs.
                    waited_from = time.time()
                    while not jobs.reachable(remote):
                        if time.time() - waited_from > REMOTE_WAIT_SECONDS or (
                            cancel and cancel.is_set()
                        ):
                            yield finish(
                                "blocked",
                                f"集群 {cluster_label} 在 {REMOTE_WAIT_SECONDS} 秒内一直不可达，本动作未执行",
                                "cluster_unreachable",
                            )
                            return
                        yield {
                            "type": "remediation_status",
                            "run_id": run_id,
                            "group_id": action["group_id"],
                            "cluster": cluster_label,
                            "message": f"集群 {cluster_label} 当前不可达，恢复连接后再执行（未执行任何命令）",
                        }
                        time.sleep(5)
                for stage, command, argv in stages:
                    if record_store and not record_store.transition(run_id, owner, "executing"):
                        yield finish("superseded", "方案已被修改请求替代，未执行旧命令")
                        return
                    if cancel and cancel.is_set():
                        yield finish("cancelled", "请求取消；已执行动作不会自动回滚")
                        return
                    validate_target_command(command, original, policy)
                    check_repair_execution(argv, policy)
                    yield {
                        "type": "remediation_tool_start",
                        "run_id": run_id,
                        "group_id": action["group_id"],
                        "action_id": action["id"],
                        "stage": stage,
                        "command": command,
                        "status": "running",
                        # "auto" = executed without a human decision (mode=auto);
                        # otherwise the approval id that authorised this exact command.
                        "approval": approval_marker,
                        "mode": mode,
                        **({"cluster": cluster_label} if cluster_label else {}),
                    }
                    try:
                        with _command_lock:
                            if cancel and cancel.is_set():
                                yield finish("cancelled", "请求已取消，未执行排队命令")
                                return
                            if remote is not None and stage == "execute":
                                output = jobs.run(
                                    remote,
                                    argv,
                                    key=f"{run_id}:{action['id']}:{stage}",
                                    approval_id=""
                                    if approval_marker == "auto"
                                    else approval_marker,
                                    timeout_s=COMMAND_TIMEOUT_SECONDS,
                                    deadline_s=max(COMMAND_TIMEOUT_SECONDS * 3, 300),
                                )
                            else:
                                output = read(argv)
                    except RemoteResultUnknown as exc:
                        audit_event(
                            "command_executed",
                            run_id=run_id,
                            action_id=action["id"],
                            stage=stage,
                            command=command,
                            status="unknown",
                            approval=approval_marker,
                            mode=mode,
                            cluster=cluster_label,
                            error=str(exc)[:300],
                        )
                        if record_store:
                            record_store.transition(
                                run_id,
                                owner,
                                "failed",
                                {
                                    "action_id": action["id"],
                                    "stage": stage,
                                    "command": command,
                                    "status": "unknown",
                                    "result": str(exc)[:6000],
                                },
                            )
                        yield {
                            "type": "remediation_tool_result",
                            "run_id": run_id,
                            "group_id": action["group_id"],
                            "action_id": action["id"],
                            "stage": stage,
                            "command": command,
                            "status": "unknown",
                            "result_preview": str(exc)[:6000],
                            "result_truncated": False,
                        }
                        yield finish("failed", f"{exc}；需人工确认", "remote_result_unknown")
                        return
                    except Exception as exc:
                        audit_event(
                            "command_executed",
                            run_id=run_id,
                            action_id=action["id"],
                            stage=stage,
                            command=command,
                            status="failed",
                            approval=approval_marker,
                            mode=mode,
                            error=str(exc)[:300],
                        )
                        if stage == "verify" and watch is not None:
                            # A model-written verify command is a heuristic (live: a bare
                            # `kubectl get` on a Pod whose deletion was the goal returned
                            # NotFound). The status-only recovery watch is the ground truth;
                            # record the failure, keep it visible, and let the watch decide.
                            verify_failures.append(
                                {
                                    "action_id": action["id"],
                                    "command": command,
                                    "error": str(exc)[:600],
                                }
                            )
                            if record_store:
                                record_store.transition(
                                    run_id,
                                    owner,
                                    "executing",
                                    {
                                        "action_id": action["id"],
                                        "stage": stage,
                                        "command": command,
                                        "status": "failed",
                                        "result": str(exc)[:6000],
                                    },
                                )
                            yield {
                                "type": "remediation_tool_result",
                                "run_id": run_id,
                                "group_id": action["group_id"],
                                "action_id": action["id"],
                                "stage": stage,
                                "command": command,
                                "status": "failed",
                                "result_preview": str(exc)[:6000],
                                "result_truncated": len(str(exc)) > 6000,
                                "verify_deferred_to_recovery": True,
                            }
                            continue
                        if record_store:
                            record_store.transition(
                                run_id,
                                owner,
                                "failed",
                                {
                                    "action_id": action["id"],
                                    "stage": stage,
                                    "command": command,
                                    "status": "failed",
                                    "result": str(exc)[:6000],
                                },
                            )
                        yield {
                            "type": "remediation_tool_result",
                            "run_id": run_id,
                            "group_id": action["group_id"],
                            "action_id": action["id"],
                            "stage": stage,
                            "command": command,
                            "status": "failed",
                            "result_preview": str(exc)[:6000],
                            "result_truncated": len(str(exc)) > 6000,
                        }
                        yield finish(
                            "failed",
                            "修复命令或验证失败；已尝试的写操作可能生效，请复查状态，未自动回滚",
                        )
                        return
                    audit_event(
                        "command_executed",
                        run_id=run_id,
                        action_id=action["id"],
                        stage=stage,
                        command=command,
                        status="success",
                        approval=approval_marker,
                        mode=mode,
                        cluster=cluster_label,
                    )
                    if record_store:
                        record_store.transition(
                            run_id,
                            owner,
                            "executing",
                            {
                                "action_id": action["id"],
                                "stage": stage,
                                "command": command,
                                "status": "success",
                                "result": str(output)[:6000],
                            },
                        )
                    yield {
                        "type": "remediation_tool_result",
                        "run_id": run_id,
                        "group_id": action["group_id"],
                        "action_id": action["id"],
                        "stage": stage,
                        "command": command,
                        "status": "success",
                        "result_preview": str(output)[:6000],
                        "result_truncated": len(str(output)) > 6000,
                    }
                done_actions += 1
                if approval_marker != "auto":
                    approved_any = True
            executed_note = (
                "已按自动执行模式执行，其中高危命令经人工批准"
                if mode == "auto" and approved_any
                else "已按自动执行模式执行全部命令（未经人工审批）"
                if mode == "auto"
                else "已执行批准的命令"
            )
            if watch is None:
                yield finish(
                    "needs_followup",
                    executed_note
                    + "并返回实际结果；命令成功不等于 Pod 根因已消除，请按证据判断恢复状态",
                )
                return
            # Recovery watch: read-only observation until recovered or timed out.
            if record_store:
                record_store.transition(run_id, owner, "verifying")
            progress = watch.run(watched, before)
            summary = None
            while True:
                try:
                    event = next(progress)
                except StopIteration as stop:
                    summary = stop.value
                    break
                if cancel and cancel.is_set():
                    progress.close()
                    yield finish(
                        "cancelled", "恢复观察被取消；命令已执行，恢复状态未确认", recovery=None
                    )
                    return
                yield {**event, "run_id": run_id}
            status = summary["status"]
            details = "；".join(
                f"{group_display_name(item['group_id'])}：{item['reason']}"
                for item in summary.get("targets", [])
            )
            if verify_failures:
                summary["verify_failures"] = verify_failures
                details += "；方案自带的验证命令未通过（见执行事件），以恢复观察为准"
            reason = {
                "recovered": executed_note + f"，目标已恢复（{details}）",
                "not_recovered": executed_note
                + f"，但在 {summary['timeout_seconds']} 秒内未观察到恢复（{details}）；请复查，未自动回滚",
                "needs_followup": executed_note + f"，但无法确认恢复状态（{details}）",
            }[status]
            yield finish(status, reason, recovery=summary)
        except Exception as exc:
            yield finish("blocked", str(exc))
        finally:
            if pending:
                self.store.close(run_id, pending)
            with _lock:
                _busy.difference_update(reserved)
