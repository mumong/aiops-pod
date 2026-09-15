## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 的 nodeSelector 要求节点具有 'aiops.lab/unavailable=true' 标签，但集群中所有可用节点均不匹配该标签，导致调度器无法找到符合条件的节点，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 确立调度失败的根本机制 |
| 2 | K8s State | kubernetes | `PodScheduled=False`, `Unschedulable`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 确认调度器对标签不匹配的最终判定 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu`: 5m, `container.resource_request.memory`: 8Mi | 排除资源超限导致调度的可能性 |
| 4 | K8s State | kubernetes | `Pending` | 确认 Pod 持续处于不可调度的状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase` 在 `Pending` 下值为 1 | 辅助确认当前 Pod 实例的状态 |

**证据印证**：
K8s 事件与状态均一致确认调度失败的原因是“未匹配节点亲和性/选择器”（fact 1, 2），而非资源不足（fact 3）。Metric 数据（fact 4）进一步佐证了 Pod 处于 Pending 状态的现实。

## 🎯 根因分析 · g1

### 因果链

```text
配置了不存在的节点标签约束 (nodeSelector: aiops.lab/unavailable=true) → 集群 3 个可用节点均无匹配标签 → default-scheduler 判定 0/3 节点可用 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 调度配置与集群节点拓扑不匹配**。
Pod 声明要求节点拥有 `aiops.lab/unavailable=true` 标签，但集群内所有节点均未配置该标签，导致调度器无法找到合适的节点（证据 1, 2）。鉴于 Pod 尚未调度，不存在运行时的资源争用问题，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 49.1s
├─ 问题定位: 14.0s
├─ 并发证据采集: 28.2s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 28.2s (Evidence 21.1s, RCA 7.0s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
