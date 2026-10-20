"""Current facts a repair plan is written against, read once before planning.

The controller chain walk (``ownership``) already fetches the Pod and the object that
owns its spec. Their compact form goes to the planner so it can construct the command
without re-reading YAML: the write target's Pod template (containers, env references,
probes, resources, volumes), the Pod's own state (deletion, finalizers, container
states) and, for every Secret/ConfigMap the template references, whether it exists
and its key names. Values are never read: the go-template prints keys only, so a
plan cannot copy a secret and has to ask for a value it cannot see.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

Runner = Callable[[str], str]

CONTAINER_KEYS = (
    "name",
    "image",
    "command",
    "args",
    "workingDir",
    "ports",
    "env",
    "envFrom",
    "resources",
    "readinessProbe",
    "livenessProbe",
    "startupProbe",
    "volumeMounts",
    "securityContext",
)
_TEMPLATE_PATHS = (
    ("spec", "jobTemplate", "spec", "template", "spec"),  # CronJob
    ("spec", "template", "spec"),  # Deployment, StatefulSet, DaemonSet, ReplicaSet, Job
    ("spec",),  # Pod
)
MAX_CONFIG_REFS = 8
KEYS_TEMPLATE = "'go-template={{range $k, $v := .data}}{{println $k}}{{end}}'"
CONFIGMAP_KEYS_TEMPLATE = (
    "'go-template={{range $k, $v := .data}}{{println $k}}{{end}}"
    "{{range $k, $v := .binaryData}}{{println $k}}{{end}}'"
)


def _dig(obj: Dict[str, Any], path: Tuple[str, ...]) -> Any:
    for key in path:
        obj = obj.get(key) if isinstance(obj, dict) else None
    return obj


def _pod_spec(obj: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    for path in _TEMPLATE_PATHS:
        spec = _dig(obj, path)
        if isinstance(spec, dict) and isinstance(spec.get("containers"), list):
            return ".".join(path), spec
    return "", {}


def _containers(items: Any) -> List[Dict[str, Any]]:
    return [
        {k: c[k] for k in CONTAINER_KEYS if k in c} for c in items or [] if isinstance(c, dict)
    ]


def spec_digest(obj: Dict[str, Any]) -> Dict[str, Any]:
    """What a patch to ``obj`` needs: identity, rollout counters and the Pod template."""
    if not isinstance(obj, dict):
        return {}
    metadata, status = obj.get("metadata") or {}, obj.get("status") or {}
    path, spec = _pod_spec(obj)
    digest: Dict[str, Any] = {
        "kind": obj.get("kind"),
        "name": metadata.get("name"),
        "namespace": metadata.get("namespace"),
        "generation": metadata.get("generation"),
        "observed_generation": status.get("observedGeneration"),
        "replicas": (obj.get("spec") or {}).get("replicas"),
        "ready_replicas": status.get("readyReplicas"),
        "deletion_timestamp": metadata.get("deletionTimestamp"),
        "finalizers": list(metadata.get("finalizers") or []),
        "template_path": path,
        "containers": _containers(spec.get("containers")),
        "init_containers": _containers(spec.get("initContainers")),
        "volumes": [v for v in spec.get("volumes") or [] if isinstance(v, dict)],
        "termination_grace_period_seconds": spec.get("terminationGracePeriodSeconds"),
    }
    return {k: v for k, v in digest.items() if v not in (None, [], "")}


def pod_state(pod: Dict[str, Any]) -> Dict[str, Any]:
    """The Pod's current phase, deletion state and container states."""
    if not isinstance(pod, dict):
        return {}
    metadata, status = pod.get("metadata") or {}, pod.get("status") or {}
    containers = [
        {
            k: c.get(k)
            for k in ("name", "ready", "restartCount", "state", "lastState")
            if c.get(k) not in (None, {})
        }
        for c in [
            *(status.get("initContainerStatuses") or []),
            *(status.get("containerStatuses") or []),
        ]
        if isinstance(c, dict)
    ]
    state = {
        "phase": status.get("phase"),
        "reason": status.get("reason"),
        "deletion_timestamp": metadata.get("deletionTimestamp"),
        "deletion_grace_period_seconds": metadata.get("deletionGracePeriodSeconds"),
        "finalizers": list(metadata.get("finalizers") or []),
        "containers": containers,
    }
    return {k: v for k, v in state.items() if v not in (None, [], "")}


def referenced_configs(digest: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Secrets and ConfigMaps the Pod template reads, sorted, without duplicates."""
    refs = set()
    for container in [*(digest.get("containers") or []), *(digest.get("init_containers") or [])]:
        for env in container.get("env") or []:
            source = (env or {}).get("valueFrom") or {}
            for key, kind in (("secretKeyRef", "Secret"), ("configMapKeyRef", "ConfigMap")):
                if (source.get(key) or {}).get("name"):
                    refs.add((kind, source[key]["name"]))
        for env_from in container.get("envFrom") or []:
            for key, kind in (("secretRef", "Secret"), ("configMapRef", "ConfigMap")):
                if ((env_from or {}).get(key) or {}).get("name"):
                    refs.add((kind, env_from[key]["name"]))
    for volume in digest.get("volumes") or []:
        if (volume.get("configMap") or {}).get("name"):
            refs.add(("ConfigMap", volume["configMap"]["name"]))
        if (volume.get("secret") or {}).get("secretName"):
            refs.add(("Secret", volume["secret"]["secretName"]))
    return sorted(refs)


def config_refs(
    namespace: str, refs: List[Tuple[str, str]], runner: Runner
) -> List[Dict[str, Any]]:
    """Existence and key names of each referenced object; values are never fetched."""
    found = []
    for kind, name in refs[:MAX_CONFIG_REFS]:
        template = KEYS_TEMPLATE if kind == "Secret" else CONFIGMAP_KEYS_TEMPLATE
        try:
            text = runner(f"kubectl get {kind.lower()}/{name} -n {namespace} -o {template}")
        except Exception as exc:
            missing = "NotFound" in str(exc)  # other failures (RBAC, timeout) stay unknown
            found.append(
                {
                    "kind": kind,
                    "name": name,
                    "exists": False if missing else None,
                    "error": str(exc)[:300],
                }
            )
            continue
        keys = sorted({line.strip() for line in str(text or "").splitlines() if line.strip()})
        found.append({"kind": kind, "name": name, "exists": True, "keys": keys})
    return found
