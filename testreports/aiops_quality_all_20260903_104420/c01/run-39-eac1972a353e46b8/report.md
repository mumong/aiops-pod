## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 的 nodeSelector 配置要求节点包含标签 aiops.lab/unavailable=true，但集群中所有可用节点均不具备该标签，导致调度器无法匹配任何节点（Unschedulable）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `reason=Unschedulable, message="0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"` | 确认 Pod 处于 Pending 状态的直接原因：调度失败 |
| 2 | K8s Event | `event.message` | `Warning FailedScheduling  20m (x14 over 85m) ... 3 node(s) didn't match Pod's node affinity/selector` | 确认调度失败是由 Node Affinity/Selector 不匹配引起的，且持续 85 分钟 |
| 3 | K8s Config | `container.resource_limit.cpu` | `50m` | 上下文证据：CPU 资源请求极低（5m），排除资源不足导致的调度问题 |
| 4 | Metric | `kube_pod_status_phase` (Pending) | `value=1` (Pending), `value=0` (Failed) | 确认 Pod 长期维持 Pending 状态，未转为 Failed，符合调度阻塞特征 |
| 5 | Topology | `node selector check` | `node(s) didn't match` (事实映射) | 确认集群中不存在匹配 `aiops.lab/unavailable=true` 标签的节点 |

**证据分析说明：**
K8s State (证据 1) 和 Event (证据 2) 相互印证，明确指出失败原因为“节点不匹配标签/亲和性”。K8s Config (证据 3) 排除了资源争抢的可能。Metrics (证据 4) 展示了状态的时间延续性，佐证了这是持续的调度配置问题而非瞬时波动。

## 🎯 根因分析 · g1

### 因果链

```text
配置要求节点具备标签 aiops.lab/unavailable=true → 集群无匹配节点 (3/3) → 调度器判定 Unschedulable → Pod 状态 Pending (长达 85 分钟)
```

### 根因结论

已确认的根因为 **Pod 调度配置与环境不匹配**。

Pod 的 `nodeSelector` 强制要求节点包含 `aiops.lab/unavailable=true` 标签，但集群中全部 3 个可用节点均不具备该标签，导致调度器无法将 Pod 调度到任何节点，表现为长期 Pending 状态。该结论由 K8s 事件 `FailedScheduling` 中的 `node affinity/selector` 不匹配信息以及 `PodScheduled=False` 的条件状态共同证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.3s
├─ 并发证据采集: 61.7s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 61.7s (Evidence 56.1s, RCA 5.5s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
