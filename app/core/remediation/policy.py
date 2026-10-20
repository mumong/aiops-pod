"""Named command rules for the repair executor: deny by default, explain every refusal.

The engine only inspects the shape of a single ``kubectl`` command (verb, flags,
resource kind, in-container executable). It never looks at fault types, fields or
manifests, so new Pods and new failure classes need no rule changes. Planning,
execution and the ``/repair/policy/check`` endpoint share ``check_command``.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.core.remediation.execution_guard import (
    DEFAULT_ALLOWED_EXEC_COMMANDS,
    DEFAULT_DENIED_EXECUTABLES,
    RepairCommandDenied,
    check_repair_execution,
)

__all__ = [
    "CommandPolicy",
    "CommandVerdict",
    "RepairCommandDenied",
    "check_command",
    "named_resources",
    "validate_target_command",
    "active_policy",
    "use_policy",
]

# kubectl verbs that cannot be reviewed as one bounded change (arbitrary manifests,
# bulk/cluster operations, interactive or host-level access). Operators may narrow or
# widen this through ``workflow.remediation.denied_operations``.
DEFAULT_DENIED_OPERATIONS = frozenset(
    {
        "delete",
        "apply",
        "replace",
        "edit",
        "run",
        "debug",
        "drain",
        "cordon",
        "uncordon",
        "taint",
        "cp",
        "port-forward",
        "proxy",
        "attach",
        "auth",
        "certificate",
    }
)
# Force / bulk switches: a reviewed command names one object, never "all".
DEFAULT_DENIED_FLAGS = frozenset(
    {
        "--force",
        "--grace-period",
        "--all",
        "--all-namespaces",
        "-A",
        "--now",
        "--cascade",
        "--overwrite",
    }
)
# Writes to these kinds change cluster-wide or security posture; reads stay allowed.
DEFAULT_DENIED_RESOURCE_KINDS = frozenset(
    {
        "node",
        "namespace",
        "clusterrole",
        "clusterrolebinding",
        "role",
        "rolebinding",
        "persistentvolume",
        "storageclass",
        "customresourcedefinition",
        "mutatingwebhookconfiguration",
        "validatingwebhookconfiguration",
        "apiservice",
        "priorityclass",
        "certificatesigningrequest",
    }
)
READ_ONLY_OPERATIONS = frozenset(
    {
        "get",
        "describe",
        "logs",
        "top",
        "explain",
        "events",
        "wait",
        "diff",
        "api-resources",
        "api-versions",
        "version",
        "auth_can-i",
        "rollout_status",
        "rollout_history",
    }
)
_KIND_ALIASES = {
    "no": "node",
    "ns": "namespace",
    "pv": "persistentvolume",
    "sc": "storageclass",
    "crd": "customresourcedefinition",
    "crds": "customresourcedefinition",
    "csr": "certificatesigningrequest",
    "pc": "priorityclass",
    "sa": "serviceaccount",
    "deploy": "deployment",
    "sts": "statefulset",
    "ds": "daemonset",
    "rs": "replicaset",
    "svc": "service",
    "cm": "configmap",
    "po": "pod",
}
_CONNECTION_FLAGS = frozenset(
    {
        "--kubeconfig",
        "--context",
        "--cluster",
        "--server",
        "-s",
        "--user",
        "--token",
        "--as",
        "--as-group",
        "--as-uid",
        "--client-certificate",
        "--client-key",
        "--certificate-authority",
        "--insecure-skip-tls-verify",
        "--tls-server-name",
    }
)
_SHELL_OPERATORS = frozenset({";", "&&", "||", "|", ">", ">>", "<"})
_VALUE_FLAGS = frozenset(
    {
        "-n",
        "--namespace",
        "--request-timeout",
        "-o",
        "--output",
        "-p",
        "--patch",
        "--type",
        "-f",
        "--filename",
        "--timeout",
        "-c",
        "--container",
    }
)
_SELECTOR_FLAGS = frozenset({"-l", "--selector", "--field-selector"})
_TRANSPORT_RULES = {
    "transport.kubectl_only": "仅支持单条 kubectl 命令，不执行本地主机 shell",
    "transport.no_shell_operators": "不支持 shell 管道、重定向或组合；请拆为可单独审阅的动作",
    "transport.no_identity_override": "命令不得切换集群、身份或修改服务自身的连接配置",
}


@dataclass(frozen=True)
class CommandVerdict:
    """Outcome of one policy check; ``rule`` is empty when allowed."""

    command: str
    allowed: bool
    operation: str = ""
    rule: str = ""
    reason: str = ""
    argv: Tuple[str, ...] = ()
    # Allowed only after a person approves this exact command (approval_required).
    requires_approval: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "allowed": self.allowed,
            "operation": self.operation,
            "rule": self.rule,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
        }


@dataclass(frozen=True)
class CommandPolicy:
    # Empty means no application operation allowlist. Explicit administrator
    # configuration still takes precedence over these defaults; deny always wins.
    allowed_operations: frozenset = frozenset()
    denied_operations: frozenset = DEFAULT_DENIED_OPERATIONS
    denied_flags: frozenset = DEFAULT_DENIED_FLAGS
    denied_resource_kinds: frozenset = DEFAULT_DENIED_RESOURCE_KINDS
    bulk_selector_on_write: bool = True
    denied_executables: frozenset = DEFAULT_DENIED_EXECUTABLES
    allowed_exec_commands: frozenset = DEFAULT_ALLOWED_EXEC_COMMANDS
    # workflow.remediation.approval_required: denied like the lists above, except a
    # repair may run them after a person approves the exact command (also in auto mode).
    approval_operations: frozenset = frozenset()
    approval_resource_kinds: frozenset = frozenset()
    approval_executables: frozenset = frozenset()
    extra: Dict[str, Any] = field(default_factory=dict, compare=False)

    _LIST_KEYS = (
        "allowed_operations",
        "denied_operations",
        "denied_flags",
        "denied_resource_kinds",
        "denied_executables",
        "allowed_exec_commands",
    )

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]]) -> "CommandPolicy":
        config = config if isinstance(config, dict) else {}
        defaults = cls()
        values: Dict[str, Any] = {}
        for key in cls._LIST_KEYS:
            value = config.get(key, getattr(defaults, key))
            if not isinstance(value, (list, tuple, set, frozenset)) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValueError("workflow.remediation." + key + " 必须为非空字符串组成的列表")
            values[key] = frozenset(item.strip() for item in value)
        bulk = config.get("bulk_selector_on_write", defaults.bulk_selector_on_write)
        if not isinstance(bulk, bool):
            raise ValueError("workflow.remediation.bulk_selector_on_write 必须为布尔值")
        values["bulk_selector_on_write"] = bulk
        values["denied_resource_kinds"] = frozenset(
            _normalize_kind(kind) for kind in values["denied_resource_kinds"]
        )
        approval = config.get("approval_required") or {}
        if not isinstance(approval, dict):
            raise ValueError("workflow.remediation.approval_required 必须为映射")
        for key, field_name in (
            ("operations", "approval_operations"),
            ("resource_kinds", "approval_resource_kinds"),
            ("executables", "approval_executables"),
        ):
            items = approval.get(key) or []
            if not isinstance(items, (list, tuple)) or any(
                not isinstance(item, str) or not item.strip() for item in items
            ):
                raise ValueError(f"workflow.remediation.approval_required.{key} 必须为字符串列表")
            values[field_name] = frozenset(
                _normalize_kind(i) if key == "resource_kinds" else i.strip() for i in items
            )
        return cls(**values)

    def strict(self) -> "CommandPolicy":
        """The same policy with approval_required treated as denied (chat, no approval)."""
        return replace(
            self,
            denied_operations=self.denied_operations | self.approval_operations,
            denied_resource_kinds=self.denied_resource_kinds | self.approval_resource_kinds,
            denied_executables=self.denied_executables | self.approval_executables,
            approval_operations=frozenset(),
            approval_resource_kinds=frozenset(),
            approval_executables=frozenset(),
        )

    @property
    def has_approval_rules(self) -> bool:
        return bool(
            self.approval_operations or self.approval_resource_kinds or self.approval_executables
        )

    def summary(self) -> Dict[str, Any]:
        """Operator-facing view of every active rule (what the check endpoint reports)."""
        return {
            "transport": dict(_TRANSPORT_RULES),
            "denied_operations": sorted(self.denied_operations),
            "allowed_operations": sorted(self.allowed_operations),
            "denied_flags": sorted(self.denied_flags),
            "bulk_selector_on_write": self.bulk_selector_on_write,
            "denied_resource_kinds": sorted(self.denied_resource_kinds),
            "denied_executables": sorted(self.denied_executables),
            "allowed_exec_commands": sorted(self.allowed_exec_commands),
            "read_only_operations": sorted(READ_ONLY_OPERATIONS),
            # Display view: what a person reads as "the blacklist".
            "kubernetes": {
                "commands": sorted(self.denied_operations),
                "resources": sorted(self.denied_resource_kinds),
                "batch": sorted(self.denied_flags)
                + (
                    ["-l/--selector/--field-selector（写操作）"]
                    if self.bulk_selector_on_write
                    else []
                ),
            },
            "shell": sorted(self.denied_executables),
            "approval_required": {
                "kubernetes": sorted(self.approval_operations | self.approval_resource_kinds),
                "shell": sorted(self.approval_executables),
            },
        }


# The policy every unparameterised check uses: set from workflow.remediation at startup
# so planning, ownership checks, execution and the published rules are one set.
_ACTIVE: Optional[CommandPolicy] = None


def use_policy(policy: Optional[CommandPolicy]) -> None:
    global _ACTIVE
    _ACTIVE = policy


def active_policy() -> CommandPolicy:
    """The configured policy; the built-in defaults only when no configuration was loaded."""
    return _ACTIVE or CommandPolicy()


def _normalize_kind(token: str) -> str:
    kind = token.strip().lower()
    if "." in kind:  # resource.group form
        kind = kind.split(".", 1)[0]
    kind = _KIND_ALIASES.get(kind, kind)
    if kind.endswith("ies"):
        kind = kind[:-3] + "y"
    elif kind.endswith("sses") or kind.endswith("ches") or kind.endswith("xes"):
        kind = kind[:-2]
    elif kind.endswith("s") and not kind.endswith("ss"):
        kind = kind[:-1]
    return _KIND_ALIASES.get(kind, kind)


def _split_prefix(args: List[str]) -> List[str]:
    return args[1 : args.index("--")] if "--" in args else args[1:]


def _words_and_flags(prefix: Iterable[str]) -> Tuple[List[str], List[str]]:
    """Positional words (verb, resource...) and bare flag names in order."""
    words: List[str] = []
    flags: List[str] = []
    skip = False
    for arg in prefix:
        if skip:
            skip = False
            continue
        if arg.startswith("-"):
            name, has_value, _ = arg.partition("=")
            flags.append(name)
            if not has_value and name in _VALUE_FLAGS | _SELECTOR_FLAGS:
                skip = True
        else:
            words.append(arg)
    return words, flags


def _resource_kinds(words: List[str], operation: str) -> List[str]:
    """Kinds named positionally: ``kind/name``, ``kind name`` or ``kind name1 name2``."""
    start = 2 if operation.startswith(("set_", "rollout_")) else 1
    kinds: List[str] = []
    for token in words[start:]:
        if "/" in token:
            kinds.append(_normalize_kind(token.split("/", 1)[0]))
        elif not kinds:
            kinds.append(_normalize_kind(token))
        else:
            break  # names after the kind
    return kinds


def named_resources(command: str) -> List[Tuple[str, str]]:
    """``(kind, name)`` pairs a kubectl command names positionally; empty when unparsable.

    Identity helper for validators (e.g. "the Deployment in the command must be the
    Pod's owner"); it does not judge the operation.
    """
    try:
        args = shlex.split(command or "")
    except ValueError:
        return []
    if len(args) < 2 or args[0] != "kubectl":
        return []
    words, _ = _words_and_flags(_split_prefix(args))
    if not words:
        return []
    verb = words[0]
    operation = (
        "_".join(words[:2]) if verb in {"set", "rollout", "auth"} and len(words) > 1 else verb
    )
    start = 2 if operation.startswith(("set_", "rollout_", "auth_")) else 1
    pairs: List[Tuple[str, str]] = []
    kind = ""
    for token in words[start:]:
        if "/" in token:
            k, _, name = token.partition("/")
            pairs.append((_normalize_kind(k), name))
        elif not kind:
            kind = _normalize_kind(token)
        else:
            pairs.append((kind, token))
    return pairs


def _patch_payload_error(args: List[str]) -> str:
    """Well-formedness of ``kubectl patch -p/--patch`` payloads, checked before approval.

    A payload the API server will reject (live: a hand-written strategic merge with
    a missing bracket) must fail at planning, where the model can fix it, not after
    a human approved it. Only JSON syntax and the json-patch op shape are checked;
    the content of the change is the reviewer's call.
    """
    if len(args) < 2 or args[1] != "patch" and "patch" not in args[1:3]:
        return ""
    patch_type = "strategic"
    payload = None
    for index, arg in enumerate(args):
        name, has_value, value = arg.partition("=")
        if name in {"-p", "--patch"}:
            payload = value if has_value else (args[index + 1] if index + 1 < len(args) else None)
        elif name == "--type":
            patch_type = (
                value if has_value else (args[index + 1] if index + 1 < len(args) else "")
            ).strip("'\"")
    if payload is None:
        return ""
    try:
        parsed = json.loads(payload)
    except ValueError as exc:
        return f"patch 内容不是合法 JSON（{exc.msg}，位置 {exc.pos}）；请修正后重新提交"
    if patch_type == "json":
        if not isinstance(parsed, list) or not all(
            isinstance(op, dict)
            and isinstance(op.get("op"), str)
            and isinstance(op.get("path"), str)
            for op in parsed
        ):
            return "--type=json 的 patch 必须是 [{op, path, value?}] 操作列表"
    elif not isinstance(parsed, dict):
        return f"--type={patch_type} 的 patch 必须是 JSON 对象"
    return ""


# Pod spec fields the API server lets you change in place (everything else is immutable).
_POD_MUTABLE_JSON_PATHS = re.compile(
    r"^/spec/(?:(?:containers|initContainers)/\d+/image|tolerations(?:/.*)?|activeDeadlineSeconds|terminationGracePeriodSeconds)$"
)


def _pod_spec_mutation_error(args: List[str], operation: str, words: List[str]) -> str:
    """A write that edits a running Pod's spec will be refused by Kubernetes.

    Pod spec is immutable except image, tolerations (additions), activeDeadlineSeconds
    and terminationGracePeriodSeconds; env, command, probes, resources, volumes must be
    changed on the controller template. Catching this at planning sends the model to
    the Deployment/StatefulSet instead of letting a reviewer approve a doomed command
    (live: `kubectl patch pod ... /spec/containers/0/env/-` -> "Forbidden").
    """
    kinds = _resource_kinds(words, operation)
    if "pod" not in kinds:
        return ""
    hint = "Pod 的 spec（env/command/探针/资源/卷等）不可原地修改；请对其控制器（Deployment/StatefulSet 等）的 Pod 模板执行变更"
    if operation in {
        "set_env",
        "set_resources",
        "set_selector",
        "set_serviceaccount",
        "set_subject",
    }:
        return hint
    if operation != "patch":
        return ""
    patch_type, payload = "strategic", None
    for index, arg in enumerate(args):
        name, has_value, value = arg.partition("=")
        if name in {"-p", "--patch"}:
            payload = value if has_value else (args[index + 1] if index + 1 < len(args) else None)
        elif name == "--type":
            patch_type = (
                value if has_value else (args[index + 1] if index + 1 < len(args) else "")
            ).strip("'\"")
    if payload is None:
        return ""
    try:
        parsed = json.loads(payload)
    except ValueError:
        return ""  # malformed_patch already reports syntax
    if patch_type == "json" and isinstance(parsed, list):
        bad = [
            op.get("path")
            for op in parsed
            if isinstance(op, dict)
            and str(op.get("path", "")).startswith("/spec")
            and not _POD_MUTABLE_JSON_PATHS.match(str(op.get("path", "")))
        ]
        return f"{hint}（路径 {', '.join(map(str, bad))}）" if bad else ""
    if isinstance(parsed, dict) and isinstance(parsed.get("spec"), dict):
        spec = parsed["spec"]
        for key, value in spec.items():
            if key in {"activeDeadlineSeconds", "terminationGracePeriodSeconds", "tolerations"}:
                continue
            if (
                key in {"containers", "initContainers"}
                and isinstance(value, list)
                and all(isinstance(c, dict) and set(c) <= {"name", "image"} for c in value)
            ):
                continue
            return f"{hint}（spec.{key}）"
    return ""


_APPROVAL_RULES = frozenset({"denied_operations", "denied_resource_kinds", "denied_executables"})


def check_command(command: str, policy: Optional[CommandPolicy] = None) -> CommandVerdict:
    """Evaluate every rule; the first violated rule names the verdict.

    A command that passes, but would be denied once approval_required counts as denied,
    is allowed with ``requires_approval`` and rule ``approval_required``.
    """
    policy = policy or active_policy()
    verdict = _evaluate(command, policy)
    if not verdict.allowed or not policy.has_approval_rules:
        return verdict
    strict = _evaluate(command, policy.strict())
    if strict.allowed or strict.rule not in _APPROVAL_RULES:
        return verdict
    return replace(
        verdict,
        rule="approval_required",
        reason=f"需人工审批的高危命令（{strict.reason}）",
        requires_approval=True,
    )


def _evaluate(command: str, policy: CommandPolicy) -> CommandVerdict:
    def deny(
        rule: str, reason: str, operation: str = "", argv: Tuple[str, ...] = ()
    ) -> CommandVerdict:
        return CommandVerdict(command, False, operation, rule, reason, argv)

    try:
        args = shlex.split(command or "")
    except ValueError:
        return deny("transport.kubectl_only", "命令引号或参数格式无法可靠解析")
    if len(args) < 2 or args[0] != "kubectl":
        return deny("transport.kubectl_only", _TRANSPORT_RULES["transport.kubectl_only"])
    if any(token in _SHELL_OPERATORS for token in args):
        return deny(
            "transport.no_shell_operators", _TRANSPORT_RULES["transport.no_shell_operators"]
        )
    prefix = _split_prefix(args)
    if any(arg.partition("=")[0] in _CONNECTION_FLAGS for arg in prefix):
        return deny(
            "transport.no_identity_override", _TRANSPORT_RULES["transport.no_identity_override"]
        )
    words, flags = _words_and_flags(prefix)
    if not words:
        return deny("transport.kubectl_only", "缺少 kubectl 操作")
    verb = words[0]
    if verb == "config":
        return deny(
            "transport.no_identity_override", _TRANSPORT_RULES["transport.no_identity_override"]
        )
    operation = (
        "_".join(words[:2]) if verb in {"set", "rollout", "auth"} and len(words) > 1 else verb
    )
    argv = tuple(args)

    if verb in policy.denied_operations or operation in policy.denied_operations:
        return deny("denied_operations", f"操作 {operation} 在高危命令黑名单中", operation, argv)
    if policy.allowed_operations and operation not in policy.allowed_operations:
        return deny(
            "allowed_operations", f"操作 {operation} 不在管理员允许的操作白名单中", operation, argv
        )

    hit = sorted(set(flags) & set(policy.denied_flags))
    if hit:
        return deny(
            "denied_flags",
            f"参数 {' '.join(hit)} 属于强制或批量操作，不可审阅为单一变更",
            operation,
            argv,
        )

    write = operation not in READ_ONLY_OPERATIONS and verb not in READ_ONLY_OPERATIONS
    if write and policy.bulk_selector_on_write and set(flags) & _SELECTOR_FLAGS:
        return deny(
            "bulk_selector_on_write",
            "写操作不得使用标签/字段选择器批量命中对象，请指定单个对象",
            operation,
            argv,
        )
    if write:
        kinds = _resource_kinds(words, operation)
        blocked = [kind for kind in kinds if kind in policy.denied_resource_kinds]
        if blocked:
            return deny(
                "denied_resource_kinds",
                f"不允许修改集群级或安全敏感资源：{', '.join(blocked)}",
                operation,
                argv,
            )

    patch_error = _patch_payload_error(args)
    if patch_error:
        return deny("malformed_patch", patch_error, operation, argv)
    if write:
        immutable = _pod_spec_mutation_error(args, operation, words)
        if immutable:
            return deny("pod_spec_immutable", immutable, operation, argv)

    try:
        check_repair_execution(args, policy)
    except RepairCommandDenied as exc:
        rule = (
            "allowed_exec_commands"
            if "allowed_exec_commands" in str(exc)
            else "denied_executables"
        )
        return deny(rule, str(exc), operation, argv)
    return CommandVerdict(command, True, operation, "", "", argv)


def validate_target_command(command, targets=(), policy=None):
    """Compatibility entry: returns ``(argv, operation)`` or raises ``RepairCommandDenied``.

    ``targets`` is retained for callers; approval covers the exact commands and
    this transport is not a namespace sandbox.
    """
    verdict = check_command(command, policy)
    if not verdict.allowed:
        raise RepairCommandDenied(verdict.reason, rule=verdict.rule)
    return list(verdict.argv), verdict.operation
