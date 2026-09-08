## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未分配节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `status: Pending`, `PodScheduled: False`, 原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认 Pod 因调度不匹配处于未调度状态，排除资源不足导致。 |
| 2 | K8s Event | kubernetes | `FailedScheduling` (事实 fact-0913e741d54b)，消息指示 `didn't match Pod's node affinity/selector` 且 `Preemption is not helpful` | 证实调度器在多次尝试（8次）中一致失败，确认是调度规则层面的阻塞。 |
| 3 | K8s Config | kubernetes | 配置引用：`aiops.lab/unavailable: true` (来自事实上下文及 RCA) | 确定 Pod 的亲和性规则要求节点必须标记为 `unavailable` 状态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 为 `1` (Pending) | 独立于 K8s API 验证 Pod 仍处于 Pending 状态，确保持续性而非瞬时波动。 |

证据总结：K8s 事件与状态均明确指向“节点亲和性/选择器不匹配” (fact-0913e741d54b, fact-113905c5797f)。Metric 数据 (fact-532b580de3d6) 佐证了状态未改变。日志与链路追踪因容器未启动而不可用，但这符合 Pending  Pod 的物理状态预期，不影响调度原因的判断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector `aiops.lab/unavailable=true` (事实 3) → 集群中所有 3 个节点均未匹配该选择器条件 → 调度器执行 `FailedScheduling`，拒绝分配 (事实 1, 2) → Pod 持续处于 Pending 状态 (事实 1, 4)
```

### 根因结论

**已确认的根因**：Pod `workload-68c557d875-llhkh` 的调度失败是由**节点亲和性/选择器配置不匹配**引起的。

具体而言，Pod 定义了 `nodeSelector` 要求节点拥有标签 `aiops.lab/unavailable: "true"`，但集群中所有 3 个候选节点均不满足此条件。这导致 `default-scheduler` 在多次尝试（至少 8 次）后，均报告 `0/3 nodes are available`，从而将 Pod 维持在 `Pending` 状态。证据 `FailedScheduling` 事件与 Pod 的 `Unschedulable` 状态相互印证。

**未知/未确认部分**：节点实际是否应该具有此标签，或该标签是否为 `false`，目前无法通过当前工具数据直接确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.1s
├─ 并发证据采集: 72.9s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 72.9s (Evidence 63.6s, RCA 9.1s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
