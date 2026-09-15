## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 的卷配置错误：Pod 声明挂载名为 'input' 的卷并引用 ConfigMap 'workload-input' 中的 key 'unavailable-key'，但该 key 在 ConfigMap 中不存在，导致 Kubelet 挂载失败（MountVolume.SetUp failed），容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `FailedMount` (x23 over 31m): MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 直接定界故障原因为 ConfigMap 键不存在的挂载错误 |
| 2 | K8s Event | Kubelet | `FailedMount` (x10 over 29m): unmounted volumes=[input]: timed out waiting for the condition | 证实挂载请求因底层配置错误持续超时 |
| 3 | K8s State | Pod/Container | `phase: Pending`, `status: Pending`, `ContainersNotReady` (Waiting: `ContainerCreating`) | 提供容器因挂载阻塞导致无法就绪的状态上下文 |
| 4 | K8s Config | Pod Spec | 挂载名为 `input` 的卷并引用 ConfigMap `workload-input` 中的 key `unavailable-key` | 揭示引发 `FailedMount` 的具体配置对象 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: `ContainerCreating`): 1 | 从监控维度确认容器处于等待挂载阶段 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (phase: `Pending`): 1 | 从监控维度确认 Pod 生命周期停滞在 Pending 阶段 |

上述证据在逻辑上形成闭环：K8s 配置显示 Pod 请求挂载不存在的 ConfigMap key (`unavailable-key` in `workload-input`)，Kubelet 在尝试挂载时明确报出 `FailedMount` 错误并反复超时，导致容器状态长期卡在 `ContainerCreating` (Waiting) 且 Pod 保持在 `Pending` 阶段，Metric 监控数据与 K8s 状态完全印证了这一阻塞现象。

## 🎯 根因分析 · g1

```text
Pod 声明挂载不存在的 ConfigMap Key ('workload-input'.'unavailable-key') 
  → Kubelet 挂载卷失败 (MountVolume.SetUp failed) 
  → 容器被 K8s 调度器阻塞在 Waiting (ContainerCreating) 状态 
  → Pod 整体处于 Pending 状态且无法启动
```

**根因结论**
已确认的根因为 **卷配置错误**（证据编号：1, 2, 4）。Pod 的定义中声明了一个名为 `input` 的卷，要求从 ConfigMap `workload-input` 中获取 `unavailable-key` 作为挂载数据源，但该 key 在目标 ConfigMap 中并不存在。Kubelet 在尝试挂载该卷时直接报错并持续失败（证据 1, 2），导致容器无法完成初始化步骤，长期停滞在 `ContainerCreating` 状态，进而表现为 Pod 整体处于 `Pending` 状态（证据 3, 5, 6）。现有证据足以形成完整且排他的因果链。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 52.9s
├─ 并发证据采集: 54.8s
│  └─ g1 aiops-case-v05/workload: 54.8s (Evidence 48.6s, RCA 6.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
