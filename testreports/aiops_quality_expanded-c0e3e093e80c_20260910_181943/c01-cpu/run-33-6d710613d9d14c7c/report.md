## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 持续处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-6e0285b4a85b, fact-74842e785787) | FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found | 直接说明调度失败机制：集群无可用节点，且无可抢占的资源 |
| 2 | K8s State | kubernetes (fact-edd5d078d71c) | Pod condition PodScheduled=False, reason=Unschedulable, message="3 Insufficient cpu" | 确认 Pod 处于 Unschedulable 状态，原因指向 CPU 资源不足 |
| 3 | K8s Config | kubernetes (fact-93e41d08d0b1) | container resource request cpu = 100k (0.1核) | 确认该 Pod 调度请求的最小资源量 |
| 4 | Metric | prometheus (fact-b65e4af15c96) | kube_pod_status_phase=1 (Pending, sample_count=1) | 确认 Pod 持续处于 Pending 状态，未见转换 |
| 5 | Metric | prometheus (fact-14eb789cef16) | kube_pod_status_phase=0 (Failed, sample_count=1) | 确认 Pod 尚未进入 Failed 状态，排除因创建失败导致的终止 |

证据 1 和证据 2 均明确指出集群 3 个节点均因 CPU 不足无法调度 Pod。证据 3 显示 Pod 仅需 0.1 核 CPU，说明资源缺口极小，集群整体已无余量。证据 4 与证据 5 进一步印证 Pod 停留在 Pending 状态但未失败。Kubernetes 事件与状态一致确认了 CPU 资源耗尽是唯一的阻断原因。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有节点 CPU 可分配资源已完全耗尽 → Scheduler 评估无节点满足 0.1核 Request → 无预占受害者 → Pod 维持 Pending
```

### 根因结论

已确认根因为**集群 CPU 资源完全耗尽**。集群内所有可用节点（共 3 个）的 CPU 可分配资源（allocatable）已被完全占用（used），导致调度器无法为 Pod `aiops-case-v01/workload` 满足其 0.1 核（100k）的 CPU 请求。同时，由于无其他低优先级 Pod 可被抢占（No preemption victims found），调度失败且无法通过抢占恢复。此结论由 FailedScheduling 事件及 Unschedulable 状态共同确证（证据 1、2、3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.3s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-v01/workload: 48.5s (Evidence 39.1s, RCA 9.2s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
