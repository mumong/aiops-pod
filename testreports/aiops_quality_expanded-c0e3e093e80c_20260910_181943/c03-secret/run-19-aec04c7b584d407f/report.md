## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod引用了不存在的Secret 'unavailable-input'且未配置为可选，导致kubelet在挂载卷阶段阻塞 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v04/workload` phase: Pending, status: ContainerCreating, ContainersReady: False | 确认 Pod 停留在调度后的挂载卷阶段，未启动容器 |
| 2 | K8s Event | kubernetes | `FailedMount`: "MountVolume.SetUp failed for volume \"input\" : secret \"unavailable-input\" not found" | 直接指出卷挂载因 Secret 缺失而失败的根本原因 |
| 3 | K8s Event | kubernetes | `FailedMount`: "timed out waiting for the condition" (x23 over 32m) | 证明 kubelet 因同一阻塞原因持续重试，导致 Pod 长期 Pending |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating) | 独立观测确认容器处于等待状态，与 K8s 事件原因一致 |
| 5 | K8s State | kubernetes | Pod 无重启 (restart_count: 0)，且无应用日志 (logging: not_applicable) | 排除容器启动后因 CrashLoop 导致的问题，确认阻塞发生在启动前 |

证据表明，Kubernetes 事件与 Prometheus 指标均指向容器处于 `ContainerCreating` 的等待状态，且 `restart_count` 为 0 排除了运行时故障。具体的阻塞原因由 `FailedMount` 事件明确解释：Volume 挂载因引用的 Secret 不存在而超时。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用不存在的 Secret 'unavailable-input' → 卷挂载失败 (FailedMount) → kubelet 阻塞并持续重试 → Pod 状态卡在 Pending / ContainerCreating
```

### 根因结论

已确认的根因是 Pod `aiops-case-v04/workload` 引用了不存在的 Secret `unavailable-input` 且未配置为可选，导致 kubelet 在挂载卷阶段（证据 2, 3）发生 `FailedMount` 错误并陷入阻塞。这一故障直接导致容器无法启动，表现为 Pod 状态长期处于 `Pending` 且 `ContainersReady` 为 `False`（证据 1），同时伴随 `ContainerCreating` 的等待指标（证据 4）。由于阻塞发生在容器启动前，未产生应用日志或重启记录（证据 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.4s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-v04/workload: 30.6s (Evidence 26.4s, RCA 4.1s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable
