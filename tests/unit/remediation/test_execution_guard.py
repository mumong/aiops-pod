import shlex
from dataclasses import replace

import pytest

from app.core.remediation.execution_guard import RepairCommandDenied, check_repair_execution
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.policy import CommandPolicy
from tests.unit.remediation.test_pod_executor import fixture


@pytest.mark.parametrize(
    "inner",
    [
        "rm -rf /tmp/test",
        "/bin/rm /tmp/test",
        "/usr/bin/rm /tmp/test",
        "busybox rm /tmp/test",
        "env rm /tmp/test",
        "command rm /tmp/test",
        "sh -c 'echo before; rm /tmp/test'",
        "bash -lc 'cat /tmp/a && /bin/rm /tmp/a'",
        "sh -c 'echo ok | rm /tmp/a'",
        "sh -c 'echo ok\nrm /tmp/a'",
        """sh -c '"r""m" /tmp/a' """,
        "sh -c '$COMMAND /tmp/a'",
        "sh -c '$(echo rm) /tmp/a'",
        "sh -c 'echo hi > /tmp/a'",
        "sh /tmp/script.sh",
        "sh -c 'echo $(date)'",
    ],
)
def test_denies_literal_destructive_or_uninspectable_execution(inner):
    with pytest.raises(RepairCommandDenied):
        check_repair_execution(
            shlex.split("kubectl exec pod/test -n demo -- " + inner), CommandPolicy()
        )


@pytest.mark.parametrize(
    "command",
    [
        "kubectl apply -n demo -f /tmp/manifest.yaml",
        """kubectl patch deployment/demo -n demo --type=merge -p '{"spec":{"replicas":2}}' """,
        "kubectl create configmap rm -n demo --from-literal=word=rm",
        "kubectl exec pod/test -n demo -- echo rm",
        "kubectl exec pod/test -n demo -- cat /tmp/rm.txt",
        "kubectl exec pod/test -n demo -- sh -c 'echo rm; cat /tmp/status'",
        "kubectl run test -n demo --image=busybox --rm --attach -- echo ok",
        "kubectl -n demo rollout restart deployment/test",
        "kubectl get pod/test -n demo",
        "kubectl exec pod/test -n demo -- curl http://service/health",
        "kubectl exec pod/test -n demo -- python3 -c 'print(1)'",
        "kubectl exec pod/test -n demo -- unlink /tmp/a",
        "kubectl exec pod/test -n demo -- mkfs.ext4 /dev/test",
    ],
)
def test_normal_repairs_and_data_are_not_substring_blocked(command):
    check_repair_execution(shlex.split(command), CommandPolicy())


def test_config_can_extend_allowlist_and_deny_takes_precedence():
    argv = shlex.split("kubectl exec pod/test -n demo -- curl http://service")
    policy = replace(CommandPolicy(), allowed_exec_commands=frozenset({"curl", "rm"}))
    check_repair_execution(argv, policy)
    with pytest.raises(RepairCommandDenied):
        check_repair_execution(shlex.split("kubectl exec pod/test -- rm /tmp/a"), policy)


@pytest.mark.parametrize("value", ["rm", None, [False], [""], {"rm": True}])
def test_invalid_configuration_cannot_silently_disable_guard(value):
    with pytest.raises(ValueError):
        CommandPolicy.from_config({"denied_executables": value})


def test_configuration_defaults_and_explicit_override():
    assert CommandPolicy.from_config({}).denied_executables == frozenset({"rm"})
    assert not CommandPolicy.from_config({}).allowed_exec_commands
    configured = CommandPolicy.from_config(
        {"denied_executables": [], "allowed_exec_commands": ["rm"]}
    )
    check_repair_execution(shlex.split("kubectl exec pod/test -- rm /tmp/a"), configured)


def test_optional_allowlist_still_supported():
    policy = CommandPolicy.from_config({"allowed_exec_commands": ["cat"]})
    with pytest.raises(RepairCommandDenied):
        check_repair_execution(shlex.split("kubectl exec pod/test -- curl http://service"), policy)


@pytest.mark.parametrize("stage", ["dry_run", "execute", "verify"])
@pytest.mark.parametrize("mode", ["auto", "review"])
def test_all_stages_are_preflighted_before_any_approval_or_execution(stage, mode):
    draft, _, _, _ = fixture()
    draft["actions"][0][stage + "_command"] = "kubectl exec pod/api-1 -n demo -- rm /tmp/a"
    calls = []
    events = list(
        PodRepairExecutor(runner=lambda args: calls.append(args)).run(
            "guard", draft, owner="alice", mode=mode
        )
    )
    assert calls == []
    assert not any(
        e["type"] in {"remediation_approval_required", "remediation_tool_start"} for e in events
    )
    assert events[-1]["status"] == "blocked"
    assert events[-2]["error_code"] == "repair_command_denied"
    assert events[-2]["execution_skipped"] is True
    assert events[-2]["stage"] == stage


def test_bad_later_action_does_not_partially_execute_plan():
    draft, _, _, _ = fixture()
    draft["actions"].append(
        {
            **draft["actions"][0],
            "id": "a2",
            "execute_command": "kubectl exec pod/api-1 -n demo -- sh -c 'rm /tmp/a'",
        }
    )
    calls = []
    events = list(
        PodRepairExecutor(runner=lambda args: calls.append(args)).run("guard", draft, mode="auto")
    )
    assert calls == [] and events[-1]["status"] == "blocked"


def test_guard_rechecks_immediately_before_runner(monkeypatch):
    import app.core.remediation.pod_executor as module

    draft, _, _, _ = fixture()
    calls, checks = [], []

    def guard(args, policy):
        checks.append(list(args))

    monkeypatch.setattr(module, "check_repair_execution", guard)
    list(
        PodRepairExecutor(runner=lambda args: calls.append(list(args)) or "ok").run(
            "guard", draft, mode="auto"
        )
    )
    assert len(checks) == 4 and len(calls) == 2
    assert checks[2:] == calls
