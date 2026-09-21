## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1-p1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源耗尽导致调度器无法为 Pod 分配节点 |
| g1-p2 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，未分配节点 |
| g1-p3 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，调度器返回 FailedScheduling 错误 |

---

## 🕵️ 证据内容 · g1-p1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `Pod(aiops-case-v01/workload)` 状态为 `Pending` | 确认当前 Pod 处于未运行状态，为待调度现象。 |
| 2 | K8s Event | `kubernetes` | `Warning FailedScheduling 73s`：`0/3 nodes are available: 3 Insufficient cpu` | 直接证明调度失败的原因是集群 3 个节点均无可用 CPU 资源。 |
| 3 | K8s Config | `kubernetes` | `app` 容器的 CPU `resource_request` 和 `resource_limit` 均为 `100k` (0.1 CPU) | 揭示该 Pod 的资源需求配置，调度失败源于此请求无法满足而非配置异常。 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase{container="kube-state-metrics", phase="Pending"}` 值为 `1` (采样数: 1) | 辅助验证系统中存在处于 Pending 状态的 Pod 记录，但因单样本无法判断趋势，仅作为当前状态的佐证。 |

**证据链说明**：
K8s 事件（证据 2）明确指出了资源耗尽的具体指标（CPU），并排除了抢占机制（`No preemption victims found`）的影响；该事件直接导致了 Pod 状态（证据 1）维持在 `Pending`。Pod 的 CPU 请求（证据 3）虽然仅为 0.1 CPU，但在集群整体可用量为零的情况下无法被满足。Metrics（证据 4）仅提供了当前时刻的状态快照。

## 🎯 根因分析 · g1-p1

### 因果链

```text
集群 3 个节点（master, node1, node2）可用 CPU 资源耗尽 → 调度器在遍历所有节点时均判定为 Insufficient cpu 且无抢占受害者 → 抛出 FailedScheduling 事件并维持 Pod(aiops-case-v01/workload) 状态为 Pending → 用户侧观察到 Pod 无法被调度且未运行
```

### 根因结论

**已确认根因**：集群节点 CPU 资源耗尽。
**分析**：
1. **直接原因**：Kubernetes 调度器在尝试将 `aiops-case-v01/workload` 分配至 `master`、`node1` 和 `node2` 三个节点时，均返回“Insufficient cpu”错误（证据 2）。
2. **机制排除**：事件日志明确指出“`preemption: 0/3 nodes are available`”，说明即使启用了抢占策略也无法找到可抢占的 Pod 来释放资源，表明集群整体处于资源完全饱和状态。
3. **现象确认**：Pod 因此处于 `Pending` 状态（证据 1），且其 CPU 配置（0.1 CPU）并非导致集群资源耗尽的唯一原因，而是集群环境本身无法提供哪怕 0.1 CPU 的可用资源。

现有 K8s 状态与事件事实已形成闭环，证据充分，无需引入日志或追踪数据即可确认根因为**集群 CPU 资源耗尽导致调度失败**。

---

## 🕵️ 证据内容 · g1-p2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.. (fact-521cfb45ef59) | 直接原因：调度器评估所有节点内存均不足且无法抢占 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory`: 1Pi (fact-5527eaef1ce6) | 核心异常：Pod 申请了 1Pi (16 EiB) 的内存，属于明显配置错误 |
| 3 | K8s State | kubernetes | `pod.condition (PodScheduled)`: status=False, reason=Unschedulable, message="0/3 nodes are available: 3 Insufficient memory." (fact-50590908bba1) | 状态确认：Pod 处于 Unschedulable 状态，验证调度器反馈 |
| 4 | K8s State | kubernetes | `pod.phase`: Pending (fact-87bcebcbd337) | 现象：Pod 长期停留在 Pending 状态，未调度到任何节点 |
| 5 | Metric | prometheus | `kube_pod_status_phase`: Pending=1 (fact-0d5a8c00d727) | 指标佐证：Prometheus 观测到该 Pod 处于 Pending 状态 (fact-0d5a8c00d727) |

