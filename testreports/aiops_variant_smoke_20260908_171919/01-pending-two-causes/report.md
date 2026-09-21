## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload (aiops-case-v01) stuck in Pending status |
| g2 | `aiops-case-v02/workload` | Pending | Pod resource limits request mismatch: container 'app' specifies a memory limit of 1Pi but lacks an explicit memory request. The scheduler interprets this constraint (using the limit as a proxy or strictly enforcing the 1Pi requirement against allocatable resources), which exceeds the available memory on all 3 nodes, resulting in FailedScheduling. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `PodScheduled` status: `False`, reason: `Unschedulable`, message: `0/3 nodes are available: 3 Insufficient cpu` | 直接确认调度器因集群节点 CPU 资源耗尽而无法调度 Pod |
| 2 | K8s Config | `container.resource_request.cpu` | `app` 容器请求: `100k` (0.1 CPU) | 提供调度失败的触发资源需求量 |
| 3 | K8s Event | `event.message` | `Warning FailedScheduling 84s default-scheduler 0/3 nodes are available: 3 Insufficient cpu` | 验证所有 3 个节点均处于 CPU 不足状态且无抢占机会 |
| 4 | Metric | `kube_pod_status_phase` | 状态 `Pending` 值为 `1` (仅 1 个样本，无趋势) | 通过指标层面确认 Pod 持续处于 Pending 状态 |

**证据关联说明：**
Kubernetes 状态与 Event 均指向同一结论：集群中所有 3 个节点均已耗尽 CPU 资源。Pod 虽然仅请求了 `100k` (0.1 CPU) 的微小资源，仍无法满足。Metric 数据佐证了 Pod 持续未变动的 Pending 状态。由于 Pod 无法调度启动，Logging 和 Tracing 维度无数据属于物理上的不可达，进一步确认故障位于调度阶段而非运行时。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源已耗尽 (0/3 可用) → 调度器无法找到满足 100k CPU 需求的节点 → Pod 处于 Unschedulable 状态 → 用户可见 Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：集群资源耗尽（Cluster CPU resource exhaustion）。

证据表明，调度器检查了集群内全部 3 个节点，结果显示所有节点均存在 `Insufficient cpu`。尽管该 Pod (`aiops-case-v01/workload`) 的 CPU 请求量 (`100k`) 较低，但集群中不存在任何可用的剩余 CPU 资源，且因无抢占受害者 (No preemption victims)，调度被阻塞。Pod 因此被标记为 `Unschedulable` 并保持在 `Pending` 状态。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` | 确认调度失败直接原因为内存资源不足，且无法抢占 |
| 2 | K8s Config | Kubernetes | `container 'app'` 内存限制 `resource_limit` = 1Pi，内存请求 `resource_request` = 1Pi | 确认 Pod 向调度器申请了极大的内存资源作为最低保障 |
| 3 | K8s State | Kubernetes | Pod `aiops-case-v02/workload` 状态为 `Pending`，`PodScheduled` 条件为 `False` | 确认 Pod 卡在调度阶段，未进入运行态 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 显示 `Pending=1`，无 `Running` 记录 | 从监控系统层面印证 Pod 长期处于未调度状态 |

**证据小结**
事件日志 (Fact 1) 明确指出 3 个节点均无法满足内存需求。配置数据 (Fact 2) 揭示了请求值为 1Pi (1 Peta-byte)，这是一个极其庞大的数值，直接解释了为何节点资源不足 (Fact 1)。Pod 状态 (Fact 3) 和监控指标 (Fact 4) 一致表明该 Pod 始终未能脱离 Pending 状态。

## 🎯 根因分析 · g2

### 因果链

```text
Pod 资源申请过大 (1Pi) → 节点资源评估不匹配 → 调度器判定 Insufficient memory → FailedScheduling
```

### 根因结论

已确认的根因为 **Pod 资源配置严重超标导致调度失败**。容器 `app` 将内存请求 (`resource_request`) 设置为 `1Pi`，这一数值远超集群中任意节点的实际可用物理内存，导致调度器在所有 3 个节点上均因 `Insufficient memory` 判定失败 (参考证据 1 和 2)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 33.3s
├─ 并发证据采集: 48.1s
│  ├─ g1 aiops-case-v01/workload: 48.1s (Evidence 42.7s, RCA 5.3s)
│  └─ g2 aiops-case-v02/workload: 37.5s (Evidence 30.9s, RCA 6.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
- **g2 aiops-case-v02/workload**: pod-pending-unschedulable
