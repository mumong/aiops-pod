"""Parse and validate remediation plans emitted by conclusion."""

from __future__ import annotations

import json
import re
import shlex
from typing import Any, Dict, Iterable, Optional

from app.core.remediation.models import RemediationAction, RemediationPlan


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.IGNORECASE | re.DOTALL)
_ALLOWED_KUBECTL_VERBS = {
    "apply",
    "create",
    "delete",
    "describe",
    "get",
    "logs",
    "patch",
    "rollout",
    "scale",
    "set",
    "top",
}
_SHELL_METACHARS = re.compile(r"[;&|`$<>]")


def extract_remediation_plan(text: str) -> Optional[RemediationPlan]:
    """Extract the first valid remediation JSON object from Markdown text."""
    for candidate in _candidate_json_objects(text or ""):
        data = _loads_json(candidate)
        if not isinstance(data, dict):
            continue
        if "remediation_plan" in data and isinstance(data.get("remediation_plan"), dict):
            data = data["remediation_plan"]
        if "remediation_available" not in data and "actions" not in data:
            continue
        return _build_plan(data)
    return None


def _candidate_json_objects(text: str) -> Iterable[str]:
    for match in _JSON_FENCE_RE.finditer(text):
        yield match.group(1)
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        yield stripped


def _loads_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _build_plan(data: Dict[str, Any]) -> RemediationPlan:
    actions = [_build_action(item) for item in data.get("actions") or [] if isinstance(item, dict)]
    issue_groups = [item for item in data.get("issue_groups") or [] if isinstance(item, dict)]
    _validate_issue_group_coverage(issue_groups, actions)
    remediation_available = bool(data.get("remediation_available", bool(actions)))
    if remediation_available and not actions:
        raise ValueError("remediation_available=true requires actions")
    return RemediationPlan(
        remediation_available=remediation_available,
        fix_type=str(data.get("fix_type") or "unknown"),
        risk_level=str(data.get("risk_level") or "medium"),
        requires_human_approval=bool(data.get("requires_human_approval", True)),
        issue_groups=issue_groups,
        basis=[str(item) for item in data.get("basis") or []],
        actions=actions,
        stop_conditions=[str(item) for item in data.get("stop_conditions") or []],
    )


def _validate_issue_group_coverage(issue_groups: list[Dict[str, Any]], actions: list[RemediationAction]) -> None:
    if len(issue_groups) < 2:
        return
    group_ids = {str(group.get("group_id") or "").strip() for group in issue_groups}
    group_ids.discard("")
    if not group_ids:
        return

    covered_group_ids = set()
    for action in actions:
        action_group_id = str(action.metadata.get("group_id") or "").strip()
        if not action_group_id:
            raise ValueError("multi-issue remediation action missing group_id")
        if action_group_id not in group_ids:
            raise ValueError(f"remediation action group_id not found in issue_groups: {action_group_id}")
        covered_group_ids.add(action_group_id)

    required_group_ids = {
        str(group.get("group_id") or "").strip()
        for group in issue_groups
        if group.get("auto_fixable") is True or str(group.get("auto_fixable")).lower() == "true"
    }
    required_group_ids.discard("")
    missing = sorted(required_group_ids - covered_group_ids)
    if missing:
        raise ValueError(f"auto-fixable issue_groups missing remediation actions: {', '.join(missing)}")


def _build_action(data: Dict[str, Any]) -> RemediationAction:
    action = RemediationAction(
        id=str(data.get("id") or data.get("action_id") or "action"),
        type=str(data.get("type") or "kubectl"),
        description=str(data.get("description") or ""),
        risk=str(data.get("risk") or "medium"),
        dry_run_command=_optional_command(data.get("dry_run_command") or data.get("command")),
        execute_command=_optional_command(data.get("execute_command")),
        verify_command=_optional_command(data.get("verify_command")),
        metadata={k: v for k, v in data.items() if k not in {
            "id",
            "action_id",
            "type",
            "description",
            "risk",
            "dry_run_command",
            "command",
            "execute_command",
            "verify_command",
        }},
    )
    for command in (action.dry_run_command, action.execute_command, action.verify_command):
        if command:
            validate_safe_kubectl_command(command)
    if not action.execute_command and not action.verify_command and not action.dry_run_command:
        raise ValueError(f"remediation action '{action.id}' has no command")
    return action


def _optional_command(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def validate_safe_kubectl_command(command: str) -> None:
    if _SHELL_METACHARS.search(command):
        raise ValueError(f"unsafe remediation command: {command}")
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"unsafe remediation command: {command}") from exc
    if len(parts) < 2 or parts[0] != "kubectl" or parts[1] not in _ALLOWED_KUBECTL_VERBS:
        raise ValueError(f"unsafe remediation command: {command}")


def is_read_only_kubectl_command(command: str) -> bool:
    validate_safe_kubectl_command(command)
    parts = shlex.split(command)
    verb = parts[1]
    if verb in {"get", "describe", "logs", "top"}:
        return True
    return verb == "rollout" and len(parts) > 2 and parts[2] == "status"
