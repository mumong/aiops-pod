## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 33m 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确记录调度失败的直接原因是节点亲和性/选择器不匹配。 |
| 2 | K8s Config | kubernetes | `container.resource_request.cpu: 5m, memory: 8Mi; limit: cpu 50m, memory 32Mi` | 排除资源配额（CPU/Memory）不足的可能性，证明 Pod 规格极低。 |
| 3 | K8s State | kubernetes | `PodScheduled: False (Unschedulable), Phase: Pending` | 确认 Pod 长时间停滞在 Pending 状态，且调度条件不满足。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 持续为 1 (Pending)，无其他状态样本 | 确认故障状态持续存在，未自动恢复或发生状态漂移。 |

**证据关联说明：**
Kubernetes Event (证据 #1) 明确指向“节点未匹配亲和性/选择器”，而资源配置 (证据 #2) 证明这不是资源瓶颈。Metric (证据 #4) 佐证了该状态是持续性的。结合已知的节点拓扑事实，所有 3 个节点均缺乏 Pod 定义中要求的 `aiops.lab/unavailable: 'true'` 标签，构成了唯一的调度阻碍。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了 nodeSelector {'aiops.lab/unavailable': 'true'} → 集群所有 3 个节点 (master, node1, node2) 均无该标签 → 调度器计算匹配节点数为 0 → Pod 持续 Pending，未分配节点
```

### 根因结论
已确认根因为 **节点标签配置缺失**。
Pod 定义强制要求节点必须包含标签 `aiops.lab/unavailable: 'true'`，但集群现有的 3 个节点均缺少该标签，导致 `default-scheduler` 无法找到满足亲和性/选择器条件的节点。该问题属于配置与集群环境不匹配，而非资源短缺。证据来源：事实 `fact-ae3c501d9511` (调度失败事件) 及 `fact-00873442197d` (调度状态)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 36.6s
├─ 并发证据采集: 60.3s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 60.3s (Evidence 50.2s, RCA 9.9s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
