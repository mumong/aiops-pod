## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 Pending/ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | `Pending` | 确认 Pod 未进入运行状态 |
| 2 | K8s Event | event.message | `Warning FailedMount 6s (x33 over 51m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 提供确切的错误原因：Kubelet 因找不到 ConfigMap 挂载卷失败 |
| 3 | K8s Config | container.resource_request.cpu | `5m` | 排除 CPU 资源不足导致调度的可能 |
| 4 | K8s State | event.message | `Warning FailedMount 5m46s (x20 over 49m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]...` | 证实挂载失败是持续 50 分钟以上的阻塞性故障 |

现有证据链完整：Pod YAML 引用了不存在的 ConfigMap `unavailable-config`，导致 `MountVolume.SetUp` 持续失败，容器处于等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 ConfigMap 'unavailable-config' → 卷挂载初始化失败 (FailedMount) → 容器等待挂载完成 → Pod 保持 Pending 状态
```

### 根因结论

根因已确认：Pod Spec 中定义的非可选 ConfigMap volume `input` 引用了不存在的 ConfigMap `unavailable-config`。

这一配置错误直接导致了证据 [2] 和 [4] 中反复出现的 `FailedMount` 事件，Kubelet 无法完成卷挂载，因此容器无法启动，Pod 一直处于 `Pending` 状态（证据 [1]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.2s
├─ 并发证据采集: 36.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 36.2s (Evidence 28.0s, RCA 8.1s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
