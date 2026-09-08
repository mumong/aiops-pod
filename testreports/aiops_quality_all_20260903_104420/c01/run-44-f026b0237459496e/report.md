## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod workload-68c557d875-llhkh 持续处于 Pending 状态且未分配 Node，调度失败已持续超过 93 分钟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact-8277880ee1c9) | 核心证据：明确指出了调度失败原因是节点匹配标签选择器（node affinity/selector）失败。 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling ...` (持续发生 x14 over 93m, fact-b481a1c41f8c) | 佐证故障持续时间长且未被自愈，排除短暂网络抖动或资源瞬时不足。 |
| 3 | K8s State | Kubernetes | `PodScheduled: False` 状态持续存在 (fact-28357debf7ca) | 确认 Pod 未获得任何节点分配，处于阻塞状态。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 32Mi` (fact-0cb38b0491a0), `container.resource_request.cpu: 5m` (fact-6b05a6b1839f) | 排除资源容量不足：Pod 请求资源极低，集群节点通常能够满足，进一步指向非容量型调度问题。 |

**证据分析：**
Kubernetes Event (fact-1) 和 State (fact-3) 共同证实了 Pod 被调度器拒绝绑定。关键在于 `3 node(s) didn't match Pod's node affinity/selector` 这一错误信息，它直接指向了调度逻辑中的标签匹配环节，而非资源不足（Node Unavailable for resources）。结合事实中未提供集群节点的详细标签列表，但 Event 已明确判定“不匹配”，表明集群节点层面存在硬性约束违反。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了 nodeAffinity/selector (需匹配 aiops.lab/unavailable=true) → 集群现有节点均缺少该标签 → 调度器因不匹配拒绝绑定 (FailedScheduling) → Pod 持续 Pending 超过 93 分钟
```

### 根因结论
**已确认根因：节点亲和性与选择器配置错误（Node Affinity/Selector Mismatch）。**

Pod `workload-68c557d875-llhkh` 的调度约束要求节点必须匹配特定的标签（如 `aiops.lab/unavailable=true`，依据诊断输入），但集群内所有 3 个节点均未设置该标签，导致 `default-scheduling` 无法找到任何可用节点。

证据 (fact-1) 明确指出 `3 node(s) didn't match Pod's node affinity/selector`，且资源请求极低（fact-4），排除了资源争用。该配置错误直接导致调度决策失败，是造成 Pod 长期 Pending 的唯一有效原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 56.4s
├─ 并发证据采集: 44.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 44.2s (Evidence 35.7s, RCA 8.3s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
