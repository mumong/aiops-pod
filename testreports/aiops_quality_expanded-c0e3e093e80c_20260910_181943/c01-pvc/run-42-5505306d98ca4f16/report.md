## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，无法被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kube-state-metrics` | `phase: "Pending"` | 确认 Pod `aiops-case-v03/workload` 处于等待调度的非运行状态 |
| 2 | K8s Config | K8s | `resource_request.cpu: "5m"`, `resource_limit.cpu: "50m"` | 展示容器的 CPU 资源边界，排除资源超卖或限制导致的内存/计算异常 |
| 3 | K8s Config | K8s | `resource_request.memory: "8Mi"`, `resource_limit.memory: "32Mi"` | 展示容器的内存资源边界 |
| 4 | K8s State | K8s | `PodScheduled=False`, `reason: "Unschedulable"`, `message: "0/3 nodes are available: persistentvolumeclaim \"unavailable-claim\" not found."` | 明确触发调度失败的机制：调度器因找不到名为 `unavailable-claim` 的 PVC 而无法将 Pod 调度至任何节点 |

**证据互证说明：**
- **事实 4 为直接故障证据**：`Unschedulable` 的 message 精确指出了 `persistentvolumeclaim "unavailable-claim" not found`。这是 Pod 状态长期停留在 Pending 的唯一原因。
- **事实 1 与 4 印证**：`phase: Pending` 是事实 4 中调度失败后的自然结果状态。
- **事实 2、3 作为排除证据**：虽然提供了资源请求与限制值，但由于调度失败的根本原因是 PVC 缺失而非计算资源不足，因此这些配置在此场景下不作为根因证据，仅作为上下文说明。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 PVC 'unavailable-claim' → 调度器无法绑定卷，触发 FailedScheduling → Pod 处于 Pending (Unschedulable) 状态
```

### 根因结论

**已确认根因：Pod Spec 中引用的 PVC 'unavailable-claim' 不存在，导致调度失败。**

- **证据支撑**：K8s State (`fact-ec431c2eb492`) 中的 `PodScheduled` 条件明确记录了调度失败原因 `persistentvolumeclaim "unavailable-claim" not found`，直接证实了 PVC 缺失导致调度器无法分配节点。
- **排除干扰**：Metric (`fact-884fda3a3561`) 确认 Pod 确实处于 Pending 阶段，且 `resource_request` 与 `resource_limit` 正常，说明故障并非由计算资源耗尽或调度策略错误引起，而是纯粹的卷绑定依赖失败。

---

## 📊 性能统计

```text
├─ 总耗时: 53.0s
├─ 问题定位: 13.1s
├─ 并发证据采集: 30.9s
│  └─ g1 aiops-case-v03/workload: 30.9s (Evidence 24.2s, RCA 6.6s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
