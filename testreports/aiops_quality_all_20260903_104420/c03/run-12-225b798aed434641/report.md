## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 持续处于 ContainerCreating/Pending 状态，因挂载失败无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: Container (`app`) 状态为 `ContainerCreating` | 确证容器未启动，等待前置条件就绪 |
| 2 | K8s Event | Kubernetes | `event.message` (x16): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指出挂载失败及缺失依赖的具体资源名 |
| 3 | K8s Event | Kubernetes | `event.message` (x7): `Unable to attach or mount volumes... timed out waiting for the condition` | 说明失败是持续阻塞，而非瞬时故障 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (Labels: `container=app`, `reason=ContainerCreating`) | 独立验证 Pod 持续处于等待容器创建的状态 |
| 5 | K8s State | Kubernetes | `pod.phase`: `Pending`; `pod.status.phase`: `Pending` | 确认 Pod 处于集群调度完成但实际运行未启动的阶段 |
| 6 | K8s Config | Kubernetes | `container.resource_limit.cpu`: `50m`; `container.resource_limit.memory`: `32Mi` | 提供资源配置上下文，排除资源超限导致的调度失败 |

证据 2 与证据 4 相互印证：K8s Event 的 `FailedMount` 错误与 Prometheus Metric 中 `waiting_reason` 为 `ContainerCreating` 指向同一阻塞点，即卷挂载未完成阻止了容器运行。由于 Pod 始终处于 Pending 阶段，Logging 和 Tracing 数据无法采集。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在命名空间 aiops-case-03 中不存在 → 容器定义中非可选卷 'input' 挂载永久失败 → Kubelet 无法创建容器挂载点 → Pod 持续处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod `workload-5b5fc86c8c-zz82w` 的卷配置依赖 ConfigMap `unavailable-config`，但该 ConfigMap 在当前命名空间中不存在。由于该卷配置为非可选（Optional: false），Kubelet 在挂载阶段持续报错（证据 2、3），导致容器无法初始化（证据 1、4），Pod 维持在 Pending 状态。

证据编号：2, 3, 4, 5

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 35.2s
├─ 并发证据采集: 99.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 99.7s (Evidence 90.7s, RCA 8.8s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
