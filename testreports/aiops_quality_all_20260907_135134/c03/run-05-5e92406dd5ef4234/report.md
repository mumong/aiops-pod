## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 状态为 Pending/ContainerCreating，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-3c29ca843c571` (aggregated) | `Warning FailedMount 11s (x11 over 6m23s) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | **决定性证据**：确认 Volume 挂载失败的核心原因是 ConfigMap 缺失 |
| 2 | K8s Config | `fact-8fdce10767d6` | `container.app.resource_request.cpu: 5m` | 排除资源不足（CPU）导致的调度或启动问题 |
| 3 | K8s Config | `fact-340f46d58549` | `container.app.resource_request.memory: 8Mi` | 排除资源不足（Memory）导致的调度或启动问题 |
| 4 | Metric | `fact-36bc864a7b7d` | `kube_pod_container_status_waiting_reason=1 (reason: ContainerCreating)` | 确认容器处于“等待创建”的停滞状态，印证 K8s 事件 |
| 5 | Metric | `fact-d94897e91161` | `kube_pod_container_status_restarts_total=0` | 确认 Pod 从未成功启动过，属于初始配置失败 |

**证据印证分析：**
Metrics 确认 Pod 处于 `Waiting` 且重启次数为 `0`（事实 #4, #5），这与 K8s Event 中反复上报的 `FailedMount` 事件（事实 #1）完全吻合。ConfigMap 配置缺失（事实 #1）直接阻止了 Volume 挂载，这是容器无法进入 `Running` 状态的直接且唯一的技术阻碍。日志与追踪数据不可用（事实 #6, #7），因为容器未启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义声明引用 ConfigMap 'unavailable-config' → 集群中不存在该 ConfigMap → kubelet 挂载 Volume 失败 (MountVolume.SetUp failed) → Pod 停留在 Waiting (ContainerCreating) 状态
```

### 根因结论

已确认的根因是：**Pod 定义中引用的 ConfigMap Volume 目标不存在**。

Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的 YAML 定义中包含一个名为 `input` 的 ConfigMap Volume，它指向 ConfigMap `unavailable-config`。集群中不存在名为 `unavailable-config` 的 ConfigMap，导致 kubelet 在尝试挂载该 Volume 时报错 `configmap "unavailable-config" not found`（见事实 #1）。这一失败阻止了容器的启动，从而引发了 `ContainerCreating` 的停滞状态（见事实 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 57.7s
├─ 问题定位: 19.9s
├─ 并发证据采集: 28.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 28.3s (Evidence 21.4s, RCA 6.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
