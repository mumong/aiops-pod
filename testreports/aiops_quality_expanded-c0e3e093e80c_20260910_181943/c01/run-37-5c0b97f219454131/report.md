## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 的 nodeSelector 配置（aiops.lab/unavailable: true）与集群节点标签不匹配，导致调度器无法将 Pod 调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-aae53d5345ce) | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. | 明确调度器判定 Pod 亲和性/选择器不匹配，直接指出故障机制。 |
| 2 | K8s State | kubernetes (fact-18001a4a7df4) | `pod.condition`: `PodScheduled=False`, reason `Unschedulable` | 佐证 Pod 处于调度失败状态，与 Event 互为印证。 |
| 3 | K8s Config | kubernetes (fact-0f9a47ac2ff1) | `container.resource_request.memory`: 8Mi | 资源请求量极小，排除因资源配额不足导致无法调度的可能。 |
| 4 | Metric | prometheus (fact-0879b5634f13) | `kube_pod_status_phase(phase="Pending")`: 1 | 监控层面持续观测到 Pod 处于 Pending 状态。 |

日志与追踪维度均不可用（Pod 未启动）。K8s 状态、Event 事件与监控指标共同确证了 Pod 因调度规则（亲和性/选择器）与集群节点不符而陷入 Pending 状态。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了 nodeSelector (aiops.lab/unavailable=true) → 集群节点不匹配该标签 → 调度器匹配失败(0/3 nodes) → Pod 处于 Pending 状态
```

### 根因结论
已确认根因：Pod 的 `nodeSelector` 配置（`aiops.lab/unavailable: true`）与集群中 3 个节点的标签不匹配。证据表明调度器因亲和性选择器不匹配拒绝了所有候选节点（见证据 #1、#2），导致 Pod 持续处于 Pending 状态（见证据 #4）。资源配置量极小（见证据 #3），排除了资源瓶颈。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.1s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 33.8s (Evidence 25.9s, RCA 7.8s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
