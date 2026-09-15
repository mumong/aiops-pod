## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod配置了CPU Request (100k)，但集群中所有3个Ready节点的可分配(Capacity) CPU资源总和虽高，调度器却判定资源不足且Preemption失败，表明节点实际可用CPU（Allocatable减去已分配）不足以满足该Pod需求或调度器存在误判/限制 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: `Pending` (fact-id: fact-6aa6b23e21cd) | 确立 Pod 处于不可调度状态，是核心故障现象。 |
| 2 | K8s State | kubernetes | pod.condition type: `PodScheduled`, status: `False`, reason: `Unschedulable`, message: `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` (fact-id: fact-b3ec4b6f787e) | 揭示调度器判定所有节点因 CPU 资源不足拒绝调度，且无法通过抢占解决。 |
| 3 | K8s Event | kubernetes | Warning FailedScheduling: `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` (fact-id: fact-a9f42b8dfe87) | 进一步证实调度失败的时间点（26分钟前）与状态一致，排除了瞬时抖动。 |
| 4 | K8s Config | kubernetes | container.resource_request.cpu: `100k` (fact-id: fact-de940f90cdf8) | 明确了 Pod 的资源门槛，是触发 Insufficient cpu 判定的直接参数。 |
| 5 | Metric | prometheus | kube_pod_status_phase value: `1` (labels: `phase: Pending`, fact-id: fact-da0aebd6c80e) | 指标数据与 K8s 状态一致，确认 Pod 持续处于 Pending 状态，无转型。 |

**证据分析：**
Kubernetes 状态（证据 1-3）与 Metrics 指标（证据 5）高度一致，均确认 Pod 因 CPU 资源不足被拒绝调度。K8s 配置（证据 4）锁定了调度器判定的资源参数。虽然集群拥有 3 个 Ready 节点，但调度器判定所有节点均 Insufficient cpu 且预emption 失败，表明集群层面的剩余可分配 CPU 已无法满足该 100k 的需求，或者存在节点级资源标记异常。

## 🎯 根因分析 · g1

### 因果链

```text
节点可用 CPU (Allocatable - 已分配) 不足 100k → 调度器调度失败 (Insufficient cpu) 且无抢占对象 → Pod 保持 Pending 状态，不可调度
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-v01/workload` 处于 Pending 状态，原因是调度器判定集群内所有 3 个 Ready 节点均不具备足够的可用 CPU 资源（Insufficient cpu）来调度该 Pod，且没有满足抢占条件的victim（Preemption failed）。

*   **证据支撑**：
    *   K8s 事件与条件明确指出 `0/3 nodes are available: 3 Insufficient cpu`（见证据 2、3）。
    *   Pod 当前状态与指标持续为 `Pending`（见证据 1、5）。
    *   Pod 配置的 CPU Request 为 `100k`（见证据 4）。

现有证据已清晰表明集群整体 CPU 资源已耗尽或不可用，导致新 Pod 无法被调度。日志与追踪维度因容器未启动而无法采集，但不影响当前调度故障的定性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.3s
├─ 并发证据采集: 49.5s
│  └─ g1 aiops-case-v01/workload: 49.5s (Evidence 43.2s, RCA 6.2s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
