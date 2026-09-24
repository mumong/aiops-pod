"""Generic command transport checks, not a catalogue of repair strategies."""
import shlex
from dataclasses import dataclass
from app.core.remediation.execution_guard import DEFAULT_ALLOWED_EXEC_COMMANDS, DEFAULT_DENIED_EXECUTABLES


@dataclass(frozen=True)
class CommandPolicy:
    # Empty means no application operation allowlist. Explicit administrator
    # configuration still takes precedence over this default.
    allowed_operations: frozenset[str] = frozenset()
    denied_operations: frozenset[str] = frozenset()
    denied_executables: frozenset[str] = DEFAULT_DENIED_EXECUTABLES
    allowed_exec_commands: frozenset[str] = DEFAULT_ALLOWED_EXEC_COMMANDS

    @classmethod
    def from_config(cls, config):
        defaults = cls()
        values = {}
        for key in ("allowed_operations", "denied_operations", "denied_executables", "allowed_exec_commands"):
            value = config.get(key, getattr(defaults, key))
            if not isinstance(value, (list, tuple, set, frozenset)) or any(
                    not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError("workflow.remediation." + key + " 必须为非空字符串组成的列表")
            values[key] = frozenset(item.strip() for item in value)
        return cls(**values)


def validate_target_command(command, targets=(), policy=None):
    """Parse argv without interpreting resource types, fields or fault causes.

    targets is retained for compatibility, not a resource allowlist. Approval
    covers the exact commands. This transport is not a namespace sandbox.
    """
    policy = policy or CommandPolicy()
    args = shlex.split(command)
    if len(args) < 2 or args[0] != "kubectl":
        raise ValueError("仅支持单条 kubectl 命令，不执行本地主机 shell")
    if any(token in {";", "&&", "||", "|", ">", ">>", "<"} for token in args):
        raise ValueError("不支持 shell 管道或组合；请拆为可单独审阅的动作")
    connection_flags = {"--kubeconfig", "--context", "--cluster", "--server", "-s",
                        "--user", "--token", "--as", "--as-group", "--as-uid",
                        "--client-certificate", "--client-key", "--certificate-authority",
                        "--insecure-skip-tls-verify", "--tls-server-name"}
    prefix = args[1:args.index("--")] if "--" in args else args[1:]
    if any(arg.partition("=")[0] in connection_flags for arg in prefix):
        raise ValueError("命令不得切换集群或执行身份")
    words = []
    skip = False
    for arg in prefix:
        if skip:
            skip = False
            continue
        if arg in {"-n", "--namespace", "--request-timeout"}:
            skip = True
        elif not arg.startswith("-"):
            words.append(arg)
    if not words:
        raise ValueError("缺少 kubectl 操作")
    verb = words[0]
    operation = "_".join(words[:2]) if verb in {"set", "rollout"} else verb
    if verb == "config":
        raise ValueError("不允许修改服务自身的 Kubernetes 连接配置")
    if (verb in policy.denied_operations or operation in policy.denied_operations or
            (policy.allowed_operations and operation not in policy.allowed_operations)):
        raise ValueError("操作被管理员配置的命令策略限制")
    return args, operation
