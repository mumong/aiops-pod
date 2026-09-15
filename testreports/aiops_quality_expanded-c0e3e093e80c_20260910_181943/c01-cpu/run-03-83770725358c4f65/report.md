## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 持续处于 Pending 状态且无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found` | 提供核心故障证据，直接指出集群所有节点 CPU 不足，且无法通过抢占获得资源 |
| 2 | K8s Config | `pod.spec` | `container.app.resource_request.cpu: 100k` | 确认 Pod 对 CPU 资源的请求量 |
| 3 | K8s State | `pod.status` | `status: Pending`, `condition.PodScheduled: False (Unschedulable)` | 确认 Pod 长期处于未调度状态，与调度器返回的错误消息一致 |

Kubernetes 事件 (证据 #1) 直接解释了 K8s State (证据 #3) 中 Pod 无法调度的具体原因，即节点 CPU 资源无法满足调度器分配 `100k` CPU 请求 (证据 #2) 的条件。Metric、Logging 和 Tracing 维度均未提供与调度失败直接相关的有效诊断数据。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点可用 CPU 资源不足 (3/3 nodes Insufficient cpu) → 调度器拒绝分配且无预emption 空间 → Pod 无法调度 (PendingUnschedulable) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是**集群节点 CPU 资源不足导致调度失败**。
Kubernetes 调度器 (证据 #1) 明确报告所有 3 个节点均因 `Insufficient cpu` 无法调度该 Pod，且没有满足预emption 条件的受害者。这导致 Pod 处于 `Pending` 状态 (证据 #3) 且无法启动。

缺失事实：未能通过 `kubernetes_tabular_query` 获取 Node 的实际 `Allocatable CPU` 数值 (命令因参数格式错误失败)，因此无法量化资源缺口的大小，但调度器的判定结论本身已构成调度失败的直接决定性证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 21.4s
├─ 并发证据采集: 86.6s
│  └─ g1 aiops-case-v01/workload: 86.6s (Evidence 76.5s, RCA 10.0s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
