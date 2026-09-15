## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 定义了不合理的资源请求与限制：`requests.memory` 和 `limits.memory` 均为 1Pi（约 1125 PiB），远超集群所有节点（master, node1, node2）的物理内存容量。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes (`fact-8963ecadad3b`, `fact-1ab987d0a7c5`) | `container.resource_request.memory`: 1Pi; `container.resource_limit.memory`: 1Pi | 确定异常根因：Pod 内存硬限制与请求值极高（1Pi） |
| 2 | K8s State | kubernetes (`fact-10717d169571`, `fact-2cc55b3e4863`) | `PodScheduled`: False, reason: `Unschedulable`, message: `3 Insufficient memory`; phase: `Pending` | 确认调度失败现象，且归因于内存不足 |
| 3 | K8s Event | kubernetes (`fact-a7d7517426b6`, `fact-ff317a6effc1`) | `Warning FailedScheduling`: `0/3 nodes are available: 3 Insufficient memory.` | 调度器事件直接印证资源缺口 |
| 4 | Metric | prometheus (`fact-1e11c4624349`) | `kube_pod_status_phase` phase=`Pending`: 1 (单样本) | 监控指标与 Pod 状态一致，确认持久处于 Pending 状态 |

**证据综合说明**：
配置事实（证据 1）明确指出了 Pod 定义了不切实际的 1Pi 内存请求，这是导致调度器判定资源不足的核心原因。K8s 状态（证据 2）和调度事件（证据 3）从系统层面证实了调度失败，且明确将原因归结为 `Insufficient memory`。Metric 数据（证据 4）在时间戳上与 Pod 状态保持一致，确认了这一故障状态的持续性。Kubernetes 内部证据已形成完整闭环，Logging 与 Tracing 因容器未启动未提供数据，不影响当前判定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义不合理的内存请求 (1Pi) → 调度器无法匹配任何可用节点 → 调度失败 (FailedScheduling) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为 Pod `aiops-case-v02/workload` 配置了极不合理的内存资源请求与限制值：`requests.memory` 和 `limits.memory` 均为 **1Pi**（约 1125 PiB）。

这一配置超出了集群中所有节点（master, node1, node2）的物理内存容量，导致 Kubernetes 调度器 `default-scheduler` 在尝试分配 Pod 时判定资源不足（`Insufficient memory`），从而触发 `FailedScheduling` 事件，使 Pod 长期处于 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.7s
├─ 并发证据采集: 35.5s
│  └─ g1 aiops-case-v02/workload: 35.5s (Evidence 29.3s, RCA 6.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
