## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1-p1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，未被调度 |
| g1-p2 | `aiops-case-v02/workload` | Pending | Pod内存资源请求/限制配置为1Pi（1 Pebibyte），远超集群3个节点的可用物理内存，导致调度器评估全部节点Insufficient memory，产生FailedScheduling事件并长期处于Pending状态。 |
| g1-p3 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 的 Pod Spec 中声明依赖名为 'unavailable-claim' 的 PersistentVolumeClaim，但该 PVC 在对应 namespace 中不存在（NotFound），导致调度器因无法满足存储卷依赖而拒绝调度，引发 FailedScheduling。 |
| g2-p1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 Pending/ContainerCreating 状态，无法正常启动。 |
| g2-p2 | `aiops-case-v05/workload` | ContainerCreating | Pod spec 中 ConfigMap volume 'input' 引用了不存在的 key 'unavailable-key'，导致 Kubelet 挂载失败，Pod 持续处于 Pending/ContainerCreating 状态。 |
| g2-p3 | `aiops-case-v06/workload` | ContainerCreating | Pod 'workload' in namespace 'aiops-case-v06' remains in 'ContainerCreating' state. |

---

## 🕵️ 证据内容 · g1-p1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase` = `Pending` | 确认 Pod 调度失败，未进入运行状态 |
| 2 | K8s Event | kubernetes | `PodScheduled` 条件为 `False`；`message`: "0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found" | 直接指向调度失败原因为 CPU 资源不足，且集群无可用抢占资源 |
| 3 | K8s Config | kubernetes | `resource_request.cpu` = `100k`, `resource_limit.cpu` = `100k` | 展示该 Pod 的资源请求与限制配置 |

**证据总结：**
Kubernetes 状态明确显示 Pod 处于 `Pending` 且 `PodScheduled` 条件为 `False`。事件详情指出集群 3 个节点均因 `Insufficient cpu` 无法满足调度需求，且不存在抢占受害者。结合 Pod 的 CPU 请求配置，故障链路清晰指向集群侧 CPU 资源枯竭。Logging 与 Tracing 维度因容器未启动标记为不适用，无冲突信息。

## 🎯 根因分析 · g1-p1

### 因果链

```text
集群 3 节点 CPU 资源不足 → 调度器无法满足 Pod 调度需求且无可抢占资源 → PodScheduled 条件为 False → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为**集群节点 CPU 资源不足**。

证据 `fact-b3eff22536d5`（K8s Event）显示，调度器在尝试调度 `aiops-case-v01/workload` 时，发现 0/3 可用节点均报告 `Insufficient cpu`，且 `preemption` 结果为 `No preemption victims found`。这一状态直接导致了 Pod 维持在 `Pending` 状态（`fact-243e5608c261`）。现有证据足以解释调度失败的直接原因，无需其他诊断数据补充。

---

## 🕵️ 证据内容 · g1-p2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | `container.resource_request.memory`: 1Pi | 确定调度所需的内存资源上限 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 1Pi | 确认内存硬限制同样配置为 1Pi |
| 3 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (4m26s) | 提供调度失败的直接原因（节点内存不足且无法抢占） |
| 4 | K8s State | kubernetes | `pod.condition`: `PodScheduled=False` (Unschedulable) | 记录 Pod 的持久不可调度状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase`: `Pending` (Value 1) | 验证 Pod 处于挂起状态的持续现象 |

**证据关联说明：**
配置事实（#1, #2）提供了 1Pi 的极高资源需求；调度器事件（#3）直接证实该需求超出了集群 3 个节点的物理上限并导致调度失败；状态与指标（#4, #5）从不同维度确认了这一失败导致了 Pod 长期处于 Pending 状态。

## 🎯 根因分析 · g1-p2

### 因果链

```text
内存资源请求/限制配置过高 (1Pi) → 调度器评估节点资源不足 (Insufficient memory) → 产生 FailedScheduling 事件 → Pod 长期处于 Pending 状态
```

### 根因结论

已确认根因为 `Pod 内存资源请求/限制配置为 1Pi`。
该配置值远超集群实际可用物理内存，导致 `default-scheduler` 在评估集群中全部 3 个节点时均判定内存不足（`Insufficient memory`）。由于集群无足够的可回收资源，抢占机制（Preemption）也失败，最终导致 Pod 调度失败并持续处于 `Pending` 状态。该结论由 K8s 配置（#1, #2）与调度器失败事件（#3）共同支撑。

---

## 🕵️ 证据内容 · g1-p3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 3m45s default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 提供直接的调度失败机制，指出 PVC 缺失是拒绝调度的根本原因 |
| 2 | K8s Config | kubernetes | Pod 声明依赖 `persistentvolumeclaim "unavailable-claim"` | 建立 Pod 对存储卷的实际依赖，证实引用资源的必要性 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v03/workload` 状态为 `Pending`，`PodScheduled=False` | 描述故障导致的最终现象，印证调度持续失败 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}=1`，`sample_count=1` | 确认 Pod 长时间处于 Pending 状态，与 K8s 状态一致 |
| 5 | K8s State | tool_error | `kubectl get pvc unavailable-claim -n aiops-case-v03` 返回 `Error from server (NotFound)` | 验证 PVC 物理确实不存在，排除因数据延迟导致的误判 |

