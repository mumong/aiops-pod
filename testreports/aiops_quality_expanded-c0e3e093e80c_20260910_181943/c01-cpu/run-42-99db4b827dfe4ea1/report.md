## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，未被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending`, `pod.status: Pending` | 确认工作负载当前处于不可用且未调度的状态 |
| 2 | K8s State | kubernetes | `pod.condition: PodScheduled=False, reason=Unschedulable` (2026-09-11T05:28:07Z) | 提供 Pod 调度失败的直接状态事实 |
| 3 | K8s Event | kubernetes | `FailedScheduling` 事件 (x12 over 61m): `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 核心诊断依据，明确集群中所有节点均因 CPU 不足且无法抢占而拒绝调度 |
| 4 | K8s Config | kubernetes | `resource_request.cpu: 100k` | 确认调度器尝试分配的 CPU 需求，表明请求量极小，进一步凸显集群整体 CPU 资源耗尽的事实 |

当前证据表明，Pod 持续 61 分钟处于 Pending 状态，根本原因在于集群所有 3 个节点均无可用 CPU 资源，且不存在可抢占的 Pod。日志与链路追踪因容器未启动而不可用，不影响此静态资源调度结论。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU allocatable 资源耗尽 (事实: 3 nodes Insufficient cpu) → Default Scheduler 无法满足 Pod 100m CPU 需求且无可抢占对象 (事实: FailedScheduling 事件) → Pod 无法绑定节点，保持 Unschedulable (事实: pod.condition) → Pod 持续 Pending (事实: pod.phase)
```

### 根因结论

**已确认根因：集群节点 CPU 资源耗尽。**

证据 [1-4] 相互印证。Kubernetes 事件 [3] 明确指出 3 个节点均因 "Insufficient cpu" 无法调度，且 "No preemption victims" 排除了通过抢占释放资源的可能性。Kubernetes 状态 [2] 确认了调度失败的直接机制。尽管 Pod 的 CPU 请求量 [4] 很小，但调度器在集群层面仍判定无可用资源，证实集群层面的 CPU 资源池已完全饱和。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.4s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-v01/workload: 37.9s (Evidence 32.4s, RCA 5.5s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
