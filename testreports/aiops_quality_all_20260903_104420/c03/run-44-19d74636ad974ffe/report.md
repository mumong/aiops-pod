## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod spec 引用了不存在的 ConfigMap `unavailable-config` 作为 volume `input` 挂载，导致 kubelet 挂载卷失败，Pod 一直处于 Pending/ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-c88d660976d0` | `Warning FailedMount 2m35s (x48 over 84m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 证实挂载失败的具体原因：依赖的 ConfigMap 不存在 |
| 2 | K8s State | `fact-0085f5e9a8ed` | `container.waiting_reason` = `ContainerCreating` | 确认容器处于等待阶段，因底层资源依赖未就绪阻塞 |
| 3 | K8s Config | `fact-032d8dd3521a` | `pod.phase` = `Pending` | 确认 Pod 整体处于待调度或等待就绪状态，未进入 Running |
| 4 | Metric | `fact-bb93c5a3bd22` | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 | 通过 Prometheus 确认该状态持续存在（单样本） |
| 5 | Metric | `fact-d7f9a94ad546` | `kube_pod_container_status_restarts_total{container="app"}` = 0 | 确认容器尚未启动，未发生过重启，排除 OOM/Kill 场景 |
| 6 | Tool Output | `failed_tool_attempts` | `configmaps "unavailable-config" not found` | 直接验证了该 ConfigMap 在目标命名空间中确实不存在 |

**证据关联说明：**
K8s 事件（#1）明确指出了挂载失败是由于 ConfigMap `unavailable-config` 缺失，这直接解释了为什么容器（#2）一直处于 `ContainerCreating` 状态且 Pod 处于 `Pending`（#3）。Metric 数据（#4, #5）与 K8s 状态一致，确认了这一阻塞状态是持续的且未引发重启。工具验证（#6）进一步证实了该 ConfigMap 确实缺失，排除了临时网络或权限故障的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 ConfigMap `unavailable-config` (K8s Config) → kubelet 挂载卷失败 (Event #1) → Pod 陷入 Pending/ContainerCreating (State #2, #3) → 业务不可用 (隐含现象)
```

### 根因结论

**已确认的根因：** Pod `workload-5b5fc86c8c-zz82w` 的卷配置中引用了 ConfigMap `unavailable-config`，但该 ConfigMap 在 `aiops-case-03` 命名空间中不存在。

**证据支撑：**
*   **K8s Event** 明确指出 `configmap "unavailable-config" not found` 导致 `MountVolume.SetUp failed`（证据 #1）。
*   **K8s State** 和 **Metric** 确认由于挂载失败，Pod 持续处于 `Pending` / `ContainerCreating` 阶段，且未触发重启（证据 #2, #3, #4, #5）。
*   **工具验证** 确认了该 ConfigMap 确实缺失（证据 #6）。

因此，故障的直接原因是**配置引用了缺失的基础设施资源**，导致 Kubernetes 无法完成卷挂载，进而阻止容器启动。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.0s
├─ 并发证据采集: 52.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 52.9s (Evidence 47.3s, RCA 5.5s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
