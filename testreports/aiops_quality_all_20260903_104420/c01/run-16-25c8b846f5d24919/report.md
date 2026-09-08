## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status = Pending` (`fact-506fd8435319`) | 描述 Pod 当前未调度的状态事实。 |
| 2 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (`fact-43a8655c7a9d`) | 直接指出调度失败的机制是节点亲和性/选择器不匹配。 |
| 3 | K8s Config | kubernetes | `resource_request.cpu = 5m` (`fact-00b5da68a73b`) | 提供上下文资源请求，排除资源耗尽导致的调度失败。 |
| 4 | Metric | prometheus | `kube_pod_status_phase(phase=Pending) = 1` (`fact-cd1942c0a231`) | 确认 Pod 在指定时间窗口内确实处于 Pending 状态。 |
| 5 | Metric | prometheus | `kube_pod_status_phase(phase=Running) = 0` (`fact-14d7d51a23f2`) | 排除 Pod 处于运行状态的可能性，辅助确认当前故障现象。 |

**证据分析**：
1. **K8s 事件与资源配置互证**：Pod 处于 Pending 状态，且资源请求极低（5m CPU, 8Mi 内存），基本排除了因集群资源不足（CPU/Memory）导致的调度失败；调度器明确指出原因是“不匹配节点亲和性/选择器”（node affinity/selector）。
2. **指标状态支撑**：Prometheus 指标中 Pending 状态计数为 1，Running 状态为 0，与 Kubernetes 侧的 Pending 状态及 FailedScheduling 事件完全一致，共同指向该 Pod 因调度规则限制无法运行。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中包含不匹配的标签选择器 (nodeSelector) → 集群节点缺乏对应标签 → 调度器触发 FailedScheduling 事件 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-01/workload-68c557d875-llhkh` 处于 Pending 状态的根本原因是**其 `nodeSelector`（或节点亲和性）与集群中所有 3 个可用节点的标签不匹配**。
* **证据支持**：Kubernetes 事件（#2）明确记录了 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。
* **分析**：调度器在遍历了集群内全部 3 个节点后，因均未满足 Pod 的节点选择器要求而宣告失败，导致 Pod 无法被调度到任何节点。结合极低的资源请求量（#3），可确定该故障纯由标签/亲和性规则限制引起，而非资源瓶颈。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 30.8s
├─ 并发证据采集: 58.7s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 58.7s (Evidence 50.6s, RCA 8.0s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
