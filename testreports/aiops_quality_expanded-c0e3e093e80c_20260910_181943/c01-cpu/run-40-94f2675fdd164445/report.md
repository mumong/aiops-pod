## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群所有节点CPU资源耗尽，导致Pod因Insufficient cpu无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling`: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod. | 确认调度失败的直接原因，显示所有节点均无法满足 Pod 对 CPU 资源的请求 |
| 2 | K8s Config | Pod 资源请求 | `requests.cpu`: 100k (等价于 100 核) | 证明 Pod 申请的资源量极其异常，远超单节点常规 CPU 容量，直接导致调度失败 |
| 3 | K8s Config | Pod 资源限制 | `limits.cpu`: 100k (等价于 100 核) | 证实 Pod 被错误配置了极高的硬限制，加剧了资源分配的不可行性 |
| 4 | K8s State | Pod 状态 | `status: Pending`, `phase: Pending`, `PodScheduled: False` | 验证 Pod 长期处于不可调度状态，与调度器拒绝事件相印证 |
| 5 | Metric | kube_pod_status_phase | `pending=1` (容器=kube-state-metrics) | 提供集群级状态视角，确认存在处于 Pending 状态的 Pod，与调度事件互为佐证 |

**证据说明：**
1. Kubernetes 调度事件（#1）明确指出了 3 个节点均因 CPU 不足拒绝调度。
2. 事实 #2 和 #3 中的异常高 CPU 请求值（100k）是造成资源不足的直接证据，解释了为何调度器找不到可调度节点，也说明了为何无法通过抢占（preemption）释放资源。
3. Metric #5 的 Pending 状态进一步证实了集群中存在未能正确调度的实例。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被错误配置了极高的 CPU 资源请求/限制 (100k) → 节点可用 CPU 无法满足该请求 → 调度器拒绝调度（Insufficient cpu） → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 配置了极其不合理的 CPU 资源请求（100k）**。
该请求值直接导致集群所有节点在资源评估时均判定为 `Insufficient cpu`，从而触发调度器事件 `FailedScheduling`，使得 Pod 无法启动，持续处于 `Pending` 状态。集群节点资源枯竭是表象，根本原因在于该特定工作负载的资源需求远超硬件实际能力（参见证据 #2、#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.6s
├─ 并发证据采集: 44.9s
│  └─ g1 aiops-case-v01/workload: 44.9s (Evidence 39.0s, RCA 5.8s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
