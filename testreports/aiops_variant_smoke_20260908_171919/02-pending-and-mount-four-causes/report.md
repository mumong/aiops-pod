## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态 |
| g2 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 namespace is stuck in Pending state with FailedScheduling event |
| g3 | `aiops-case-v04/workload` | ContainerCreating | Pod workload (aiops-case-v04) stuck in ContainerCreating/Pending state |
| g4 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 卡在 ContainerCreating (Pending) 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod. (fact_id: fact-47c5de5483f6) | 直接证明调度器因节点 CPU 资源耗尽且无可用抢占目标而拒绝调度。 |
| 2 | K8s State | kubernetes | Pod `aiops-case-v01/workload` 状态为 `Pending` (fact_id: fact-25f45054af9b) | 确认调度失败的最终症状。 |
| 3 | K8s Config | kubernetes | Pod 请求 CPU `100k` (50m)，容器 CPU 硬限制 `100k` (50m)，内存请求/限制均为低值 (8Mi/32Mi) (fact_id: fact-7665d523e189, fact-098792018a07, fact-055eab40b04c, fact-5def0194d94a) | 确认资源请求量极小，排除因配置异常巨大导致的资源不足。 |
| 4 | Metric | prometheus | `kube_pod_status_phase{container="kube-state-metrics", phase="Pending"}` 值为 1，无 Running 状态记录 (fact_id: fact-e3dc8b5005e5) | 量化确认 Pod 持续处于 Pending 状态，且无启动记录。 |

**证据互证说明**：K8s 事件（#1）直接提供了调度失败的具体原因（Insufficient cpu 且无抢占空间），状态指标（#4）与 Pod 当前状态（#2）相互印证，表明故障为持续性阻塞而非瞬时波动。资源配置（#3）显示该 Pod 资源需求极低，进一步支撑了集群侧资源极度枯竭的根因。

## 🎯 根因分析 · g1

### 因果链
```text
集群 3 个节点 CPU 资源耗尽 → 调度器分配失败且无抢占目标 → Pod 持续处于 Pending 状态
```

### 根因结论
已确认根因为**集群节点 CPU 资源不足**。集群所有 3 个节点 CPU 均无法满足 Pod 的请求（#1），且没有足够的负载可被抢占（#1），导致 Pod 无法启动。K8s 事件是确凿的判定证据。

*   **证据引用**：K8s 事件（#1）。
*   **补充说明**：Pod 资源请求量（100k CPU）极低（#3），表明集群资源枯竭已达到极端程度，或存在大规模资源泄漏。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes available: 3 Insufficient memory | 核心失败原因：调度器发现所有节点内存不足 |
| 2 | K8s State | kubernetes | Pod `aiops-case-v02/workload` 状态: Pending, 条件 `PodScheduled=False` (Unschedulable) | 直接症状确认 |
| 3 | K8s Config | kubernetes | Container `app` 内存请求 (`resource_request.memory`): `1Pi` | 关键上下文：资源申请量远超常规物理极限 |
| 4 | K8s Config | kubernetes | Container `app` 内存限制 (`resource_limit.memory`): `1Pi` | 关键上下文：确认资源定义上限 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}`: 1 (仅 1 个样本，无法评估趋势) | 独立观测确认 Pod 状态 |

**证据说明**：
Kubernetes 事件（#1）明确记录了 3 个节点均因 `Insufficient memory` 拒绝调度。K8s 配置事实（#3, #4）展示了 Pod 声明了 1Pi 的内存，这是导致所有节点无法满足资源请求的根源。K8s 状态（#2）和 Metric（#5）独立印证了 Pod 持续处于 Pending 状态。日志和追踪维度标记为 `not_applicable`，因为 Pod 未启动，该结论由 K8s 控制面事实充分支撑。

## 🎯 根因分析 · g2

### 因果链

```text
Pod 声明了 1Pi 的内存资源限制与请求 → 调度器在所有 3 个可用节点上均判定内存不足 → 预抢占机制失败且无满足条件的节点 → Pod 卡在 Pending 状态，无法被调度
```

### 根因结论

已确认的根因是调度器因集群节点内存不足（`Insufficient memory`）拒绝了 Pod 的调度请求（证据 1）。这一现象的直接触发因素是 Pod 定义的资源规格中声明了 `1Pi` 的内存请求与限制（证据 3, 4）。该数值远超集群节点的实际物理内存容量，导致 3 个节点均无法满足分配条件，从而进入 Pending 状态（证据 2, 5）。

---

## 🕵️ 证据内容 · g3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedMount: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接确认了导致挂载失败的明确原因和缺失资源名称 |
| 2 | K8s State | kubernetes | pod.status: Pending, phase: Pending | 确认 Pod 因挂载依赖未满足而处于等待/挂起状态 |
| 3 | K8s State | kubernetes | container.waiting_reason: ContainerCreating (container: "app") | 印证 K8s Event 的挂载失败现象，容器处于创建前的等待期 |
| 4 | K8s Config | kubernetes | resource_request: memory=8Mi, cpu=5m; resource_limit: memory=32Mi, cpu=50m | 排除资源配额（CPU/内存）不足导致的调度失败 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason=1 (container: app, reason: ContainerCreating) | 从监控维度确认应用容器持续处于 ContainerCreating 状态 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total=0 (container: app) | 确认容器尚未进入运行期，无重启记录 |

证据 1 的 K8s 事件日志直接指出了 `secret "unavailable-input"` 不存在这一事实；证据 2 和 3 分别从 Pod 状态和容器状态两个 K8s 维度印证了该缺失导致的持续阻塞现象。Metric 证据（5, 6）排除了运行后资源耗尽或重启波动，进一步确认故障发生在容器初始化（MountVolume）阶段。

## 🎯 根因分析 · g3

### 因果链

```text
Secret 'aiops-case-v04/unavailable-input' 不存在 → Pod spec 强制挂载 volume "input" → Kubelet MountVolume.SetUp 失败 → Container 'app' 卡在 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因为：**关键 Secret 资源缺失**。

