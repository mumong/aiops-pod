import pytest

from app.core.remediation.policy import CommandPolicy, validate_target_command

TARGETS = {("demo", "pod", "api-123"), ("demo", "deployment", "api")}


@pytest.mark.parametrize("command", [
    "kubectl get pod/api-123 -n demo -o json",
    "kubectl -n demo set resources deployment/api --limits=memory=256Mi --dry-run=server",
    "kubectl rollout restart deployment/api --namespace=demo",
    '''kubectl patch deployment/api -n demo --type=json -p '[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"256Mi"}]' ''',
])
def test_exact_targets_allowed(command):
    assert validate_target_command(command, TARGETS)[0][0] == "kubectl"


@pytest.mark.parametrize("command", [
    "rm -rf /tmp/reports", "bash -c true", "kubectl delete pod/api-123 -n demo",
    "kubectl get pod/api-123 -n demo --server=https://other",
    "kubectl get pod/api-123 -n demo --as=admin",
    "kubectl get pod/api-123 -n demo --kubeconfig=/tmp/config",
    "kubectl get pod/api-123 -n other", "kubectl get pod/other -n demo",
    "kubectl get secret/token -n demo", "kubectl get pods -n demo --all",
    "kubectl get pod/api-123 -n demo --namespace=other",
    "kubectl get pod/api-123 -n demo; rm -rf /tmp/a",
    "kubectl exec pod/api-123 -n demo -- sh",
    "kubectl apply -n demo -f https://example.invalid/pod.yaml",
    '''kubectl patch deployment/api -n demo --type=json -p '[{"op":"remove","path":"/metadata/finalizers"}]' ''',
    '''kubectl patch deployment/api -n demo --type=json -p '[{"op":"add","path":"/spec/template/spec/containers/0/securityContext/privileged","value":true}]' ''',
])
def test_dangerous_or_out_of_scope_commands_rejected(command):
    with pytest.raises(ValueError):
        validate_target_command(command, TARGETS)


def test_blacklist_wins_over_whitelist():
    policy = CommandPolicy(denied_operations=frozenset({"rollout_restart"}))
    with pytest.raises(ValueError):
        validate_target_command("kubectl rollout restart deployment/api -n demo", TARGETS, policy)
