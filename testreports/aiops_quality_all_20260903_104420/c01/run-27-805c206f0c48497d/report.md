## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod `aiops-case-01/workload-68c557d875-llhkh` 配置了 `nodeSelector: {aiops.lab/unavailable: true}`，该调度约束要求节点必须拥有 `aiops.lab/unavailable=true` 标签，但集群中全部 3 个节点（master, node1, node2）均未配置此标签，导致调度器无法满足亲和性条件，Pod 持续处于 `PendingUnschedulable` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling` (x8): `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认调度失败直接原因：节点不符合亲和性选择器条件。 |
| 2 | K8s State | Kubernetes | Pod 状态 `Pending`，`PodScheduled` 条件为 `False`，原因 `Unschedulable`。 | 确认 Pod 当前持续处于未调度状态。 |
| 3 | K8s Config | Kubernetes | 资源配置：Request `cpu=5m, memory=8Mi`；Limit `cpu=50m, memory=32Mi`。 | 证明 Pod 资源请求极低，调度失败并非由资源不足引起，而是策略限制。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{container="kube-state-metrics", phase="Pending"}` = `1`。 | 辅助确认集群内存在处于 Pending 状态的 Pod 样本。 |

调度器事件 `FailedScheduling` 指出 3 个节点均不匹配 Pod 的亲和性/选择器条件，结合低资源需求，排除了资源瓶颈，直指 `nodeSelector` 约束问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义配置了 nodeSelector: {aiops.lab/unavailable: true} → 集群节点（master, node1, node2）缺失该标签 → 调度器判定无可用节点 → Pod 持续处于 PendingUnschedulable 状态
```

### 根因结论

已确认根因为 **调度约束不匹配**。Pod `aiops-case-01/workload-68c557d875-llhkh` 强制要求节点必须拥有 `aiops.lab/unavailable: true` 标签（证据 #1, #2），但集群中所有节点均未配置此标签，导致调度器无法完成调度。Pod 自身的资源需求极低（CPU 5m/内存 8Mi），因此非资源不足导致（证据 #3）。

*注：无法判断是配置错误还是后续运维变更导致节点标签缺失（未知因素）。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.0s
├─ 并发证据采集: 49.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 49.2s (Evidence 39.4s, RCA 9.6s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- 未调用 Runbook
