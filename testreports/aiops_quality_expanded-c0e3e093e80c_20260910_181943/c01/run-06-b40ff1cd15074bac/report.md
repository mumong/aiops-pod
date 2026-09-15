## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 (aiops-case-01) remains in Pending state with nodeName=None and condition PodScheduled=False due to FailedScheduling. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (events) | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-b1d006215ea0) | 明确调度失败的原因为节点亲和性或选择器不匹配 |
| 2 | K8s Config | kubernetes (state) | `container.resource_request.cpu: 5m`, `container.resource_request.memory: 8Mi` (fact-89f094fceaba) | 提供资源请求上下文，排除资源容量不足导致的调度失败 |
| 3 | Metric | prometheus (kube_pod_status_phase) | `phase: Pending, value: 1` (fact-258bc1327dbe) | 确认 Pod 目前处于 Pending 状态的事实 |

- **证据印证**：K8s 事件直接指明了失败机制是“节点亲和性/选择器不匹配”（#1）；资源请求极低（#2），排除了资源不足；Metric 数据（#3）证实了 Pod 卡在 Pending 阶段。三者结合指向明确的拓扑/标签匹配问题，而非资源瓶颈。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义了 nodeSelector/affinity 'aiops.lab/unavailable=true' → 集群中 master/node1/node2 均无该标签 → 0/3 节点匹配，调度器触发 FailedScheduling → Pod 处于 Pending 状态
```

### 根因结论
**已确认的根因**：Pod `workload-68c557d875-gtzc8` 被配置为仅调度到带有 `aiops.lab/unavailable=true` 标签的节点，但当前集群的 3 个节点（master, node1, node2）均不具备此标签，导致调度器评估 0/3 节点匹配，从而抛出 `FailedScheduling` 事件（#1）。Pod 因无法绑定到任何节点而保持在 Pending 状态（#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.0s
├─ 问题定位: 18.3s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 30.6s (Evidence 22.5s, RCA 7.9s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
