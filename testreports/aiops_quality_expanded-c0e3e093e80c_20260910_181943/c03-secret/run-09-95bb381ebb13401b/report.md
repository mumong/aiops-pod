## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod定义的Secret卷 'input' 引用了不存在的Secret 'unavailable-input'，且配置为Optional: false，导致VolumeMount失败，Pod卡在Pending/ContainerCreating状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount` 40s (x17 over 19m): MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接定位卷挂载失败原因：依赖的 Secret 不存在 |
| 2 | K8s Event | kubernetes | `Warning FailedMount` 72s (x8 over 17m): Unable to attach or mount volumes: unmounted volumes=[input] | 确认挂载超时及未挂载状态，佐证挂载失败持续发生 |
| 3 | K8s State | kubernetes | `pod.status`: Pending | 确认 Pod 整体调度完成但处于未运行状态 |
| 4 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认容器等待阶段，符合挂载阻塞时的标准状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: app, reason: ContainerCreating) = 1 | 从监控维度证实容器处于 ContainerCreating 等待态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` (container: app) = 0 | 确认容器未启动且未发生重启，排除因 CrashLoop 导致的异常 |

**证据说明：**
K8s Event 中的 `FailedMount` 错误明确指出了卷 `input` 因找不到 Secret `unavailable-input` 而挂载失败。这一状态与 K8s State 中 `Pending` 阶段和 `ContainerCreating` 等待原因一致，且被 Metric 中的 `waiting_reason` 和 `restarts=0` 独立证实，排除了容器启动后崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
引用了不存在的 Secret 'unavailable-input' (Optional: false) → 卷挂载失败 (FailedMount) → 容器无法启动 (ContainerCreating) → Pod 卡在 Pending 状态
```

### 根因结论

已确认根因为：Pod `aiops-case-v04/workload` 中定义的卷 `input` 引用了当前集群中不存在的 Secret `unavailable-input`，且配置为不可忽略的必选项，导致 Kubelet 无法挂载该卷。挂载失败直接阻塞了容器的启动过程，使 Pod 停滞在 `Pending` 状态且容器处于 `ContainerCreating` 等待态。

证据链包括：
1. **直接错误**：K8s Event 显示 `secret "unavailable-input" not found` 导致 `MountVolume.SetUp failed`（证据 1）。
2. **状态一致性**：Pod 状态为 `Pending`，容器等待原因为 `ContainerCreating`（证据 3, 4），且无重启记录（证据 6）。
3. **监控印证**：Metrics 确认容器处于 `ContainerCreating` 等待态且未重启（证据 5, 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.5s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-v04/workload: 38.1s (Evidence 31.7s, RCA 6.3s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
