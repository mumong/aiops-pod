## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 持续处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `PodScheduled=False`: `0/3 nodes are available: 3 Insufficient memory` | 确认 Pod 调度失败的确切原因是内存不足，且集群所有节点（3/3）均被拒绝。 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling`: `0/3 nodes are available: 3 Insufficient memory` (重复事件持续 21m) | 提供故障的时间跨度（至少 21 分钟），确认为持续性故障而非瞬时抖动。 |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存请求 (`resource_request`) = `1Pi` | 核心冲突证据：Pod 请求的资源量远超物理节点承载能力。 |
| 4 | K8s Config | Kubernetes | 容器 `app` 内存限制 (`resource_limit`) = `1Pi` | 进一步证实该资源请求是用户明确配置的策略，非系统猜测值。 |
| 5 | Metric | Prometheus | `kube_pod_container_resource_requests` (container=app, resource=memory) = `1125899906842624` bytes (约 1 Pi) | 验证 K8s 配置事实：PromQL 查询到容器实际占用的 Request 资源值与 K8s Spec 完全一致，确认该异常值已在监控中生效。 |

**证据关联说明：**
K8s 事件与状态（#1, #2）一致表明调度器在所有节点上均因内存不足而失败；配置事实（#3, #4）揭示了原因：请求了 `1Pi` 内存。Metric 数据（#5）独立验证了这一配置在监控系统中的呈现，三者结合确证了配置请求量是导致 `Insufficient memory` 的唯一事实根源。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存资源配置错误 (request=1Pi) → 请求量远超集群节点最大可用容量 (Insufficient memory) → 调度器拒绝调度 (FailedScheduling) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 资源配置错误**。容器 `app` 被配置为请求 `1Pi` (1,125,899,906,842,624 bytes) 的内存（依据事实 #3, #4, #5），该数值远超集群中任何节点的可用物理内存上限。由于调度器无法在任何 3 个节点上找到满足此内存要求的资源槽位，触发了 `Insufficient memory` 错误并拒绝调度（依据事实 #1, #2）。

现有的 Kubernetes 事件、状态与资源配置事实已形成完整闭环，足以支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 68.0s
├─ 并发证据采集: 81.7s
│  └─ g1 aiops-case-v02/workload: 81.7s (Evidence 72.8s, RCA 8.7s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
