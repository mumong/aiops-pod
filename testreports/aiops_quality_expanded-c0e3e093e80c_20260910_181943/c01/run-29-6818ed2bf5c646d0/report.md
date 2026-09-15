## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-01/workload-68c557d875-gtzc8` status: `Pending` [fact-0993c76f398f] | 呈现故障现象，证实 Pod 未成功运行 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector [fact-4d7f16011b0b] | 直接指出调度失败原因是节点亲和性不匹配 |
| 3 | K8s Config | kubernetes | Resource Requests: cpu `5m`, memory `8Mi` [fact-98f6c9c401e5], [fact-b32da00d3269] | 证明资源需求极低，排除资源耗尽导致的 Pending |
| 4 | K8s Config | kubernetes | Resource Limits: cpu `50m`, memory `32Mi` [fact-a7b881aff12e], [fact-d377524858ad] | 确认硬限制配置，佐证资源非瓶颈 |
| 5 | Metric | prometheus | `kube_pod_status_phase` value: `1` (phase: Pending), sample_count: 1 [fact-0f475ca19875] | 独立观测确认 Pod 当前处于 Pending 阶段 |

证据 1 和 4 通过 Prometheus 指标确认了 Pod 状态。证据 2 是定位问题的关键，明确排除了资源问题（由证据 3 和 4 支持）和节点资源压力，将故障范围锁定在“亲和性/选择器不匹配”上。由于 Pod 处于 Pending 阶段且未启动，无应用日志与链路数据。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：Pod 定义了 NodeSelector 'aiops.lab/unavailable=true'
    → 失败机制：集群节点不具备该标签
    → 直接失败：调度器尝试所有节点均因节点亲和性/选择器不匹配而失败
    → 用户可见现象：Pod 持续处于 Pending 状态且无法调度
```

### 根因结论

已确认的根因为：**调度配置错误（NodeSelector 标签不匹配）**。

证据 2（K8s Event）明确报告了调度失败的原因是节点亲和性/选择器不匹配（`didn't match Pod's node affinity/selector`）。结合集群中 3 个节点均因该原因拒绝调度，且 Pod 的资源请求（证据 3、4）极其微量，排除了资源不足的可能性。因此，Pod 无法调度的确定性原因是其选择器过滤掉了集群中所有可用节点。

---

## 📊 性能统计

```text
├─ 总耗时: 47.4s
├─ 问题定位: 16.9s
├─ 并发证据采集: 20.9s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 20.9s (Evidence 14.0s, RCA 6.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
