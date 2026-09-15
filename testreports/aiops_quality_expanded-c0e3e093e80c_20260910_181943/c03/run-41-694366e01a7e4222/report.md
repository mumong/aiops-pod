## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 持续处于 ContainerCreating/Pending 状态，未能进入 Ready。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-aceb2065fcd9` | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 揭示阻塞容器启动的底层存储故障原因 |
| 2 | K8s State | `fact-eb4ca07c41c2` | `container.waiting_reason: ContainerCreating` | 确认 Pod 处于挂载卷等待状态 |
| 3 | K8s State | `fact-117fb59b9c02` | `pod.phase: Pending` | 确认 Pod 未能进入 Running 阶段 |
| 4 | Metric | `fact-e87fc119af09` | `kube_pod_container_status_waiting_reason: 1` (labels: `container=app`, `reason=ContainerCreating`) | 确认容器处于等待状态，与 K8s 事件原因一致 |

K8s 事件（#1）明确指出 `configmap "unavailable-config"` 缺失导致卷挂载失败（FailedMount）；K8s 状态（#2, #3）和 Metric 指标（#4）均证实容器因挂载卷问题卡在等待阶段（ContainerCreating/Pending），数据相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 ConfigMap 'unavailable-config' 作为非可选卷 → 
kubelet 执行 MountVolume.SetUp 校验失败，持续报错 → 
Pod 卡在 ContainerCreating 阶段，无法启动容器 → 
Pod 状态持久化为 Pending/ContainerCreating，容器未运行
```

### 根因结论

已确认根因为 **Pod YAML 中 volume 'input' 引用了不存在的 ConfigMap 'unavailable-config'**。

该不存在的资源直接导致 kubelet 在挂载卷阶段持续报错 `FailedMount`，从而阻塞了后续容器的拉取与启动流程。证据 #1 记录了具体的挂载失败日志，证据 #2 至 #4 确认了这一阻塞状态（ContainerCreating）贯穿了 Pod 运行周期。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.4s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 45.0s (Evidence 37.2s, RCA 7.7s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed
