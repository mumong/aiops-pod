"""Parse and validate remediation plans emitted by conclusion."""

from __future__ import annotations

import json
import re
import shlex
from typing import Any, Dict, Iterable, Optional

from app.core.remediation.models import RemediationAction, RemediationPlan


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.IGNORECASE | re.DOTALL)
_FACT_LEDGER_REMEDIATION_CONTRACTS = {
    "fact-ledger-authoritative-v1",
    "fact-ledger-diagnostic-only-v1",
}
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
_CONTROL_WHITESPACE_RE = re.compile(r"[\t\n\r\v\f]")
_PLACEHOLDER_VALUE_RE = re.compile(
    r"(?i)(?:=|:)(?:your[_-][A-Za-z0-9_-]*|replace[_-]?me|change[_-]?me|"
    r"placeholder|example[_-]?value|actual[_-]?value|token[_-]?value)(?:\s|$)"
)
_KUBECTL_GLOBAL_OPTIONS_WITH_VALUE = {
    "--as",
    "--as-group",
    "--cache-dir",
    "--certificate-authority",
    "--client-certificate",
    "--client-key",
    "--cluster",
    "--context",
    "--kubeconfig",
    "--namespace",
    "--request-timeout",
    "--server",
    "--tls-server-name",
    "--token",
    "--user",
    "--v",
    "--vmodule",
    "-n",
}
_KUBECTL_GLOBAL_BOOLEAN_OPTIONS = {
    "--disable-compression",
    "--insecure-skip-tls-verify",
    "--match-server-version",
    "--warnings-as-errors",
}


def extract_remediation_plan(text: str) -> Optional[RemediationPlan]:
    """Extract the canonical plan, or the first legacy plan when absent."""
    candidates = []
    fact_ledger_marker_present = False
    for candidate in _candidate_json_objects(text or ""):
        fact_ledger_marker_present = (
            fact_ledger_marker_present
            or _contains_fact_ledger_contract_marker(candidate)
        )
        data = _loads_json(candidate)
        if not isinstance(data, dict):
            continue
        if "remediation_plan" in data and isinstance(data.get("remediation_plan"), dict):
            data = data["remediation_plan"]
        if "remediation_available" not in data and "actions" not in data:
            continue
        candidates.append(data)

    if fact_ledger_marker_present:
        source = candidates[0] if candidates else {}
        return _build_plan({
            "remediation_available": False,
            "fix_type": "manual_only",
            "risk_level": "medium",
            "requires_human_approval": True,
            "issue_groups": _fact_ledger_issue_groups(source),
            "basis": [
                "Fact Ledger reports are diagnostic-only; executable "
                "writes require a typed policy contract."
            ],
            "actions": [],
            "stop_conditions": [],
        })

    for data in candidates:
        return _build_plan(data)
    return None


def _fact_ledger_issue_groups(data: Dict[str, Any]) -> list[Dict[str, Any]]:
    groups: list[Dict[str, Any]] = []
    for item in data.get("issue_groups") or []:
        if not isinstance(item, dict):
            continue
        group: Dict[str, Any] = {
            key: item[key]
            for key in (
                "group_id",
                "problem_type",
                "target",
                "strategy",
            )
            if item.get(key) not in (None, "")
        }
        for key, value in list(group.items()):
            if isinstance(value, str) and re.search(
                r"(?i)\bkubectl\b",
                value,
            ):
                group[key] = (
                    "[未授权的 Kubernetes 写操作已移除]"
                )
        group["auto_fixable"] = False
        groups.append(group)
    return groups


def _candidate_json_objects(text: str) -> Iterable[str]:
    for match in _JSON_FENCE_RE.finditer(text):
        yield match.group(1)
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        yield stripped


def _loads_json(raw: str) -> Any:
    def reject_duplicate_keys(
        pairs: list[tuple[str, Any]],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError):
        return None


def _contains_fact_ledger_contract_marker(raw: str) -> bool:
    marker_present = False

    def inspect_object(
        pairs: list[tuple[str, Any]],
    ) -> Dict[str, Any]:
        nonlocal marker_present
        for key, value in pairs:
            if (
                key == "remediation_contract"
                and value in _FACT_LEDGER_REMEDIATION_CONTRACTS
            ):
                marker_present = True
        return dict(pairs)

    try:
        json.loads(raw, object_pairs_hook=inspect_object)
    except json.JSONDecodeError:
        return False
    return marker_present


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
    if _CONTROL_WHITESPACE_RE.search(command) or _SHELL_METACHARS.search(command):
        raise ValueError(f"unsafe remediation command: {command}")
    if _PLACEHOLDER_VALUE_RE.search(command):
        raise ValueError(f"placeholder remediation value: {command}")
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"unsafe remediation command: {command}") from exc
    verb_index = _kubectl_verb_index(parts)
    if (
        verb_index is None
        or parts[verb_index].lower() not in _ALLOWED_KUBECTL_VERBS
    ):
        raise ValueError(f"unsafe remediation command: {command}")


def is_read_only_kubectl_command(command: str) -> bool:
    validate_safe_kubectl_command(command)
    parts = shlex.split(command)
    verb_index = _kubectl_verb_index(parts)
    if verb_index is None:
        return False
    verb = parts[verb_index].lower()
    if verb in {"get", "describe", "logs", "top"}:
        return True
    return (
        verb == "rollout"
        and len(parts) > verb_index + 1
        and parts[verb_index + 1].lower() == "status"
    )


def _kubectl_verb_index(parts: list[str]) -> Optional[int]:
    if not parts or parts[0].lower() != "kubectl":
        return None

    index = 1
    while index < len(parts) and parts[index].startswith("-"):
        option = parts[index]
        option_name = option.split("=", 1)[0].lower()
        if "=" in option:
            if (
                option_name not in _KUBECTL_GLOBAL_OPTIONS_WITH_VALUE
                and option_name not in _KUBECTL_GLOBAL_BOOLEAN_OPTIONS
            ):
                return None
            index += 1
            continue
        if option_name in _KUBECTL_GLOBAL_BOOLEAN_OPTIONS:
            index += 1
            continue
        if option_name not in _KUBECTL_GLOBAL_OPTIONS_WITH_VALUE:
            return None
        if index + 1 >= len(parts):
            return None
        index += 2

    return index if index < len(parts) else None
