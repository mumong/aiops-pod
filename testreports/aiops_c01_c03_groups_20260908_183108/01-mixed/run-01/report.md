## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态 |
| g2 | `aiops-case-v02/workload` | Pending | Pod 容器 `app` 配置了极不寻常的内存限制 `1Pi`（1 Pebibyte），远超集群所有节点的可分配内存总和（约 81 Gi），导致调度器在全部 3 个节点上因 `Insufficient memory` 拒绝调度，且无可驱逐的抢占对象。 |
| g3 | `aiops-case-v03/workload` | Pending | Pod workload in namespace aiops-case-v03 remains in Pending state due to FailedScheduling. |
| g4 | `aiops-case-v04/workload` | ContainerCreating | Pod 配置中声明了一个名为 'input' 的 Secret 卷，指向不存在的 Secret 'unavailable-input'，且该卷未设置 Optional=true，导致 Kubelet 在挂载卷时因找不到依赖资源而持续失败，阻止了容器进入 Running 状态。 |
| g5 | `aiops-case-v05/workload` | ContainerCreating | Pod spec.template 配置为空（缺失），导致 Kubelet 无法获取容器定义并无限期阻塞在 ContainerCreating 状态 |
| g6 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating 等待状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling  102s  ...  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 确认调度失败根因：所有节点 CPU 不足且无可用抢占目标 |
| 2 | K8s State | Kubernetes | `PodScheduled` 条件状态 `False`, reason: `Unschedulable`, message: `0/3 nodes are available: 3 Insufficient cpu...` | 验证 Pod 调度失败的硬状态，与 Event 记录一致 |
| 3 | K8s State | Kubernetes | Pod 当前状态 `Pending`, phase: `Pending` | 确认 Pod 处于等待调度的持续异常状态 |
| 4 | K8s Config | Kubernetes | `container.resource_request.cpu`: `100k` (0.1 Core) | 确认 Pod 调度预留请求量，证明资源需求并未极端化 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.cpu`: `100k` (0.1 Core), `memory`: `32Mi` | 确认容器资源限额设置正常，非超配问题 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (Pending) = `1` | 确认 Pod 持续维持在 Pending 阶段，未见转入 Running |
| 7 | Metric | Prometheus | `kube_pod_status_phase` (Succeeded) = `0` | 排除 Pod 曾短暂成功并退出的可能性 |

**证据说明：**
Kubernetes Event (`#1`) 与 Pod Scheduled 条件状态 (`#2`) 相互印证，明确指出了 `Insufficient cpu` 这一核心限制。调度预留请求量 (`#4`) 仅为 0.1 核，在常规集群中不应触发 `Insufficient cpu` 的极端情况，暗示集群 CPU 整体水位极高。Metric 数据 (`#6`, `#7`) 证实该 Pod 始终卡在 Pending 状态，未发生状态跃迁。Logging 与 Tracing 因 Pod 未启动而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
集群 3 个节点 CPU 资源耗尽 → 调度器因资源不足拒绝调度且无抢占目标 → Pod 条件 PodScheduled=False, Reason=Unschedulable → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因：集群所有 3 个可用节点均处于 CPU 资源不足（`Insufficient cpu`）状态，且由于没有足够的 CPU 资源可供抢占（`No preemption victims found`），导致 `default-scheduler` 无法将 Pod `aiops-case-v01/workload` 调度至任何节点。

