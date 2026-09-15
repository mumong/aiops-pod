## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 配置引用了不存在的 ConfigMap 'unavailable-config'，导致 kubelet 挂载卷失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount  93s (x35 over 56m)  kubelet  MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-ad67bddfb79f) | 核心直接证据，指明挂载失败的具体原因是引用了不存在的 ConfigMap |
| 2 | K8s Event | kubernetes | `FailedMount  11m (x20 over 54m)  kubelet  Unable to attach or mount volumes: unmounted volumes=[input]` (fact-cf1fc332950f) | 辅助证据，确认挂载失败具有持续性，并非偶发事件 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` (fact-b6ea2e611933)、`pod.status: Pending` (fact-e6e1a39556a6) | 现象证据，验证容器未启动导致 Pod 处于 Pending 状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-c21ce91fcc7f) | 佐证现象，指标层面确认容器处于等待挂载阶段 |

证据 1 和 2 均源于 kubelet 日志，明确将 Pod 的 `Pending` 状态和 `ContainerCreating` 等待原因（证据 4）归因为 `configmap "unavailable-config" not found`，形成完整的证据闭环。

## 🎯 根因分析 · g1

```text
Pod 配置引用了不存在的 ConfigMap 'unavailable-config' (fact-4d34c0c04012/fact-ad67bddfb79f) → 挂载卷失败 (FailedMount) → Pod 状态停留在 Pending / 容器等待挂载 (fact-b6ea2e611933/fact-c21ce91fcc7f) → 应用服务不可用
```

**根因结论：**
已确认根因为 Pod 配置错误。Pod 定义中引用了名为 `unavailable-config` 的 ConfigMap 用于挂载卷，但该 ConfigMap 在当前命名空间下不存在，导致 `kubelet` 挂载卷操作持续失败（失败次数超过 35 次，持续时间超 56 分钟）。受此阻塞，容器无法启动，Pod 处于 `Pending` 状态，应用服务不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 59.2s
├─ 问题定位: 12.4s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 38.3s (Evidence 33.4s, RCA 4.7s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
