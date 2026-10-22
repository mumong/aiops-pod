"""Command gate on the edge: the center's rules, enforced again where commands run.

- ``read``: only read-only kubectl operations; write-side rules (bulk flags,
  protected kinds) do not apply to reads, matching the center's read tools.
  A write command with ``--dry-run=client`` (repair preflight) is read-only in
  effect: allowed unless the policy denies the command itself.
- ``exec`` / ``write``: the configured remediation policy. Without an approval
  id the strict policy applies (approval_required counts as denied, as in
  chat); with one, approval_required commands may run. Denylisted commands are
  refused either way.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import List

from aiops_edge import kubectl_args
from app.core.remediation.policy import READ_ONLY_OPERATIONS, CommandPolicy, check_command

MODES = ("read", "exec", "write")


@dataclass(frozen=True)
class Decision:
    ok: bool
    status: int = 200
    error: str = ""
    rule: str = ""
    reason: str = ""

    def body(self) -> dict:
        return {"error": self.error, "rule": self.rule, "reason": self.reason}


def _deny(status: int, error: str, reason: str, rule: str = "") -> Decision:
    return Decision(False, status, error, rule, reason)


def evaluate(argv: List[str], mode: str, approval_id: str, policy: CommandPolicy) -> Decision:
    if mode not in MODES:
        return _deny(400, "bad_request", f"mode must be one of {MODES}")
    actual, reason = kubectl_args.classify(argv)
    if actual is None:
        return _deny(403, "mode_denied", reason)
    if actual != mode:
        return _deny(
            403, "mode_denied", f"command is a {actual} operation but the request declared {mode}"
        )
    command = shlex.join(argv)
    if mode == "read":
        verdict = check_command(command, policy)
        if "--dry-run=client" in argv:
            # Repair preflight: a client dry run changes nothing, so it needs no approval;
            # a denylisted command is still refused, which tells the planner early.
            if not verdict.allowed:
                return _deny(403, "policy_denied", verdict.reason, verdict.rule)
            return Decision(True)
        if verdict.operation not in READ_ONLY_OPERATIONS:
            return _deny(403, "mode_denied", f"{verdict.operation or 'command'} is not read-only")
        return Decision(True)
    verdict = check_command(command, policy)
    if not verdict.allowed:
        return _deny(403, "policy_denied", verdict.reason, verdict.rule)
    if verdict.requires_approval and not approval_id:
        return _deny(
            403, "policy_denied", verdict.reason + "；需携带人工审批 ID", "approval_required"
        )
    return Decision(True)
