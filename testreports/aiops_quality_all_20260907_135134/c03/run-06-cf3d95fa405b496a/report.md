## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod 配置中引用了不存在的 ConfigMap 'unavailable-config' 作为 volume 'input' 的数据源，且未标记为 optional，导致 kubelet 无法完成卷挂载，Pod 永久卡在 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning FailedMount 74s (x11 over 7m26s) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 明确指出卷挂载失败是由于引用的 ConfigMap 缺失 |
| 2 | K8s State | K8s | `Container.waiting_reason: ContainerCreating` | 表明容器因前置条件不满足而无法启动 |
| 3 | K8s State | K8s | `Pod.phase: Pending` / `ContainersNotReady: True` | 反映 Pod 整体处于未就绪的挂起状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (labels: reason=ContainerCreating) | 确认容器处于等待创建状态，未出现 CrashLoopBackOff |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (container=app) | 排除了容器因业务错误重启导致启动失败的可能性 |

**证据说明：**
- **证据 1** 提供了决定性原因：Kubelet 尝试挂载名为 `input` 的卷时，明确报告找不到 ConfigMap `unavailable-config`。
- **证据 2, 3, 4** 在状态层面一致印证了该原因：Pod 卡在 `Pending/ContainerCreating` 阶段，且 `restart_count` 为 0，说明容器未有机会运行，而是被调度器/ kubelet 拦截在初始化阶段。
- **证据 5** 进一步排除了容器因内存限制或应用代码错误而频繁重启的潜在故障路径。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 ConfigMap 'unavailable-config' (未标记 optional) 
→ Kubelet 挂载 volume 'input' 失败 (Missing ConfigMap) 
→ 容器启动前校验失败，Pod 停留在 Pending 状态 
→ 用户可见 Pod 永久卡在 ContainerCreating，无法提供服务
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的配置错误引用了一个不存在的 ConfigMap `unavailable-config` 作为卷 `input` 的数据源。由于未将其标记为 `optional`，Kubelet 在尝试挂载该卷时失败，导致 Pod 无法完成初始化并永久处于 `ContainerCreating/Pending` 状态。

**关键证据支撑：**
- 错误源自 **证据 1** 中 kubelet 发出的 `FailedMount` 事件，明确指出 `configmap "unavailable-config" not found`。
- 状态与指标数据（**证据 2-5**）一致显示 Pod 处于启动等待阶段且无重启记录，排除了其他可能导致启动失败的因素（如 OOMKilled 或 CrashLoop）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.2s
├─ 并发证据采集: 33.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 33.1s (Evidence 27.1s, RCA 5.9s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