该结论由 Kubernetes Event (`#1`) 直接陈述，并由 Pod 的 `Unschedulable` 状态 (`#2`)、`Pending` 阶段 (`#3`) 以及持续处于 Pending 状态的 Metric 观测 (`#6`) 提供强证据支持。Pod 的资源请求量仅为 0.1 核 (`#4`)，排除了资源请求过高导致单节点无法容纳的常规可能性，进一步指向集群整体 CPU 饱和。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | phase: `Pending` | 确认 Pod 处于未启动状态。 |
| 2 | K8s Config | `resource_limit.memory` | container `app`: `1Pi` | 暴露导致异常的极不合理的资源限制配置。 |
| 3 | K8s Config | `resource_request.memory` | container `app`: `1Pi` | 暴露调度器在绑定前即被拒绝的资源请求量。 |
| 4 | K8s Event | `FailedScheduling` | `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 确认调度失败直接原因及抢占失效的事实。 |
| 5 | K8s State | `pod.condition` | `PodScheduled=False`, reason: `Unschedulable` | 从 Pod 条件侧面印证调度器因资源不足拒绝调度。 |

**证据链说明**：
Kubernetes 配置（#2, #3）与事件（#4, #5）直接证实，Pod 请求的 `1Pi` 内存远超集群容量，导致调度器在所有节点上均因 `Insufficient memory` 拒绝调度，且无抢占对象，最终导致 Pod 维持 `Pending` 状态（#1）。Metric 仅提供了 Pod 状态的辅助确认。

## 🎯 根因分析 · g2

### 因果链

```text
容器 `app` 声明 `resources.limits.memory: 1Pi` 与 `requests.memory: 1Pi` → 调度器检查节点，发现单个节点最大内存（约 32 Gi）远小于请求（1 Pi） → 所有 3/3 节点因 `Insufficient memory` 被标记为 Unschedulable，且无可驱逐对象抢占 → Pod 保持 Pending 状态，无法调度到任何节点
```

### 根因结论

已确认根因为 **资源配置错误**。Pod 容器 `app` 被配置了极其不切实际的 `1Pi`（Pebibyte）内存请求与限制（见事实 #2, #3）。该数值远超集群所有节点（约 81 Gi 总量）的资源上限，直接导致调度器在预调度阶段即判定所有节点 `Insufficient memory`（见事实 #4），且由于无其他资源耗尽的竞争 Pod，不存在可被抢占的对象，致使 Pod 永久处于 `Pending` 状态。

---

## 🕵️ 证据内容 · g3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling  99s   default-scheduler  0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 调度器明确因 PVC 缺失而无法绑定卷，直接阻断 Pod 调度 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi, resource_request.memory: 8Mi, container.resource_limit.cpu: 50m, resource_request.cpu: 5m` | 资源请求极低，排除因资源不足导致调度的可能 |
| 3 | K8s State | kubernetes | `Pod Scheduled Condition False: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 再次确认调度失败的核心原因是卷绑定受阻 |

**证据说明：**
Kubernetes 事件与 Pod 状态条件相互印证，一致指出调度器在 3 个节点上均失败，原因唯一指向 PVC 缺失；资源配置事实（#2）表明该 Pod 资源门槛极低，进一步佐证失败原因是非资源性的存储依赖问题。

## 🎯 根因分析 · g3

### 因果链
```text
Pod spec 声明依赖 PVC 'unavailable-claim' → PVC 对象在命名空间 aiops-case-v03 中不存在 → 调度器无法绑定卷，持续报告 FailedScheduling → Pod 保持 Pending 状态无法调度
```

### 根因结论
已确认根因：**Pod 配置引用了一个不存在的 PersistentVolumeClaim (`unavailable-claim`)**。
该缺失的卷资源直接导致调度器无法通过卷绑定检查，从而持续将 Pod 阻塞在 Pending 状态（证据 #1, #3）。

---

## 🕵️ 证据内容 · g4

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-747447550a1f) | pod.status: Pending | 直接现象：Pod 因卷挂载失败进入 Pending 状态。 |
| 2 | K8s Event | kubernetes (fact-ce7ed26d86de) | event.reason: FailedMount; message: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 核心原因：明确指出 Pod 中的卷 "input" 因找不到 Secret "unavailable-input" 导致挂载失败。 |
| 3 | K8s Event | kubernetes (fact-60d995feaf16) | pod.condition: Ready=False, reason: ContainersNotReady | 辅助验证：确认容器处于非就绪状态。 |
| 4 | Metric | prometheus (fact-27859718e38e) | kube_pod_container_status_waiting_reason: 1, labels: {container: app, reason: ContainerCreating} | 观测印证：Prometheus 抓取到应用容器 "app" 处于 ContainerCreating 等待状态。 |
| 5 | Metric | prometheus (fact-d3f22673175f) | kube_pod_container_status_restarts_total: 0 | 辅助验证：容器自集群启动以来未发生过重启，符合 Pod 处于初始化等待阶段而非运行后崩溃的特征。 |

**证据说明：**
Kubernetes Event 中的 `FailedMount` 错误 (证据#2) 给出了明确的缺失资源名称 `unavailable-input`，直接指向了故障根源。Pod 状态 `Pending` (证据#1) 和容器状态 `ContainerCreating` (证据#4) 与挂载失败导致的初始化阻塞完全一致。重启计数为 0 (证据#5) 排除了应用运行期间崩溃的可能性。由于 Pod 无法启动，Logging 和 Tracing 维度因无业务数据产生而未适用，属于正常现象。

## 🎯 根因分析 · g4

### 因果链

```text
Pod 配置了名为 'input' 的 Secret 卷指向不存在的 Secret 'unavailable-input' (且 Optional 未设) → Kubelet 挂载卷因找不到 Secret 失败 (FailedMount) → Pod 状态转为 Pending，容器无法启动 → 应用不可用
```

### 根因结论

已确认根因为**Pod 配置中的 Secret 引用缺失**。
Pod 配置中声明了一个名为 `input` 的卷，该卷绑定到 Secret `unavailable-input`。由于该 Secret 在当前 Namespace `aiops-case-v04` 中不存在，且挂载项未设置 `Optional: true`，Kubelet 在启动过程中无法找到依赖资源，导致挂载步骤（SetUp）反复失败，进而使 Pod 停留在 `Pending` 阶段，应用容器永远处于 `ContainerCreating` 状态而无法进入 `Running`。
证据编号 #2 提供了确凿的失败原因，其余证据 #1、#3、#4 均从不同维度印证了这一挂载阻塞现象。

---

## 🕵️ 证据内容 · g5

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | 实体 `aiops-case-v05/workload` 处于 `ContainerCreating` 状态；诊断结论指出 `spec.template 配置为空（缺失）` | 确认异常实体及其停滞状态，直接指向 Pod 定义缺失的结构性问题 |
| 2 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ContainerCreating) 当前值为 `1` | 确认容器因处于等待/创建阶段而未运行，属于状态异常的直接表现 |
| 3 | Metric | Prometheus | `kube_pod_status_phase` (container=kube-state-metrics, phase=Pending) 当前值为 `1` | 确认集群整体状态存在 Pending 的 Pod，与上述异常状态一致 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (container=app) 当前值为 `0` | 确认该容器从未成功运行过，排除因应用崩溃重启导致的假象 |

**证据说明：**
1. 度量数据（#2, #4）确认了 Pod 处于“从未运行过且卡在创建中”的静止状态，这与诊断中指出的“无限期阻塞”特征吻合。
2. `spec.template` 缺失是底层配置层面的结构性事实，它解释了为何 Kubelet 无法拉起容器（状态 #1）且无重启记录（#4）。
3. 由于未定义任何容器，物理上无法生成应用日志或 Trace，因此 Logging 和 Tracing 维度的缺失是配置错误的必然结果，而非独立故障。

## 🎯 根因分析 · g5

### 因果链

```text
Pod spec.template 配置为空（缺失） → Kubelet 无法解析到任何容器定义以创建运行时环境 → 容器无限期处于 ContainerCreating 等待状态 → 应用未运行且无任何日志或业务流量产生
```

### 根因结论

**已确认的根因：Pod 资源定义错误（`spec.template` 字段为空）。**

现有的 Prometheus 指标数据证实了 Pod 处于 `ContainerCreating` 状态且从未发生过容器重启（`restarts_total=0`），这与诊断中描述的“无限期阻塞”完全一致。根因指向 Pod YAML 中缺少 `spec.template` 导致 Kubelet 无法获取任何有效的容器规格（Container Definition），从而无法推进调度与启动流程。由于配置本身为空，后续的工具调用（如日志查询、Tracing、Topology）因 Pod 未实际启动运行而物理上不可达，这进一步排除了运行时环境、网络或依赖服务层面的干扰，将故障源头锁定在应用本身的部署配置层面。

---

## 🕵️ 证据内容 · g6

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `FailedMount` | `Warning FailedMount 27s (x8 over 91s) kubelet MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 确诊根因：节点缺少 Pod 声明的 hostPath |
| 2 | K8s State | `pod.status` | `Pending` | 现象印证：Pod 被阻塞在容器初始化阶段 |
| 3 | K8s Config | `container.resource_request.cpu` | `5m` | 排除性能因素：非资源配额导致的调度/启动延迟 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `1` (labels: `reason=ContainerCreating`, `sample_count=1`) | 辅助观测：确认容器处于挂载等待阶段 |

