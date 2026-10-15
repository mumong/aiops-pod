"""Small repair-only guard for explicit executable names, not a shell sandbox.

Does not inspect manifests or prescribe Kubernetes repair operations. Only
literal simple shell commands are supported inside kubectl exec/run.
"""
import fnmatch
import shlex
from pathlib import PurePosixPath

DEFAULT_DENIED_EXECUTABLES = frozenset({"rm"})
# Empty disables the optional executable allowlist; explicit deny still wins.
DEFAULT_ALLOWED_EXEC_COMMANDS = frozenset()


class RepairCommandDenied(ValueError):
    """Expected policy refusal; never an actual command execution failure."""


def check_repair_execution(args, policy):
    """Check all explicit executable positions; never substring-match data."""
    denied = policy.denied_executables
    allowed = policy.allowed_exec_commands

    def reject(reason):
        raise RepairCommandDenied("修复命令未执行：" + reason)

    def shell_script(script, depth):
        # Deliberately no expansion, interpretation, loops, redirects or scripts.
        if any(c in script for c in ("$", "`", "\\")):
            reject("动态或转义 shell 语法无法可靠检查，请改用明确的单条命令")
        lexer = shlex.shlex(script, posix=True, punctuation_chars=";&|<>()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        lexer.commenters = ""
        segment = []
        for token in list(lexer) + [";"]:
            if token in {";", "&&", "||", "|", "\n"}:
                if segment:
                    executable(segment, depth + 1)
                    segment = []
            elif token and all(c in ";&|<>()\n" for c in token):
                reject("不支持重定向、后台执行或复杂 shell 语法")
            else:
                segment.append(token)

    def executable(argv, depth=0):
        if depth > 8 or not argv or not argv[0]:
            reject("嵌套命令过深或执行目标不明确")
        name = PurePosixPath(argv[0]).name
        if any(fnmatch.fnmatchcase(name, pattern) for pattern in denied):
            reject("命中 denied_executables：" + name)
        if name in {"sh", "bash", "dash", "ash"}:
            if len(argv) != 3 or argv[1] not in {"-c", "-lc", "-ec", "-ce"}:
                reject("仅支持可直接检查的 shell -c 字面量命令")
            shell_script(argv[2], depth + 1)
        elif name in {"env", "command", "busybox"}:
            # Only unambiguous wrappers; flags/assignments are intentionally not
            # interpreted. An operator can extend the executable allowlist.
            if len(argv) < 2 or argv[1].startswith("-") or "=" in argv[1]:
                reject("包装命令参数无法可靠检查")
            executable(argv[1:], depth + 1)
        elif allowed and name not in allowed:
            reject("容器内命令不在 allowed_exec_commands：" + name)

    try:
        if not args or args[0] != "kubectl":
            reject("修复执行入口仅允许 kubectl")
        front = args[1:args.index("--")] if "--" in args else args[1:]
        # kubectl global flags may precede the verb. The transport validator
        # already rejects connection overrides; consume common value options.
        words, skip = [], False
        for arg in front:
            if skip:
                skip = False
            elif arg in {"-n", "--namespace", "--request-timeout"}:
                skip = True
            elif not arg.startswith("-"):
                words.append(arg)
        verb = words[0] if words else ""
        if verb in {"exec", "run", "debug"}:
            if "--" in args:
                executable(args[args.index("--") + 1:])
            elif verb == "exec":
                reject("kubectl exec 必须用 -- 明确分隔容器命令")
    except RepairCommandDenied:
        raise
    except (ValueError, TypeError):
        reject("命令引号或参数格式无法可靠检查")
