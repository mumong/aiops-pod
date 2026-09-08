## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in aiops-case-01 is stuck in Pending state and unschedulable. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact_id: `fact-33c204062efa`) | 确认调度失败的核心原因为节点亲和性/选择器不匹配，且所有 3 个节点均不满足条件。 |
| 2 | K8s State | `Pod Condition` | `type: PodScheduled, status: False, reason: Unschedulable` (fact_id: `fact-8baf57f83917`) | 佐证 Pod 处于 Unschedulable 状态，符合调度失败的预期结果。 |
| 3 | K8s State | `Pod Phase` | `phase: Pending` (fact_id: `fact-06a631069423`) | 确认 Pod 停留在 Pending 状态，无容器启动迹象。 |
| 4 | Metric | `kube_pod_status_phase` | `phase: Pending, value: 1` (fact_id: `fact-d6b0e85a372f`) | 独立于 K8s 状态检查，确认 Pod 持续处于 Pending 阶段。 |
| 5 | K8s Config | `Container Resource Request` | `app container: CPU 5m, Memory 8Mi` (fact_id: `fact-025f803f993f`, `fact-bba2fd821e80`) | 证明资源请求极低（5m CPU, 8Mi Mem），排除资源不足（NoFreeResources）导致失败的可能。 |

**证据交叉印证：**
Kubernetes 事件明确指出“节点不匹配亲和性/选择器”是调度拒绝的原因，结合极低的资源请求（证据 #5），排除了资源不足的可能性。K8s 状态与 Metrics 均确认 Pod 处于 Pending 阶段，未进入创建或运行阶段，印证了调度阶段的阻断导致了后续所有状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中包含 nodeSelector aiops.lab/unavailable: 'true' → 集群中 0/3 个节点拥有该标签（不匹配） → 调度器拒绝所有可用节点（Unschedulable） → Pod 卡在 Pending 状态，用户应用无法启动
```

### 根因结论

已确认的根因是 **Pod 调度亲和性/选择器不匹配**。

Pod `workload-68c557d875-bsq52` 被配置了 `nodeSelector` 条件 `aiops.lab/unavailable: 'true'`，但集群当前所有的 3 个节点均不满足此标签要求。由于 K8s 调度器在预选阶段无法满足该选择器条件，导致所有 3 个节点都被判定为不可用（didn't match Pod's node affinity/selector），进而使 Pod 无法被调度到任何节点上。资源请求极低的事实排除了资源不足的因素，证实该问题完全由标签匹配失败引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.4s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 37.9s (Evidence 29.6s, RCA 8.1s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
