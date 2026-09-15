## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload in aiops-case-v01 namespace remains in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `type: PodScheduled, status: False, reason: Unschedulable, message: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found` | 确诊调度失败直接原因：集群所有可用节点 CPU 资源耗尽，且不存在可抢占的 Pod。 |
| 2 | K8s Event | event.message | `FailedScheduling 16m... 0/3 nodes are available: 3 Insufficient cpu.` | 调度器（default-scheduler）确认无法将 Pod 分配至任何节点。 |
| 3 | K8s Config | container.resource_request.cpu | `value: 100k` | 提供资源需求背景：请求量极低（0.1核），排除了因资源需求过大导致的调度困难。 |
| 4 | Metric | kube_pod_status_phase | `phase: Pending, value: 1 (sample_count: 1)` | 验证当前 Pod 处于持续挂起状态，与调度失败现象一致。 |

**证据分析**：
证据 1 与 2 共同证实了调度失败的具体机制：3个节点 CPU 不足，且因为没有其他资源受压的 Pod 可被抢占（Preemption），导致调度器处于无解状态。证据 3 排除了配置错误导致资源请求过高的可能性，表明故障在于集群整体容量瓶颈。

## 🎯 根因分析 · g1

### 因果链

```text
集群内所有可用节点（3个）CPU资源不足 → 默认调度器 (default-scheduler) 在3个节点上均调度失败 → Preemption 机制未找到可抢占的victims → Pod 状态维持在 Pending
```

### 根因结论

**已确认的根因**：集群内所有可用节点（3个）CPU 资源不足，且无可抢占（Preemption）的 Pod 资源，导致调度器无法为 `aiops-case-v01/workload` 分配节点 [证据 1, 2]。该结论得到了 Pod 持续处于 `Pending` 状态且 `Unschedulable` 的 Kubernetes 状态事实支撑 [证据 4]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 31.0s
├─ 并发证据采集: 27.4s
│  └─ g1 aiops-case-v01/workload: 27.4s (Evidence 21.4s, RCA 5.9s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
