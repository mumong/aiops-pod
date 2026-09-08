## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 Pending/ContainerCreating 状态，无法启动应用容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-112ebc2c8ccf) | `Warning FailedMount 12m (x50 over 98m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 确认为 ConfigMap 'unavailable-config' 缺失导致挂载卷操作被拒绝。 |
| 2 | K8s Event | kubernetes (fact-7dbf9748c755) | `Warning FailedMount 2m57s (x42 over 96m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 证实挂载请求在超时后仍持续失败，表明问题未自愈且处于阻塞状态。 |
| 3 | K8s State | kubernetes (fact-dca9fbe0aef7) | `reason: "ContainerCreating"` | 反映应用容器 'app' 处于等待挂载卷完成的挂起状态，无法启动。 |
| 4 | K8s State | kubernetes (fact-2bba10d248be) | `status: "Pending"` | 确认 Pod 整体调度状态为 Pending，未进入运行阶段。 |
| 5 | K8s Config | kubernetes (fact-dca9fbe0aef7) | `ContainerCreating` (Wait Reason) | 佐证容器正处于预启动检查阶段，阻塞点在于卷挂载。 |
| 6 | Metric | prometheus (fact-57eb6fce7d31) | `kube_pod_container_status_waiting_reason=1` (reason="ContainerCreating") | 从监控系统视角确认当前 Pod 确实处于 ContainerCreating 的等待态。 |

**证据总结：**
Kubernetes 事件与 Pod 状态高度一致，明确指向 `FailedMount` 是由于引用了不存在的 `configmap "unavailable-config"`。监控指标仅反映了这一阻塞状态，未提供额外信息。由于容器未启动，日志和链路追踪不可用，但现有的 Kubernetes 事实链已足够形成闭环证据。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中缺失 → Pod 规范引用该 ConfigMap 且未设为可选 → Kubelet 执行 MountVolume.SetUp 失败 → Pod 状态阻塞在 Pending/ContainerCreating
```

### 根因结论

已确认根因：Pod `workload-5b5fc86c8c-zz82w` 的 Volume 'input' 依赖 ConfigMap `unavailable-config`，而该 ConfigMap 在命名空间 `aiops-case-03` 中不存在（事实 1、2）。这导致 kubelet 无法完成挂载操作，Pod 因此持续处于 `ContainerCreating` 和 `Pending` 状态，未能启动应用容器（事实 3、4、6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.6s
├─ 并发证据采集: 47.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.6s (Evidence 38.2s, RCA 9.2s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-sandbox-create-failed
