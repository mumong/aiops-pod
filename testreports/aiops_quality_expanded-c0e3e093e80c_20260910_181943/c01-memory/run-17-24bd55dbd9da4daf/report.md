## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 namespace is stuck in Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (fact-9d293c187066) | 调度器直接报告集群所有 3 个节点均因内存不足且无抢占受害者而拒绝调度。 |
| 2 | K8s Config | kubernetes | 容器 `app` 请求/限制配置：`memory=1Pi`, `cpu_request=5m`, `cpu_limit=50m` (fact-18015d479d2f, fact-804380571432) | 定义资源约束；1Pi（1 Petabyte）的内存配置远超常规节点规格，是导致“Insufficient memory”的直接原因。 |
| 3 | K8s State | kubernetes | Pod `workload` 处于 `Pending` 状态 (fact-b1de43bbccde) | 确认 Pod 未能通过调度阶段，未进入运行态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase=Pending) 值为 1, sample_count=1 (fact-787e6fea77bb) | 确认 Pod 当前持续处于 Pending 阶段，无 Running 样本。 |

**证据分析**：
调度事件（#1）明确指出所有节点内存不足。K8s 配置（#2）证实 Pod 请求了 1Pi 内存。在单节点物理硬件无法提供 1Pi 内存的情况下，调度失败是必然结果。状态（#3）和监控（#4）确认了故障的持续性。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置 memory 设置为 1Pi (1 Petabyte) → 调度器尝试寻找满足该资源的节点 → 集群节点内存无法满足，且无更高优先级 Pod 可抢占 (No preemption victims) → Pod 停留在 Pending 状态
```

### 根因结论
已确认根因：**Pod 资源请求配置存在严重错误**。
Pod `workload` 将内存请求和限制（`resource_request.memory` 和 `resource_limit.memory`）均设置为 `1Pi`。这一数值远超集群中任何单节点的物理内存容量，导致 `default-scheduler` 在所有 3 个节点上均判定资源不足（`Insufficient memory`）并拒绝调度。

**证据支撑**：
- 调度事件明确指出“3 Insufficient memory”及无抢占受害者 (#1)。
- K8s 配置证实了 `1Pi` 的内存请求值 (#2)。

---

## 📊 性能统计

```text
├─ 总耗时: 52.2s
├─ 问题定位: 12.5s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-v02/workload: 30.5s (Evidence 22.6s, RCA 7.9s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
