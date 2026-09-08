## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.phase: Pending; pod.status: Pending | 确认 Pod 未进入运行状态，停留在调度/挂载阶段 |
| 2 | K8s Event | Kubernetes | `FailedMount` (x23 over 36m): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 明确失败机制：因 ConfigMap 引用不存在导致挂载失败，且该错误持续发生 36 分钟 |
| 3 | K8s State | Kubernetes | container.waiting_reason: ContainerCreating; container.restart_count: 0 | 确认容器处于初始等待阶段，尚未启动，排除了运行后崩溃重启的可能 |
| 4 | K8s Config | Kubernetes | container "app" resource_request.cpu: 5m; resource_limit.cpu: 50m | 确认资源限制设置正常，非资源配额或限制导致的 Pending |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 独立监控指标印证 Kubernetes 状态，确认等待原因为 ContainerCreating |

**证据说明：**
Kubernetes 事件（事实 #2）提供了决定性证据，指出 volume "input" 挂载失败的具体原因是引用了一个不存在的 ConfigMap (`unavailable-config`)。该失败直接导致 Pod 状态为 Pending（事实 #1），且容器一直处于 ContainerCreating 的等待中（事实 #3），未产生应用日志或重启。Metric 数据（事实 #5）与 K8s 状态一致，排除了临时性抖动，确认这是一个持续存在的配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Pod volume 'input' 引用缺失导致 FailedMount → MountVolume.SetUp 持续失败 → Pod 卡在 ContainerCreating/Pending
```

### 根因结论

**已确认根因：挂载卷关联的 ConfigMap 'unavailable-config' 缺失。**

证据表明 Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 在启动过程中，试图挂载名为 `input` 的卷时，Kubernetes 发现所需的 ConfigMap `unavailable-config` 不存在（见事实 #2）。这导致 `MountVolume.SetUp` 失败并反复超时。由于挂载未通过，容器无法启动，Pod 因此停滞在 `ContainerCreating` 和 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 40.3s (Evidence 33.4s, RCA 6.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-config-error, pod-volume-mount-failed, pod-pending-unschedulable
