"""High-risk commands that may run only after a person approves them (break-glass, minimal).

Boss 2026-10-20: when a repair genuinely needs a blacklisted command (rm inside a Pod,
kubectl drain, deleting a namespace), it should run after explicit human approval.
Minimal design, reusing the repair approval: ``workflow.remediation.approval_required``
lists those commands; the rules answer "allowed, requires approval"; a repair plan may
contain them; the executor always asks for approval for such an action - also in auto
mode; chat execution and the MCP tools still refuse them. Everything else unchanged.
"""

import shlex

import pytest

from app.core.remediation.approval import ApprovalStore
from app.core.remediation.pod_executor import PodRepairExecutor
from app.core.remediation.policy import CommandPolicy, check_command, validate_target_command
from app.core.workflow.operate_tools import deny_reason
from tests.unit.remediation.test_pod_executor import fixture

CONFIG = {
    "denied_operations": ["edit"],
    "denied_flags": ["--all", "-A"],
    "denied_resource_kinds": ["node", "clusterrole"],
    "denied_executables": ["mkfs*", "dd", "reboot"],
    "allowed_exec_commands": [],
    "allowed_operations": [],
    "approval_required": {
        "operations": ["drain"],
        "resource_kinds": ["namespace"],
        "executables": ["rm"],
    },
}
POLICY = CommandPolicy.from_config(CONFIG)
RM = "kubectl exec pod/api-1 -n demo -- rm -f /tmp/app.lock"


@pytest.mark.parametrize(
    "command",
    [
        RM,
        "kubectl exec pod/api-1 -n demo -- sh -c 'rm /tmp/app.lock'",
        "kubectl drain node2 --ignore-daemonsets",
        "kubectl delete namespace scratch",
    ],
)
def test_listed_commands_are_allowed_only_with_approval(command):
    verdict = check_command(command, POLICY)
    assert verdict.allowed and verdict.requires_approval
    assert verdict.rule == "approval_required"
    assert verdict.as_dict()["requires_approval"] is True


@pytest.mark.parametrize(
    "command,rule",
    [
        ("kubectl exec pod/api-1 -n demo -- mkfs.ext4 /dev/sdb", "denied_executables"),
        ("kubectl edit deployment/api -n demo", "denied_operations"),
        ("kubectl patch node/node2 -p '{}'", "denied_resource_kinds"),
        ("kubectl delete pods --all -n demo", "denied_flags"),
    ],
)
def test_absolute_rules_still_deny(command, rule):
    verdict = check_command(command, POLICY)
    assert not verdict.allowed and verdict.rule == rule and not verdict.requires_approval


def test_ordinary_commands_need_no_extra_approval():
    verdict = check_command("kubectl delete pod/api-1 -n demo", POLICY)
    assert verdict.allowed and not verdict.requires_approval


def test_without_the_section_nothing_changes():
    plain = {k: v for k, v in CONFIG.items() if k != "approval_required"}
    assert not CommandPolicy.from_config(plain).approval_executables
    assert not check_command(RM, CommandPolicy.from_config(plain)).requires_approval


def test_plans_may_contain_them():
    argv, operation = validate_target_command(RM, (), POLICY)
    assert operation == "exec" and argv[-1] == "/tmp/app.lock"


def test_chat_execution_still_refuses_them():
    run = "run_bash_command"
    assert deny_reason(run, {"command": RM}, POLICY).startswith("approval_required")
    assert deny_reason(run, {"command": "kubectl drain node2"}, POLICY).startswith(
        "approval_required"
    )
    assert deny_reason(run, {"command": "rm -rf /tmp/x"}, POLICY).startswith("denied_executables")
    assert deny_reason(run, {"command": "kubectl get pods -n demo"}, POLICY) == ""


def test_summary_lists_them_separately():
    view = POLICY.summary()
    assert view["approval_required"] == {
        "kubernetes": ["drain", "namespace"],
        "shell": ["rm"],
    }
    assert "rm" not in view["shell"]


def _rm_draft():
    draft, _, _, _ = fixture()
    draft["actions"][0].update(execute_command=RM, verify_command="")
    return draft


def test_auto_mode_still_waits_for_a_person():
    calls = []
    store = ApprovalStore()
    stream = PodRepairExecutor(store, lambda argv: calls.append(argv) or "ok").run(
        "auto-high-risk", _rm_draft(), owner="alice", mode="auto", policy=POLICY
    )
    event = next(stream)
    assert event["type"] == "remediation_approval_required"
    assert event["high_risk"] and "rm" in event["high_risk"][0]
    assert event["payload"]["high_risk"] == event["high_risk"]
    assert calls == []
    store.resolve("auto-high-risk", event["approval_id"], True, owner="alice")
    events = list(stream)
    assert calls == [shlex.split(RM)]
    start = next(e for e in events if e["type"] == "remediation_tool_start")
    assert start["approval"] == event["approval_id"]  # not "auto"
    assert "未经人工审批" not in events[-1]["reason"] and "经人工批准" in events[-1]["reason"]


def test_rejection_never_runs_it():
    calls = []
    store = ApprovalStore()
    stream = PodRepairExecutor(store, lambda argv: calls.append(argv) or "ok").run(
        "reject-high-risk", _rm_draft(), owner="alice", mode="auto", policy=POLICY
    )
    event = next(stream)
    store.resolve("reject-high-risk", event["approval_id"], False, owner="alice")
    assert list(stream)[-1]["status"] == "rejected"
    assert calls == []


def test_auto_mode_unchanged_for_ordinary_actions():
    draft, _, writes, runner = fixture()
    events = list(
        PodRepairExecutor(ApprovalStore(), runner).run(
            "auto-plain", draft, mode="auto", policy=POLICY
        )
    )
    assert not any(e["type"] == "remediation_approval_required" for e in events)
    assert writes
