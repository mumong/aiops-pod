## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 持续处于 ContainerCreating/Pending 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount 108s (x13 over 12m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指出 Volume "input" 因 ConfigMap "unavailable-config" 缺失导致挂载失败 |
| 2 | K8s State | Kubernetes | `pod.condition` (ContainersReady=False, reason=ContainersNotReady); `pod.phase` (Pending); `container.waiting_reason` (ContainerCreating) | 确证 Pod 卡在初始化阶段，容器未进入就绪状态 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory` (8Mi), `container.resource_limit.memory` (32Mi) | 排除容器资源限制导致挂载/启动阻塞的可能性 |

*证据关联：K8s 事件直接引用了不存在的 ConfigMap ID 以及挂载失败的具体动作（FailedMount），与 K8s 状态（Pending/ContainerCreating）形成了从“触发原因”到“当前症状”的完整闭环。由于容器未启动，Metrics/Logging/Tracing 维度无实际业务数据可佐证或补充。*

## 🎯 根因分析 · g1

### 因果链

```text
Pod 声明挂载 ConfigMap 'unavailable-config' → ConfigMap 缺失导致 FailedMount → Volume 挂载超时且未重试成功 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为**Pod 定义的 Volume "input" 引用了不存在的 ConfigMap "unavailable-config"**。该配置错误导致 kubelet 在初始化容器时持续触发 `FailedMount` 错误，进而使 Pod 处于 `Pending` 且 `ContainerCreating` 状态。这一结论由 Kubernetes 事件日志中的明确报错（证据 #1）与当前的 Pod 状态（证据 #2）直接支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.7s
├─ 并发证据采集: 49.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 49.6s (Evidence 42.0s, RCA 7.3s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-sandbox-create-failed
