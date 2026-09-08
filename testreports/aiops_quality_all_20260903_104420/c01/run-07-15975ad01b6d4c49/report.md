## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod配置了nodeSelector 'aiops.lab/unavailable=true'，但集群中全部3个节点均未设置该标签，导致调度器无法找到匹配节点（FailedScheduling）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. | 直接证明调度器因节点不匹配无法调度 |
| 2 | K8s State | kubernetes | `pod.condition(PodScheduled)`: False, reason: Unschedulable | 确认 Pod 长期处于不可调度状态 |
| 3 | K8s State | kubernetes | `pod.phase` / `pod.status`: Pending | 确认 Pod 尚未进入运行阶段 |
| 4 | K8s Config | kubernetes | `resource_limit.memory`: 32Mi; `resource_limit.cpu`: 50m; `resource_request.memory`: 8Mi; `resource_request.cpu`: 5m | 提供资源上下文，证明非资源不足导致的调度失败 |
| 5 | Metric | prometheus | `kube_pod_status_phase(Pending)`: 1 | 监控层面确认 Pod 持续处于 Pending 状态 |

证据间互相印证：K8s Event 指出 3 个节点均不匹配 NodeSelector 标签，这是导致 `PodScheduled=False` 和 `Pending` 状态的直接原因；Metric 数据在监控维度上确认了这一长期状态，而资源配置（Fact 4）显示资源极小且非限制因素，排除了资源不足的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector 'aiops.lab/unavailable=true' → 集群 3 个节点均无此标签 → 调度器返回 FailedScheduling (0/3 nodes match) → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为 **节点标签选择器不匹配**。
集群中所有节点均未设置标签 `aiops.lab/unavailable=true`，导致调度器无法将 Pod `aiops-case-01/workload-68c557d875-llhkh` 分配到任何节点（证据 1, 2）。

当前证据不足以判断该配置的意图：
- 是否属于配置错误（误填了禁止调度的标签）；
- 还是业务确实需要部署到具有该特定标签的节点（需确认集群中是否有带该标签的节点被隔离或未纳入查询范围）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.1s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 41.5s (Evidence 34.6s, RCA 6.7s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
