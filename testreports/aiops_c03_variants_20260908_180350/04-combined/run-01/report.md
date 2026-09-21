## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1-p1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 ContainerCreating/Pending 状态 |
| g1-p2 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating / Pending 状态，挂载失败 |
| g1-p3 | `aiops-case-v06/workload` | ContainerCreating | HostPath volume 'input' 挂载失败，因为节点 node2 上的宿主机路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或不是目录，导致 kubelet 无法完成卷挂载。 |

---

## 🕵️ 证据内容 · g1-p1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `ContainersReady: False` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 确认 Pod 未能进入 Ready 状态的直接症状，且该状态在 24s 内持续存在。 |
| 2 | K8s Event | Kubernetes Events | `FailedMount` (Warning, x7 over 56s) `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | **决定性证据**，指明 Pod 停滞的具体原因是挂载卷所需的 Secret 缺失。 |
| 3 | K8s State | Container Status | `waiting_reason: ContainerCreating` | 确认 Pod 当前正处于等待挂载卷及配置环境阶段的容器等待状态。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (labels: `container=app`, `reason=ContainerCreating`) = `1` | 独立于 K8s 事件数据，从监控指标维度印证了容器当前处于 `ContainerCreating` 的等待状态。 |

**证据综述：**
K8s 事件 `fact-1005142cef71` 直接指出了挂载失败的根本原因为 Secret 缺失，而 K8s 状态与 Prometheus 指标（`fact-50400edcfe50` 等）从多维度一致印证了 Pod 始终停滞在 `ContainerCreating/Pending` 且未发生重启（`restart_count=0`）的状态。

## 🎯 根因分析 · g1-p1

### 因果链

```text
Secret 'unavailable-input' 缺失 → kubelet 挂载失败 (FailedMount, Optional=false) → Pod 停滞在 ContainerCreating/Pending → 服务不可用
```

### 根因结论

已确认的根因是 **Pod Spec 中声明引用了不存在的 Secret (`unavailable-input`) 且该挂载卷未设置为可选**。

这一配置错误导致 kubelet 在执行 `MountVolume.SetUp` 时持续失败（K8s Event 记录到 7 次失败，跨度 56s），直接使得 Pod 无法完成容器启动准备，从而长期处于 `ContainerCreating` 和 `Pending` 状态，无法对外提供服务。

---

## 🕵️ 证据内容 · g1-p2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 直接揭示挂载失败的具体原因是引用了 ConfigMap 中不存在的 key |
| 2 | K8s State | kubernetes | Pod 状态: `Pending`; 容器状态: `ContainerCreating` | 描述 Pod 当前的停滞状态和挂载阶段阻塞现象 |
| 3 | K8s Config | kubernetes | CPU: `req=5m, limit=50m`; Memory: `req=8Mi, limit=32Mi` | 提供容器基础资源配置，排除资源超限导致的调度失败 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}`: 1 (sample_count=1) | 从监控指标层面确认并量化了 Pod 等待启动的异常状态 |

**证据关联说明**：
Kubernetes 事件（证据 1）提供了明确的失败原因，指出 `input` 卷引用的 `unavailable-key` 在 ConfigMap 中不存在；该错误直接导致了 Pod 卡在 `ContainerCreating` 状态（证据 2）；Prometheus 指标（证据 4）作为辅助观测，证实了该 Pod 长期处于等待挂载的 `ContainerCreating` 状态。

## 🎯 根因分析 · g1-p2

### 因果链

```text
ConfigMap 'workload-input' 中缺少 key 'unavailable-key' → Volume 'input' 引用不存在 key 触发 Kubelet 挂载失败 → FailedMount 错误导致 Pod 阻塞 → Pod 状态卡在 ContainerCreating / Pending
```

### 根因结论

**已确认的根因**：
Pod 的 Volume `input` 配置中引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`，导致 `kubelet` 在启动容器时挂载卷失败（证据 1、2）。这一挂载错误直接导致容器无法进入运行状态，从而表现为 Pod 停留在 `ContainerCreating` 状态（证据 2）。

**缺失信息**：
输入数据中明确标记 `unknowns` 为 `ConfigMap 'workload-input' 实际存在的 keys 列表`，因此无法确认该 key 是拼写错误还是 ConfigMap 定义遗漏。

---

## 🕵️ 证据内容 · g1-p3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接指明卷挂载失败的具体机制 |
| 2 | K8s State | kubernetes | `container.waiting_reason: reason="ContainerCreating"` | 确认容器处于等待挂载状态 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` | 确认 Pod 未完成初始化 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 数值指标印证 K8s 事件中的容器等待原因 |
| 5 | K8s Event | kubernetes | `event.message: FailedMount` (累计 7 次，跨度 63s) | 确认该挂载错误具有持续性和重复性 |

**证据说明：**
- K8s 事件 `fact-9e0c7a594f13` 指出具体的宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 类型检查失败。
- 该 K8s 事件中的 `Waiting` 原因与 `fact-c042f4055288` 中 `reason="ContainerCreating"` 的指标数值完全一致。
- 日志和追踪因容器未启动而未采集到数据，但 K8s 层面的事件和指标已能闭环证明卷挂载问题。

## 🎯 根因分析 · g1-p3

### 因果链

```text
Pod 配置请求挂载 HostPath '/var/lib/aiops-fixture-unavailable-7f394bef/input' 
  → 节点 node2 该路径不存在或不是目录（K8s 类型检查失败）
  → kubelet MountVolume.SetUp 持续重试失败
  → 容器卡在 ContainerCreating 状态，Pod 处于 Pending
```

### 根因结论

已确认的根因是宿主机节点上缺少符合要求的挂载路径。K8s 事件明确指出 `hostPath type check failed`，且指标确认了容器因此原因处于 `ContainerCreating` 等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.4s
├─ 并发证据采集: 63.9s
│  ├─ g1-p1 aiops-case-v04/workload: 44.2s (Evidence 32.3s, RCA 11.8s)
│  ├─ g1-p2 aiops-case-v05/workload: 63.9s (Evidence 54.2s, RCA 9.4s)
│  └─ g1-p3 aiops-case-v06/workload: 62.5s (Evidence 52.7s, RCA 9.7s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1-p1 aiops-case-v04/workload**: pod-volume-mount-failed
- **g1-p2 aiops-case-v05/workload**: pod-volume-mount-failed
- **g1-p3 aiops-case-v06/workload**: pod-volume-mount-failed
