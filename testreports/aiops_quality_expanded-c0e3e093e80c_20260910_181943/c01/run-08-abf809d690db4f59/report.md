## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 判定调度失败的根本原因是亲和性/选择器匹配失败 |
| 2 | K8s State | kubernetes | `pod.condition` 中 `PodScheduled=False`，错误信息同上 | 确认当前 Pod 持续处于未调度状态 |
| 3 | K8s State | kubernetes | `pod.phase` 为 `Pending` | 确认 Pod 生命周期停滞在初始阶段 |
| 4 | K8s Config | kubernetes | `resource_request.memory`: 8Mi, `resource_request.cpu`: 5m | 确认资源请求量极低，排除因资源总量不足导致的调度延迟 |
| 5 | Metric | prometheus | `kube_pod_status_phase` 中 Pending 状态值为 1 (sample_count=1) | 从监控维度印证 Pod 当前仍保持在 Pending 状态 |

**证据关联说明**：
K8s Event (1) 与 K8s State (2,3) 在物理状态与事件反馈上完全一致，共同指向 `FailedScheduling`。Metric 数据 (5) 确认该状态为当前持续现象而非瞬时波动。由于调度失败原因为亲和性规则不匹配（非资源不足），因此低资源请求配置 (4) 佐证了该现象是由节点标签配置错误引起，而非资源争抢。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含节点选择器/亲和性配置 → 集群 3 个节点均不满足该选择器规则 → 默认调度器抛出 FailedScheduling 事件 → Pod 保持 Pending 状态无法调度
```

### 根因结论

已确认的根因为 **节点亲和性/选择器（Node Affinity/Selector）不匹配**。

该 Pod 定义中指定的 `nodeSelector` 或 `affinity` 规则要求节点具备特定标签，但集群内现有的 3 个节点均不包含该标签，导致 `default-scheduler` 在调度阶段判定无可用节点（0/3 nodes available）并拒绝调度。该结论由 K8s Event (fact-067511fa49ed) 明确记录的 `didn't match Pod's node affinity/selector` 以及 Pod 持续 Pending 状态共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.7s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 38.0s (Evidence 29.2s, RCA 8.7s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
