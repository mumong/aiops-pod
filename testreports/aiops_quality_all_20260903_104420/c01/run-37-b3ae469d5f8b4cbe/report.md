## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态，未分配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-4050ad1bec07) | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认调度器因标签不匹配拒绝调度，失败持续 73 分钟。 |
| 2 | K8s Config | kubernetes (fact-08140c0ff057) | `container.app.memory: 8Mi`, `container.app.cpu: 5m` | 确认 Pod 资源请求极低，排除资源不足导致的调度失败。 |
| 3 | K8s State | kubernetes (fact-4218ce38b6ef) | `PodScheduled: False` (`reason: Unschedulable`) | 佐证 Pod 长期处于不可调度状态。 |
| 4 | Metric | prometheus (fact-0d648c0c7826) | `kube_pod_status_phase{phase="Pending"} = 1` (采样数: 1) | 确认 Pod 持续处于 Pending 阶段。 |
| 5 | Metric | prometheus (fact-0d9d49aaa55b) | `kube_pod_status_phase{phase="Succeeded"} = 0` (采样数: 1) | 确认 Pod 从未成功启动。 |

**证据印证说明：**
1. K8s Event 明确指出调度失败的原因是“节点不匹配 Pod 的 node affinity/selector”，而非资源耗尽（与 Fact 2 的低资源请求一致）。
2. Metric 确认 Pod 状态长期停留在 Pending，佐证了 Fact 1 中“持续 73 分钟”的调度失败现象。
3. Logging/Tracing 标记为 `not_applicable`，符合 Pod 未启动的物理事实，排除了应用层崩溃或业务错误的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector 要求 `aiops.lab/unavailable=true` → 集群 3 个节点均缺少该标签 → 调度器无法匹配任何可用节点触发 FailedScheduling → Pod 持续 Pending
```

### 根因结论

已确认根因为 **Pod 调度亲和性配置与集群节点标签不匹配**。
- Pod `aiops-case-01/workload-68c557d875-llhkh` 配置了 `nodeSelector: {aiops.lab/unavailable: 'true'}`。
- 集群所有可用节点（3 个）均缺少此标签，导致调度器 `FailedScheduling`，Pod 被无限期保持在 Pending 状态。
- 引用证据：Event `fact-4050ad1bec07`、Pod 状态 `fact-4218ce38b6ef`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.3s
├─ 并发证据采集: 68.9s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 68.9s (Evidence 59.0s, RCA 9.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
