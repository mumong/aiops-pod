"""Where a Pod's spec is really owned: the top of its ownerReferences chain.

Kubernetes overwrites the spec of any object that has a controller owner: a
ReplicaSet's template is rewritten by its Deployment, a Job by its CronJob, a
Pod by whatever created it. A repair that edits an intermediate object therefore
looks accepted and changes nothing (live 2026-10-19, job ``fb639f92ad5c4a32``:
``kubectl patch replicaset workload-7bf9698f49`` succeeded, the Deployment kept
the old command, recovery timed out). The chain is read from the cluster with
read-only ``kubectl get`` calls and handed to planning as a fact; commands that
write to a managed member are rejected with the root controller named. No
workload kind is special-cased: the rule is "write where the controller writes".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.remediation.policy import _normalize_kind, check_command, named_resources

Runner = Callable[[str], str]

MAX_CHAIN_DEPTH = 6
READ_OPERATIONS = frozenset(
    {
        "get",
        "describe",
        "logs",
        "top",
        "explain",
        "events",
        "wait",
        "rollout_status",
        "rollout_history",
        "diff",
        "api-resources",
        "version",
    }
)


@dataclass(frozen=True)
class OwnerLink:
    kind: str  # Kubernetes kind as reported (Deployment, ReplicaSet, ...)
    name: str
    uid: str = ""

    @property
    def key(self) -> Tuple[str, str]:
        return _normalize_kind(self.kind), self.name

    def label(self) -> str:
        return f"{self.kind}/{self.name}"


@dataclass(frozen=True)
class ControllerChain:
    namespace: str
    links: List[OwnerLink] = field(default_factory=list)  # Pod first, root last
    complete: bool = True  # False when a lookup failed before reaching the top

    @property
    def pod(self) -> Optional[OwnerLink]:
        return self.links[0] if self.links else None

    @property
    def root(self) -> Optional[OwnerLink]:
        """The controller nobody else controls; ``None`` for a bare Pod."""
        return self.links[-1] if len(self.links) > 1 else None

    def managed_by(self, kind: str, name: str) -> Optional[OwnerLink]:
        """The direct controller of ``kind/name`` when it is a managed member of this chain."""
        key = (_normalize_kind(kind), name)
        for index, link in enumerate(self.links[:-1]):
            if link.key == key:
                return self.links[index + 1]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "namespace": self.namespace,
            "chain": [
                {"kind": link.kind, "name": link.name, "uid": link.uid} for link in self.links
            ],
            "root": self.root.label() if self.root else None,
            "complete": self.complete,
        }


def _get_json(runner: Runner, command: str) -> Optional[Dict[str, Any]]:
    text = runner(command)
    try:
        value = json.loads(text) if isinstance(text, str) else None
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _controller_ref(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    refs = ((obj.get("metadata") or {}).get("ownerReferences")) or []
    controllers = [r for r in refs if isinstance(r, dict) and r.get("controller")]
    chosen = (
        controllers[0]
        if controllers
        else (refs[0] if refs and isinstance(refs[0], dict) else None)
    )
    return chosen if chosen and chosen.get("kind") and chosen.get("name") else None


def resolve_controller_chain(
    namespace: str,
    pod: str,
    runner: Runner,
    *,
    max_depth: int = MAX_CHAIN_DEPTH,
) -> ControllerChain:
    """Walk ``ownerReferences`` from the Pod to the top; read-only, bounded, best effort."""
    links: List[OwnerLink] = []
    complete = True
    try:
        current = _get_json(runner, f"kubectl get pod/{pod} -n {namespace} -o json")
    except Exception:
        current = None
    if current is None:
        return ControllerChain(namespace=namespace, links=[OwnerLink("Pod", pod)], complete=False)
    links.append(OwnerLink("Pod", pod, str((current.get("metadata") or {}).get("uid") or "")))
    for _ in range(max_depth):
        ref = _controller_ref(current)
        if ref is None:
            break
        link = OwnerLink(str(ref["kind"]), str(ref["name"]), str(ref.get("uid") or ""))
        links.append(link)
        if "/" in str(ref.get("apiVersion") or "") and str(ref["kind"]).lower() == "node":
            break  # cluster-scoped owner: static Pods / mirror Pods stop here
        try:
            current = _get_json(
                runner,
                f"kubectl get {_normalize_kind(link.kind)}/{link.name} -n {namespace} -o json",
            )
        except Exception:
            current = None
        if current is None:
            complete = False
            break
    return ControllerChain(namespace=namespace, links=links, complete=complete)


def managed_write_error(command: str, chain: Optional[ControllerChain]) -> str:
    """Non-empty when ``command`` writes to a chain member that another controller rewrites."""
    if chain is None or not chain.links:
        return ""
    verdict = check_command(command)
    if verdict.operation in READ_OPERATIONS:
        return ""
    for kind, name in named_resources(command):
        if kind == "pod":
            continue  # pod_spec_immutable already explains Pods
        owner = chain.managed_by(kind, name)
        if owner is not None:
            root = chain.root.label() if chain.root else owner.label()
            return (
                f"{kind}/{name} 由 {owner.label()} 管理，对它的修改会被控制器覆盖、不会生效；"
                f"请把变更施加到最上层控制器 {root}"
            )
    return ""


def chains_for_targets(
    targets: List[Dict[str, Any]],
    runner: Runner,
) -> Dict[str, ControllerChain]:
    """``{"namespace/pod": chain}`` for every Pod entity in the diagnosis targets."""
    chains: Dict[str, ControllerChain] = {}
    for target in targets or []:
        for entity in (target or {}).get("entities") or []:
            if str((entity or {}).get("kind") or "").lower() != "pod":
                continue
            namespace, name = str(entity.get("namespace") or ""), str(entity.get("name") or "")
            if not namespace or not name:
                continue
            key = f"{namespace}/{name}"
            if key not in chains:
                chains[key] = resolve_controller_chain(namespace, name, runner)
    return chains