证据之间相互印证：K8s Event (1) 明确指出调度器因找不到 PVC 而阻塞，Metric (4) 与 Pod 状态 (3) 证实了这一阻塞状态持续存在。工具执行失败 (5) 提供了底层资源缺失的决定性事实，完全支撑了调度事件的结论，不存在矛盾证据。

## 🎯 根因分析 · g1-p3

### 因果链

```text
声明依赖 PVC 'unavailable-claim' 但不存在 → 调度器判定无法满足存储依赖 → FailedScheduling → Pod 长期处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 依赖的 PersistentVolumeClaim ('unavailable-claim') 不存在**。

1. **机制**：Pod 在 Spec 中引用了名为 'unavailable-claim' 的 PVC (证据 2)。
2. **失败点**：调度器在尝试调度时，无法在 namespace `aiops-case-v03` 中找到该 PVC，导致 `FailedScheduling` (证据 1, 5)。
3. **现象**：Pod 因此被阻塞在 `Pending` 状态 (证据 3, 4)。

现有 K8s 维度证据（事件、状态、配置）与工具执行事实已充分闭合，排除了资源不足等干扰项。日志与 Trace 维度不适用，因为 Pod 尚未启动（证据说明）。

---

## 🕵️ 证据内容 · g2-p1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-4f8316a8f5ba` | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 确认 Pod 卡在挂载步骤，指出具体失败的 volume 名称为 `input` |
| 2 | K8s Event | `fact-5d8e0faa52cd` | `FailedMount`: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 根本原因定位：指定名称的 Secret 不存在 |
| 3 | K8s State | `fact-c7021f8c5307` | `status: Pending` | 确认 Pod 处于调度完成但容器未运行的阻塞状态 |
| 4 | Metric | `fact-bb9cbc1251b2` | `kube_pod_container_status_waiting_reason`: value="1", reason="ContainerCreating" | 指标层面独立确认容器处于等待挂载资源的阶段，且仅发生 1 次，与事件时间线一致 |

上述证据形成闭环：Event 明确指出 `unavailable-input` Secret 缺失导致 `input` volume 挂载失败；State 和 Metric 共同佐证了因无法完成挂载而导致的 `Pending` / `ContainerCreating` 状态。

## 🎯 根因分析 · g2-p1

### 因果链

```text
Secret 'unavailable-input' 不存在 → Volume 'input' 挂载失败 (Optional: false) → Pod 进入 Pending 状态 (ContainerCreating) → 应用容器 'app' 未启动
```

### 根因结论

已确认根因为 **Secret 缺失导致挂载失败**。

根据事实 `fact-5d8e0faa52cd`，Pod 定义中引用的 Secret `unavailable-input` 不存在，且该挂载项非 Optional，直接导致 Kubelet 挂载 volume 超时失败（见事实 `fact-4f8316a8f5ba`）。这符合正式 RCA 的描述，并有 Kubernetes Event、Metric 和 State 多维度事实支撑（证据编号 1-4）。

---

## 🕵️ 证据内容 · g2-p2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` configmap references non-existent config key: unavailable-key (fact-ae39450f46c0) | 直接证明挂载失败原因 |
| 2 | K8s State | kubernetes | `status`: Pending (fact-38031f6392d8) | 确认 Pod 当前异常状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason: `ContainerCreating` (fact-6bdf9478916a) | 确认容器卡在启动等待阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-c1d59490c2a1) | 确认容器未发生过启动/重启行为 |

**证据关联说明：**
Kubernetes 事件 (1) 指出挂载失败的具体原因为引用了不存在的 ConfigMap Key。Metrics 数据 (2, 3) 显示 Pod 持续处于 `Pending` 且容器处于 `ContainerCreating` 状态，这与挂载受阻导致的启动失败机制完全一致。Metric (4) 的 0 重启次数排除了容器健康探针或 OOM 等后续启动问题的干扰。Logging 和 Tracing 因容器未启动而未采集到数据，符合预期。

## 🎯 根因分析 · g2-p2

### 因果链

```text
ConfigMap volume 引用了不存在的 key 'unavailable-key' (1) → Kubelet 执行 MountVolume.SetUp 失败 → 容器挂载受阻，状态维持在 Waiting/ContainerCreating (3) → Pod 整体处于 Pending 状态，无法进入 Running (2)
```

### 根因结论

