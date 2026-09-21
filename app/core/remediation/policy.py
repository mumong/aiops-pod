"""Fail-closed command policy for exact, independently verified Pod targets.

This is execution authorization, not diagnostic reasoning. The caller supplies
targets verified from Kubernetes, never merely trusts model-declared owners.
"""
import json
import re
import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandPolicy:
    allowed_operations: frozenset[str] = frozenset({
        "get", "describe", "logs", "top", "rollout_status",
        "rollout_restart", "set_resources", "patch",
    })
    denied_operations: frozenset[str] = frozenset({
        "delete", "apply", "create", "exec", "replace", "drain", "cordon",
    })


def validate_target_command(command, targets, policy=None):
    """Return argv and operation; reject ambiguous scopes and unknown options."""
    policy = policy or CommandPolicy()
    if re.search(r"[\n\r\t;&|`$<>]", command):
        raise ValueError("禁止 shell 组合、替换或多行命令")
    args = shlex.split(command)
    if not args or args[0] != "kubectl":
        raise ValueError("修复仅允许受限 kubectl，不允许任意 shell")
    flags, words = {}, []
    allowed_flags = {"-n", "--namespace", "-o", "--output", "--dry-run",
                     "--limits", "--requests", "--containers", "--type", "-p", "--patch",
                     "--timeout", "--request-timeout", "--tail", "--since"}
    i = 1
    while i < len(args):
        value = args[i]
        if value.startswith("-"):
            flag, sep, data = value.partition("=")
            if flag not in allowed_flags or flag in flags:
                raise ValueError("命令包含禁止、未知或重复参数")
            if not sep:
                i += 1
                if i >= len(args) or args[i].startswith("-"):
                    raise ValueError("参数缺少值")
                data = args[i]
            flags[flag] = data
        else:
            words.append(value)
        i += 1
    namespaces = [flags[k] for k in ("-n", "--namespace") if k in flags]
    if len(namespaces) != 1 or not namespaces[0]:
        raise ValueError("必须且只能指定一个命名空间")
    if not words:
        raise ValueError("缺少操作")
    verb = words.pop(0)
    operation = verb
    if verb in {"set", "rollout"}:
        if not words:
            raise ValueError("缺少子操作")
        operation += "_" + words.pop(0)
    if verb in policy.denied_operations or operation in policy.denied_operations or operation not in policy.allowed_operations:
        raise ValueError("该操作不在修复白名单或命中黑名单")
    if len(words) == 1 and words[0].count("/") == 1:
        kind, name = words[0].split("/")
    elif len(words) == 2:
        kind, name = words
    else:
        raise ValueError("必须指定一个确切资源，不允许批量或选择器")
    aliases = {"pods": "pod", "deployments": "deployment", "deploy": "deployment",
               "statefulsets": "statefulset", "daemonsets": "daemonset", "replicasets": "replicaset"}
    kind = aliases.get(kind, kind)
    if kind not in {"pod", "deployment", "statefulset", "daemonset", "replicaset"}:
        raise ValueError("只允许已核实的 Pod 或所属工作负载")
    if (namespaces[0], kind, name) not in set(targets):
        raise ValueError("目标不属于当前已核实修复范围")
    if flags.get("--dry-run", "server") != "server":
        raise ValueError("dry-run 只允许 server，不能伪装为不执行")
    if sum(k in flags for k in ("-p", "--patch")) > 1:
        raise ValueError("重复 patch 参数")
    if operation == "patch":
        if flags.get("--type") != "json":
            raise ValueError("只允许可审计路径的 JSON Patch")
        patch = json.loads(flags.get("-p", flags.get("--patch", "null")))
        if not isinstance(patch, list) or not patch:
            raise ValueError("JSON Patch 不能为空")
        prefix = "/spec/containers/" if kind == "pod" else "/spec/template/spec/containers/"
        for item in patch:
            if not isinstance(item, dict) or item.get("op") not in {"test", "add", "replace"}:
                raise ValueError("禁止删除、移动或复制字段")
            path = str(item.get("path", ""))
            if not re.fullmatch(re.escape(prefix) + r"\d+/resources/(limits|requests)/(cpu|memory)", path):
                raise ValueError("默认 patch 仅允许容器 CPU/内存资源字段")
            if not isinstance(item.get("value"), str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?[a-zA-Z]*", item["value"]):
                raise ValueError("无效资源量")
    elif "-p" in flags or "--patch" in flags:
        raise ValueError("patch 参数与操作不匹配")
    return args, operation
