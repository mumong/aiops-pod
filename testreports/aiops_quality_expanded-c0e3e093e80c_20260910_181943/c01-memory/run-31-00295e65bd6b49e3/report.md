## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (重复出现 47m 至 7m21s 期间) | 确认调度器因集群缺乏可用内存，且无法触发抢占而持续调度失败。 |
| 2 | K8s Config | `kubernetes` | `container.resource_limit.memory: 1Pi` (容器 `app`) | 暴露出该 Pod 请求的内存资源上限极大，超出了集群常规节点的物理容量。 |
| 3 | K8s Config | `kubernetes` | `container.resource_request.memory: 1Pi` | 进一步确认 Pod 调度请求的内存资源规模同样为 1Pi。 |
| 4 | K8s State | `kubernetes` | `Pod status: Pending` | 描述 Pod 当前处于无法被调度的异常停滞状态。 |
| 5 | Metric | `prometheus` | `kube_pod_status_phase(phase="Pending")` 值为 1 | 指标层面佐证了目标 Pod 当前仍处于 Pending 状态。 |

上述 K8s 事件明确指出集群中所有 3 个节点均无法满足内存需求，且无法通过抢占释放资源。结合配置事实，该 Pod 申请的资源上限与请求量均为 `1Pi`（即 1 Pebibyte），这是导致调度器直接拒绝调度的决定性上下文。Metric 数据确认了该状态已持续存在。由于容器未能启动，Logging 和 Tracing 维度无可观测事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 资源配置 memory 设为 1Pi，远超集群节点实际物理容量 → 调度器评估集群内所有节点均无法满足资源调度要求 → 调度器抛出 FailedScheduling 事件，且无抢占机制介入 → Pod 保持在 Pending 状态未调度
```

### 根因结论

已确认根因为 Pod 资源配置 `memory: 1Pi` 严重超出集群节点可用内存。
该配置导致调度器（证据 #1）在尝试将 Pod 分配到 3 个节点时，发现所有节点均存在内存不足（Insufficient memory），且无合适的抢占目标（No preemption victims）。这直接导致了 Pod 持续保持 `Pending` 状态（证据 #4、#5）。现有事实已完整覆盖异常现象的起因与结果，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.9s
├─ 并发证据采集: 31.1s
│  └─ g1 aiops-case-v02/workload: 31.1s (Evidence 24.2s, RCA 6.9s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
