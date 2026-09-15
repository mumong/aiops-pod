## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v02/workload` 处于 `Pending` 状态 | 描述异常现象，确认 Pod 未运行 |
| 2 | K8s Config | kubernetes | Container `app` 配置 `memory.request=1Pi`、`memory.limit=1Pi` | 提供异常资源申请配置，说明集群调度所需资源量 |
| 3 | K8s Event | kubernetes | `Warning FailedScheduling`：`0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 解释 Pod Pending 的调度失败原因，集群节点内存不足且无抢占空间 |

**证据说明**
Kubernetes 事件 (第 3 项) 明确指出调度失败的具体原因为 `Insufficient memory`，集群中所有 3 个节点均无法满足 Pod 的资源请求。这与 Kubernetes 配置数据 (第 2 项) 中 Container `app` 申请的巨大内存量 `1Pi` 形成直接因果关联，排除了网络或插件故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 容器 'app' 配置 memory request=1Pi、limit=1Pi → 集群 3 个节点均无足够可用内存 → 调度器拒绝调度 (Insufficient memory) 且无可抢占的 Pod → Pod 保持 Pending 状态
```

### 根因结论
已确认根因为资源调度失败。Pod `aiops-case-v02/workload` 中的容器 `app` 配置了 `1Pi` 的内存请求 (同时 memory request 与 limit 均为 `1Pi`，fact-07621a2176e3, fact-4aab8a2360de)，这远远超出了集群所有节点当前的可用内存容量。调度器由于无法找到满足此资源需求的节点，返回了 `Insufficient memory` 错误并拒绝调度 (fact-45558bb254d6)，导致 Pod 一直处于 Pending 状态。集群中不存在能够承载该内存请求的节点资源。

---

## 📊 性能统计

```text
├─ 总耗时: 49.9s
├─ 问题定位: 16.7s
├─ 并发证据采集: 25.7s
│  └─ g1 aiops-case-v02/workload: 25.7s (Evidence 19.9s, RCA 5.7s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
