## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态且持续 91 分钟未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling`: 26m (x14 over 91m) 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. | 确认 Pod 长时间（91分钟）调度失败，且集群所有 3 个节点均因亲和性规则不匹配被过滤。 |
| 2 | K8s Config | Kubernetes | `container.resource_request.cpu`: 5m; `memory`: 8Mi; `limit.cpu`: 50m; `limit.memory`: 32Mi | 提供资源上下文，确认资源请求量极小，排除因资源不足（Insufficient CPU/Memory）导致的调度失败。 |
| 3 | K8s State | Kubernetes | `pod.condition` PodScheduled=False (reason: Unschedulable); `pod.phase`: Pending | 确认 Pod 当前处于未调度（Pending）状态，且调度条件持续为假。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` (Pending)=1; (Failed)=0 | 从监控数据层面印证 Pod 持续处于 Pending 状态，且未进入 Failed 状态。 |

**证据印证说明：**
Kubernetes 事件（证据 #1）与 K8s 状态（证据 #3）高度一致，均指向“因节点匹配失败导致无法调度”。资源配置数据（证据 #2）排除了资源短缺这一常见调度失败原因，反证了调度瓶颈在于节点标签匹配（Node Affinity/Selector）。Metric 数据（证据 #4）为 Pod 长期维持该状态提供了持续性的监控佐证。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了不存在的 nodeSelector 约束 (aiops.lab/unavailable=true) → 调度器过滤掉集群中所有 3 个节点 (0/3 nodes match) → 触发 FailedScheduling 事件，Pod 状态持续为 Pending → Pod 无法被分配到节点，处于 PendingUnschedulable 异常状态
```

### 根因结论

**已确认根因**：Pod 配置了节点选择器 `nodeSelector` 要求标签 `aiops.lab/unavailable=true`，但集群中所有 3 个节点均未配置该标签。

**分析**：Kubernetes 调度器的核心机制要求 Pod 必须满足其定义的所有 `nodeSelector` 约束才能被调度。根据事实 `FailedScheduling` 事件（证据 #1），集群中 3 个节点全部被过滤器排除，且错误信息明确指出是“didn't match Pod's node affinity/selector”。结合 Pod 极低的资源请求（证据 #2），排除资源瓶颈，确认调度失败完全由标签不匹配引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.1s
├─ 并发证据采集: 38.4s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 38.4s (Evidence 30.3s, RCA 7.9s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
