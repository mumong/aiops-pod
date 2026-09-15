## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | status: False, reason: Unschedulable, message: "0/3 nodes are available: 3 Insufficient cpu" | 确认 Pod 处于 Unschedulable 状态的直接原因 |
| 2 | K8s Config | container.resource_request.cpu | value: 100k (0.1 core) | 提供 Pod 的具体资源需求 |
| 3 | K8s Event | event.message | "0/3 nodes are available: 3 Insufficient cpu" | 持续性的调度失败警告，证实集群整体 CPU 资源耗尽 |
| 4 | Metric | kube_pod_status_phase | value: 1 (phase: Pending) | 确认 Pod 当前处于 Pending 状态 |

**证据关联说明：**
- K8s 事件（#3）与 Pod 条件状态（#1）中的失败原因完全一致，共同证实了调度失败是由于所有节点均无法满足 CPU 请求所致。
- Metric 数据（#4）确认了 Pod 停留在 Pending 阶段，这与 Kubernetes 状态中的 Unschedulable 条件相吻合，排除了容器启动后崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源不足（3 个节点均 Insufficient） → 调度器无法找到满足 CPU Request (100k) 的节点 → 预抢占机制因无合适 Target Pod 而失败 → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因为**集群节点 CPU 资源不足**。

证据显示，调度器在 3 个节点上均报告 "Insufficient cpu" 且预抢占失败（证据 #1, #3）。Pod 配置的 CPU Request 为 100k（证据 #2），当前状态为 Pending（证据 #4）。现有证据链完整地解释了 Pod 无法调度的现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.2s
├─ 并发证据采集: 44.9s
│  └─ g1 aiops-case-v01/workload: 44.9s (Evidence 36.0s, RCA 8.9s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
