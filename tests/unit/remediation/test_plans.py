import json

import pytest

from app.core.remediation.plans import extract_remediation_plan


def test_extracts_remediation_plan_from_json_fence():
    text = """
## 🛠️ 修复计划

```json
{
  "remediation_available": true,
  "fix_type": "create_missing_configmap",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["kubectl describe 显示 configmap missing"],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_apply",
      "description": "创建缺失 ConfigMap",
      "risk": "medium",
      "dry_run_command": "kubectl apply --dry-run=server -f /tmp/cm.yaml",
      "execute_command": "kubectl apply -f /tmp/cm.yaml",
      "verify_command": "kubectl get configmap missing -n aiops-e2e"
    }
  ]
}
```
"""

    plan = extract_remediation_plan(text)

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.fix_type == "create_missing_configmap"
    assert plan.actions[0].id == "a1"
    assert plan.actions[0].dry_run_command.startswith("kubectl apply")


def test_canonical_fact_ledger_contract_precedes_ordinary_remediation_json():
    ordinary_plan = {
        "remediation_available": True,
        "fix_type": "delete_pod",
        "actions": [
            {
                "id": "delete-api",
                "type": "kubectl_delete",
                "execute_command": "kubectl delete pod api -n demo",
            }
        ],
    }
    canonical_plan = {
        "remediation_contract": "fact-ledger-diagnostic-only-v1",
        "remediation_available": False,
        "fix_type": "manual_only",
        "requires_human_approval": True,
        "issue_groups": [],
        "actions": [],
    }
    text = "\n\n".join(
        [
            "```json\n"
            + json.dumps(ordinary_plan, ensure_ascii=False)
            + "\n```",
            "```json\n"
            + json.dumps(canonical_plan, ensure_ascii=False)
            + "\n```",
        ]
    )

    plan = extract_remediation_plan(text)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.actions == []


@pytest.mark.parametrize("separator", ["\n", "\t"])
def test_rejects_decoded_control_whitespace_in_kubectl_commands(separator):
    text = "```json\n" + json.dumps(
        {
            "remediation_available": True,
            "fix_type": "delete_pod",
            "actions": [
                {
                    "id": "delete-api",
                    "type": "kubectl_delete",
                    "execute_command": (
                        f"kubectl{separator}delete pod api -n demo"
                    ),
                }
            ],
        },
        ensure_ascii=False,
    ) + "\n```"

    with pytest.raises(ValueError, match="unsafe remediation command"):
        extract_remediation_plan(text)


def test_legacy_multiple_plans_keep_first_valid_plan():
    first_plan = {
        "remediation_available": True,
        "fix_type": "delete_pod",
        "actions": [
            {
                "id": "delete-api",
                "type": "kubectl_delete",
                "execute_command": "kubectl delete pod api -n demo",
            }
        ],
    }
    second_plan = {
        "remediation_available": False,
        "fix_type": "manual_only",
        "actions": [],
    }
    text = "\n\n".join(
        [
            "```json\n"
            + json.dumps(first_plan, ensure_ascii=False)
            + "\n```",
            "```json\n"
            + json.dumps(second_plan, ensure_ascii=False)
            + "\n```",
        ]
    )

    plan = extract_remediation_plan(text)

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.fix_type == "delete_pod"


def test_extracts_issue_groups_and_action_group_metadata():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_resources",
  "risk_level": "medium",
  "requires_human_approval": true,
  "issue_groups": [
    {
      "group_id": "g1",
      "problem_type": "OOMKilled",
      "target": "aiops-e2e/deployment/memhog",
      "auto_fixable": false,
      "strategy": "应用持续分配内存，需要人工改代码"
    },
    {
      "group_id": "g2",
      "problem_type": "ImagePullFailed",
      "target": "default/statefulset/test-redis",
      "auto_fixable": false,
      "strategy": "镜像仓库网络不可达，需要人工修复网络或代理"
    }
  ],
  "basis": ["kubectl get pods 显示两个异常组"],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_verify",
      "group_id": "g1",
      "target_issue": "OOMKilled",
      "description": "验证 memhog 状态",
      "execute_command": "kubectl get pod -n aiops-e2e -l app=memhog"
    }
  ]
}
```
"""

    plan = extract_remediation_plan(text)

    assert plan is not None
    assert [group["group_id"] for group in plan.issue_groups] == ["g1", "g2"]
    assert plan.actions[0].metadata["group_id"] == "g1"
    assert plan.actions[0].metadata["target_issue"] == "OOMKilled"


def test_rejects_non_kubectl_write_command():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "unsafe",
  "risk_level": "high",
  "actions": [
    {
      "id": "a1",
      "type": "run_shell",
      "description": "unsafe",
      "execute_command": "rm -rf /"
    }
  ]
}
```
"""

    with pytest.raises(ValueError, match="unsafe remediation command"):
        extract_remediation_plan(text)


def test_rejects_unsafe_kubectl_write_command_even_for_auto_mode_plan():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "remove_finalizer",
  "risk_level": "medium",
  "actions": [
    {
      "id": "a1",
      "type": "kubectl",
      "description": "unsafe chained command",
      "execute_command": "kubectl patch pod terminating-stuck -n aiops-e2e --type=merge; kubectl delete pod other"
    }
  ]
}
```
"""

    with pytest.raises(ValueError, match="unsafe remediation command"):
        extract_remediation_plan(text)


