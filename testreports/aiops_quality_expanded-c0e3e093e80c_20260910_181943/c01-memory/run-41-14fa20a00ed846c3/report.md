## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 is stuck in Pending state (node: <none>) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v02/workload` status: `Pending` | 明确异常实体及其当前停滞状态 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling` (8 times over 61m): `0/3 nodes are available: 3 Insufficient memory` | 调度失败的直接原因，明确是资源不足导致 |
| 3 | K8s Config | Kubernetes | `resource_request.memory`: `1Pi` (Pebibyte) | 异常的资源需求数值，超出常规集群容量 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory`: `1Pi` | 内存硬限制同样为 1Pi，确认 Pod 意图申请该资源 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` `Pending`: `1` (sample_count: 1) | 确认当前 Pod 持续处于 Pending 阶段 |

**证据分析：**
1. 调度器事件（#2）与 Pod 状态（#1）相互印证，确认 Pod 因内存不足被 3 个节点全部拒绝。
2. 资源请求配置（#3, #4）提供了导致 #2 发生的直接上下文，即 Pod 声明了 `1Pi` 的内存需求，这在物理集群中极大概率不可用。
3. 度量数据（#5）仅用于辅助确认当前状态持续，无多周期趋势。
4. 由于容器未启动，Logging 和 Tracing 维度被标记为 `not_applicable`，物理上无法提供应用层证据。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 声明 memory limit/request 为 1Pi (1 Pebibyte) → Scheduler 评估节点可用内存无法满足请求 → 调度器对所有 3 个节点返回 Insufficient memory 错误 → Pod 停留在 Pending 状态，持续触发 FailedScheduling 事件
```

### 根因结论
已确认根因：Pod `aiops-case-v02/workload` 的内存请求（`resource_request.memory`）和限制（`resource_limit.memory`）均被设置为 **1Pi (1 Pebibyte)**。这一资源需求远超集群中任意节点的可用内存容量，导致 Kubernetes 调度器在执行调度决策时，发现所有 3 个节点均无法满足该需求（证据 #2, #3, #4），因此 Pod 无法被绑定到任何节点，持续处于 **Pending** 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 17.6s
├─ 并发证据采集: 557.6s
│  └─ g1 aiops-case-v02/workload: 557.6s (Evidence 550.6s, RCA 6.8s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
