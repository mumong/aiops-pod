# Pod Abnormal Status Agent Design

## Goal

`/ask` 诊断主线从“泛 L0-L4 运维分层”调整为“Pod 异常状态优先”。`L0-L4` 保留为兼容字段，但含义变为 Pod 异常状态的归因分类。

## Core Model

主分类顺序固定为：

1. 识别当前仍异常的 Pod。
2. 提取用户可见状态 `pod_status_keyword`。
3. 归一化为诊断异常类型 `pod_abnormal_type`。
4. 派生兼容字段 `derived_layer` 和 `layer`。

## Pod Abnormal Types

| pod_abnormal_type | Typical signals | derived_layer |
|---|---|---|
| `Evicted` | Evicted, ephemeral-storage, DiskPressure, MemoryPressure | `L0` |
| `VolumeMountFailed` | FailedMount, FailedAttachVolume, PVC/PV/NFS/CSI errors | `L0` |
| `PendingUnschedulable` | Pending, FailedScheduling, insufficient resources, taint, nodeSelector, affinity | `L1` |
| `NodeLostOrUnknown` | Pod Unknown, Node NotReady, kubelet not reporting | `L1` |
| `TerminatingStuck` | long Terminating, finalizer, kubelet/volume detach stuck | `L1` |
| `OOMKilled` | Last State OOMKilled, Exit Code 137 | `L2` |
| `CrashLoopBackOffRuntime` | CrashLoopBackOff with process/command/runtime exit, non-137 | `L2` |
| `ImagePullFailed` | ImagePullBackOff, ErrImagePull, registry timeout, auth, image missing | `L3` |
| `SandboxCreateFailed` | FailedCreatePodSandBox, CNI, sandbox runtime failure | `L3` |
| `ConfigError` | CreateContainerConfigError, missing ConfigMap/Secret/env | `L4` |
| `NotReadyProbeFailed` | Running but NotReady, readiness/liveness/startup probe failed | `L4` |

`CrashLoopBackOff` is a status keyword, not a final type. Evidence decides whether it becomes `OOMKilled`, `CrashLoopBackOffRuntime`, or `ConfigError`.

## Workflow Impact

The four-node workflow remains unchanged:

- `layer`: becomes the Pod status classifier. It still writes `layer` for compatibility and additionally writes `derived_layer`, `status_category`, `primary_pod`, `abnormal_pods`, `pod_status_keyword`, and `pod_abnormal_type`.
- `evidence`: plans around `primary_pod + pod_status_keyword + pod_abnormal_type`, not generic L0-L4.
- `rca`: treats evidence facts as the main source and uses `derived_layer` only as a compatibility grouping.
- `conclusion`: reports Pod abnormal status first, then shows the compatible layer.

## Runbooks

Runtime catalog should expose Pod abnormal-status runbooks. Existing L0-L4 IDs may remain for backward compatibility, but their descriptions must describe the Pod abnormal type they diagnose.

Disabled runbooks such as generic private health baselines and non-Pod dependency runbooks remain disabled for `/ask`.

## Success Criteria

- Prompts explicitly define the 11 Pod abnormal types and derived layer mapping.
- `layer_handoff` includes `derived_layer` and `status_category`.
- Runtime catalog exposes Pod abnormal mainline runbooks.
- Existing query direct behavior remains unchanged.