def test_rejects_placeholder_secret_value_in_remediation_command():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_env",
  "risk_level": "low",
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_set",
      "description": "set required token",
      "execute_command": "kubectl set env deployment/api -n demo PAYMENT_GATEWAY_TOKEN=your_token_value"
    }
  ]
}
```
"""

    with pytest.raises(ValueError, match="placeholder remediation value"):
        extract_remediation_plan(text)


def test_rejects_multi_issue_auto_fix_plan_without_group_action_coverage():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_resources",
  "risk_level": "medium",
  "requires_human_approval": true,
  "issue_groups": [
    {"group_id": "g1", "problem_type": "OOMKilled", "auto_fixable": true},
    {"group_id": "g2", "problem_type": "ImagePullFailed", "auto_fixable": true}
  ],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_verify",
      "group_id": "g1",
      "description": "verify g1",
      "execute_command": "kubectl get pod -n aiops-e2e -l app=memhog"
    }
  ]
}
```
"""

    with pytest.raises(ValueError, match="missing remediation actions"):
        extract_remediation_plan(text)


def test_rejects_multi_issue_action_without_group_id():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_resources",
  "risk_level": "medium",
  "requires_human_approval": true,
  "issue_groups": [
    {"group_id": "g1", "problem_type": "OOMKilled", "auto_fixable": true},
    {"group_id": "g2", "problem_type": "ImagePullFailed", "auto_fixable": false}
  ],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_verify",
      "description": "verify g1",
      "execute_command": "kubectl get pod -n aiops-e2e -l app=memhog"
    }
  ]
}
```
"""

    with pytest.raises(ValueError, match="missing group_id"):
        extract_remediation_plan(text)


def test_returns_none_when_no_plan_exists():
    assert extract_remediation_plan("## 诊断报告\n没有修复 JSON") is None


def test_rejects_available_plan_without_actions():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "remove_finalizer",
  "risk_level": "medium",
  "basis": ["deletionTimestamp exists", "finalizers non-empty"],
  "actions": []
}
```
"""

    with pytest.raises(ValueError, match="remediation_available=true requires actions"):
        extract_remediation_plan(text)


def test_extracts_terminating_stuck_finalizer_patch_action():
    text = """
```json
{
  "remediation_available": true,
  "fix_type": "remove_finalizer",
  "risk_level": "medium",
  "requires_human_approval": true,
  "issue_groups": [
    {
      "group_id": "g1",
      "problem_type": "TerminatingStuck",
      "target": "pod/terminating-stuck",
      "auto_fixable": true
    }
  ],
  "basis": [
    "kubectl_get_yaml shows deletionTimestamp exists",
    "kubectl_get_yaml shows finalizers: aiops.e2e/hold"
  ],
  "actions": [
    {
      "id": "remove-finalizer-g1",
      "type": "kubectl",
      "group_id": "g1",
      "description": "Remove confirmed blocking finalizer",
      "risk": "medium",
      "dry_run_command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
      "execute_command": "kubectl patch pod terminating-stuck -n aiops-e2e -p '{\\"metadata\\":{\\"finalizers\\":null}}' --type=merge",
      "verify_command": "kubectl get pod terminating-stuck -n aiops-e2e"
    }
  ]
}
```
"""

    plan = extract_remediation_plan(text)

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.actions[0].execute_command.startswith("kubectl patch pod terminating-stuck")
    assert plan.actions[0].metadata["group_id"] == "g1"
