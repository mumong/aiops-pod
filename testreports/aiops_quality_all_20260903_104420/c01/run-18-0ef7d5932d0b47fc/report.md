## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了 nodeSelector `aiops.lab/unavailable=true`，但集群中所有可用节点均不包含该标签，导致调度器无法找到匹配节点，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-01/workload-68c557d875-llhkh` | `status=Pending`, `phase=Pending`，条件 `PodScheduled=False` (原因 `Unschedulable`) | 确认 Pod 处于不可调度状态 |
| 2 | K8s Config | Pod Spec | `nodeSelector` 包含键 `aiops.lab/unavailable=true` | 明确导致调度的过滤条件 |
| 3 | K8s Event | `default-scheduler` | 连续 3 次 `FailedScheduling`，详细消息均指出 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认调度失败的具体机制是节点标签不匹配 |

证据说明：Kubernetes 事件（#3）直接复现了状态（#1）的不可调度原因，而原因的根本来源在于配置的节点选择器（#2）。集群内所有节点（3个）均不满足该选择器条件，导致物理上的无节点匹配。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector `aiops.lab/unavailable=true`（配置事实） → 集群所有可用节点均缺失该标签，调度器过滤失败（机制） → Pod 无法找到匹配节点持续调度（直接失败） → Pod 保持 Pending 状态（用户可见现象）
```

### 根因结论

已确认根因：Pod `aiops-case-01/workload-68c557d875-llhkh` 的调度配置（`nodeSelector`）要求节点具备标签 `aiops.lab/unavailable=true`，但当前集群内所有节点均未包含此标签（证据 #3）。这导致 Kubernetes 调度器无法为该 Pod 找到符合条件的节点，从而使其持续处于 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.7s
├─ 并发证据采集: 50.3s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 50.3s (Evidence 45.2s, RCA 4.9s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
