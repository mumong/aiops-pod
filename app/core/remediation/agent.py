"""LLM-guided remediation loop with bounded tool execution.

The conclusion node proposes an initial plan. This executor treats that plan as
guidance, then repeatedly asks an LLM (or test decision provider) what to do
next based on the latest real command observations.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Callable, Dict, Generator, List, Optional

from app.core.prompts import (
    LEGACY_REMEDIATION_AGENT_PROMPT,
)
from app.core.remediation.approval import ApprovalStore, approval_store
from app.core.remediation.executor import (
    CommandRunner,
    healthy_remediation_observation,
    run_local_command,
    unhealthy_remediation_reason,
)
from app.core.remediation.models import (
    RemediationAction,
    RemediationPlan,
    RemediationRuntimeConfig,
    normalize_remediation_mode,
)
from app.core.remediation.plans import is_read_only_kubectl_command, validate_safe_kubectl_command


@dataclass(frozen=True)
class RemediationAgentConfig(RemediationRuntimeConfig):
    executor: str = "react"


@dataclass(frozen=True)
class AgentDecision:
    decision: str
    description: str = ""
    command: str = ""
    dry_run_command: str = ""
    verify_command: str = ""
    risk: str = "medium"
    status: str = ""
    reason: str = ""


DecisionProvider = Callable[..., AgentDecision]


class RemediationAgentExecutor:
    def __init__(
        self,
        approval_store: ApprovalStore = approval_store,
        command_runner: CommandRunner = run_local_command,
        ai_call: object = None,
        decision_provider: Optional[DecisionProvider] = None,
    ) -> None:
        self.approval_store = approval_store
        self.command_runner = command_runner
        self.ai_call = ai_call
        self.decision_provider = decision_provider

    def run(
        self,
        run_id: str,
        plan: Optional[RemediationPlan],
        report: str,
        approval_timeout_seconds: float = 600,
        approval_mode: str = "review",
        config: Optional[RemediationAgentConfig] = None,
    ) -> Generator[Dict, None, None]:
        cfg = config or RemediationAgentConfig()
        if plan is None or not plan.remediation_available:
            yield self._finished(run_id, "skipped", "no remediation plan")
            return

        review_mode = normalize_remediation_mode(approval_mode) != "auto"
        if review_mode:
            plan_request = self.approval_store.create_request(
                timeout_seconds=approval_timeout_seconds,
                run_id=run_id,
                kind="plan",
                title="是否认可诊断报告中的修复方案",
                payload={
                    "executor": "react",
                    "fix_type": plan.fix_type,
                    "risk_level": plan.risk_level,
                    "issue_groups": plan.issue_groups,
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

        observations: List[str] = [f"plan_basis: {item}" for item in plan.basis]
        started = time.time()
        write_count = 0
        completed_action_ids: set[str] = set()
        completed_group_ids: set[str] = set()

        for iteration in range(1, max(1, cfg.max_iterations) + 1):
            if time.time() - started > cfg.max_duration_seconds:
                yield self._finished(run_id, "timeout", "remediation agent duration limit reached")
                return

            decision = self._next_decision(
                plan=plan,
                report=report,
                observations=observations,
                iteration=iteration,
                config=cfg,
            )

            if decision.decision == "finish":
                status = str(decision.status or "").strip().lower()
                if status not in {"success", "failed"}:
                    status = "failed"
                    reason = decision.reason or "remediation agent finish decision must include status=success or status=failed"
                else:
                    reason = decision.reason or "agent finished"
                yield self._finished(run_id, status, reason)
                return

            if decision.decision == "run_command" and not decision.command and (decision.dry_run_command or decision.verify_command):
                observations.append(
                    "invalid_decision: run_command was ignored because command is empty. "
                    "Return finish failed/success, or run a concrete kubectl command. "
                    "If a field-level patch was verified, run rollout status or pod health verification next."
                )
                continue

            if decision.decision != "run_command" or not decision.command:
                yield self._finished(run_id, "failed", f"invalid remediation agent decision: {decision}")
                return

            commands = [
                ("dry_run", decision.dry_run_command),
                ("execute", decision.command),
                ("verify", decision.verify_command),
            ]
            verify_succeeded = False
            verify_accepted_not_found = False
            verify_result = ""
            # Field names are model output, not authority: a write hidden in
            # dry_run_command or verify_command requires the same approval.
            try:
                is_write = any(not is_read_only_kubectl_command(command)
                               for _, command in commands if command)
            except ValueError as exc:
                yield self._finished(run_id, "failed", str(exc))
                return
            if is_write:
                write_count += 1
                if write_count > cfg.max_write_actions:
                    yield self._finished(run_id, "failed", "remediation write action limit reached")
                    return
                if review_mode:
                    action_request = self.approval_store.create_request(
                        timeout_seconds=approval_timeout_seconds,
                        run_id=run_id,
                        kind="action",
                        title=f"是否执行修复动作 react-{iteration}: {decision.description or decision.command}",
                        payload=decision.__dict__,
                    )
                    yield {**self._approval_event(
                        run_id,
                        action_request.approval_id,
                        "action",
                        action_request.title,
                        action_request.payload,
                    ), "expires_at": action_request.expires_at, "server_time": time.time()}
                    action_decision = self.approval_store.wait_for_decision(
                        run_id, action_request.approval_id, approval_timeout_seconds
                    )
                    if action_decision is None:
                        yield self._finished(run_id, "timeout", f"action react-{iteration} approval timeout")
                        return
                    if not action_decision.approved:
                        yield self._finished(run_id, "rejected", action_decision.reason or f"action react-{iteration} rejected")
                        return

            for stage, command in commands:
                if not command:
                    continue
                if stage == "verify" and cfg.verify_settle_seconds > 0:
                    time.sleep(float(cfg.verify_settle_seconds))
                try:
                    validate_safe_kubectl_command(command)
                    result = self.command_runner(command)
                except Exception as exc:
                    error_text = str(exc)
                    if stage == "verify" and _verify_not_found_is_success(decision, command, error_text):
                        result = (
                            f"{error_text}\n"
                            "verification accepted: target resource is NotFound after deletion/finalizer remediation"
                        )
                        verify_succeeded = True
                        verify_accepted_not_found = True
                        verify_result = result
                        observation = f"{stage}: {command}\n{result}"
                        observations.append(observation)
                        yield {
                            "type": "remediation_tool_result",
                            "run_id": run_id,
                            "action_id": f"react-{iteration}",
                            "stage": stage,
                            "command": command,
                            "status": "success",
                            "result_preview": str(result or "")[:1200],
                        }
                        continue
                    observations.append(f"{stage}: {command}\nERROR: {error_text}")
                    yield {
                        "type": "remediation_tool_result",
                        "run_id": run_id,
                        "action_id": f"react-{iteration}",
                        "stage": stage,
                        "command": command,
                        "status": "failed",
                        "result_preview": error_text[:1200],
                    }
                    yield self._finished(run_id, "failed", error_text)
                    return
                observation = f"{stage}: {command}\n{result}"
                observations.append(observation)
                if stage == "verify":
                    verify_succeeded = True
                    verify_result = str(result or "")
                yield {
                    "type": "remediation_tool_result",
                    "run_id": run_id,
                    "action_id": f"react-{iteration}",
                    "stage": stage,
                    "command": command,
                    "status": "success",
                    "result_preview": str(result or "")[:1200],
                }

            matched_action = _matched_plan_action(plan, decision.command)
            if (
                matched_action is not None
                and verify_succeeded
                and _verify_establishes_terminal_success(decision.verify_command, verify_result, verify_accepted_not_found)
            ):
                completed_action_ids.add(matched_action.id)
                group_id = str(matched_action.metadata.get("group_id") or "").strip()
                if group_id:
                    completed_group_ids.add(group_id)
                if _planned_remediation_complete(plan, completed_action_ids, completed_group_ids):
                    reason = _completion_reason(completed_action_ids, completed_group_ids)
                    yield self._finished(run_id, "success", reason)
                    return

        latest = observations[-1] if observations else ""
        reason = unhealthy_remediation_reason(latest) or "remediation agent iteration limit reached"
        yield self._finished(run_id, "failed", reason)

    def _next_decision(
        self,
        plan: RemediationPlan,
        report: str,
        observations: List[str],
        iteration: int,
        config: RemediationAgentConfig,
    ) -> AgentDecision:
        if self.decision_provider is not None:
            return self.decision_provider(
                plan=plan,
                report=report,
                observations=observations,
                iteration=iteration,
                config=config,
            )
        if self.ai_call is None:
            if iteration == 1 and plan.actions:
                action = plan.actions[0]
                return AgentDecision(
                    decision="run_command",
                    description=action.description,
                    dry_run_command=action.dry_run_command or "",
                    command=action.execute_command or action.verify_command or "",
                    verify_command=action.verify_command or "",
                    risk=action.risk,
                )
            return AgentDecision(decision="finish", status="failed", reason="no remediation AI is configured")

        prompt = _AGENT_PROMPT
        question = json.dumps(
            {
                "remediation_plan": {
                    "fix_type": plan.fix_type,
                    "risk_level": plan.risk_level,
                    "issue_groups": plan.issue_groups,
                    "basis": plan.basis,
                    "actions": [action.__dict__ for action in plan.actions],
                },
                "report": report[-8000:],
                "observations": observations[-8:],
                "iteration": iteration,
                "limits": {
                    "max_iterations": config.max_iterations,
                    "max_write_actions": config.max_write_actions,
                },
            },
            ensure_ascii=False,
        )
        raw = self.ai_call.call_simple(prompt, question, node_id="remediation")
        return _parse_decision(raw)

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


_AGENT_PROMPT = LEGACY_REMEDIATION_AGENT_PROMPT


def _parse_decision(text: str) -> AgentDecision:
    data = _loads_json_object(text)
    if not isinstance(data, dict):
        return AgentDecision(decision="finish", status="failed", reason="remediation agent did not return JSON")
    return AgentDecision(
        decision=str(data.get("decision") or "").strip(),
        description=str(data.get("description") or ""),
        dry_run_command=str(data.get("dry_run_command") or ""),
        command=str(data.get("command") or ""),
        verify_command=str(data.get("verify_command") or ""),
        risk=str(data.get("risk") or "medium"),
        status=str(data.get("status") or ""),
        reason=str(data.get("reason") or ""),
    )


def _loads_json_object(text: str) -> Optional[Dict]:
    raw = str(text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1)
    elif "{" in raw and "}" in raw:
        raw = raw[raw.find("{") : raw.rfind("}") + 1]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _matched_plan_action(plan: RemediationPlan, command: str) -> Optional[RemediationAction]:
    normalized_command = _normalize_command(command)
    if not normalized_command:
        return None
    for action in plan.actions:
        if _normalize_command(action.execute_command or "") == normalized_command:
            return action
    return None


def _planned_remediation_complete(
    plan: RemediationPlan,
    completed_action_ids: set[str],
    completed_group_ids: set[str],
) -> bool:
    required_group_ids = {
        str(group.get("group_id") or "").strip()
        for group in plan.issue_groups
        if group.get("auto_fixable") is True or str(group.get("auto_fixable")).lower() == "true"
    }
    required_group_ids.discard("")
    if required_group_ids:
        return required_group_ids <= completed_group_ids

    write_action_ids = {
        action.id
        for action in plan.actions
        if _normalize_command(action.execute_command or "")
    }
    return bool(write_action_ids) and write_action_ids <= completed_action_ids


def _verify_establishes_terminal_success(command: str, result: str, accepted_not_found: bool) -> bool:
    if accepted_not_found:
        return True
    if unhealthy_remediation_reason(result):
        return False
    command_text = str(command or "").lower()
    result_text = str(result or "").lower()
    if "rollout status" in command_text and "successfully rolled out" in result_text:
        return True
    return healthy_remediation_observation(result)


def _completion_reason(completed_action_ids: set[str], completed_group_ids: set[str]) -> str:
    action_part = ", ".join(sorted(completed_action_ids)) or "planned actions"
    group_part = ", ".join(sorted(completed_group_ids))
    if group_part:
        return f"planned remediation verified successfully for actions: {action_part}; groups: {group_part}"
    return f"planned remediation verified successfully for actions: {action_part}"


def _normalize_command(command: str) -> str:
    return " ".join(str(command or "").split())


def _verify_not_found_is_success(decision: AgentDecision, command: str, error_text: str) -> bool:
    if "NotFound" not in str(error_text) and "not found" not in str(error_text).lower():
        return False
    command_text = str(command or "").lower()
    intent_text = " ".join(
        [
            str(decision.description or ""),
            str(decision.reason or ""),
            str(decision.command or ""),
            str(decision.verify_command or ""),
        ]
    ).lower()
    deletion_intent_markers = (
        "finalizer",
        "finalizers",
        "delete",
        "deletion",
        "terminating",
        "删除",
        "移除",
        "清理",
    )
    return "kubectl get" in command_text and any(marker in intent_text for marker in deletion_intent_markers)
