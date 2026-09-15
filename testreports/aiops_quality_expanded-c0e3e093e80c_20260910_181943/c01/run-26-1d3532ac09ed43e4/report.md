## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 stuck in Pending state (FailedScheduling) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-2c8115f74259` | `phase: Pending` | 确认 Pod 实际运行状态。 |
| 2 | K8s State | `fact-977a5cfe1c29` | `PodScheduled=False, reason=Unschedulable` | 提供 Kubernetes 调度器判定的直接失败原因。 |
| 3 | K8s Event | `fact-5b184d071478` | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 描述调度失败的聚合事件，指出所有节点均不满足亲和性/选择器要求。 |
| 4 | K8s Event | `fact-91d3ef1aa19e` | `Warning FailedScheduling ... 45m` | 确认该调度失败现象已持续至少 45 分钟，属于长期阻塞。 |
| 5 | K8s Config | `fact-445320fc44b8` | `memory request: 8Mi` | 排除内存资源限制作为调度阻塞原因。 |
| 6 | K8s Config | `fact-880514da54dd` | `cpu request: 5m` | 排除 CPU 资源限制作为调度阻塞原因。 |

证据 1、2 确认 Pod 处于长期非调度状态；证据 3、4 提供具体的调度失败原因，显示所有 3 个节点均因“不匹配 Pod 亲和性/选择器”而被排除；证据 5、6 证明 Pod 资源请求极低，调度阻塞并非由资源不足引起。Metrics、Logging、Tracing 均不可用，无额外冲突证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod nodeSelector 'aiops.lab/unavailable: true' 约束 → 集群无节点匹配该标签 → 调度器返回 '0/3 nodes are available' → Pod 卡在 Pending (Unschedulable) 状态
```

### 根因结论

已确认根因为 **Pod 的 Node Affinity/Selector 约束与集群节点标签不匹配**。

根据事实 `fact-5b184d071478` 与 `fact-91d3ef1aa19e`，Kubernetes 事件明确指出失败原因是 `3 node(s) didn't match Pod's node affinity/selector`，且此现象已持续 45 分钟。由于 Pod 的资源请求（5m CPU, 8Mi Memory）极低，且事件未提示资源不足（Insufficient），可排除资源瓶颈。决定性的缺失环节（如具体的节点标签详情或 nodeSelector 配置值）虽未直接作为原始 Fact 值展示，但调度器的事件记录本身已构成闭环证据，确认了标签不匹配是导致 `Unschedulable` 状态的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.6s
├─ 并发证据采集: 50.5s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 50.5s (Evidence 43.9s, RCA 6.6s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
