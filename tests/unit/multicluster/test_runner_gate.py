"""Edge runner command gate: same rules as the center (spec FR-015)."""

from pathlib import Path

import pytest
import yaml

from aiops_edge.runner.gate import evaluate
from app.core.remediation.policy import CommandPolicy

CONFIG = Path(__file__).resolve().parents[3] / "deploy" / "configmap" / "config.yaml"


@pytest.fixture(scope="module")
def policy():
    raw = yaml.safe_load(yaml.safe_load(CONFIG.read_text())["data"]["config.yaml"])
    return CommandPolicy.from_config(raw["workflow"]["remediation"])


def K(text):
    return ["kubectl", *text.split()]


def test_read_allows_cluster_wide_listing(policy):
    # -A is a bulk flag for writes; reads must not be blocked by write rules.
    assert evaluate(K("get pods -A -o json"), "read", "", policy).ok


def test_read_refuses_write_operations(policy):
    decision = evaluate(K("delete pod x -n demo"), "read", "", policy)
    assert not decision.ok and decision.status == 403 and decision.error == "mode_denied"


def test_declared_mode_must_match_command(policy):
    decision = evaluate(K("exec x -n demo -- ls"), "read", "", policy)
    assert decision.error == "mode_denied"


def test_exec_of_safe_command_allowed(policy):
    assert evaluate(K("exec x -n demo -- ls /tmp"), "exec", "", policy).ok


def test_approval_required_command_needs_approval(policy):
    decision = evaluate(K("exec x -n demo -- rm -f /tmp/a"), "exec", "", policy)
    assert (
        not decision.ok
        and decision.error == "policy_denied"
        and decision.rule == "approval_required"
    )
    assert evaluate(K("exec x -n demo -- rm -f /tmp/a"), "exec", "b8f563d97f52", policy).ok


def test_denylisted_command_refused_even_with_approval(policy):
    decision = evaluate(K("exec x -n demo -- reboot"), "exec", "b8f563d97f52", policy)
    assert not decision.ok and decision.rule == "denied_executables"


def test_drain_needs_approval(policy):
    assert evaluate(K("drain n1"), "write", "", policy).rule == "approval_required"
    assert evaluate(K("drain n1"), "write", "a1", policy).ok


def test_scoped_write_allowed(policy):
    assert evaluate(K("delete pod x -n demo"), "write", "", policy).ok


def test_argument_rules_apply_on_runner_too(policy):
    decision = evaluate(K("logs x -f"), "read", "", policy)
    assert decision.error == "mode_denied" and "follow" in decision.reason
    assert evaluate(K("--as=admin get pods"), "read", "", policy).error == "mode_denied"


def test_unknown_mode_refused(policy):
    assert evaluate(K("get pods"), "admin", "", policy).status == 400
