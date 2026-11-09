"""Check a repair plan's write commands with ``kubectl --dry-run=server`` before approval.

Run 9062db56: an approved plan ran ``kubectl set env ... --remove=env/X`` (unknown
flag) and others hit "namespace not found" on the wrong cluster; nothing checked a
command before the operator approved it. A server-side dry run sends the change to
the plan's own cluster, where the API server checks it (syntax, object, RBAC of the
identity that would run it, admission and validation) and discards it, so these
mistakes surface while the model can still fix them; nothing is changed. The check is generic:
it reports kubectl's own error, it does not judge what the command should be.
"""

from __future__ import annotations

import re
import shlex
from typing import Callable, List, Optional

Runner = Callable[[List[str]], str]
_UNSUPPORTED = "unknown flag: --dry-run"
# kubectl's own verdict that the server-side object would not change: "patched (no
# change)" (patch, set, label, annotate) and "unchanged" (apply), optionally followed
# by "(server dry run)". Live run 9a22d797: a merge patch deleting an annotation
# the object did not have printed "replicaset.apps/x patched (no change)".
_OBJECT_LINE = re.compile(r"^\S+/\S+ ")
_NO_CHANGE = re.compile(r"(?:\(no change\)| unchanged)(?: \(server dry run\))?\s*$")


def reports_no_change(output) -> bool:
    """True when every object line kubectl printed says the object was left unchanged."""
    lines = [line.strip() for line in str(output or "").splitlines() if line.strip()]
    objects = [line for line in lines if _OBJECT_LINE.match(line)]
    return bool(objects) and all(_NO_CHANGE.search(line) for line in objects)


def dry_run_argv(command: str) -> Optional[List[str]]:
    """The dry-run form of a kubectl write command, or None when it does not apply."""
    from aiops_edge.kubectl_args import classify

    try:
        argv = shlex.split(command or "")
    except ValueError:
        return None  # malformed quoting is already reported by the plan's own validation
    if not argv or argv[0] != "kubectl" or any(t.startswith("--dry-run") for t in argv):
        return None
    mode, _ = classify(argv)
    if mode != "write":
        return None  # reads need no check; exec has no dry run
    cut = argv.index("--") if "--" in argv else len(argv)
    return [*argv[:cut], "--dry-run=server", *argv[cut:]]


def remote_errors(action) -> List[str]:
    """Commands a remote cluster cannot run (e.g. ``rollout status``, ``-w``), with the reason."""
    from aiops_edge.kubectl_args import classify

    errors = []
    for field in ("dry_run_command", "execute_command", "verify_command"):
        command = getattr(action, field, "") or ""
        try:
            argv = shlex.split(command)
        except ValueError:
            continue
        if argv[:1] == ["kubectl"] and classify(argv)[0] is None:
            errors.append(
                f"{getattr(action, 'id', '?')}.{field}: `{command}` → 远端集群不支持：{classify(argv)[1]}"
            )
    return errors


def preflight_errors(actions, run: Runner, remote: bool = False) -> List[str]:
    """kubectl's own error for every write command whose dry run fails.

    On a remote cluster every command must also be runnable there; live run
    bd48672e verified with ``rollout status``, which the tunnel cannot carry.
    """
    errors = []
    for action in actions:
        if remote:
            errors.extend(remote_errors(action))
        command = getattr(action, "execute_command", "") or ""
        argv = dry_run_argv(command)
        if argv is None:
            continue
        try:
            output = run(argv)
        except Exception as exc:  # noqa: BLE001 - the error text is the finding
            text = str(exc).strip()
            if _UNSUPPORTED in text:
                continue  # this subcommand has no dry run; nothing to learn
            errors.append(f"{getattr(action, 'id', '?')}: `{command}` → {text[:400]}")
            continue
        if reports_no_change(output):
            errors.append(
                f"{getattr(action, 'id', '?')}: `{command}` → 服务端预检显示该命令不会改变任何对象"
                f"（kubectl：{str(output).strip()[:200]}）。要改的字段不存在、已是目标值，或写在了不生效的位置"
                "（例如对象自身的 metadata 与 spec.template 的区别）；请读取对象核对字段路径后修正"
            )
    return errors


def runner_for(contract) -> Runner:
    """Dry runs go to the plan's cluster: the edge through the shim, else this Pod's SA."""
    from app.core import multicluster
    from app.core.remediation.pod_executor import run_argv

    remote = multicluster.job_cluster(contract)
    cluster = remote.name if remote is not None else None
    return lambda argv: run_argv(argv, cluster=cluster)


def is_remote(contract) -> bool:
    from app.core import multicluster

    return multicluster.job_cluster(contract) is not None
