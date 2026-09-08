## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态且无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `Warning FailedScheduling 56m ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 提供直接证据：调度器因无法匹配亲和性/选择器而放弃调度 |
| 2 | K8s Config | container resource | `cpu.request=5m, cpu.limit=50m; memory.request=8Mi, memory.limit=32Mi` | 提供上下文：确认 Pod 资源配置极低，排除了资源不足导致调度失败的可能性 |
| 3 | K8s State | Pod Status | `phase: Pending`, `PodScheduled: False (Unschedulable)` | 描述现象：Pod 停留在 Pending 状态且调度条件未满足 |

**证据关联说明**：
证据 3 (Pod 未调度) 是现象表现。证据 1 (调度器事件) 明确了导致该现象的直接技术原因——节点标签/亲和性不匹配。证据 2 证实资源消耗极低，排除了资源不足（Resource Insufficient）的干扰。日志和追踪维度因容器未启动而不可用（`not_applicable`），但不影响基于 K8s 调度器日志对调度失败原因的定性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector: aiops.lab/unavailable=true → 集群节点缺乏该标签 → 调度器触发 FailedScheduling 并返回 Unschedulable → Pod 保持 Pending 状态
```

### 根因结论

**根因**：Pod 定义了 `nodeSelector: aiops.lab/unavailable=true`，而集群中现有的 3 个节点均不具备该标签，导致调度器无法找到任何符合要求的节点（证据 1）。

**排除因素**：Pod 的 CPU 请求 (5m) 和内存请求 (8Mi) 极低（证据 2），排除了资源竞争或资源不足的可能性。

**现状**：基于现有事实，根因已确认。

---

## 📊 性能统计

```text
├─ 总耗时: 57.4s
├─ 问题定位: 16.7s
├─ 并发证据采集: 33.5s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 33.5s (Evidence 26.7s, RCA 6.7s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
