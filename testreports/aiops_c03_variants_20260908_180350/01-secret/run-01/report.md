## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod volume 'input' 引用了不存在的 Secret 'unavailable-input'，导致 kubelet 挂载失败，Pod 处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount` (28s, x7) `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 直接确认 Secret 缺失导致挂载失败 |
| 2 | K8s Config | kubernetes | container `app` 配置: `cpu limit=50m, memory limit=32Mi`, `cpu request=5m, memory request=8Mi` | 排除资源不足导致调度/启动异常 |
| 3 | K8s State | kubernetes | Pod `phase: Pending`, `container.waiting_reason: ContainerCreating` | 确认 Pod 处于等待挂载资源阶段，未进入运行态 |
| 4 | K8s Event | kubernetes | `ContainersNotReady`: `containers with unready status: [app]` | 印证容器未成功启动 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 | 确认等待原因为 ContainerCreating |
| 6 | Metric | prometheus | `kube_pod_status_phase{container="app"}` = 1 (Pending), `restarts` = 0 | 确认 Pod 处于 Pending 且未重启 |

**证据分析**：K8s Event (证据 1) 提供决定性错误信息（Secret 缺失），K8s State (证据 3) 和 Metrics (证据 5) 均将 Pod 状态锁定在“等待/ContainerCreating”阶段，且重启计数为 0 (证据 6)，排除了应用运行失败。

## 🎯 根因分析 · g1

### 因果链
```text
Secret 'unavailable-input' 缺失 → kubelet 执行 MountVolume.SetUp 失败 → Pod 持续 Pending (ContainerCreating) → 容器未启动
```

### 根因结论
已确认根因：**Pod 配置引用了不存在的 Secret 'unavailable-input'**。
Kubelet 在挂载名为 'input' 的卷时因找不到 Secret 而失败，导致 Pod 容器无法启动，状态保持在 Pending。该结论由 `FailedMount` 事件 (证据 1) 及 Pod 等待状态 (证据 3, 5) 共同印证。

---

## 📊 性能统计

```text
├─ 总耗时: 59.0s
├─ 问题定位: 21.3s
├─ 并发证据采集: 29.9s
│  └─ g1 aiops-case-v04/workload: 29.8s (Evidence 24.3s, RCA 5.4s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed
