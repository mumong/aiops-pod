## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 Pending 状态，容器处于 ContainerCreating 阶段，无法正常启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | event.message | `Warning FailedMount 5m21s (x45 over 80m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-9ef3f9d07f7b) | 确认底层挂载失败的根本原因是引用的 ConfigMap 缺失 |
| 2 | K8s Event | event.message | `Warning FailedMount 10m (x31 over 78m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]` (fact-1148d84012ab) | 确认挂载失败导致的 Pod 持续重试与资源锁定 |
| 3 | K8s State | container.waiting_reason | `ContainerCreating` (fact-e8b4c12fc684) | 确认容器处于因资源准备失败而阻塞的等待阶段 |
| 4 | K8s State | pod.phase | `Pending` (fact-d07ba952510e) | 确认 Pod 未完成初始化并调度至运行状态 |
| 5 | K8s Event | pod.condition | `ContainersNotReady`: `containers with unready status: [app]` (fact-94d587ffda5f) | 确认就绪探针未能通过，应用处于不可用状态 |
| 6 | Metric | kube_pod_status_phase | `Pending=1` (fact-06ecbaca3bf0) | Metric 数据与 Kubernetes 声明式状态一致，排除监控延迟导致的误判 |
| 7 | Metric | kube_pod_container_status_waiting_reason | `ContainerCreating=1` (fact-eb43d0de15c9) | 独立确认容器处于等待创建的状态 |

**证据关联说明：**
K8s Event 中的 `FailedMount` 错误直接指出了失败对象为 `volume "input"`，原因是 `configmap "unavailable-config" not found`。这一事实解释了为什么 Pod 和容器分别卡在 `Pending` 和 `ContainerCreating` 阶段 (证据 1-4)。Metric 数据提供了独立的观测视角，确认了该状态在监控端也呈现为稳定的 `Pending` 和 `ContainerCreating`，无波动或状态跳跃 (证据 6-7)。日志与 Tracing 因容器未启动而不适用，无冲突证据。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在命名空间 aiops-case-03 中缺失 → Pod 挂载卷 'input' 时因 required 依赖缺失导致 MountVolume.SetUp 失败 → kubelet 持续触发 FailedMount 事件并阻止容器启动 → Pod 状态停留在 Pending，容器状态为 ContainerCreating
```

### 根因结论

已确认的根因是：Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的容器 `app` 配置中引用了名为 `input` 的卷，该卷依赖于 ConfigMap `unavailable-config`，但该 ConfigMap 在当前命名空间内不存在。

该根因直接导致了 `MountVolume.SetUp` 操作失败 (证据 1)，进而触发 kubelet 不断的挂载重试 (证据 2)，使得容器无法进入运行状态，最终表现为 Pod 处于 `Pending` 且容器为 `ContainerCreating` 的阻塞状态 (证据 3-5)。现有证据链完整，足以定论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 28.2s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 30.2s (Evidence 23.0s, RCA 7.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-sandbox-create-failed, pod-imagepull-failed
