## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 处于 ContainerCreating 状态（Phase: Pending），容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `status: Pending`, `phase: Pending`, `ContainersReady: False` (`app`) | 确定故障发生时的 Pod 最终运行状态 |
| 2 | K8s Event | kubelet | `Warning FailedMount`: `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指出挂载失败的根本原因（ConfigMap 缺失） |
| 3 | K8s Event | kubelet | `Warning FailedMount`: `Unable to attach or mount volumes: unmounted volumes=[input]` (over 16m) | 证明挂载失败是持续性且未自愈的 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (labels: `reason: ContainerCreating`) | 独立于 K8s API 确认容器正处于挂载/创建阻塞中 |
| 5 | K8s Config | Pod Spec | `container.resource_request.cpu: 5m`, `container.resource_request.memory: 8Mi` | 排除调度资源不足导致 Pending 的可能 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认容器从未启动过，非 CrashLoopBackOff 等生命周期后故障 |

**证据分析：**
K8s Event 中的错误信息（#2）直接揭示了根因，即挂载卷 `input` 对应的 ConfigMap `unavailable-config` 不存在。Metric 数据（#4）与 K8s Event（#2）高度吻合，分别通过监控指标和 K8s 事件确认了容器卡在 `ContainerCreating` 状态。由于 Pod 处于 `Pending` 且未创建容器实例，日志和链路追踪工具返回空结果符合物理预期，无诊断价值缺失。

## 🎯 根因分析 · g1

### 因果链
```text
Pod YAML 配置了不存在的 ConfigMap 'unavailable-config' (未标记为 Optional) → 
kubelet 执行 MountVolume.SetUp 时因找不到资源而挂载失败 → 
卷 'input' 挂载持续失败，导致 Pod 处于 Waiting/ContainerCreating 阻塞状态 → 
Pod 状态永远停留在 Pending，用户应用无法启动
```

### 根因结论
已确认的根因为 **Kubernetes Pod 配置错误**。

Pod 的定义中引用了一个不存在的 ConfigMap `unavailable-config` 作为卷 `input` 的挂载源，且该卷未设置为可选（Optional）模式。这一配置缺陷导致 kubelet 无法完成卷挂载任务，进而使 Pod 永久处于 `Pending`（ContainerCreating）状态，无法进入运行阶段。该结论由 K8s Event 中的 `MountVolume.SetUp failed` 明确日志（证据 #2）和 Pod 状态指标（证据 #4）直接证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 46.9s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 39.4s (Evidence 30.6s, RCA 8.6s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-imagepull-failed
