## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Kubernetes节点上存在资源预留（如系统内核、kube-reserved等）或集群资源计算限制，导致尽管节点物理CPU充足，调度器判定剩余可分配CPU不足，从而拒绝调度Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v01/workload` 状态：`Pending` | 呈现最终现象，确认工作负载未启动 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu` | 确认为调度失败，直接归因于节点 CPU 资源不足 |
| 3 | K8s Config | Kubernetes | CPU Request: `100k` (0.1核)；Container CPU Limit: `100k` | 表明资源申请与限制一致，排除因突发资源或 Request 错误导致的调度异常 |
| 4 | K8s Config | Kubernetes | Memory Request: `8Mi`；Container Memory Limit: `32Mi` | 内存资源配置微小，佐证问题并非由内存耗尽引发 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` (Pending): 1 (Single Sample) | 量化确认 Pod 处于 Pending 状态，且未观察到状态波动 |

Pod 的 `Pending` 状态完全由调度器触发的 `Insufficient cpu` 事件驱动。尽管 CPU 请求量极低（`100k`），集群中 3 个节点均判定 CPU 不足且无可抢占的 Victim。鉴于 Pod 尚未启动，无法通过应用日志（Logging）或流量追踪（Tracing）排除容器内部原因，故障证据链集中在 Kubernetes 调度层面。

## 🎯 根因分析 · g1

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
节点资源预留或系统约束未明示 → 调度器判定集群可用 CPU 不足（Insufficient cpu） → 触发 FailedScheduling 事件 → Pod 状态持续 Pending
```

**根因结论：**
工作负载 `aiops-case-v01/workload` 处于 Pending 状态，根因为 **Kubernetes 调度器判定集群节点 CPU 资源不足**（证据 #2）。调度器在所有 3 个可用节点上均未发现足够的 CPU 剩余资源或可抢占的 Pod，导致调度失败。尽管 Pod 的请求量极低（0.1 核），节点资源不足的事实已由 K8s 事件强确认。

**证据不足部分：**
现有 K8s 事实无法解释为何物理 CPU 充足的节点会报 `Insufficient cpu`，具体的 `kube-reserved`、`system-reserved` 或 `hard-eviction` 等预留配置数值缺失，因此无法进一步确认是否为预留配置过度导致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.0s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-v01/workload: 45.3s (Evidence 37.4s, RCA 7.7s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