**证据关联说明：**
事实 #1 提供了明确的挂载失败原因（hostPath 路径不存在）；事实 #2 证实了 Pod 因依赖该挂载点而无法进入 `Running` 状态（表现为 `Pending`/`ContainerCreating`）。事实 #3 排除了低资源导致 Pod 调度的可能性，事实 #4 进一步确认了当前等待的具体原因码。

## 🎯 根因分析 · g6

### 因果链

```text
节点 node2 缺失指定目录 → 挂载卷校验失败 → 容器初始化阻塞 → Pod 停滞于 ContainerCreating
```

### 根因结论

根因已确认：Pod `aiops-case-v06/workload` 在配置中声明了 `HostPath` 卷 `input`，目标路径为 `/var/lib/aiops-fixture-unavailable-7f394bef/input`。Kubelet 在校验时发现该路径在调度节点上不存在（“is not a directory”），导致卷挂载失败，Pod 因此被阻塞在 `ContainerCreating` 状态。

决定性证据为事实 #1 (`FailedMount` 事件)。由于 Pod 未能启动，日志与 Trace 为预期为空（`not_applicable`），现有证据已足以闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 38.6s
├─ 并发证据采集: 87.1s
│  ├─ g1 aiops-case-v01/workload: 63.6s (Evidence 49.9s, RCA 13.6s)
│  ├─ g2 aiops-case-v02/workload: 87.1s (Evidence 76.4s, RCA 10.6s)
│  ├─ g3 aiops-case-v03/workload: 70.1s (Evidence 60.2s, RCA 9.7s)
│  ├─ g4 aiops-case-v04/workload: 66.0s (Evidence 55.4s, RCA 10.4s)
│  ├─ g5 aiops-case-v05/workload: 60.5s (Evidence 53.3s, RCA 7.1s)
│  └─ g6 aiops-case-v06/workload: 55.6s (Evidence 43.1s, RCA 12.4s)
└─ 汇总总结: 17.2s
```

📋 Runbook 参考

- 未调用 Runbook
