## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，无法调度 |
| g2 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 持续处于 Pending 状态，未调度到任何节点 |
| g3 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，未能调度至节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found | 确认调度器判定集群所有节点均存在 CPU 资源短缺，且无法通过抢占解决 |
| 2 | K8s State | kubernetes | PodScheduled: False (Unschedulable); phase: Pending; status: Pending | 证实 Pod 当前因无法调度而处于停滞状态 |
| 3 | K8s Config | kubernetes | resource_request.cpu: 100k; resource_limit.cpu: 100k | 说明 Pod 申请了特定规格的计算资源，是导致资源争用的直接原因 |

Kubernetes 事件明确指出了 `Insufficient cpu` 是 Pod 被拒绝分配节点的直接原因，Pod 状态同步反映了这一调度失败结果。

## 🎯 根因分析 · g1

### 因果链

```text
集群 3 个节点 CPU 资源耗尽 → 调度器因 Insufficient cpu 拒绝分配且无抢占 victim → Pod 持续处于 Unschedulable 状态 → 用户可见 Pod Pending 现象
```

### 根因结论

已确认的根因为集群节点 CPU 资源不足（Insufficient cpu）导致调度失败 [证据 #1, #2]。集群内所有可用节点均无法满足 Pod 的 CPU 请求，且不存在可抢占的节点，导致 Pod 维持 Pending 状态。由于当前维度中 Metric 仅有单一样本（不评估趋势），且 Logging/Tracing 因容器未启动不可用，缺少关于各节点具体 CPU 容量与剩余可用量的量化事实以进一步定位资源瓶颈点。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod. | **直接原因**：调度器明确拒绝，因无节点提供足够内存 |
| 2 | K8s Config | kubernetes | memory requests/limits = 1Pi (约 1099511627776 Bytes) | **关键事实**：容器资源请求量级异常，远超常规物理节点容量 |
| 3 | K8s State | kubernetes | status = Pending | **症状表现**：Pod 始终停留在待调度阶段，未进入启动流程 |
| 4 | Metric | prometheus | kube_pod_status_phase(phase=Pending, label=aiops-case-v02/workload) = 1 | **状态确认**：监控确认 Pod 持续处于 Pending 状态 |
| 5 | Metric | prometheus | kube_pod_status_phase(phase=Running, label=aiops-case-v02/workload) = 0 | **排除证据**：确认 Pod 没有任何运行记录 |

**证据说明：**
1. Kubernetes 事件 `FailedScheduling` 与 Pod 状态 `Pending` 相互印证，确认了调度失败的持续性（证据 1、3）。
2. 事件原因 `Insufficient memory` 与 Pod 配置中 `1Pi` 的超大内存请求直接对应，揭示了节点无法满足资源需求的根本矛盾（证据 1、2）。
3. 监控指标从运行态和 Pending 态两个维度确认了 Pod 未启动的事实，排除了短暂启动失败的可能性（证据 4、5）。

## 🎯 根因分析 · g2

### 因果链

```text
Pod 定义 memory requests/limits 为 1Pi → 集群节点最大可用内存远小于请求 → Scheduler 拒绝调度 → Pod 持续 Pending 未启动
```

### 根因结论

已确认根因为 **资源请求量级严重超出集群物理容量**。

具体机制为：Pod `aiops-case-v02/workload` 的请求和限制被配置为 `1Pi`（约 1099511627776 Bytes），这远超了集群节点的实际可用内存上限。因此，调度器在尝试调度时检测到所有 3 个节点均 `Insufficient memory`，且不存在可抢占的 Pod 以腾出空间，最终导致 Pod 无法被调度并长期处于 Pending 状态。

证据编号：事件 (1) 和资源配置 (2) 提供了决定性的事实支撑。

---

## 🕵️ 证据内容 · g3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Pending` | 确认 Pod 处于未调度状态 |
| 2 | K8s Config | `container.resource_request.cpu` | `5m` | 排除因 CPU 资源不足导致的调度失败 |
| 3 | K8s Event | `FailedScheduling` | `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接指出调度器在卷绑定检查阶段因 PVC 缺失而中断 |
| 4 | Metric | `kube_pod_status_phase` | `Pending` 状态值为 1 | 从监控维度独立印证 Pod 持续处于 Pending 状态 |

**证据印证：**
K8s Event (3) 中的 `FailedScheduling` 失败原因明确指向 PersistentVolumeClaim 对象不存在，这直接解释了 Pod (1) 无法进入 Running 状态的阻塞机制。Metric (4) 进一步排除了 Pod 状态波动的可能，确证了故障现象的持续性。资源请求值 (2) 表明该 Pod 本身并非因资源超卖而被延迟调度。

## 🎯 根因分析 · g3

### 因果链

```text
PVC unavailable-claim 缺失 → 调度器预检查失败 → FailedScheduling 事件触发 → Pod 保持 Pending 状态
```

### 根因结论

已确认根因：**Pod 引用的 PersistentVolumeClaim (PVC) 'unavailable-claim' 不存在** [证据#3]。

该 PVC 的缺失导致 Kubernetes default-scheduler 在调度的早期预检查（Pre-check）阶段即判定无法绑定卷资源，从而立即抛出 `FailedScheduling` 错误。因为卷绑定是 Pod 能够进入绑定节点的前提，这一前置条件的缺失直接阻断了 Pod 的后续生命周期，使其永久卡在 `Pending` 状态 [证据#1, #4]。现有的 K8s 配置与事件日志已构成完整且自洽的证据链，无需额外的日志或追踪数据即可定性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.9s
├─ 并发证据采集: 49.4s
│  ├─ g1 aiops-case-v01/workload: 39.6s (Evidence 30.3s, RCA 9.2s)
│  ├─ g2 aiops-case-v02/workload: 42.3s (Evidence 34.2s, RCA 8.0s)
│  └─ g3 aiops-case-v03/workload: 49.4s (Evidence 43.0s, RCA 6.3s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
- **g2 aiops-case-v02/workload**: pod-pending-unschedulable
- **g3 aiops-case-v03/workload**: pod-pending-unschedulable
