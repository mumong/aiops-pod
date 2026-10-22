"""Which kubectl invocations may run on a remote cluster, and in which mode.

The xnet tunnel carries one buffered HTTP request (20 s cap), so streaming,
interactive and local-file commands cannot work remotely; credential flags are
refused so a caller cannot switch identity. Shared by the shim (fail fast at
the center) and the runner (enforced at the edge).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

READ_VERBS = frozenset(
    {
        "get",
        "describe",
        "logs",
        "top",
        "explain",
        "events",
        "api-resources",
        "api-versions",
        "version",
    }
)
READ_ROLLOUT = frozenset({"history"})
UNSUPPORTED_VERBS = frozenset(
    {"port-forward", "proxy", "attach", "cp", "edit", "wait", "debug", "diff"}
)
CREDENTIAL_FLAGS = frozenset(
    {
        "--kubeconfig",
        "--context",
        "--cluster",
        "--server",
        "-s",
        "--token",
        "--as",
        "--as-group",
        "--as-uid",
        "--user",
        "--username",
        "--password",
        "--certificate-authority",
        "--client-certificate",
        "--client-key",
        "--insecure-skip-tls-verify",
        "--tls-server-name",
    }
)
# Global flags that take a separate value and may precede the verb.
VALUE_FLAGS = frozenset({"-n", "--namespace", "--request-timeout", "-v", "--v"})


def _flag_name(token: str) -> str:
    return token.split("=", 1)[0]


def _kubectl_part(argv: List[str]) -> List[str]:
    """Arguments that belong to kubectl itself (everything before ``--``)."""
    return argv[: argv.index("--")] if "--" in argv else list(argv)


def _verb(tokens: List[str]) -> Tuple[str, List[str]]:
    skip = False
    for i, token in enumerate(tokens):
        if skip:
            skip = False
            continue
        if token.startswith("-"):
            skip = token in VALUE_FLAGS
            continue
        return token, tokens[i + 1 :]
    return "", []


def dry_run(argv: List[str]) -> Optional[str]:
    """``client`` / ``server`` when the kubectl command is a dry run, else None."""
    for token in _kubectl_part(argv[1:]):
        if token in ("--dry-run=client", "--dry-run=server"):
            return token.split("=", 1)[1]
    return None


def classify(argv: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Return (mode, None) with mode in read/exec/write, or (None, reason)."""
    if not argv or argv[0] != "kubectl":
        return None, "only kubectl commands can run on a remote cluster"
    own = _kubectl_part(argv[1:])
    flags = {_flag_name(t) for t in own if t.startswith("-")}
    if flags & CREDENTIAL_FLAGS:
        return (
            None,
            f"credential or identity flags are not allowed: {sorted(flags & CREDENTIAL_FLAGS)}",
        )
    verb, rest = _verb(own)
    if not verb:
        return None, "missing kubectl subcommand"
    if verb in UNSUPPORTED_VERBS or (verb == "rollout" and rest[:1] == ["status"]):
        return (
            None,
            f"kubectl {verb} is not supported on a remote cluster (needs a long-lived connection)",
        )
    if flags & {"-f", "--follow"} and verb == "logs":
        return None, "log follow (-f/--follow) is not supported on a remote cluster"
    if flags & {"-w", "--watch", "--watch-only"}:
        return None, "watch (-w/--watch) is not supported on a remote cluster"
    if flags & {"-i", "-t", "-it", "-ti", "--stdin", "--tty"}:
        return None, "interactive sessions (-i/-t) are not supported on a remote cluster"
    if flags & {"-f", "--filename", "-k", "--kustomize"}:
        return None, "manifests from a local file (-f/-k) are not supported on a remote cluster"
    if verb in READ_VERBS or (verb == "rollout" and rest[:1] and rest[0] in READ_ROLLOUT):
        return "read", None
    if verb == "auth" and rest[:1] == ["can-i"]:
        return "read", None
    if verb == "exec":
        return "exec", None
    if dry_run(argv):
        # A dry run never persists a change: client dry runs only read, server dry runs
        # are evaluated (RBAC, admission, validation) and discarded. Repair preflight
        # uses them before a plan is approved; the runner picks the identity.
        return "read", None
    return "write", None
