"""Deterministic Pod identity completion: the model selects targets, code binds identity.

Small models sometimes deliver a correct Pod target (name + UID) but omit its
namespace, which disqualified the whole location result from per-Pod lanes.
A UID is cluster-unique, so the namespace is resolved authoritatively from the
API server; a bare name is used only when it is unique across namespaces.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

_POD_INDEX_ARGV = [
    "kubectl",
    "get",
    "pods",
    "-A",
    "-o",
    'jsonpath={range .items[*]}{.metadata.namespace}{"\\t"}{.metadata.name}{"\\t"}{.metadata.uid}{"\\n"}{end}',
]


def _default_runner(argv: List[str]) -> str:
    from app.core.remediation.pod_executor import (
        run_argv,  # read-only kubectl get, in-cluster identity
    )

    return run_argv(argv)


def complete_pod_namespaces(
    entities: Iterable[Dict[str, Any]], runner: Optional[Callable[[List[str]], str]] = None
) -> int:
    """Fill missing namespaces of Pod entities in place; return how many were filled."""
    missing = [
        entity
        for entity in entities
        if isinstance(entity, dict)
        and str(entity.get("kind") or "").lower() == "pod"
        and not entity.get("namespace")
        and (entity.get("uid") or entity.get("name"))
    ]
    if not missing:
        return 0
    try:
        # Resolved at call time so tests (and operators) can substitute the index
        # source; a definition-time default silently read the live cluster.
        listing = (runner or _default_runner)(_POD_INDEX_ARGV)
    except Exception as exc:  # identity completion is best effort; caller keeps the serial path
        logger.warning("[pod_identity] Pod 命名空间补全失败: %s", exc)
        return 0
    by_uid: Dict[str, str] = {}
    by_name: Dict[str, set] = defaultdict(set)
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        namespace, name, uid = parts
        by_uid[uid] = namespace
        by_name[name].add(namespace)
    filled = 0
    for entity in missing:
        namespace = by_uid.get(str(entity.get("uid") or ""))
        if not namespace:
            candidates = by_name.get(str(entity.get("name") or ""), set())
            namespace = next(iter(candidates)) if len(candidates) == 1 else ""
        if namespace:
            entity["namespace"] = namespace
            filled += 1
    if filled:
        logger.info(
            "[pod_identity] 已按 UID/唯一名称补全 %d/%d 个 Pod 命名空间", filled, len(missing)
        )
    return filled
