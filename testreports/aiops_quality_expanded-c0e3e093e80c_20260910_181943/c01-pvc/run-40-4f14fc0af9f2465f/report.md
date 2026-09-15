## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload stuck in Pending state since 50m ago |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 50m default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found...` (fact-1a526a6a1a7d) | 明确失败机制：调度器因找不到 PVC 拒绝调度。 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling 24m (x5 over 44m) default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found...` (fact-f15a9f32875b) | 确认该失败为持续性故障，且重试了多次。 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v03/workload` 状态：`Pending` (fact-f44de9f95e6f) | 确认可见现象为 Pod 停滞在 Pending 状态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 在 phase=Pending 的标签下值为 `1` (fact-a44d83266441) | 量化确认 Pod 当前处于 Pending 阶段。 |
| 5 | Metric | prometheus | `kube_pod_status_phase` 在 phase=Running 的标签下值为 `0` (fact-2750113fdc81) | 确认 Pod 从未成功进入 Running 阶段。 |

**证据印证：** K8s Event 提供了根本原因的精确描述（找不到 PVC `unavailable-claim`），解释了调度器为何在所有 3 个节点上均返回 `FailedScheduling`。K8s State 确认 Pod 处于 Pending 状态，而 Metric 数据进一步佐证了 Pod 长期处于非运行阶段（Pending 计数为 1，Running 为 0）。

## 🎯 根因分析 · g1

### 因果链
```text
PVC 'unavailable-claim' 不存在 → default-scheduler 调度阶段无法绑定卷 → 持续触发 FailedScheduling (0/3 nodes available) → Pod aiops-case-v03/workload 陷入 Pending 状态
```

### 根因结论
根因是 `aiops-case-v03` 命名空间中引用了缺失的 PersistentVolumeClaim `unavailable-claim`（证据 #1, #2）。由于该 PVC 不存在，Kubernetes 的 `default-scheduler` 在尝试分配 Pod 时无法完成卷绑定，导致在所有节点上调度失败（证据 #1, #2）。这一机制直接导致 Pod `aiops-case-v03/workload` 持续停留在 `Pending` 状态（证据 #3, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 48.6s
├─ 问题定位: 14.1s
├─ 并发证据采集: 25.3s
│  └─ g1 aiops-case-v03/workload: 25.3s (Evidence 18.5s, RCA 6.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
