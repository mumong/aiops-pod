## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod 定义中依赖的 ConfigMap `unavailable-config` 在 `aiops-case-03` 命名空间中不存在，导致 kubelet 挂载 volume 持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | status: Pending; phase: Pending | 确定 Pod 处于不可用的阻塞状态 |
| 2 | K8s Event | kubernetes | Warning FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (x21 over 30m) | 直接指出 kubelet 挂载 volume "input" 时找不到 ConfigMap 的具体错误 |
| 3 | K8s Event | kubernetes | Warning FailedMount: Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition (x10 over 28m) | 确认挂载超时是持续的阻塞现象 |
| 4 | K8s Event | kubernetes | ContainerCreating (containers with unready status: [app]) | 将挂载失败与 Pod 无法就绪的现象关联起来 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason="ContainerCreating") | 确认应用容器 app 处于等待状态且原因与 K8s 状态一致 |

**证据说明**：
- 事实 2 (FailedMount) 提供了具体的缺失资源标识（ConfigMap `unavailable-config`），事实 3 (timed out) 证实该缺失导致的挂载尝试具有持续性和重复性。
- 事实 1, 4 (K8s State) 与事实 5 (Metric) 相互印证：Pod 的状态 Pending、条件 NotReady 与 Metrics 中的 ContainerCreating 等待原因完全匹配，排除了其他容器状态异常的可能。
- 事实 4 的 message 明确关联了 `ContainersNotReady` 与 `app` 容器，说明阻塞点位于容器启动阶段，这与挂载 volume 失败导致容器无法进入 Running 状态的机制吻合。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 ConfigMap unavailable-config (事实 2) → Kubelet 挂载 volume "input" 失败 (事实 2, 3) → 容器 app 处于 ContainerCreating 等待状态 (事实 1, 4, 5) → Pod 状态 Pending 且不可用 (事实 1, 5)
```

### 根因结论

已确认根因是 **Pod 定义中依赖的 ConfigMap `unavailable-config` 在 `aiops-case-03` 命名空间中不存在**。

该缺失资源直接导致 kubelet 在执行 `volume "input"` 的挂载操作时持续失败（事实 2, 3），引发 MountVolume.SetUp 报错与挂载超时。由于该 volume 挂载是启动前置条件，应用容器 `app` 被卡在 `ContainerCreating` 状态（事实 1, 4, 5），最终表现为 Pod 处于 `Pending` 且未就绪。现有 Kubernetes 事件与指标已提供闭环证据，无需更多日志或追踪数据即可定论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.6s
├─ 并发证据采集: 49.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 49.4s (Evidence 43.4s, RCA 5.8s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
