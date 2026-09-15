## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源不足 (Insufficient cpu) 导致 Pod 无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu` (fact-2c592aac574b) | 直接证实调度失败的根本原因是所有 3 个可用节点均缺少 CPU 资源。 |
| 2 | K8s State | Kubernetes | `Pending` 状态 (fact-900b0d111900) / `PodScheduled=False` (fact-9a624b87fe73) | 确认 Pod 持续处于未调度状态，且条件明确指向资源不足。 |
| 3 | K8s Config | Kubernetes | `resource_request.cpu` = `100k` (fact-28499c85bb27) | 提供具体的资源请求量，结合事件确认集群节点无法满足该微小请求。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}=1` (fact-ecadcc974c8a) | 通过监控数据在另一个时间点(05:34)确认 Pod 仍处于 Pending 状态。 |

**证据分析**：
Kubernetes 事件 (`#1`) 提供了决定性的失败原因，指出所有节点均因 `Insufficient cpu` 拒绝调度。Pod 的状态 (`#2`) 和监控数据 (`#4`) 提供了持续的异常佐证。虽然日志和追踪因容器未启动无法采集，但 K8s 核心状态与事件链已构成完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源耗尽 (Insufficient cpu) → default-scheduler 无法找到可用节点 → Pod aiops-case-v01/workload 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：集群节点 CPU 资源不足导致 Pod 无法调度。

**分析**：
Kubernetes 事件 (fact-2c592aac574b, fact-f1dbc7e34811) 明确记录了 `FailedScheduling` 原因，指出集群中 3 个节点均无法满足 Pod 的 CPU 资源请求（`100k`）。Pod 状态 (fact-900b0d111900) 和监控指标 (fact-ecadcc974c8a) 均证实 Pod 长时间处于 `Pending` 状态，且无抢占受害者。这构成了完整的因果链，排除了其他调度或配置错误的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.8s
├─ 并发证据采集: 37.3s
│  └─ g1 aiops-case-v01/workload: 37.3s (Evidence 31.3s, RCA 5.9s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
