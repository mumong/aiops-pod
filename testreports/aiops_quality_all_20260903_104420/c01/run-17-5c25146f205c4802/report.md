## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (多次记录) | 明确展示调度失败的核心原因是标签/亲和性不匹配，而非资源不足。 |
| 2 | K8s State | Pod Status | `phase: Pending`, `PodScheduled: False` | 确认 Pod 处于持续无法调度的状态。 |
| 3 | K8s Config | pod.spec | `nodeSelector {aiops.lab/unavailable: true}` | 直接指出约束条件：Pod 强制要求节点拥有 `aiops.lab/unavailable: true` 标签。 |
| 4 | K8s Config | Container Resources | `cpu.request: 5m`, `cpu.limit: 50m`, `memory.request: 8Mi`, `memory.limit: 32Mi` | 排除资源超卖或配额限制导致调度的可能，资源要求极低。 |
| 5 | Metric | prometheus | `kube_pod_status_phase=1` (phase: Pending) | 量化确认该 Pod 在当前查询时刻仍处于 Pending 状态。 |

**证据总结：**
Kubernetes 事件（#1）和 Pod 状态（#2）共同证实了调度失败的现状。根本原因由 Pod 配置（#3）中的 `nodeSelector` 与集群节点标签不匹配所导致。资源配置数据（#4）排除了资源瓶颈，Metrics（#5）仅作为状态确认，未提供额外故障细节。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector {aiops.lab/unavailable: true} → 集群所有可用节点缺失该标签 → 调度器 FailedScheduling → Pod 持续 Pending
```

### 根因结论

已确认的根因为**Pod 调度约束与节点标签不匹配**。

1. **根因**：Pod `aiops-case-01/workload-68c557d875-llhkh` 定义了必须选择包含 `aiops.lab/unavailable: true` 标签的节点（证据 #3）。
2. **现象成因**：集群中的 3 个节点均未包含该标签，导致 `default-scheduler` 无法找到任何满足条件的节点进行绑定（证据 #1）。
3. **结果**：Pod 陷入 `Pending` 状态且 `nodeName` 为 `None`（证据 #2, #5）。

现有证据足以支撑此结论，无需更多工具输入。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.1s
├─ 并发证据采集: 53.5s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 53.5s (Evidence 45.0s, RCA 8.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
