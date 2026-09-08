## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 处于 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 37s (x12 over 8m51s) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (`fact-9f726bb80ffe`) | 明确定位失败机制为 Volume 挂载失败，具体原因是 ConfigMap 缺失 |
| 2 | K8s Event | kubernetes | `Warning FailedMount 2m12s (x3 over 6m49s) kubelet Unable to attach or mount volumes: unmounted volumes=[input]` (`fact-1572411dc2a6`) | 佐证 Volume 长期处于未挂载状态，是配置错误的延续现象 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (`fact-2eac03371a74`); `pod.status: Pending` (`fact-5b630d3f95ce`); `pod.phase: Pending` (`fact-e3e70480b2d8`) | 定义 Pod 当前停滞状态，与挂载失败现象一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason = 1` (labels: `container=app, reason=ContainerCreating`) (`fact-92770163df52`) | 独立观测指标验证 Pod 容器处于等待挂载的特定状态 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` (`fact-1342ffa2b560`); `container.resource_limit.memory: 32Mi` (`fact-658b63a3fcd5`) | 确认资源限制配置已定义，排除资源不足导致的 Pending 可能 |

**证据分析：**
Kubernetes 事件（#1, #2）与指标（#4）互相印证，明确指出容器处于 `ContainerCreating` 等待状态的原因是 `MountVolume.SetUp` 失败。事件数据进一步给出了决定性的失败原因：挂载 Volume `input` 所需的 ConfigMap `unavailable-config` 在命名空间 `aiops-case-03` 中不存在（#1）。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 (事实#1) → Kubelet 无法挂载 Volume 'input' (事实#1) → MountVolume.SetUp 失败 (事实#1) → Pod 处于 ContainerCreating/Pending 状态 (事实#2, #4)
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` 的容器启动失败，根本原因是其引用的 Volume `input` 绑定的 ConfigMap `unavailable-config` 不存在。

- 该缺失导致 Kubelet 在执行 `MountVolume.SetUp` 时直接报错 `configmap "unavailable-config" not found`（证据 #1），从而无法完成 Volume 挂载。
- 这一机制直接导致容器无法启动，Pod 状态长期停留在 `ContainerCreating`（等待中）和 `Pending`，被事件和指标一致捕获（证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.4s
├─ 并发证据采集: 48.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 48.2s (Evidence 40.5s, RCA 7.6s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-imagepull-failed, pod-pending-unschedulable, pod-sandbox-create-failed, pod-config-error
