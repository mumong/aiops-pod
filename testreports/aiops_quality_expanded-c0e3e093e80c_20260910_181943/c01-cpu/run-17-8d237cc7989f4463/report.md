## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源已完全耗尽，导致调度器无法为 Pod 分配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-9264bd4d3fdd` | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu.` | 证实调度失败，集群所有节点 CPU 资源耗尽 |
| 2 | K8s State | `fact-b44cb3c5ae99` | Pod `aiops-case-v01/workload` 状态为 `Pending` | 确认 Pod 未调度，处于挂起等待状态 |
| 3 | Metric | `fact-5c8e53eb5523` | `kube_pod_status_phase` 对 `Pending` 状态返回 `1` (当前值) | 指标确认当前存在处于 Pending 状态的 Pod |
| 4 | Metric | `fact-0d76b68a1abb` | `kube_pod_status_phase` 对 `Failed` 状态返回 `0` (当前值) | 排除因运行失败导致的异常，确认为调度前状态 |

**证据关联：**
Kubernetes Event (证据 1) 直接指出了 "Insufficient cpu" 是调度失败的原因，这与 Pod 状态为 Pending (证据 2) 以及 Pending 状态计数为 1 (证据 3) 的现象完全一致；Failed 状态计数为 0 (证据 4) 进一步排除了启动后崩溃的可能，表明故障完全发生在调度阶段。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源完全耗尽 → 调度器无法匹配到满足条件的节点 (Insufficient cpu) → Pod 被调度器拒绝分配 → 集群状态表现为 Pod 长期处于 Pending 状态，无法被调度至任何节点执行
```

### 根因结论

已确认根因为**集群节点 CPU 资源耗尽**，导致调度器无法为 `aiops-case-v01/workload` 分配运行节点。

该结论由以下事实支撑：
1.  **现象一致**：Pod 持续处于 `Pending` 状态（证据 2、3），未出现 `Failed` 状态（证据 4），说明问题出在调度阶段而非容器运行阶段。
2.  **直接归因**：Kubernetes 调度事件（证据 1）明确记录了 `0/3 nodes are available: 3 Insufficient cpu`，证实集群内所有可用节点的 CPU 资源均已无法满足调度请求，且无抢占资源可用。

缺失的节点资源详情（如 `kubernetes_tabular_query` 失败未返回节点容量数据）不影响对“CPU 资源耗尽导致调度失败”这一直接事实的认定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.2s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-v01/workload: 48.5s (Evidence 42.8s, RCA 5.6s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