Pod `workload` 的定义中引用了名为 `input` 的存储卷，且该卷依赖的 `secretName` 为 `unavailable-input`（配置为非可选 `optional: false`）。由于该 Secret 在当前命名空间下不存在，Kubelet 在执行 `MountVolume.SetUp` 时失败，直接导致容器无法完成挂载并进入创建阶段（见证据 1）。Pod 因此停留在 `Pending` / `ContainerCreating` 状态（见证据 2, 3），且未触发重启（见证据 6）。

现有证据已充分支撑该结论，无需更多事实。

---

## 🕵️ 证据内容 · g4

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-f83d8ce76171` | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 直接指示挂载失败的具体原因及缺失的键名 |
| 2 | K8s State | `fact-229c28552af0` | `pod.phase`: Pending | 确认 Pod 整体停留在启动前的等待阶段 |
| 3 | K8s State | `fact-98f9aa6f0d08` | `container.waiting_reason`: ContainerCreating | 定位到具体的容器 `app` 卡在创建并挂载卷的阶段 |
| 4 | K8s Config | `fact-30b642a331ce` | `container.resource_request.memory`: 8Mi | 提供启动所需的内存请求限制，排除调度资源不足的可能 |

**证据印证说明**：
- 容器状态 `ContainerCreating` 和 Pod 状态 `Pending` 共同印证了 Pod 尚未进入运行阶段，属于启动前阻塞（[证据 2, 3]）。
- `FailedMount` 事件明确给出了阻塞的因果关系，即 ConfigMap 配置错误导致挂载无法完成，从而使得容器无法进入 `Running` 状态（[证据 1]）。

## 🎯 根因分析 · g4

### 因果链

```text
ConfigMap 'workload-input' 缺少 key 'unavailable-key' → kubelet 挂载卷验证失败 (FailedMount) → 容器 'app' 持续处于 ContainerCreating → Pod 处于 Pending 状态无法启动
```

### 根因结论

已确认根因：Pod 挂载卷失败。

Pod `aiops-case-v05/workload` 无法启动是因为其定义的 Volume `input` 引用了 ConfigMap 中不存在的 Key `unavailable-key`。这一配置错误导致 `kubelet` 在挂载卷时抛出 `FailedMount` 异常，进而使容器 `app` 卡在 `ContainerCreating` 状态，最终导致整个 Pod 处于 `Pending` 状态。证据 `fact-f83d8ce76171` 提供了确切的失败原因，足以构成根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 39.8s
├─ 并发证据采集: 56.2s
│  ├─ g1 aiops-case-v01/workload: 32.9s (Evidence 24.6s, RCA 8.3s)
│  ├─ g2 aiops-case-v02/workload: 56.2s (Evidence 48.6s, RCA 7.5s)
│  ├─ g3 aiops-case-v04/workload: 46.1s (Evidence 35.7s, RCA 10.2s)
│  └─ g4 aiops-case-v05/workload: 45.8s (Evidence 38.8s, RCA 6.9s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable, pod-volume-mount-failed
- **g2 aiops-case-v02/workload**: pod-pending-unschedulable, pod-volume-mount-failed
- **g3 aiops-case-v04/workload**: pod-volume-mount-failed
- **g4 aiops-case-v05/workload**: pod-volume-mount-failed
