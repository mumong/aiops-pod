"""Deterministic remediation executor with human approval gates."""

from __future__ import annotations

import subprocess
import shlex
from typing import Callable, Dict, Generator, Optional

from app.core.remediation.approval import ApprovalStore, approval_store
from app.core.remediation.models import RemediationAction, RemediationPlan


UNHEALTHY_REMEDIATION_MARKERS = (
    "OOMKilled",
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "CreateContainerError",
    "RunContainerError",
    "Error",
    "BackOff",
    "0/1",
    "0/2",
)


CommandRunner = Callable[[str], str]


def run_local_command(command: str) -> str:
    result = subprocess.run(shlex.split(command), text=True, capture_output=True, check=False)
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

        review_mode = str(approval_mode or "review").strip().lower() != "auto"
        if review_mode:
            plan_request = self.approval_store.create_request(
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
            yield self._approval_event(run_id, plan_request.approval_id, "plan", plan_request.title, plan_request.payload)
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
                    run_id=run_id,
                    kind="action",
                    title=f"是否执行修复动作 {action.id}: {action.description}",
                    payload=action.__dict__,
                )
                yield self._approval_event(run_id, action_request.approval_id, "action", action_request.title, action_request.payload)
                action_decision = self.approval_store.wait_for_decision(run_id, action_request.approval_id, approval_timeout_seconds)
                if action_decision is None:
                    yield self._finished(run_id, "timeout", f"action {action.id} approval timeout")
                    return
                if not action_decision.approved:
                    yield self._finished(run_id, "rejected", action_decision.reason or f"action {action.id} rejected")
                    return
            try:
                unhealthy_reason = None
                for event in self._execute_action(run_id, action):
                    yield event
                    if event.get("stage") == "verify":
                        unhealthy_reason = unhealthy_remediation_reason(event.get("result_preview", ""))
                if unhealthy_reason:
                    yield self._finished(run_id, "needs_followup", unhealthy_reason)
                    return
            except Exception as exc:
                yield self._finished(run_id, "failed", str(exc))
                return

        yield self._finished(run_id, "success", "all remediation actions completed")

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
    value = str(text or "")
    if not value.strip():
        return None
    for marker in UNHEALTHY_REMEDIATION_MARKERS:
        if marker in value:
            return f"verification still shows unhealthy workload: {marker}"
    return None


def healthy_remediation_observation(text: str) -> bool:
    value = str(text or "")
    if unhealthy_remediation_reason(value):
        return False
    ready_signal = "Ready=True" in value or "1/1" in value or "2/2" in value
    running_signal = "Running" in value or "successfully rolled out" in value
    return ready_signal and running_signal
