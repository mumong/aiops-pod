## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload处于Pending状态，持续37分钟未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (pod.phase/status) | Pending | 确认 Pod 处于未调度状态 (fact-2c6de2a05059, fact-a1989c1b1aec) |
| 2 | K8s Config | kubernetes (container.resource_request.cpu) | 100k | 确认该容器请求了 100m 的 CPU 资源作为基准 (fact-6d7f9d812dd6) |
| 3 | K8s Event | kubernetes (event.message) | `FailedScheduling 37m default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 证明调度器检查了全部 3 个节点，均因 CPU 不足失败且无预emption 目标 (fact-24449f8fd975, fact-59999d140c7d) |
| 4 | K8s State | kubernetes (pod.condition) | `PodScheduled: False, Reason: Unschedulable, Message: ... 0/3 nodes are available: 3 Insufficient cpu` | 再次确认集群节点级别的资源枯竭与调度失败的直接关联 (fact-4cc5a6a5da18) |
| 5 | Metric | prometheus (kube_pod_status_phase) | Pending=1, Unknown=0 (仅单样本，无趋势) (fact-b67d696a0e2b, fact-4e7878c846f1) | 从监控层面对 Pod 持续 Pending 状态进行了侧面印证 |

**证据印证说明：**
所有来自 Kubernetes 状态、事件和条件的证据都一致指向同一个结论：集群中 3 个节点的资源（尤其是 CPU）无法容纳新的 Pod 请求，且因为没有任何处于可抢占状态的高优先级 Pod，调度器放弃了该请求。Metric 数据由于 Pod 未启动（处于 Pending），仅提供状态确认，无其他诊断价值。日志与 Trace 因 Pod 未运行而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有3个节点CPU资源耗尽 → 调度器检查 0/3 nodes are available: 3 Insufficient cpu，且 0/3 nodes available for preemption → Pod 触发 FailedScheduling 事件，处于 Unschedulable 状态 → Pod 持续 Pending 37分钟未启动
```

### 根因结论

已确认的根因为**集群节点 CPU 资源完全耗尽**。
证据表明，调度器尝试将 Pod `aiops-case-v01/workload` 调度到集群中的 3 个节点上，但所有节点均报告 `Insufficient cpu`。由于集群中没有发现任何可被抢占的 Pod（`No preemption victims found`），调度失败成为必然。该结论由多次重复的 `FailedScheduling` 事件（fact-24449f8fd975, fact-59999d140c7d）和明确的调度器状态消息（fact-4cc5a6a5da18）相互印证。
目前的证据足以说明“为什么这个 Pod 调度失败”，但由于缺少节点级别的详细 CPU 用量及资源分配事实，尚无法进一步确认是哪一个或哪几个特定 Pod 占用了过多 CPU（如 unknowns 所述）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 14.9s
├─ 并发证据采集: 557.6s
│  └─ g1 aiops-case-v01/workload: 557.6s (Evidence 549.0s, RCA 8.4s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