已确认根因为 **Pod 配置错误**。Pod spec 中的 ConfigMap volume 'input' 引用了不存在的 key 'unavailable-key'，导致 Kubelet 在挂载卷时失败（见证据 1）。这使得容器无法完成启动前的卷准备阶段，导致 Pod 持续处于 `Pending/ContainerCreating` 状态（见证据 2, 3）。现有证据链完整，无需补充日志或追踪数据即可确诊。

---

## 🕵️ 证据内容 · g2-p3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | fact-c9c04c99c187: Pod `aiops-case-v06/workload` 状态 `Pending` | 确认异常实体及其当前停滞状态 |
| 2 | K8s Event | kubernetes | fact-9ea11870e19a: `Warning FailedMount ... hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 锁定直接故障机制，表明节点上目标路径不符合目录预期 |
| 3 | K8s Event | kubernetes | fact-a60fbdc3e420: `Warning FailedMount ... timed out waiting for the condition` | 证明挂载阻塞导致 Pod 调度停滞 |
| 4 | Metric | prometheus | fact-75e91e8fb233: `kube_pod_container_status_waiting_reason` = `ContainerCreating` | 从指标层独立确认容器处于等待挂载的状态 |
| 5 | K8s Config | kubernetes | fact-4c65b2419d8b: `container.resource_request.memory` = `8Mi`; fact-83f09a99ee78: `container.resource_limit.memory` = `32Mi` | 确认该维度资源申请合法，排除资源不足导致的 Pending |
| 6 | K8s Config | kubernetes | fact-bf091b6a7489: `container.resource_limit.cpu` = `50m`; fact-c3d346722fcc: `container.resource_request.cpu` = `5m` | 确认该维度资源申请合法，排除资源不足导致的 Pending |
| 7 | Metric | prometheus | fact-5366d2264d56: `kube_pod_container_status_restarts_total` = `0` | 佐证 Pod 尚未成功启动，与 K8s 事件记录的等待状态一致 |

证据互证：K8s 事件 (`fact-9ea11870e19a`) 提供了明确的挂载失败原因，Prometheus 指标 (`fact-75e91e8fb233`) 从观测面印证了容器卡在 `ContainerCreating` 阶段。资源配置检查（如 `fact-4c65b2419d8b`、`fact-bf091b6a7489`）确认资源需求合法，排除了资源限制导致 Pending 的其他可能。由于容器未启动，Logging 与 Tracing 维度的数据缺失属于合理物理限制，不影响基于 K8s 核心维度的根因判定。

## 🎯 根因分析 · g2-p3

### 因果链

```text
HostPath 挂载卷 "input" 在 node2 上配置的物理路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或非目录 → kubelet 挂载检查失败，持续超时等待挂载条件满足 → Pod "workload" 状态锁定为 Pending (ContainerCreating) → 容器无法启动，应用无法交付
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v06/workload` 的启动失败是由于其配置挂载的 `HostPath` 卷在宿主机节点上缺少合法的目录路径。

具体而言，Kubelet 在尝试挂载名为 `input` 的卷时，发现路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 未通过目录类型检查（`is not a directory`），导致挂载失败并触发超时重试（见证据 `fact-9ea11870e19a`）。这一物理存储层的故障直接阻断了容器的初始化过程，使得 Pod 长期停留在 `Pending` 状态（见证据 `fact-c9c04c99c187`）。该根因与 Prometheus 指标中观测到的 `ContainerCreating` 等待状态完全吻合（见证据 `fact-75e91e8fb233`）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.5m
├─ 问题定位: 19.6s
├─ 并发证据采集: 588.6s
│  ├─ g1-p1 aiops-case-v01/workload: 51.8s (Evidence 42.9s, RCA 8.7s)
│  ├─ g1-p2 aiops-case-v02/workload: 104.6s (Evidence 98.9s, RCA 5.7s)
│  ├─ g1-p3 aiops-case-v03/workload: 76.7s (Evidence 68.2s, RCA 8.4s)
│  ├─ g2-p1 aiops-case-v04/workload: 37.9s (Evidence 25.9s, RCA 11.8s)
│  ├─ g2-p2 aiops-case-v05/workload: 70.1s (Evidence 58.0s, RCA 12.0s)
│  └─ g2-p3 aiops-case-v06/workload: 588.6s (Evidence 580.3s, RCA 8.2s)
└─ 汇总总结: 19.4s
```

📋 Runbook 参考

- **g1-p1 aiops-case-v01/workload**: pod-pending-unschedulable, pod-volume-mount-failed
- **g1-p2 aiops-case-v02/workload**: pod-pending-unschedulable, pod-volume-mount-failed
- **g1-p3 aiops-case-v03/workload**: pod-pending-unschedulable, pod-volume-mount-failed
- **g2-p1 aiops-case-v04/workload**: pod-volume-mount-failed
- **g2-p2 aiops-case-v05/workload**: pod-volume-mount-failed
- **g2-p3 aiops-case-v06/workload**: pod-volume-mount-failed
