"""A plan that can only contain blacklisted commands says so, by rule and command.

Acceptance 2026-10-20 (job e5e020809f044b86): feedback asked for `rm -rf /tmp/*` and
`kubectl drain`; validation rejected every draft and the person saw only "未获得完整有效
的结构化修复方案". The blacklist did its job, invisibly. The validator now tags policy
denials, and a plan that failed on them reports the rule and the command.
"""

import pytest
from pydantic import ValidationError

from app.core.remediation.policy import CommandPolicy, use_policy
from app.core.workflow.nodes.remediation import RepairDraft, policy_block_message

CONFIGURED = {
    "denied_operations": ["drain"],
    "denied_flags": ["--all"],
    "denied_resource_kinds": ["namespace"],
    "denied_executables": ["rm"],
    "allowed_exec_commands": [],
    "allowed_operations": [],
}


@pytest.fixture(autouse=True)
def _policy():
    from app.core.remediation import policy as module

    previous = module._ACTIVE
    use_policy(CommandPolicy.from_config(CONFIGURED))
    yield
    module._ACTIVE = previous


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


def test_validation_names_the_rule_and_the_command():
    with pytest.raises(ValidationError) as err:
        RepairDraft.model_validate(_draft("kubectl exec pod/api-1 -n demo -- rm -rf /tmp/x"))
    text = str(err.value)
    assert "高危规则拦截" in text and "denied_executables" in text and "rm -rf /tmp/x" in text


def test_failure_message_reports_policy_blocks_from_stop_reasons():
    reasons = [
        "结构化结果连续 3 次未通过校验（上限 2）：高危规则拦截（denied_executables）："
        "kubectl exec pod/api-1 -n demo -- rm -rf /tmp/x；停止重试"
    ]
    message = policy_block_message(reasons)
    assert message.startswith("方案中的命令被高危规则拦截")
    assert "denied_executables" in message and "rm -rf /tmp/x" in message
    assert policy_block_message(["达到工具执行步数上限"]) == ""
