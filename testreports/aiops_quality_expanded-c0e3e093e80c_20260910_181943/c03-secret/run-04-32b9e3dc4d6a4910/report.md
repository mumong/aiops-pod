## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload stuck in ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v04/workload` phase: Pending, status: Pending, ContainersReady: False | 确认 Pod 处于无法启动的异常状态 [fact-af55004f1e09] |
| 2 | K8s Event | kubernetes | `FailedMount` (x14 over 13m): MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 揭示挂载失败的具体原因及引用缺失资源的错误 [fact-7f0c95c7679a] |
| 3 | K8s Event | kubernetes | `FailedMount` (x6 over 11m): timed out waiting for the condition (unmounted volumes=[input]) | 证实 Kubelet 在持续重试挂载，导致容器阻塞 [fact-2b117d0c5653] |
| 4 | K8s State | kubernetes | Container `app` waiting_reason: `ContainerCreating` | 确认容器进程因挂载阶段阻塞而未被创建 [fact-ad12da5ed319] |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ContainerCreating): value 1 | 独立指标验证容器处于等待状态且原因一致 [fact-d7f3442be644] |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` (container=app): value 0 | 排除因容器启动后崩溃导致重启的可能性 [fact-02860abe7d40] |

**证据说明**：
Kubernetes 事件（事实 2、3）直接指明了失败原因是 Secret `unavailable-input` 不存在，这完美解释了为什么 Volume `input` 无法挂载。Metric 数据（事实 5、6）在宏观层面确认了容器卡在 `ContainerCreating` 且从未启动过，这与 Kubelet 层面的挂载阻塞逻辑一致，形成完整证据闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret 'unavailable-input' → Kubelet 尝试挂载 volume 'input' 失败 → FailedMount 事件报错并持续重试 → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-v04/workload` 的 Spec 配置错误，引用了一个在当前命名空间 `aiops-case-v04` 中不存在的 Secret（`unavailable-input`）来提供 Volume `input` 的数据。这一配置缺失直接导致 Kubelet 在启动容器前无法完成 Volume 挂载，引发 `FailedMount` 错误并持续重试，从而阻止了容器进程的创建和启动。证据编号：[fact-7f0c95c7679a], [fact-2b117d0c5653], [fact-ad12da5ed319]。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 23.6s
├─ 并发证据采集: 550.8s
│  └─ g1 aiops-case-v04/workload: 550.8s (Evidence 544.2s, RCA 6.5s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
