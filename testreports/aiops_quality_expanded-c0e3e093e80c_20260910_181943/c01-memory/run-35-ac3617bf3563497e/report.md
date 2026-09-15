## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod `aiops-case-v02/workload` 处于 Pending 状态，调度器返回 0/3 nodes available: 3 Insufficient memory。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `aiops-case-v02/workload` | `Pending` | 证实 Pod 未调度，处于待处理状态 |
| 2 | K8s Event | `default-scheduler` | `FailedScheduling 0/3 nodes available: 3 Insufficient memory` | 证明调度失败的根本原因为内存资源不足 |
| 3 | K8s Config | `container.app` | `memory limit = 1Pi`, `memory request = 1Pi` | 异常事实：Pod 定义中配置了 1Pi 的内存需求 |

**证据关联分析**：
事件 `fact-baba6c802802` 指出集群 3 个节点均无法满足 Pod 的资源请求。事实 `fact-43dc1d9c83cc` 和 `fact-a9914b2b78c6` 显示 Pod 的内存 `request` 和 `limit` 均为 1Pi（1 Pebibyte）。这一极端数值远超普通节点容量，直接导致调度器因 `Insufficient memory` 拒绝调度，进而使 Pod 维持在 `Pending` 状态（证据 #1）。Metric 仅确认了 Pod 持续处于 Pending 阶段，未提供其他冲突信息。

## 🎯 根因分析 · g1

```text
Pod 定义中 memory limit 设置为 1Pi → 调度器以 limits (1Pi) 作为资源需求评估 → 集群 3 个节点的可分配内存均远小于 1Pi，调度器判定 Insufficient memory → Pod 无法调度，持续处于 Pending 状态
```

**根因结论**：
已确认根因为 **Pod 资源配置错误**。Pod 的 `memory limit` 被错误设置为 `1Pi`，导致 `memory request` 自动继承该极大值。这超出了集群所有节点的可分配内存上限，引发持续的 `FailedScheduling` 事件。
*   直接证据：调度器返回 `3 Insufficient memory` 事件（证据 #2）。
*   配置异常：`memory request` 高达 `1Pi`（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.5s
├─ 并发证据采集: 45.2s
│  └─ g1 aiops-case-v02/workload: 45.2s (Evidence 37.6s, RCA 7.5s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
