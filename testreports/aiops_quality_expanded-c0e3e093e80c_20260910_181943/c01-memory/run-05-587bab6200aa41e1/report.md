## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 的容器资源请求 memory 被设置为 1Pi（1 Pebibyte），该值远超集群中所有 3 个 Ready 节点（master, node1, node2）的实际可用内存上限。kube-scheduler 在调度时检测到此资源不可满足，连续触发 FailedScheduling 事件且因无足够内存的 Pod 可抢占（preemption）而失败，导致 Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Pod aiops-case-v02/workload` 状态为 `Pending` [fact-dd84672abea6] | 确认故障现象 |
| 2 | K8s Config | kubernetes | `memory` 请求量与限制量均为 `1Pi` (1 Pebibyte) [fact-ca91f53c81d3, fact-3dd67f1ea3c1] | 确定异常配置值 |
| 3 | K8s Event | kubernetes | `FailedScheduling`：`0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` [fact-809d5a09d023, fact-ed90ba8161e6] | 确认调度失败直接原因与抢占情况 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 值为 `1` (Pending)，无 Unknown 状态 [fact-4026f9d124fc] | 确认 Pod 持续处于 Pending 阶段 |

**证据印证说明**：
Pod 的 `Pending` 状态（#1, #4）与 Kubernetes 调度器发出的 `FailedScheduling` 事件（#3）直接对应。事件详情指出所有 3 个节点均因 `Insufficient memory` 拒绝调度，且无抢占受害者（No preemption victims），这直接由 Pod 配置中高达 `1Pi` 的内存请求（#2）导致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod aiops-case-v02/workload 配置了 1Pi 的内存请求（#2） → kube-scheduler 无法找到满足该资源需求的节点（#3） → 调度器触发 FailedScheduling 且无可用抢占对象 → Pod 持续处于 Pending 状态（#1, #4）
```

### 根因结论

已确认根因为 `aiops-case-v02/workload` 的容器资源配置错误。
具体而言，该 Pod 将 `memory` 的请求（request）和限制（limit）均设置为 `1Pi`（1 Pebibyte），该数值远超集群节点的实际内存容量。Kubernetes 调度器在尝试调度时因无法找到满足 `Insufficient memory` 要求的节点而失败，且由于没有更小的 Pod 可供抢占（preemption），导致该 Pod 无限期处于 `Pending` 状态。证据（#2, #3）充分支持此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 53.0s
├─ 问题定位: 14.9s
├─ 并发证据采集: 29.3s
│  └─ g1 aiops-case-v02/workload: 29.3s (Evidence 22.4s, RCA 6.8s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
