## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 持续处于 Pending 状态，调度器返回 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-23bbddef2a42) | 明确调度器在评估亲和性/选择器时判定 3 个节点均不满足条件 |
| 2 | K8s Event | kubernetes | `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact-66bf6cf9911d) | 排除资源抢占干扰，直接指向标签/选择器不匹配问题 |
| 3 | K8s State | kubernetes | `node affinity/selector` 匹配失败 (fact-bca1370d5a9c) | 确认节点亲和性/选择器检查是 Pod 处于 Pending 状态的原因 |
| 4 | K8s Config | kubernetes | `Pod` 资源请求：`memory=8Mi`, `cpu=5m` (fact-9b938c77b55b) | 证明资源需求极低，排除因资源配额不足导致 0/3 节点不匹配的可能性 |
| 5 | Metric | prometheus | `kube_pod_status_phase` = 1, 标签包含 `phase: Pending` (fact-b169e7d4f3fd) | 独立观测确认 Pod 持续处于 Pending 状态 |

**证据印证说明**：Kubernetes 状态、事件与 Metric 均证实 Pod 卡在 Pending 阶段；事件明确将根因定位在 `node affinity/selector` 不匹配，而 `resource_request` 事实排除了资源资源不足的可能性，逻辑闭环完整。

## 🎯 根因分析 · g1

```text
Pod 定义中设置了不匹配的 nodeSelector 约束 (fact-23bbddef2a42) → 集群节点（3/3）未包含对应标签，不满足亲和性条件 → 调度器判定 0/3 节点满足调度需求，触发 FailedScheduling → Pod 持续处于 Pending 状态
```

**根因结论**：已确认的根因是 **Pod 的节点选择器（nodeSelector）或亲和性（affinity）要求与集群节点的标签不匹配**，导致调度器无法在任何节点（3/3）找到符合条件的目标，从而引发 Pod 持续 Pending。此结论主要由调度器返回的 `FailedScheduling` 事件（fact-23bbddef2a42, fact-66bf6cf9911d）及 `node affinity/selector` 状态（fact-bca1370d5a9c）直接支撑。

注：输入提供的 `supporting_fact_ids_hint` 中包含部分 ID（如 `fact-616672d13970`）在当前事实列表中未直接出现或为元数据标签，未作为主证据引用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.4s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 38.1s (Evidence 30.3s, RCA 7.7s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
