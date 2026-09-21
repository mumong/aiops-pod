## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 Pending 阶段，容器 app 卡在 ContainerCreating 状态，Volume 'input' 挂载失败导致容器无法启动。 |
| g2 | `aiops-case-v05/workload` | ContainerCreating | Pod workload 持续处于 ContainerCreating (Pending) 状态，容器无法启动。 |
| g3 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating 状态并卡在 Pending 阶段 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Phase: Pending; ContainerWaitingReason: ContainerCreating (fact-308e510cbb6f, fact-9a26049dce15) | 确认 Pod 处于调度完成但容器未启动的阻塞状态 |
| 2 | K8s Event | Kubernetes | FailedMount: "secret \"unavailable-input\" not found" (fact-f229ff4e4bab) | 直接指出 Volume 挂载失败的具体缺失资源 |
| 3 | K8s Event | Kubernetes | FailedMount: "timed out waiting for the condition" (fact-4ebf4f8c813d) | 表明挂载操作因依赖缺失而持续超时 |
| 4 | K8s Config | Kubernetes | Volume 'input' 引用 Secret 'unavailable-input' | 提供 Volume 挂载配置上下文 |
| 5 | Metric | Prometheus | kube_pod_container_status_waiting_reason = 1 (reason: ContainerCreating) (fact-cad9317c38e8) | 外部观测确认容器持续处于等待原因 |

**证据关联说明：**
Kubernetes 事件 `fact-f229ff4e4bab` 明确指出挂载失败的直接原因是 Secret 不存在，这与 `fact-4ebf4f8c813d` 记录的挂载超时现象互为因果，共同解释了容器为何卡在 `fact-308e510cbb6f` 记录的 Pending 状态。Metric `fact-cad9317c38e8` 从外部指标层面独立佐证了这一阻塞状态的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 在 namespace 'aiops-case-v04' 中缺失 → Pod spec 定义 Volume 'input' 引用不存在的 Secret 且 Optional=false → kubelet 执行 MountVolume.SetUp 时因 Secret 缺失而失败 → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

**已确认的根因：** 诊断状态为 `diagnosed`，正式 RCA 已发布。
根本原因是 Pod 的卷配置 `input` 引用了一个在对应命名空间中不存在的 Secret `unavailable-input`（证据引用 `fact-f229ff4e4bab`）。由于该 Secret 在挂载时被标记为必须（非可选），kubelet 无法完成卷挂载步骤，导致容器启动流程被永久阻塞。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-6961b945fa2e` | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 直接指出卷挂载失败的精确原因 |
| 2 | K8s Event | `fact-7e8121003b2a` | `FailedMount`: Unable to attach or mount volumes... timed out waiting for the condition | 验证了挂载操作陷入阻塞并超时的现象 |
| 3 | Metric | `fact-10292b7c713c` | `kube_pod_container_status_waiting_reason` (container=app, reason=ContainerCreating) = 1 | 确认容器因挂载失败而停留在等待状态 |

上述证据相互印证：Kubernetes 事件直接定位到 ConfigMap 中 Key `unavailable-key` 缺失导致挂载失败，指标显示容器持续处于 `ContainerCreating` 等待状态，证实了故障的持续性和具体阻塞点。

## 🎯 根因分析 · g2

### 因果链

```text
ConfigMap 'workload-input' 缺少 Key 'unavailable-key' → kubelet 挂载引用该 Key 的 Volume 'input' 失败 → MountVolume.SetUp 持续报错并超时 → Pod 无限期处于 ContainerCreating (Pending) 状态
```

### 根因结论

已确认根因为 **配置引用错误**（证据 #1）。Pod 中定义的 Volume `input` 引用了 ConfigMap 中不存在的配置项，导致 kubelet 无法完成卷挂载操作，进而阻塞了容器的启动过程（证据 #2, #3）。

---

## 🕵️ 证据内容 · g3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: Pending, status: ContainerCreating (fact-5b80fb4646cb) | 确认为调度成功但启动失败的挂起状态 |
| 2 | K8s Event | kubernetes | "hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory" (fact-d4caecbe8fe6) | 直接证据：节点上指定路径类型不匹配 |
| 3 | K8s Config | kubernetes | Volume `input` 定义为 HostPath 类型，指向路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` (事实隐含于事件) | 提供触发条件：容器应用挂载请求 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` 值为 1 (fact-5bd21c93dfd6) | 辅助印证：容器处于等待挂载或启动阶段，无重启（值为0） |

**证据逻辑：**
Kubernetes 事件 `fact-d4caecbe8fe6` 与配置事实共同揭示了物理资源缺失：Pod 配置挂载了一个 `HostPath` 卷，但 Kubelet 在节点上检测时发现该路径不存在或类型不符合预期。`K8s State` 和 `Metric` 结果一致显示 Pod 处于 `ContainerCreating` / `Pending` 状态，无重启记录，排除启动后崩溃的可能。

## 🎯 根因分析 · g3

### 因果链

```text
Pod spec 定义 HostPath 卷指向 /var/lib/aiops-fixture-unavailable-7f394bef/input
  →
节点 node2 上的该路径不存在或类型不匹配
  →
Kubelet 执行 MountVolume.SetUp 失败 (hostPath type check failed)
  →
Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因：HostPath 卷挂载路径配置错误或节点状态不一致。**
Pod `aiops-case-v06/workload` 配置了名为 `input` 的 HostPath 卷。在调度到节点 `node2` 时，Kubelet 尝试挂载该卷，但检测到指定路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不符合目录要求（"is not a directory" 或路径不存在）。这一文件系统层面的不匹配导致卷挂载过程永久失败，进而使容器无法进入 `Running` 状态。证据 `fact-d4caecbe8fe6` 提供了直接的失败原因说明。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 42.9s
├─ 并发证据采集: 58.2s
│  ├─ g1 aiops-case-v04/workload: 53.8s (Evidence 43.0s, RCA 10.7s)
│  ├─ g2 aiops-case-v05/workload: 42.3s (Evidence 33.5s, RCA 8.8s)
│  └─ g3 aiops-case-v06/workload: 58.2s (Evidence 49.4s, RCA 8.7s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **未归属 lane**: pod-config-error, pod-imagepull-failed
