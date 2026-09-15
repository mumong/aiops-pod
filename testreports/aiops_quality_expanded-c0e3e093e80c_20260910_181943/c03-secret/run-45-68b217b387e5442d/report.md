## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod 'workload' in namespace 'aiops-case-v04' is stuck in 'ContainerCreating' state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `ContainersReady=False` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 确认容器未进入就绪状态 |
| 2 | K8s State | pod.phase / container.waiting_reason | `phase=Pending`, `waiting_reason=ContainerCreating` | 定位 Pod 卡在调度后、启动前的阶段 |
| 3 | K8s Event | event.message | `Warning FailedMount 8m53s (x35 over 63m) MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 指出卷挂载失败的直接原因是 Secret 不存在 |
| 4 | K8s Event | event.message | `Warning FailedMount 2m57s (x27 over 61m) Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 补充说明卷处于超时未挂载的状态 |
| 5 | K8s Config | container.resource_limit.memory | `32Mi` | 确认内存限制配置（与挂载失败无关的上下文） |
| 6 | Metric | kube_pod_container_status_waiting_reason | 值: `1` (labels: `container="app"`, `reason="ContainerCreating"`) | 在 Prometheus 指标中印证 Pod 处于等待原因 `ContainerCreating` |
| 7 | Metric | kube_pod_container_status_restarts_total | 值: `0` (labels: `container="app"`) | 排除因容器反复 CrashLoop 导致的现象 |

**证据关联说明**：
Kubernetes 事件表（#3, #4）明确指出挂载卷 `input` 失败，原因是 `secret "unavailable-input" not found`。这一配置缺失直接导致容器无法初始化，进而表现为 K8s 状态（#1, #2）中 Pod 处于 `Pending` 且 `Waiting` 状态，同时 Metric（#6）也一致显示 `ContainerCreating`。日志和追踪维度因容器未启动而物理上不存在（#7），因此诊断完全依赖 K8s 原生状态与事件链。

## 🎯 根因分析 · g1

### 因果链

```text
Config Secret 'unavailable-input' 不存在 → kubelet 挂载卷 'input' 失败 → 容器无法初始化挂载依赖 → Pod 永久卡在 'ContainerCreating' (Waiting)
```

### 根因结论

**已确认的根因**：工作负载依赖的 Config/Secret `unavailable-input` 在集群中缺失，导致 Pod 卷挂载（Volume Mount）阻塞。

**证据支撑**：
- 多个 `FailedMount` 事件（#3, #4）直接报错 `secret "unavailable-input" not found`，证实配置引用错误。
- 容器未启动，因此未产生重启（#7），Pod 状态始终被卷挂载机制锁定在 `Pending` 阶段（#1, #2, #6）。

**缺失决定性事实**：无。现有 K8s 事件与状态事实已形成闭环，足以解释当前故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 11.3s
├─ 并发证据采集: 122.5s
│  └─ g1 aiops-case-v04/workload: 122.5s (Evidence 116.2s, RCA 6.2s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-config-error, pod-sandbox-create-failed
