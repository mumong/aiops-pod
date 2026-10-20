"""Explicit execution requests run on the operate path: rules deny, otherwise run and audit.

Live 3453c7ecdddc40bf: "用 helm delete 卸载 default/cloud-server" went to the repair node,
whose RepairDraft contract (group_id, kubectl-only) rejected every helm command.
"""

import asyncio
import json

from langchain_core.tools import StructuredTool

from app.core.remediation.policy import CommandPolicy
from app.core.workflow.operate_tools import (
    HELM_READ_TOOLS,
    WRITE_TOOLS,
    command_text,
    deny_reason,
    guard_write_tool,
)

POLICY = CommandPolicy.from_config(
    {
        "denied_operations": ["drain", "taint"],
        "denied_flags": ["--all", "-A"],
        "denied_resource_kinds": ["node", "namespace"],
        "denied_executables": ["rm", "mkfs*", "reboot"],
    }
)


def test_kubectl_through_bash_follows_the_repair_rules():
    assert (
        deny_reason("run_bash_command", {"command": "kubectl delete pod/x -n demo"}, POLICY) == ""
    )
    assert deny_reason("run_bash_command", {"command": "kubectl drain node1"}, POLICY).startswith(
        "denied_operations"
    )
    assert "denied_resource_kinds" in deny_reason(
        "run_bash_command", {"command": "kubectl delete ns demo"}, POLICY
    )
    assert "denied_flags" in deny_reason(
        "run_bash_command", {"command": "kubectl delete pods --all -n demo"}, POLICY
    )


def test_blocked_executables_anywhere_in_a_shell_or_run_image_command():
    for args in (
        {"command": "rm /tmp/a"},
        {"command": "kubectl exec pod/x -n demo -- rm /tmp/a"},
        {"command": "sh -c 'ls; /bin/rm -f /tmp/a'"},
        {"command": "kubectl exec pod/x -- mkfs.ext4 /dev/sdb"},
    ):
        assert "denied_executables" in deny_reason("run_bash_command", args, POLICY), args
    assert "rm" in deny_reason(
        "kubectl_run_image",
        {
            "namespace": "demo",
            "pod_name": "p",
            "image": "busybox",
            "command": ["sh", "-c", "rm -rf /data"],
        },
        POLICY,
    )
    assert deny_reason("run_bash_command", {"command": "helm list -A"}, POLICY) == ""
    assert "rm" in deny_reason("run_bash_command", {"command": "ls /tmp;rm /tmp/a"}, POLICY)
    benign = "kubectl exec pod/x -n demo -- sh -c 'ls /tmp/x; cat /tmp/y'"
    assert deny_reason("run_bash_command", {"command": benign}, POLICY) == ""
    assert (
        deny_reason("run_bash_command", {"command": "kubectl exec pod/x -- cat /tmp/a"}, POLICY)
        == ""
    )


def test_helm_mutations_are_write_tools_with_an_auditable_command():
    assert {"helm_install", "helm_uninstall", "helm_upgrade", "helm_rollback"} <= WRITE_TOOLS
    assert "helm_list_releases" in HELM_READ_TOOLS and "helm_status" in HELM_READ_TOOLS
    assert (
        command_text("helm_uninstall", {"release_name": "cloud-server", "namespace": "default"})
        == "helm uninstall cloud-server -n default"
    )
    assert deny_reason("helm_uninstall", {"release_name": "cloud-server"}, POLICY) == ""


def test_guarded_tool_denies_without_running_and_audits_both_outcomes():
    calls, audit = [], []

    def run(command: str) -> str:
        calls.append(command)
        return "ok"

    tool = StructuredTool.from_function(func=run, name="run_bash_command", description="bash")
    guarded = guard_write_tool(
        tool,
        POLICY,
        principal="boss",
        question="删文件",
        audit=lambda kind, **f: audit.append((kind, f)),
    )
    denied = json.loads(guarded.invoke({"command": "kubectl exec pod/x -n demo -- rm /tmp/a"}))
    assert denied["success"] is False and "未执行" in denied["error"] and calls == []
    assert audit[-1][0] == "execution_denied" and audit[-1][1]["principal"] == "boss"
    assert guarded.invoke({"command": "kubectl delete pod/x -n demo"}) == "ok"
    assert calls == ["kubectl delete pod/x -n demo"]
    assert audit[-1][0] == "command_executed" and audit[-1][1]["command"] == calls[0]
    assert asyncio.run(guarded.ainvoke({"command": "kubectl drain node1"})).startswith(
        '{"success": false'
    )
    assert calls == ["kubectl delete pod/x -n demo"]
    assert guarded.name == "run_bash_command"
