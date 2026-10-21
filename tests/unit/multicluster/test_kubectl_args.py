"""Remote kubectl argument rules shared by the shim and the runner (spec edge cases)."""

import pytest

from aiops_edge import kubectl_args as ka


@pytest.mark.parametrize(
    "argv,mode",
    [
        (["kubectl", "get", "pods", "-A", "-o", "json"], "read"),
        (["kubectl", "-n", "demo", "describe", "pod", "x"], "read"),
        (["kubectl", "--namespace=demo", "logs", "x", "--tail=50"], "read"),
        (["kubectl", "top", "pods", "-n", "demo"], "read"),
        (["kubectl", "events", "-n", "demo"], "read"),
        (["kubectl", "api-resources"], "read"),
        (["kubectl", "rollout", "history", "deploy/x"], "read"),
        (["kubectl", "exec", "x", "-n", "demo", "--", "ls", "/tmp"], "exec"),
        (["kubectl", "delete", "pod", "x", "-n", "demo"], "write"),
        (["kubectl", "run", "t", "--image=busybox", "--", "sleep", "1"], "write"),
        (["kubectl", "rollout", "restart", "deploy/x"], "write"),
        (["kubectl", "patch", "deploy", "x", "-p", "{}"], "write"),
    ],
)
def test_mode_classification(argv, mode):
    assert ka.classify(argv) == (mode, None)


@pytest.mark.parametrize(
    "argv,fragment",
    [
        (["kubectl", "logs", "x", "-f"], "follow"),
        (["kubectl", "logs", "x", "--follow"], "follow"),
        (["kubectl", "get", "pods", "-w"], "watch"),
        (["kubectl", "get", "pods", "--watch"], "watch"),
        (["kubectl", "exec", "-it", "x", "--", "sh"], "interactive"),
        (["kubectl", "exec", "-i", "x", "--", "sh"], "interactive"),
        (["kubectl", "exec", "--stdin", "x", "--", "sh"], "interactive"),
        (["kubectl", "port-forward", "x", "80"], "not supported"),
        (["kubectl", "proxy"], "not supported"),
        (["kubectl", "attach", "x"], "not supported"),
        (["kubectl", "cp", "x:/a", "/b"], "not supported"),
        (["kubectl", "edit", "deploy", "x"], "not supported"),
        (["kubectl", "rollout", "status", "deploy/x"], "not supported"),
        (["kubectl", "wait", "--for=condition=Ready", "pod/x"], "not supported"),
        (["kubectl", "apply", "-f", "x.yaml"], "local file"),
        (["kubectl", "create", "--filename=x.yaml"], "local file"),
        (["kubectl", "--kubeconfig", "/x", "get", "pods"], "credential"),
        (["kubectl", "--context=a", "get", "pods"], "credential"),
        (["kubectl", "get", "pods", "--server", "https://x"], "credential"),
        (["kubectl", "get", "pods", "--as=admin"], "credential"),
        (["kubectl", "get", "pods", "--token", "t"], "credential"),
        (["kubectl"], "subcommand"),
        (["helm", "list"], "kubectl"),
    ],
)
def test_rejected_arguments(argv, fragment):
    mode, reason = ka.classify(argv)
    assert mode is None
    assert fragment in reason


def test_exec_args_after_double_dash_are_not_flags():
    # "-f" after "--" belongs to the in-container command, not kubectl.
    assert ka.classify(["kubectl", "exec", "x", "--", "tail", "-f", "/x"]) == ("exec", None)
    assert ka.classify(["kubectl", "exec", "x", "--", "ls", "-w"]) == ("exec", None)
