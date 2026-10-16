"""High-risk command rules: default-deny list, named verdicts, deny wins, config overrides.

Acceptance item (Sprint 2): "高危命令黑名单拦截测试" must be demonstrable without a
model: every denial names its rule; the same engine serves planning, execution
and the /repair/policy/check endpoint.
"""

import pytest

from app.core.remediation.policy import (
    CommandPolicy,
    CommandVerdict,
    RepairCommandDenied,
    check_command,
    validate_target_command,
)

DANGEROUS = [
    ("kubectl delete pod/api-1 -n demo", "denied_operations"),
    ("kubectl delete pod api-1 -n demo --force --grace-period=0", "denied_operations"),
    ("kubectl delete ns demo", "denied_operations"),
    ("kubectl apply -n demo -f https://example.invalid/pod.yaml", "denied_operations"),
    ("kubectl replace -f /tmp/x.yaml -n demo", "denied_operations"),
    ("kubectl run shell -n demo --image=busybox -- sh", "denied_operations"),
    ("kubectl debug node/node1 -it --image=busybox", "denied_operations"),
    ("kubectl drain node1 --ignore-daemonsets", "denied_operations"),
    ("kubectl cordon node1", "denied_operations"),
    ("kubectl taint nodes node1 key=value:NoSchedule", "denied_operations"),
    ("kubectl patch pod/api-1 -n demo --all -p '{}'", "denied_flags"),
    ("kubectl rollout restart deployment -n demo --all", "denied_flags"),
    ("kubectl scale deployment --all --replicas=0 -A", "denied_flags"),
    ("kubectl patch deployment api -n demo -l app=api -p '{}'", "bulk_selector_on_write"),
    ("kubectl label nodes node1 role=x", "denied_resource_kinds"),
    ("kubectl patch node/node1 -p '{}'", "denied_resource_kinds"),
    ("kubectl patch clusterrolebinding/admin -p '{}'", "denied_resource_kinds"),
    ("kubectl patch crd/widgets.example.com -p '{}'", "denied_resource_kinds"),
    ("kubectl patch ns/demo -p '{}'", "denied_resource_kinds"),
    ("kubectl exec pod/api-1 -n demo -- rm -rf /data", "denied_executables"),
    ("kubectl exec pod/api-1 -n demo -- sh -c 'kill -9 1'", "denied_executables"),
    ("kubectl exec pod/api-1 -n demo -- mkfs.ext4 /dev/sda", "denied_executables"),
    ("kubectl get pod/api-1 -n demo --kubeconfig=/tmp/c", "transport.no_identity_override"),
    ("kubectl get pods -n demo ; rm -rf /", "transport.no_shell_operators"),
    ("bash -c 'kubectl get pods'", "transport.kubectl_only"),
    ("kubectl config use-context other", "transport.no_identity_override"),
]

ALLOWED = [
    "kubectl get pod/api-1 -n demo -o json",
    "kubectl get nodes -o wide",
    "kubectl describe node node1",
    'kubectl patch pod/api-1 -n demo --type=merge -p \'{"metadata":{"finalizers":null}}\'',
    'kubectl patch deployment/api -n demo --type=json -p \'[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/port","value":8080}]\'',
    "kubectl set env deployment/api -n demo APP_CONFIG_PATH=/etc/workload/app.json",
    "kubectl rollout restart deployment/api -n demo",
    "kubectl scale deployment/api -n demo --replicas=2",
    "kubectl exec pod/api-1 -n demo -- curl -s http://localhost:8080/ready",
    "kubectl create configmap settings -n demo --from-literal=mode=test",
    "kubectl rollout status deployment/api -n demo --timeout=60s",
    "kubectl get pods -n demo -l app=api",
]


@pytest.mark.parametrize("command,rule", DANGEROUS)
def test_default_policy_denies_high_risk_commands_with_named_rule(command, rule):
    verdict = check_command(command)
    assert isinstance(verdict, CommandVerdict)
    assert verdict.allowed is False
    assert verdict.rule == rule, verdict
    assert verdict.reason
    with pytest.raises(RepairCommandDenied) as excinfo:
        validate_target_command(command)
    assert excinfo.value.rule == rule


@pytest.mark.parametrize("command", ALLOWED)
def test_default_policy_allows_reviewable_repairs(command):
    verdict = check_command(command)
    assert verdict.allowed is True, verdict
    assert verdict.rule == ""
    assert verdict.operation


def test_admin_can_narrow_but_deny_always_wins():
    narrow = CommandPolicy.from_config({"allowed_operations": ["patch"]})
    assert (
        check_command("kubectl set env deployment/api -n demo A=b", narrow).rule
        == "allowed_operations"
    )
    loose = CommandPolicy.from_config({"denied_operations": []})
    assert check_command("kubectl delete pod/api-1 -n demo", loose).allowed is True
    both = CommandPolicy.from_config(
        {"denied_operations": ["patch"], "allowed_operations": ["patch"]}
    )
    assert check_command("kubectl patch pod/x -n demo -p '{}'", both).rule == "denied_operations"


def test_policy_summary_lists_every_rule_for_operators():
    summary = CommandPolicy().summary()
    assert set(summary) >= {
        "denied_operations",
        "denied_flags",
        "bulk_selector_on_write",
        "denied_resource_kinds",
        "denied_executables",
        "allowed_exec_commands",
        "allowed_operations",
        "transport",
    }
    assert "delete" in summary["denied_operations"] and "rm" in summary["denied_executables"]


def test_invalid_configuration_is_rejected_not_ignored():
    with pytest.raises(ValueError):
        CommandPolicy.from_config({"denied_flags": "--force"})
    with pytest.raises(ValueError):
        CommandPolicy.from_config({"denied_resource_kinds": [""]})
