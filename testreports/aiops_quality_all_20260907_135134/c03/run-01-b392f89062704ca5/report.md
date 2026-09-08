## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 状态停滞在 ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount`：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 记录导致容器启动停滞的直接失败原因 |
| 2 | K8s Event | Kubernetes | `ContainersReady=False`、`Ready=False`，Reason: `ContainersNotReady`，Message: `containers with unready status: [app]` | 确认 Pod 核心组件处于不就绪状态 |
| 3 | K8s State | Kubernetes | Pod `Pending`，`Initialized=True`，`phase=Pendding`；Container `app` waiting_reason `ContainerCreating`，`restart_count=0` | 表明 Pod 资源调度已同意但实际初始化/启动未通过 |
| 4 | K8s Config | Kubernetes | `container.app` resource limits: `cpu=50m, memory=32Mi`; requests: `cpu=5m, memory=8Mi` | 提供资源配置上下文，排除因超卖导致的资源争用 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}=1`；`kube_pod_container_status_restarts_total=0` | 数值上佐证容器处于等待挂载/启动阶段且未发生重启 |

**证据关联说明**：
`K8s Event (Fact 1)` 中 `FailedMount` 明确指向缺失的 ConfigMap `unavailable-config`，直接解释了为什么容器无法退出 `ContainerCreating` 状态（Fact 3 & Fact 5）。同时，`K8s Event (Fact 2)` 确认了由此引发的 Pod 整体未就绪状态。日志与追踪系统（Logging/Tracing）因容器未启动而处于 `not_applicable`，属于预期现象。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 挂载 volume 'input' 引用了 configMap 'unavailable-config' → 命名空间内 ConfigMap 不存在 → kubelet 执行 MountVolume.SetUp 失败 → 容器无法启动，维持在 ContainerCreating 状态
```

### 根因结论
**已确认根因**：Pod `workload-5b5fc86c8c-2xgjz` 中定义的卷 `input` 引用了 ConfigMap `unavailable-config`，但该 ConfigMap 在对应命名空间 `aiops-case-03` 中不存在。
- **现象支撑**：`FailedMount` 事件（证据 #1）直接报出 `configmap "unavailable-config" not found`，导致挂载失败（证据 #2、#3）。
- **决策依据**：该故障是纯配置层面的缺失，逻辑链条完整，由 K8s Event 和 Metric 双重印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.0s
├─ 并发证据采集: 71.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 71.9s (Evidence 63.5s, RCA 8.2s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-config-error, pod-sandbox-create-failed