**证据总结**：
事实 1 和 3 确认了 K8s 调度器的拒绝行为（3/3 节点 Insufficient memory）。事实 2 提供了导致这一结果的直接原因（请求了 1Pi 内存）。事实 4 和 5 从 Pod 状态层面确认了该异常一直持续。

## 🎯 根因分析 · g1-p2

### 因果链

```text
Pod 资源定义错误：requests.memory=1Pi → 调度器内存评估失败：1Pi 超过所有 3 个节点的 Allocatable 内存 → 调度拒绝：3 Insufficient memory → 现象：Pod Pending 且处于 Unschedulable 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-v02/workload` 的内存请求配置错误。

该 Pod 配置了 `1Pi`（1 Pebibyte，约 16 EiB 字节）的 `requests.memory`，这一数值远超集群中所有节点的最大可分配内存（通常在几十 GiB 级别）。调度器在执行资源调度时，发现没有节点的可用内存能够满足此请求，且无其他 Pod 可被抢占，因此对所有 3 个节点均返回 `Insufficient memory`。这导致 Pod 无法被调度，从而长期处于 `Pending` 状态。

**关键证据引用**：
- `fact-5527eaef1ce6`: 确认了 1Pi 的请求值。
- `fact-521cfb45ef59`: 调度事件明确记录了 Insufficient memory。
- `fact-50590908bba1`: 确认了 Unschedulable 条件。

---

## 🕵️ 证据内容 · g1-p3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `Warning FailedScheduling 64s default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 直接指出 Pod 因找不到 PVC `unavailable-claim` 而被调度器拒绝。 |
| 2 | K8s Config | pod.spec | Volume 引用 PVC `unavailable-claim`，但集群中未找到该 PVC 的定义。 | 验证调度报错的根源配置，确认是资源依赖缺失而非调度策略错误。 |
| 3 | K8s State | Pod Status | `Pending` | 确认 Pod 处于不可运行状态，与调度失败事件因果一致。 |
| 4 | Metric | prometheus/kube-state-metrics | `kube_pod_status_phase{phase="Pending"}` 值为 1，`kube_pod_status_phase{phase="Succeeded"}` 值为 0。 | 从 Prometheus 观测确认 Pod 始终处于 Pending 状态，无正常运行记录。 |

**证据分析：**
Kubernetes 调度事件直接给出了失败原因（PVC 缺失），Pod 的状态和指标进一步印证了该 Pod 从未成功调度。资源请求（CPU 5m/50m, Memory 8Mi/32Mi）与失败无关，排除了资源不足的可能。

## 🎯 根因分析 · g1-p3

### 因果链

```text
Pod Spec 中引用不存在的 PVC 'unavailable-claim' → 调度器预检 PVC 存在性失败 → FailedScheduling 事件抛出 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因：Pod 配置引用了不存在的 PersistentVolumeClaim (PVC)。**

Pod `aiops-case-v03/workload` 的 Spec 中声明依赖名为 `unavailable-claim` 的持久卷声明，但集群中不存在该 PVC。这导致 `default-scheduler` 在调度预检阶段无法满足该依赖，直接抛出 `FailedScheduling` 事件，使得 Pod 无法被调度并一直处于 Pending 状态。

此结论由 K8s Event（证据 #1）和 K8s State（证据 #3）直接支持。指标数据（证据 #4）证实了 Pod 未能进入运行状态。资源配置证据（#2）确认失败并非由 CPU 或内存限制引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 22.5s
├─ 并发证据采集: 63.3s
│  ├─ g1-p1 aiops-case-v01/workload: 63.3s (Evidence 55.7s, RCA 7.5s)
│  ├─ g1-p2 aiops-case-v02/workload: 60.6s (Evidence 48.5s, RCA 12.0s)
│  └─ g1-p3 aiops-case-v03/workload: 42.1s (Evidence 33.2s, RCA 8.8s)
└─ 汇总总结: 14.7s
```

📋 Runbook 参考

- **g1-p1 aiops-case-v01/workload**: pod-pending-unschedulable
- **g1-p2 aiops-case-v02/workload**: pod-pending-unschedulable
- **g1-p3 aiops-case-v03/workload**: pod-pending-unschedulable
