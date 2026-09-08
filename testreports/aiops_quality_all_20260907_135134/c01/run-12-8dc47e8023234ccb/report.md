## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 处于 Pending 状态，持续无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` (fact-a5d5eccd6312) | `PodScheduled: False (Unschedulable)` - "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" | 确认 Pod 被调度器拒绝，并直接指出失败原因是节点亲和性/选择器不匹配。 |
| 2 | K8s Event | `event.message` (fact-0a02f215376a) | `FailedScheduling` (重复 2 次) - "3 node(s) didn't match Pod's node affinity/selector" | 记录异常触发时间跨度（15分钟内），确认调度器一直在尝试调度但持续失败。 |
| 3 | K8s Config | `resource_request` (fact-7ab1758a6bb2) | `cpu: 5m`, `memory: 8Mi` | 作为配置上下文：资源请求量极小，排除因资源不足（CPU/内存）导致无法调度的可能性。 |
| 4 | K8s Config | `resource_limit` (fact-0312866640d4) | `cpu: 50m`, `memory: 32Mi` | 作为配置上下文：确认资源限制与请求匹配且极低，进一步佐证非资源瓶颈问题。 |
| 5 | Metric | `kube_pod_status_phase` (fact-ee6f1fbc1329) | `Pending: 1` | 辅助验证：Prometheus 指标确认 Pod 处于 Pending 状态，无 Succeeded 状态样本。 |
| 6 | Logging | `query_pod_logs` | `not_applicable` (容器未启动，无日志产生) | 说明当前维度无法获取应用行为数据，符合 Pod 处于 Pending 状态的事实。 |

**证据说明：**
- 证据 #1、#2 直接证明调度失败是由“节点亲和性/选择器不匹配”（node affinity/selector mismatch）引起的。
- 证据 #3、#4 提供的极低资源请求值，排除了集群资源不足导致调度的可能性，将故障范围缩小至标签匹配逻辑问题。
- 证据 #5 提供了观测层面的旁证，确认 Pod 处于持续挂起状态，且没有运行成功的迹象。

## 🎯 根因分析 · g1

### 因果链

```text
nodeSelector 配置要求匹配节点标签 aiops.lab/unavailable=true → 调度器在所有 3 个节点上匹配失败 → FailedScheduling 事件触发，Pod 保持 Pending 且 nodeName 为 None → Pod 未启动，无日志和追踪数据
```

### 根因结论

**已确认根因：Pod 的 nodeSelector 配置要求匹配节点标签 `aiops.lab/unavailable=true`，但集群中无节点满足此条件。**

- **机制说明**：Kubernetes 调度器（default-scheduler）在尝试调度 Pod `workload-68c557d875-bsq52` 时，检查集群内所有 3 个可用节点。由于配置了特定的标签匹配要求（`node affinity/selector`），且集群中没有任何节点携带 `aiops.lab/unavailable=true` 标签，调度器判定所有节点均不可用（`0/3 nodes are available`）。
- **证据支撑**：
  - `fact-a5d5eccd6312` (K8s State) 和 `fact-0a02f215376a` (K8s Event) 明确指出失败原因是 `didn't match Pod's node affinity/selector`。
  - 低资源请求 (`fact-7ab1758a6bb2`) 排除了资源不足。
  - Logging/Tracing 缺失 (`not_applicable`) 符合 Pod 尚未被调度到任何节点、容器未启动的物理状态。

---

## 📊 性能统计

```text
├─ 总耗时: 56.7s
├─ 问题定位: 22.3s
├─ 并发证据采集: 21.5s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 21.5s (Evidence 13.6s, RCA 7.8s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
