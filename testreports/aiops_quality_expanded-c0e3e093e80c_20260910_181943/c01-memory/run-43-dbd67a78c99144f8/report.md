## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload (aiops-case-v02) remains Pending with node <none> |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`：`0/3 nodes are available: 3 Insufficient memory` | 证实所有节点因内存不足无法调度，直接原因 |
| 2 | K8s Config | kubernetes | 容器 `app` `memory_request`: `1Pi` | 证实请求值达到 1Pi，导致调度器要求分配 1Pi 内存 |
| 3 | K8s Config | kubernetes | 容器 `app` `memory_limit`: `1Pi` | 证实无独立请求值时请求值继承自硬限制 1Pi |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase=Pending) 当前值: `1` (sample_count: 1) | 确认 Pod 当前处于 Pending 状态 |

- **结论 1**：根据规则 `resource_request` 是调度保留量，且当未独立配置 `request` 时，调度器通常使用 `limit` 作为调度请求。证据 #2 和 #3 显示 Pod 被配置为 `1Pi` (1,125,899,906,842,624 字节) 的内存配置，这超出了集群任何单节点的可分配内存（证据 #1 指出所有 3 个节点均 `Insufficient memory`），从而解释了 `FailedScheduling` 事件。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存配置为 1Pi (request 继承 limit) → 调度器无法满足单节点 1Pi 内存分配需求 → 调度器因 Insufficient memory 失败 → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod 的内存资源配置错误。

- **配置不当导致调度失败**：Pod `aiops-case-v02/workload` 被配置为 `1Pi` 的 `memory_limit`（证据 #3），且未设置独立的 `memory_request`，导致调度器根据 `memory_request`（即 `1Pi`，证据 #2）尝试分配该量级的内存。
- **资源超限**：集群中没有任何一个节点拥有 `1Pi` 的可分配内存，导致所有节点（0/3）均因 `Insufficient memory` 被拒绝（证据 #1）。
- **现象确认**：Pod 因此无法被调度，保持在 `Pending` 状态（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 58.0s
├─ 问题定位: 14.0s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v02/workload: 35.7s (Evidence 28.4s, RCA 7.2s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
