# Research: Runbook Remediation Guidance

## Decision: Finalizer remediation is a scoped patch after confirmation

**Rationale**: Kubernetes finalizers intentionally block deletion until cleanup is
complete. A stuck resource with a confirmed non-empty finalizers list can be
unblocked by removing finalizers, but this bypasses the controller's cleanup
contract and must be branch-specific.

**Reference**: Kubernetes finalizers concept:
https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/

**Alternatives considered**:
- Recommend `kubectl delete --force` first: rejected because it is less scoped
  and can hide whether finalizers, node/kubelet, volume, or grace period is the
  actual branch.
- Tell the agent only to diagnose: rejected because the user needs repair-plan
  guidance for confirmed common cases.

## Decision: Force deletion is an emergency fallback, not the default

**Rationale**: Pod termination has a grace period and kubelet/container-runtime
cleanup semantics. Forcing deletion can remove the API object while work may
still be running or cleanup may be incomplete. Runbooks must place force delete
behind evidence prerequisites and safer actions.

**Reference**: Kubernetes Pod lifecycle and termination:
https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/

**Alternatives considered**:
- Omit force delete entirely: rejected because emergency operator fallback still
  exists and the agent should know its risk boundary.
- Put force delete in every branch: rejected because it encourages destructive
  generic repair.

## Decision: Keep remediation guidance compact and branch-driven

**Rationale**: The runbooks are prompt context. A short `## 标准修复建议` section
per runbook gives the model enough repair-ordering signal without turning the
ConfigMap into a full Kubernetes tutorial.

**References**:
- Images and image pull behavior:
  https://kubernetes.io/docs/concepts/containers/images/
- Private registry pull secret workflow:
  https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/
- Liveness/readiness/startup probes:
  https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Node-pressure eviction:
  https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/
- Taints and tolerations:
  https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
- Persistent volumes:
  https://kubernetes.io/docs/concepts/storage/persistent-volumes/

**Alternatives considered**:
- Add long command recipes for every possible Kubernetes failure: rejected
  because it bloats prompt context and increases conflicting advice.
- Change remediation executor code: rejected for this feature because the issue
  is model reference guidance, not action execution plumbing.

## Decision: Backup outside deployment-applied directories

**Rationale**: `make deploy` applies `deploy/` recursively. A backup ConfigMap in
that tree can be applied accidentally and overwrite the active `aiops-runbooks`
ConfigMap. Store backups under `docs/runbooks-backups/`.

**Alternatives considered**:
- Reuse `deploy/configmap/runbooks.bak.yaml`: rejected because it is inside the
  recursive deploy tree and currently also declares `name: aiops-runbooks`.
