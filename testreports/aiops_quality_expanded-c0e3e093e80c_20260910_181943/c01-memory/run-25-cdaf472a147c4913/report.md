## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，持续触发 FailedScheduling 且无节点可满足资源请求 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling 0/3 nodes are available: 3 Insufficient memory.` (fact-59dec83c5df2) | 记录 Pod 持续无法调度的直接失败机制。 |
| 2 | K8s State | `pod.condition` | `PodScheduled: False, Reason: Unschedulable` (fact-6c0d1bcec8a8) | 确认 Pod 因资源评估失败而处于 Unschedulable 状态。 |
| 3 | K8s Config | `container.resource_request.memory` | `container: app, value: 1Pi` (fact-199ba403403a) | 揭示 Pod 定义中显式申请了 1 PiB 内存，这是导致调度失败的直接原因。 |
| 4 | K8s Config | `container.resource_limit.memory` | `container: app, value: 1Pi` (fact-d36c1d1f4051) | 确认 Pod 的内存硬限制同样为 1 PiB，进一步排除了调度回退机制的可能性。 |
| 5 | Metric | `prometheus` | `kube_pod_status_phase` 为 Pending (fact-3820ad561c48) | 确认 Pod 当前物理运行阶段仍处于 Pending 状态。 |

**证据链说明**：
K8s 事件（#1）明确显示集群中所有节点均因“内存不足”而拒绝调度。K8s 配置数据（#3, #4）证实 Pod 请求并限制了 `1Pi` 内存。这种极端的资源需求与典型的集群容量严重不匹配，直接导致了调度器返回 `Unschedulable`（#2）且 Pod 保持 Pending（#5）的状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置中 memory 请求设置为 1Pi → 调度器评估节点内存无法满足 → 触发 Insufficient memory 拒绝调度 → Pod 持续 Pending
```

### 根因结论

已确认根因为**Pod 资源配置严重超限**。
事实 #3 和 #4 确凿显示 `aiops-case-v02/workload` 的容器配置了 `1Pi`（1 Pebibyte，约 1125 TiB）的内存请求与限制。这一数值远超任何标准节点的物理容量，直接导致调度器在评估所有 3 个节点时均判定资源不足（`Insufficient memory`），从而触发 `FailedScheduling` 事件并维持 Pod 的 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 11.6s
├─ 并发证据采集: 56.4s
│  └─ g1 aiops-case-v02/workload: 56.4s (Evidence 48.2s, RCA 8.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
