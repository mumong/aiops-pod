"""Execution tools of the lightweight operate path: deny rules, run, audit - no approval.

Boss (2026-10-20): explicit instructions ("卸载 default/cloud-server", "用 helm 部署 xx",
"执行 xx") run directly on the focused route as ``task=operate``; the repair node stays
for diagnosed anomalies. The high-risk rules are the only gate here: a kubectl command
goes through the same ``CommandPolicy`` as a repair, any shell command is checked
against ``denied_executables``, and every attempt - run or denied - is written to the
repair audit with the caller and the command.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
from typing import Any, Callable, Dict, List, Optional

from app.core.remediation.audit import audit_event
from app.core.remediation.policy import CommandPolicy, check_command

WRITE_TOOLS = frozenset(
    {
        "run_bash_command",
        "kubectl_run_image",
        "helm_install",
        "helm_uninstall",
        "helm_upgrade",
        "helm_rollback",
    }
)
HELM_READ_TOOLS = frozenset(
    {
        "helm_list_releases",
        "helm_list",
        "helm_search_repo",
        "helm_values",
        "helm_status",
        "helm_history",
        "helm_manifest",
        "helm_hooks",
        "helm_chart",
        "helm_notes",
    }
)
_HELM_VERBS = {
    "helm_install": "install",
    "helm_uninstall": "uninstall",
    "helm_upgrade": "upgrade",
    "helm_rollback": "rollback",
}


def command_text(tool_name: str, args: Dict[str, Any]) -> str:
    """The command a tool call amounts to, for the rules and the audit line."""
    args = args or {}
    if tool_name == "run_bash_command":
        return str(args.get("command") or "").strip()
    if tool_name == "kubectl_run_image":
        inner = args.get("command") or []
        inner = (
            " ".join(shlex.quote(str(c)) for c in inner) if isinstance(inner, list) else str(inner)
        )
        return f"kubectl run {args.get('pod_name', '')} --image={args.get('image', '')} -n {args.get('namespace', '')} -- {inner}".strip()
    if tool_name in _HELM_VERBS:
        parts = ["helm", _HELM_VERBS[tool_name], str(args.get("release_name") or "")]
        if args.get("chart"):
            parts.append(str(args["chart"]))
        if args.get("namespace"):
            parts += ["-n", str(args["namespace"])]
        return " ".join(parts)
    return json.dumps(args, ensure_ascii=False)


def _executing_tokens(text: str) -> List[str]:
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        tokens = text.split()
    out: List[str] = []
    for token in tokens:
        out.append(token)
        if " " in token:  # a quoted sub-shell string: "ls; rm x" after sh -c
            inner = _executing_tokens(token)
            if inner != [token]:
                out.extend(inner)
    return out


def _blocked_executable(text: str, names) -> str:
    for token in _executing_tokens(text):
        for part in re.split(r"[;|&()]+", token):  # "ls;rm x" is two commands in one token
            base = os.path.basename(part.strip("\"'"))
            if not base:
                continue
            for name in names:
                if base == name or fnmatch.fnmatchcase(base, name):
                    return base
    return ""


def deny_reason(tool_name: str, args: Dict[str, Any], policy: CommandPolicy) -> str:
    """Non-empty when the high-risk rules reject this call; names the rule."""
    if tool_name not in WRITE_TOOLS:
        return ""
    command = command_text(tool_name, args)
    if tool_name == "run_bash_command":
        tokens = _executing_tokens(command)
        if tokens and os.path.basename(tokens[0]) == "kubectl":
            verdict = check_command(command, policy)
            if not verdict.allowed:
                return f"{verdict.rule}: {verdict.reason}"
    if tool_name in {"run_bash_command", "kubectl_run_image"}:
        blocked = _blocked_executable(command, policy.denied_executables)
        if blocked:
            return f"denied_executables: 命令 {blocked} 在高危名单中"
    return ""


def guard_write_tool(
    tool: Any,
    policy: CommandPolicy,
    *,
    principal: str = "",
    question: str = "",
    audit: Callable[..., Optional[Dict[str, Any]]] = audit_event,
) -> Any:
    """Wrap a write tool: deny by rule (never executed) or run and audit the outcome."""
    from langchain_core.tools import StructuredTool

    tool_name = str(getattr(tool, "name", "") or "")

    def _check(kwargs: Dict[str, Any]) -> Optional[str]:
        reason = deny_reason(tool_name, kwargs, policy)
        if not reason:
            return None
        audit(
            "execution_denied",
            tool=tool_name,
            command=command_text(tool_name, kwargs),
            rule=reason,
            principal=principal,
            question=question,
        )
        return json.dumps(
            {"success": False, "error": f"命令被高危规则拦截（{reason}），未执行"},
            ensure_ascii=False,
        )

    def _done(kwargs: Dict[str, Any], result: Any) -> Any:
        text = (
            result
            if isinstance(result, str)
            else json.dumps(result, ensure_ascii=False, default=str)
        )
        audit(
            "command_executed",
            tool=tool_name,
            command=command_text(tool_name, kwargs),
            result=text[:300],
            principal=principal,
            question=question,
        )
        return result

    async def _acoroutine(**kwargs: Any) -> Any:
        denied = _check(kwargs)
        if denied is not None:
            return denied
        return _done(kwargs, await tool.ainvoke(kwargs))

    def _func(**kwargs: Any) -> Any:
        denied = _check(kwargs)
        if denied is not None:
            return denied
        return _done(kwargs, tool.invoke(kwargs))

    wrapped = StructuredTool.from_function(
        func=_func,
        coroutine=_acoroutine,
        name=tool_name,
        description=getattr(tool, "description", "") or "",
        args_schema=getattr(tool, "args_schema", None),
        return_direct=getattr(tool, "return_direct", False),
        response_format="content",
    )
    wrapped.metadata = dict(getattr(tool, "metadata", None) or {})
    return wrapped
