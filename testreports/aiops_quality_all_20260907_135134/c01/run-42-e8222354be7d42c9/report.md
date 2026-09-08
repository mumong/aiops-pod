## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，节点分配为 <none> |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling. (fact-7a390071f4c7) | 解释调度失败的直接原因：节点亲和性/选择器不匹配 |
| 2 | K8s State | kubernetes | pod.status: Pending (fact-8802f9de4c16) | 确认 Pod 最终状态，与 FailedScheduling 事件一致 |
| 3 | Metric | prometheus | kube_pod_status_phase{phase="Pending"} = 1 (fact-941ab66c0fde) | 从监控维度确认 Pod 持续处于 Pending 状态，排除瞬时波动 |

## 🎯 根因分析 · g1

### 因果链

```text
Pod 部署配置定义了 NodeSelector: aiops.lab/unavailable=true → 集群节点 (master, node1, node2) 缺少标签 aiops.lab/unavailable=true → Scheduler 因节点亲和性不匹配拒绝调度 (3 node(s) didn't match Pod's node affinity/selector) → Pod 保持 Pending 状态且 node=<none>
```

### 根因结论

已确认的根因是**调度器因节点亲和性不匹配拒绝调度**（证据 #1）。Pod 定义中要求节点包含标签 `aiops.lab/unavailable=true`，而集群中所有节点均不具备该标签，导致无法匹配到任何可用节点。监控指标确认 Pod 持续处于 Pending 状态（证据 #2、#3），该现象完全由上述标签不匹配逻辑造成。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 30.5s
├─ 并发证据采集: 59.0s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 59.0s (Evidence 48.2s, RCA 10.7s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
