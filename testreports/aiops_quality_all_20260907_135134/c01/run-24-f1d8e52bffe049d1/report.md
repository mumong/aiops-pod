## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，无法被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling` 警告: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认调度失败的直接原因：没有节点匹配亲和性/选择器。 |
| 2 | K8s State | Kubernetes | `PodScheduled` 条件状态为 `False`，原因 `Unschedulable`。 | 证实 Pod 被调度器拒绝。 |
| 3 | K8s State | Kubernetes | Pod 状态持续为 `Pending`。 | 描述当前 Pod 处于不可调度的停滞状态。 |
| 4 | K8s Config | Kubernetes | 资源限制较低：CPU `50m` / 内存 `32Mi`。 | 证明 Pod 资源请求极小，通常应易于调度，排除资源不足导致的 Pending。 |

证据表明，Pod 处于 Pending 状态且被调度器拒绝，但资源限制极低且未触及容量瓶颈，调度失败完全归因于节点的标签匹配失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义 nodeSelector: {"aiops.lab/unavailable": "true"} → 集群 3 个节点均无此标签 → Scheduler 拒绝调度 (FailedScheduling) → Pod 处于 Pending 状态
```

### 根因结论

**根因确认**：调度失败的根本原因是 Pod 定义了不存在的节点选择器（`aiops.lab/unavailable=true`），导致集群中所有节点均无法匹配。证据来自 K8s Event `FailedScheduling` 明确指出未匹配亲和性/选择器，且资源限制（`50m` CPU/`32Mi` 内存）极低，排除了资源不足的可能 [1, 2]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.1s
├─ 并发证据采集: 39.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 39.3s (Evidence 31.8s, RCA 7.4s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
