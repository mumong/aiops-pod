## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod `workload-5b5fc86c8c-2xgjz` 声明挂载了名为 `input` 的 ConfigMap 卷，但其引用的 ConfigMap `unavailable-config` 在命名空间 `aiops-case-03` 中不存在，导致 Kubelet 挂载卷永久失败，Pod 始终处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `phase: Pending`、`container.waiting_reason: ContainerCreating` | 确认 Pod 卡在初始化阶段，容器未能进入就绪或运行状态。 |
| 2 | K8s Event | Kubelet | `FailedMount`: `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 提供决定性证据，明确挂载失败原因是指定的 ConfigMap 不存在。 |
| 3 | K8s Event | Kubelet | `FailedMount`: `timed out waiting for the condition` (持续 8m45s) | 证明该挂载错误是持续发生的阻塞性问题。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 指标层面确认容器处于等待状态。 |

**证据印证分析**：Kubernetes 事件中的 `FailedMount` 错误（#2、#3）直接解释了 Pod 为何持续处于 `Pending` 状态且容器处于 `ContainerCreating`（#1、#4）。日志和追踪数据不适用（容器未启动），因此 K8s 内部状态和事件是唯一的判定依据。

## 🎯 根因分析 · g1

```text
ConfigMap unavailable-config 不存在于命名空间 aiops-case-03 → Kubelet 执行 volume mount 失败 → Pod 无法挂载 input 卷并进入 ContainerCreating 状态 → Pod 长期处于 Pending 状态
```

**根因结论**：
Pod `workload-5b5fc86c8c-2xgjz` 声明挂载了名为 `input` 的 ConfigMap 卷，但引用了不存在的 ConfigMap `unavailable-config`。这导致 Kubelet 无法完成卷挂载，Pod 被阻塞在 `Pending` 状态且无法启动容器 [证据 #2, #3]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 27.5s
├─ 并发证据采集: 30.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 30.4s (Evidence 23.5s, RCA 6.8s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
