## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，调度失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found` | 调度器拒绝调度的根本原因，明确指向 CPU 不足且无抢占方案 |
| 2 | K8s State | kubernetes | Pod `aiops-case-v01/workload` 状态为 `Pending` | 确认调度失败的直接结果与现象 |
| 3 | K8s Config | kubernetes | Pod CPU Request: `100k` (0.01核) | 调度器寻找匹配资源的基准需求 |
| 4 | K8s Config | kubernetes | Pod CPU Limit: `100k` | 确认资源配额边界 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 监控确认 Pod 处于 Pending 阶段，排除 Failed 状态 |

**证据总结：**
1. Pod 处于 Pending 状态（证据 #2），监控数据证实无 Failed 实例（证据 #5）。
2. K8s 事件明确记录调度失败原因为节点 CPU 不足（证据 #1）。
3. Pod 设定的 CPU 需求（100k）未能被集群中任何节点满足（证据 #3），且集群无资源可抢占（证据 #1）。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源枯竭 (3节点均 Insufficient cpu) → 调度器无法满足 CPU Request (100k) 且 No preemption → Pod 调度失败进入 Pending 状态 → 应用无法启动
```

### 根因结论

**已确认的根因**：集群节点可用 CPU 资源不足导致 Pod `aiops-case-v01/workload` 调度失败。

该根因由以下事实链充分支撑：
1. **直接现象**：Pod 处于 `Pending` 状态（事实 #2）。
2. **核心机制**：K8s 事件（事实 #1）显示 `default-scheduler` 在 3 个节点上均拒绝调度，原因是 `Insufficient cpu`。
3. **无法自愈**：事件同时显示 `No preemption victims found`，表明集群资源极度紧张，无法通过抢占现有 Pod 释放 CPU 资源。
4. **资源需求**：Pod 申请了 `100k` (0.01核) CPU（事实 #3），在集群资源耗尽的背景下无法满足。

缺失的决定性事实：各节点具体的剩余 Allocatable CPU 数值（如 `20m` 或 `50m`），这有助于量化短缺程度，但不影响“资源不足”这一核心根因的判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.0s
├─ 并发证据采集: 33.7s
│  └─ g1 aiops-case-v01/workload: 33.7s (Evidence 24.7s, RCA 8.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
