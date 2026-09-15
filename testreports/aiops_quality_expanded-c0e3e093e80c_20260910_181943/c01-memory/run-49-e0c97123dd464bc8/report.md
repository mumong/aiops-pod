## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod配置了不切实际的内存限制(1Pi)，导致调度器在所有3个集群节点上因'Insufficient memory'而持续调度失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling 5m6s (x14 over 70m) 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` | 证实集群内所有节点因内存不足导致 Pod 被调度器反复拒绝（已重复 14 次） |
| 2 | K8s Config | kubernetes | `resource_request.memory: 1Pi` (container: app) | 揭示 Pod 请求了 1 PetaByte 内存，远超物理节点容量，是触发调度失败的直接原因 |
| 3 | K8s Config | kubernetes | `resource_limit.memory: 1Pi` (container: app) | 证实 Pod 硬限制同样设置为 1Pi，属于不可实现的资源约束 |
| 4 | K8s State | kubernetes | `Pod Status: Pending` | 确认 Pod 当前未处于运行状态，停留在调度过渡期 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}=1` (sample_count: 1, timestamp: 2026-09-11T08:00:36.133000Z) | 独立确认 Pod 正处于 Pending 状态 |

**证据互证说明：**
证据 2、3 指出资源请求存在极端不合理数值，直接导致证据 1 中调度器报告节点资源不足；证据 4、5 的状态确认了该调度失败造成的持续性结果（Pending）。

## 🎯 根因分析 · g1

```text
Pod 配置 1Pi 内存限制与请求（事实 2,3） → 调度器判定集群所有节点无足够内存（事实 1） → 持续调度失败（事实 1） → Pod 处于 Pending 状态（事实 4,5）
```

**根因结论：**
根因确认为 **Pod 资源规格配置错误（内存 1Pi）**。
Pod 被配置了 `1Pi` 的内存请求与限制，这一数值远远超出物理集群节点的实际容量，导致 Kubernetes 调度器在所有 3 个节点上均计算为“内存不足”（`Insufficient memory`），从而引发持续调度失败及 Pod 长期处于 `Pending` 状态。

*   **事实支撑：** 证据 1 中的调度失败日志；证据 2、3 中的配置项值。

---

## 📊 性能统计

```text
├─ 总耗时: 54.4s
├─ 问题定位: 12.6s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-v02/workload: 33.4s (Evidence 29.8s, RCA 3.4s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
