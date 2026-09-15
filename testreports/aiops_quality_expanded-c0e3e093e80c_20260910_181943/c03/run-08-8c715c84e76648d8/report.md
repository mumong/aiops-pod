## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 中的 volume `input` 引用了不存在的 ConfigMap `unavailable-config` (Optional: false)，导致 kubelet 挂载失败，Pod 持续处于 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending` | 确认为阻塞状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 确认处于挂载尝试阶段 |
| 3 | K8s Config | kubernetes | `volume.input` 引用 `ConfigMap` `unavailable-config` | 指向挂载目标缺失 |
| 4 | K8s Event | kubernetes | `FailedMount: configmap "unavailable-config" not found` (x17) | 证实挂载失败的确切原因是 ConfigMap 缺失 |
| 5 | K8s Event | kubernetes | `FailedMount: unmounted volumes=[input]` (x8) | 提供历史重试与阻塞的佐证 |
| 6 | Metric | prometheus | `kube_pod_status_phase: Pending=1` | 与 K8s 状态一致 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason: ContainerCreating=1` | 与 K8s 状态一致 |

证据表明，Pod 因为 `configmap "unavailable-config" not found` 导致 `volume.input` 挂载一直失败。Metric 数据的 Pending 与 ContainerCreating 状态与 K8s 事件和状态完全吻合，确认阻塞在启动前的挂载环节。

## 🎯 根因分析 · g1

```text
ConfigMap unavailable-config 缺失 → kubelet 挂载 volume input 失败 → 容器持续等待挂载 (ContainerCreating) → Pod 处于 Pending 状态
```

**根因结论**
已确认根因为 **Pod 挂载不存在的 ConfigMap**。
证据 #4 直接指出了 `configmap "unavailable-config" not found` 的错误，结合证据 #3 确认该卷为必填配置，导致 Pod 被 kubelet 阻塞在挂载阶段，无法启动容器，最终表现为 Pending 状态（证据 #1, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 55.2s
├─ 问题定位: 23.7s
├─ 并发证据采集: 24.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 24.7s (Evidence 20.7s, RCA 3.9s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
