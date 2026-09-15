## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload stuck in Pending phase |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `PodScheduled=False`, message: `0/3 nodes are available: 3 Insufficient memory` | 确认 Pod 处于 Unschedulable 状态，且集群内所有 3 个节点均因内存不足被拒绝 |
| 2 | K8s Event | kubernetes | `FailedScheduling` (x8 over 66m), `preemption: 0/3 nodes are available: 3 No preemption victims found` | 揭示调度器在尝试抢占后依然失败，证明请求的资源规模远超集群回收能力 |
| 3 | K8s Config | kubernetes | `container.app.resource_request.memory`: `1Pi`, `resource_limit.memory`: `1Pi` | 确立异常请求的具体数值，证实 Pod 定义的单实例内存需求为 1 Pebibyte |
| 4 | K8s Config | kubernetes | `container.app.resource_request.cpu`: `5m`, `resource_limit.cpu`: `50m` | 提供对比上下文：CPU 配置极低，进一步凸显内存请求的异常不合理性 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = `1`, `phase="Running"` = `0` | 从指标维度独立确认 Pod 持续处于 Pending 状态，无运行实例 |

**证据关联说明：**
K8s 事件（#2）解释了调度失败的根本原因（内存不足且无法抢占），状态（#1）和指标（#5）分别从控制面状态和监控侧证实了调度失败导致的 Pending 结果。配置信息（#3）提供了导致内存不足的具体量化依据（1Pi 远超常规集群容量）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义 1Pi 内存请求/限制 → 调度器计算节点可用内存无法满足 → 3 个节点均报 Insufficient memory → 抢占失败且无可用节点 → Pod 处于 Pending/Unschedulable 状态
```

### 根因结论

**已确认的根因：Pod 资源请求量级错误，单实例内存需求（1Pi）严重超出集群节点容量。**

根据 K8s 事件和状态事实，调度器因内存不足拒绝了 Pod，且由于内存请求量过大（1Pi），集群中不存在可作为“抢占受害者”的现有 Pod，导致预emption 完全失效。这一配置错误直接导致了 Pod 永远无法被调度。证据编号：#2, #3, #5。

---

## 📊 性能统计

```text
├─ 总耗时: 56.2s
├─ 问题定位: 14.4s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-v02/workload: 33.4s (Evidence 26.6s, RCA 6.7s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
