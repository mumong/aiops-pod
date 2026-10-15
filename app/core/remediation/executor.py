"""Deterministic remediation executor with human approval gates."""

from __future__ import annotations

import shlex
import subprocess
import time
from typing import Callable, Dict, Generator, Optional

from app.core.remediation.approval import ApprovalStore, approval_store
from app.core.remediation.models import (
    RemediationAction,
    RemediationPlan,
    normalize_remediation_mode,
)

CommandRunner = Callable[[str], str]


# Same bound as PodRepairExecutor's kubectl runner; a hung command must not pin the run.
LOCAL_COMMAND_TIMEOUT_SECONDS = 60


def run_local_command(command: str) -> str:
    try:
        result = subprocess.run(
            shlex.split(command),
            text=True,
            capture_output=True,
            check=False,
            timeout=LOCAL_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"command timed out after {LOCAL_COMMAND_TIMEOUT_SECONDS}s: {command}") from exc
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode != 0:
        raise RuntimeError(output or f"command failed with exit code {result.returncode}: {command}")
    return output


class RemediationExecutor:
    def __init__(
        self,
        approval_store: ApprovalStore = approval_store,
        command_runner: CommandRunner = run_local_command,
    ) -> None:
        self.approval_store = approval_store
        self.command_runner = command_runner

    def run(
        self,
        run_id: str,
        plan: Optional[RemediationPlan],
        approval_timeout_seconds: float = 600,
        approval_mode: str = "review",
    ) -> Generator[Dict, None, None]:
        if plan is None or not plan.remediation_available or not plan.actions:
            yield {
                "type": "remediation_finished",
                "run_id": run_id,
                "status": "skipped",
                "reason": "no remediation plan",
            }
            return

        review_mode = normalize_remediation_mode(approval_mode) != "auto"
        if review_mode:
            plan_request = self.approval_store.create_request(
                timeout_seconds=approval_timeout_seconds,
                run_id=run_id,
                kind="plan",
                title="是否认可诊断报告中的修复方案",
                payload={
                    "fix_type": plan.fix_type,
                    "risk_level": plan.risk_level,
                    "basis": plan.basis,
                    "actions": [action.__dict__ for action in plan.actions],
                },
            )
            yield {**self._approval_event(run_id, plan_request.approval_id, "plan", plan_request.title, plan_request.payload),
                   "expires_at": plan_request.expires_at, "server_time": time.time()}
            decision = self.approval_store.wait_for_decision(run_id, plan_request.approval_id, approval_timeout_seconds)
            if decision is None:
                yield self._finished(run_id, "timeout", "plan approval timeout")
                return
            if not decision.approved:
                yield self._finished(run_id, "rejected", decision.reason or "plan rejected")
                return

        for action in plan.actions:
            if review_mode:
                action_request = self.approval_store.create_request(
                    timeout_seconds=approval_timeout_seconds,
                    run_id=run_id,
                    kind="action",
                    title=f"是否执行修复动作 {action.id}: {action.description}",
                    payload=action.__dict__,
                )
                yield {**self._approval_event(run_id, action_request.approval_id, "action", action_request.title, action_request.payload),
                       "expires_at": action_request.expires_at, "server_time": time.time()}
                action_decision = self.approval_store.wait_for_decision(run_id, action_request.approval_id, approval_timeout_seconds)
                if action_decision is None:
                    yield self._finished(run_id, "timeout", f"action {action.id} approval timeout")
                    return
                if not action_decision.approved:
                    yield self._finished(run_id, "rejected", action_decision.reason or f"action {action.id} rejected")
                    return
            try:
                for event in self._execute_action(run_id, action):
                    yield event
            except Exception as exc:
                yield self._finished(run_id, "failed", str(exc))
                return

        yield self._finished(run_id, "needs_followup", "命令已执行；恢复条件尚未经结构化核验，请复查实际状态")

    def _execute_action(self, run_id: str, action: RemediationAction) -> Generator[Dict, None, None]:
        for stage, command in (
            ("dry_run", action.dry_run_command),
            ("execute", action.execute_command),
            ("verify", action.verify_command),
        ):
            if not command:
                continue
            result = self.command_runner(command)
            yield {
                "type": "remediation_tool_result",
                "run_id": run_id,
                "action_id": action.id,
                "stage": stage,
                "command": command,
                "status": "success",
                "result_preview": str(result or "")[:1200],
            }

    @staticmethod
    def _approval_event(run_id: str, approval_id: str, kind: str, title: str, payload: Dict) -> Dict:
        return {
            "type": "remediation_approval_required",
            "run_id": run_id,
            "approval_id": approval_id,
            "approval_kind": kind,
            "title": title,
            "payload": payload,
        }

    @staticmethod
    def _finished(run_id: str, status: str, reason: str) -> Dict:
        return {
            "type": "remediation_finished",
            "run_id": run_id,
            "status": status,
            "reason": reason,
        }


def unhealthy_remediation_reason(text: str) -> Optional[str]:
    # Compatibility only: prose does not establish a resource's health.
    return None
