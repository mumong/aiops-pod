## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 定义中引用的 ConfigMap 'unavailable-config' 在命名空间 aiops-case-03 中不存在，且 volume 配置未设置 Optional: true，导致 kubelet 执行 MountVolume.SetUp 时发生 FailedMount 错误，阻碍容器创建。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount 2m35s (x50 over 88m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-131915dd2358) | 直接证据：确认 ConfigMap 'unavailable-config' 缺失导致卷挂载失败 |
| 2 | K8s State | Kubernetes | Pod phase: `Pending`, Pod Ready condition: `False` (reason: `ContainersNotReady`) (fact-52a62bac7253, fact-740e6fe5da75) | 现象：Pod 处于 Pending 状态且未就绪 |
| 3 | K8s State | Kubernetes | Container `app` waiting reason: `ContainerCreating` (fact-3d7aaca009a9) | 现象：容器处于等待挂载卷的初始阶段，未能进入 Running |
| 4 | K8s Event | Kubernetes | `Warning FailedMount 6m51s (x36 over 86m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]` (fact-2b4ab62985f0) | 佐证：挂载失败持续发生，确认问题非瞬时 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-8b640802c1ef) | 现象验证：Prometheus 监控指标确认容器停留在 `ContainerCreating` 状态 |
| 6 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (fact-28967b79214b) | 现象验证：Prometheus 监控指标确认 Pod 停留在 `Pending` 阶段 |

**证据印证分析：**
Kubernetes 的事件 (fact-131915dd2358) 明确指出卷 `input` 挂载失败是因为 ConfigMap `unavailable-config` 不存在，这直接解释了容器为何一直处于 `ContainerCreating` 状态 (fact-3d7aaca009a9, fact-8b640802c1ef)。Metric 指标 (fact-28967b79214b) 独立确认了 Pod 处于 `Pending` 阶段，与 K8s 状态一致。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 不存在 → FailedMount (MountVolume.SetUp failed) → ContainerCreating (waiting for volume) → Pod 状态 Pending / 容器未就绪
```

### 根因结论
已确认的根因是：**Pod 定义中引用的 ConfigMap 'unavailable-config' 在命名空间 aiops-case-03 中不存在，且 volume 配置未设置 `Optional: true`**。
- **证据支持**：K8s Event `fact-131915dd2358` 明确指出 `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found`。
- **现象解释**：由于该 ConfigMap 缺失且配置非可选，kubelet 在挂载卷时持续报错，导致容器无法完成初始化，表现为容器状态为 `ContainerCreating` (fact-3d7aaca009a9) 且 Pod 状态为 `Pending` (fact-52a62bac7253)。Metric `fact-8b640802c1ef` 独立佐证了这一等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.5s
├─ 并发证据采集: 42.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 42.3s (Evidence 36.2s, RCA 6.0s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
