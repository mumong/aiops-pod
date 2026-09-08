## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，持续 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `Warning FailedScheduling 35m... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确记录调度失败原因，指出节点亲和性/选择器不匹配导致 0/3 节点可用。 |
| 2 | K8s Config | pod.spec | `nodeSelector: {aiops.lab/unavailable: true}` | 提供具体的亲和性约束配置，作为判定调度失败的理论依据。 |
| 3 | K8s State | kubelet/k8s-api | `PodScheduled: False, reason: Unschedulable, message: 3 node(s) didn't match Pod's node affinity/selector` | 状态层面的直接证据，证实 Pod 因调度条件不满足而卡在 Pending 状态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 指标确认 Pod 持续处于 Pending 阶段，无 Succeeded 记录。 |

**证据关联说明：**
事件（#1）与状态消息（#3）共同指向同一失败机制：调度器在评估 3 个节点时，均发现它们不满足 Pod 的亲和性约束。配置事实（#2）提供了该约束的具体内容（`aiops.lab/unavailable: true`）。指标数据（#4）从监控维度证实了该 Pod 持续无法进入运行状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector {aiops.lab/unavailable: true} → 集群所有节点均缺少该标签 → 调度器判定 0/3 节点匹配 → Pod 持续 Pending 且未分配 nodeName
```

### 根因结论

**已确认根因**：Pod 的 `nodeSelector` 配置要求节点具有 `aiops.lab/unavailable: true` 标签，但集群中所有节点（3 个）均不满足此条件，导致调度器无法为 Pod 分配任何节点。

**证据支撑**：
- K8s 事件与状态消息均明确指出失败原因是 `node(s) didn't match Pod's node affinity/selector` (#1, #3)；
- Pod 配置事实显示其强制要求该特定标签 (#2)。

该结论逻辑闭环完整，无需补充其他维度的证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.4s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 43.9s (Evidence 35.9s, RCA 7.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
