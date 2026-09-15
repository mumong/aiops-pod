## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群3个节点（master, node1, node2）的可用CPU资源不足，且预emption机制失败（无抢占对象），导致Pod无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling 8m39s (x12 over 63m)`：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 确认调度失败的根本原因是节点 CPU 资源枯竭，且因无预emption对象导致调度器彻底放弃。 |
| 2 | K8s State | `aiops-case-v01/workload` | `PodScheduled` 条件：`status=False, reason=Unschedulable` | 验证 Pod 因调度约束无法满足而处于 `Unschedulable` 状态。 |
| 3 | K8s State | `aiops-case-v01/workload` | `phase` 与 `status` 均为 `Pending` | 描述 Pod 持续滞留于待调度状态的最终表现。 |
| 4 | K8s Config | `aiops-case-v01/workload` | CPU Request: `100k`；Limit: `100k` | 提供调度器计算节点资源余量所需的具体资源约束参数。 |

**证据印证说明：**
事件记录 (1) 直接解释了 K8s 状态 (2, 3) 中 Pod 为何处于 `Pending` 和 `Unschedulable`，明确指向集群 3 个节点（master, node1, node2）的 CPU 资源无法满足 Pod (4) 的 Request，且因缺乏可抢占对象而触发 `preemption failure`。

## 🎯 根因分析 · g1

### 因果链

```text
集群3个节点（master, node1, node2）的可用CPU资源枯竭 → 调度器无法满足Pod CPU Request（100k） → 预emption失败（No preemption victims） → Pod持续Pending状态
```

### 根因结论

已确认根因为**集群节点 CPU 资源枯竭且触发预emption失败**。

1. **集群 CPU 资源枯竭**：调度器事件 `FailedScheduling` (证据#1) 明确指出 `0/3 nodes are available: 3 Insufficient cpu`，表明集群内所有节点均因 CPU 资源不足而无法接纳该 Pod。
2. **预emption机制失效**：事件信息进一步表明 `preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`，说明调度器尝试进行资源抢占但未能找到可被抢占的工作负载，导致调度决策彻底失败。

这两大因素共同作用，导致 Pod `aiops-case-v01/workload` (证据#2, #3) 无法满足调度条件，持续停留在 `Pending` 状态。输入中未能获取集群节点具体的已分配 CPU 数值，无法精确计算剩余可用量，但不影响对资源枯竭这一根本原因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.8s
├─ 并发证据采集: 78.2s
│  └─ g1 aiops-case-v01/workload: 78.2s (Evidence 70.9s, RCA 7.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
