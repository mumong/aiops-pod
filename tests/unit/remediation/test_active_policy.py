"""Planning, ownership checks and execution apply the configured rules, not code defaults.

Live 2026-10-20: the policy panel showed the configured (narrowed) lists, execution used
them, but RepairDraft validation called check_command without a policy and fell back to
the stricter built-in defaults - 'kubectl delete pod' passed execution rules yet was
rejected while planning. One active policy, set from config at startup, removes the gap.
"""

import pytest

from app.core.remediation import policy as policy_module
from app.core.remediation.policy import CommandPolicy, active_policy, check_command, use_policy
from app.core.workflow.nodes.remediation import RepairDraft

CONFIGURED = {
    "denied_operations": ["drain", "edit"],
    "denied_flags": ["--all", "-A"],
    "denied_resource_kinds": ["namespace", "node"],
    "denied_executables": ["rm"],
    "allowed_exec_commands": [],
    "allowed_operations": [],
}


@pytest.fixture(autouse=True)
def _reset():
    previous = policy_module._ACTIVE
    yield
    policy_module._ACTIVE = previous


def _draft(command):
    return {
        "intent": "repair",
        "scope": "ns",
        "status": "answered",
        "answer": "x",
        "targets": [{"namespace": "demo", "pod": "api-1", "group_id": "g1"}],
        "actions": [
            {
                "id": "a1",
                "group_id": "g1",
                "description": "d",
                "risk": "r",
                "execute_command": command,
                "rollback_advice": "b",
            }
        ],
    }


def test_without_configuration_the_built_in_defaults_apply():
    policy_module._ACTIVE = None
    assert active_policy() == CommandPolicy()
    assert not check_command("kubectl delete pod/api-1 -n demo").allowed


def test_configured_policy_is_what_unparameterised_checks_use():
    use_policy(CommandPolicy.from_config(CONFIGURED))
    assert check_command("kubectl delete pod/api-1 -n demo").allowed
    assert check_command("kubectl drain node1").rule == "denied_operations"
    assert (
        check_command("kubectl exec pod/api-1 -n demo -- rm /tmp/a").rule == "denied_executables"
    )


def test_plan_validation_follows_the_configured_policy():
    use_policy(CommandPolicy.from_config(CONFIGURED))
    RepairDraft.model_validate(_draft("kubectl delete pod/api-1 -n demo"))  # allowed by config
    with pytest.raises(ValueError):
        RepairDraft.model_validate(_draft("kubectl exec pod/api-1 -n demo -- rm /tmp/a"))


def test_display_groups_rules_as_kubernetes_and_shell():
    view = CommandPolicy.from_config(CONFIGURED).summary()
    assert view["kubernetes"] == {
        "commands": ["drain", "edit"],
        "resources": ["namespace", "node"],
        "batch": ["--all", "-A", "-l/--selector/--field-selector（写操作）"],
    }
    assert view["shell"] == ["rm"]
