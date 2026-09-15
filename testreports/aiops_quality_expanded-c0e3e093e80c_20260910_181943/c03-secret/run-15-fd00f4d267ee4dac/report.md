## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload (aiops-case-v04) stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `FailedMount 5m30s (x10 over 25m) ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 直接定位到卷挂载失败的具体错误及原因 |
| 2 | K8s State | `kubernetes` | `container.waiting_reason`: Container (app) is in `ContainerCreating` 状态 | 确认 Pod 容器启动前的阻塞状态 |
| 3 | K8s Config | `kubernetes` | Pod 资源请求/限制 (CPU: 5m/50m, Memory: 8Mi/32Mi) | 排除资源调度资源不足导致的 Pending 原因 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1 (reason: `ContainerCreating`) | 从监控指标层面印证 Pod 处于等待挂载的状态 |

**证据总结：**
`kubelet` 的 `FailedMount` 事件与 `kube_pod_container_status_waiting_reason` 指标共同证实，Pod 卡在 `ContainerCreating` 阶段是因为缺少关键依赖。配置检查排除了资源不足的可能性，确认为明确的资源缺失错误。

## 🎯 根因分析 · g1

```text
缺失 Secret 'unavailable-input' (namespace: aiops-case-v04) → Pod 卷 'input' 引用该 Secret 且未设置为 Optional → 导致 Kubelet 挂载卷失败 (FailedMount) → Pod 无法进入运行状态 (Pending/ContainerCreating)
```

**根因结论：**
已确认根因为 **Pod 引用的 Secret 不存在**。
Pod 定义中声明了一个名为 `input` 的卷，该卷指向 `unavailable-input` 这个 Secret。由于该 Secret 在 `aiops-case-v04` 命名空间中不存在，且卷挂载未配置为可选，导致 kubelet 无法完成卷挂载（`MountVolume.SetUp failed`）。这一上游原因直接引发了 `FailedMount` 错误，并最终导致 Pod 持续卡在 `ContainerCreating` 状态（见证据 1、2、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.8s
├─ 并发证据采集: 37.7s
│  └─ g1 aiops-case-v04/workload: 37.7s (Evidence 28.3s, RCA 9.2s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed, pod-config-error, pod-pending-unschedulable
