## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 配置了 nodeSelector {aiops.lab/unavailable: true}，但集群中不存在该标签的节点，导致调度器无法将 Pod 调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling 18m (x7 over 48m) ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-3ae23597f1a6) | 确认调度器连续尝试失败的核心原因。 |
| 2 | K8s State | Kubernetes | `pod.status: Pending`, `pod.condition: False (Unschedulable)` (fact-25865972c19b, fact-343be9183dab) | 确认 Pod 当前处于不可调度状态。 |
| 3 | K8s Config | Kubernetes | `container.resource_request.cpu: 5m`, `container.resource_request.memory: 8Mi`, `container.resource_limit.cpu: 50m`, `container.resource_limit.memory: 32Mi` (fact-971a54b29992 等) | 证明资源请求极低，排除资源耗尽导致的调度失败。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 当前值为 1 (Pending)，0 为 Succeeded，样本数 1 (fact-1d06bc138879) | 确认 Pod 长期未进入运行或完成状态。 |
| 5 | Logging | Elasticsearch | 物理上未产生日志（容器未启动） | 日志缺失佐证了故障发生在调度阶段，应用层无交互。 |

**证据印证说明：**
Kubernetes Event (fact-3ae23597f1a6) 明确指出 3 个节点均未匹配 Pod 的亲和性/选择器，结合 Resource Config (fact-971a54b29992) 中极低的资源门槛，证实调度失败纯粹是由拓扑标签（nodeSelector）不匹配导致，而非资源不足。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的 nodeSelector {aiops.lab/unavailable: true} → 调度器校验失败，无满足条件的节点 → Pod 状态变为 Unschedulable (Pending) → 应用无法启动
```

### 根因结论

已确认的根因是**调度策略与集群拓扑不匹配**。
具体为：Pod `aiops-case-01/workload-68c557d875-bsq52` 声明了 `nodeSelector`（即 `aiops.lab/unavailable: true`），但集群中所有 3 个节点均不具备该标签。

此配置直接触发了 Kubernetes 调度器的 `FailedScheduling` 事件（见证据 #1），导致 Pod 长期处于 `Pending` 状态（见证据 #2, #4）。低资源请求（见证据 #3）排除了计算资源不足的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 29.1s
├─ 并发证据采集: 28.7s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 28.7s (Evidence 24.0s, RCA 4.6s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
