## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | aiops-case-v02/workload Pod 持续处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`：`0/3 nodes are available: 3 Insufficient memory` (55m 及 15m 记录) | 直接证据：调度器明确报告集群所有节点均因内存不足而无法调度该 Pod |
| 2 | K8s Config | kubernetes | `container.resource_request.memory`: `1Pi` | 根本原因：Pod 内存请求量异常庞大（1 PiB），远超常规集群节点容量 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: `1Pi` | 辅助证据：内存限制同样设置为 1PiB，表明该资源规格设定是一致且刻意的 |
| 4 | K8s State | kubernetes | `pod.status`: `Pending` | 现象确认：Pod 未能分配任何节点，处于永久挂起状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase` (phase: Pending): `1` (样本数: 1) | 状态佐证：监控确认 Pod 处于 Pending 阶段；同时 Failed 状态为 0，排除 CrashLoopBackOff 等启动后失败 |

证据 1 的 `Insufficient memory` 警告直接关联证据 2 中高达 1PiB 的内存请求。调度器拒绝调度是因为节点 allocatable 资源无法满足该极端请求，这同时也解释了证据 4 中 Pod 长期 Pending 而证据 5 中未出现 Failed 状态的现象（因为根本未曾启动）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 资源配置异常 (memory request 1PiB) → 调度器资源校验失败 (所有 3 个节点资源均不满足) → 持续 FailedScheduling 事件 → Pod 状态始终 Pending
```

### 根因结论

已确认的根因是 **Pod 的资源请求规格严重超出集群承载能力**（引用证据 2, 3）。

`default-scheduler` 在调度过程中，逐一检查集群内所有 3 个节点的资源，发现每个节点的可用内存均小于 Pod 请求的 `1PiB`（引用证据 1）。因此调度器无法找到任何符合条件的节点，导致 Pod 持续处于 `Pending` 状态（引用证据 4, 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.4s
├─ 问题定位: 16.2s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-v02/workload: 32.3s (Evidence 26.0s, RCA 6.2s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
