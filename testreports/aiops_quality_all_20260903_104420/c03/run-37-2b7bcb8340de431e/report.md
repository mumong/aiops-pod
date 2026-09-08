## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 Pending/ContainerCreating 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 'workload-5b5fc86c8c-zz82w' 状态为 Pending | 提供异常实体的当前生命周期状态 |
| 2 | K8s Event | kubernetes | FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 证实卷挂载失败，直接原因指向 ConfigMap 缺失 |
| 3 | K8s Event | kubernetes | FailedMount: Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting | 证实挂载卷失败导致容器启动阻塞 |
| 4 | K8s Config | kubernetes | Pod 定义挂载卷 'input'，容器资源 requests(memory: 8Mi, cpu: 5m) 与 limits(memory: 32Mi, cpu: 50m) | 确认 Pod 资源与卷配置，排除资源限制导致的问题 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1 (reason: ContainerCreating) | 确认容器处于等待状态 |
| 6 | Metric | prometheus | kube_pod_status_phase: 1 (phase: Pending) | 确认 Pod 集群整体状态 |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 确认容器尚未启动，无重启记录 |

**证据印证说明**
- 证据 2 的 K8s Event 与证据 5 的 Metric（ContainerCreating）共同指向：Pod 因挂载失败而阻塞。
- 证据 1 与证据 2、3 互证：Pending 状态是由于挂载卷 'input' 持续失败（FailedMount）造成的。
- 证据 4 的资源配置与证据 6、7 的状态一致，排除了资源超限导致 Pod 被调度器或 kubelet 拒绝的可能。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Volume 'input' 挂载失败 (FailedMount) → kubelet 无法完成卷挂载 → Pod 持续 Pending/ContainerCreating
```

### 根因结论

已确认根因：**Pod 定义的 Volume 'input' 强依赖 ConfigMap 'unavailable-config'，但该 ConfigMap 在 namespace 'aiops-case-03' 中不存在，导致 kubelet 挂载卷持续失败（FailedMount），进而阻塞容器启动。**

- 证据编号 2 明确记录了 `configmap "unavailable-config" not found` 的错误，证实了依赖缺失。
- 证据编号 3、5 和 6 证实了挂载失败直接导致了 Pod 处于 Waiting/Pending 状态。
- 证据编号 4 证实了 Pod 的资源配置并非故障原因。
- 关于 ConfigMap 缺失的根本原因（是被误删还是未创建），当前证据不足以确定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.8s
├─ 并发证据采集: 42.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 42.2s (Evidence 32.8s, RCA 9.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
