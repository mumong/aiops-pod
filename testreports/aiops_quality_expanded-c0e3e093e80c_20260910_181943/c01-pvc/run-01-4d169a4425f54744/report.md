## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload is stuck in Pending state with FailedScheduling status. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 64s default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 明确调度器因找不到 PVC 而拒绝分配，提供了直接的根因证据。 |
| 2 | K8s State | kubernetes | `PodScheduled: False, reason: Unschedulable, message: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found...` | 证实 Pod 处于 Unschedulable 状态，其失败消息与 Event 完全一致，进一步确认 PVC 丢失是阻塞点。 |
| 3 | K8s State | kubernetes | `phase: Pending, status: Pending` | 证实 Pod 当前未分配节点，符合 PVC 缺失导致的挂起状态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase=1` (labels: `{container: kube-state-metrics, phase: Pending}`, sample_count: 1) | 通过监控指标证实该 Pod 持续处于 Pending 状态。 |

**证据关联说明**：Kubernetes Event (#1) 与 Pod Condition (#2) 互为表里，共同指向 `unavailable-claim` 缺失是调度器无法分配节点的直接原因；Metric 数据 (#4) 提供了客观的时序状态佐证。由于 Pod 未启动，Logging 和 Tracing 维度无数据。

## 🎯 根因分析 · g1

### 因果链

```text
PVC 'unavailable-claim' 在 'aiops-case-v03' 命名空间不存在 → 调度器无法绑定存储卷，触发 Unschedulable 拒绝调度 → Pod 保持 Pending 状态，无法绑定到任何节点 → 容器 'app' 永远无法启动
```

### 根因结论

已确认的根因是：**Pod 规范中引用的 PVC 'unavailable-claim' 在当前命名空间下不存在**。

该缺失资源导致 Kubernetes 调度器在尝试分配节点时触发 `FailedScheduling` 事件（证据 #1、#2），使 Pod 状态永久停留在 `Pending`（证据 #3、#4）。现有证据链完整，足以确立此结论，无需进一步排查其他维度。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 27.8s
├─ 并发证据采集: 30.3s
│  └─ g1 aiops-case-v03/workload: 30.3s (Evidence 23.5s, RCA 6.7s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
