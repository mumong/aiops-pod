## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod yaml中volume 'input'引用的ConfigMap 'unavailable-config'不存在，导致MountVolume.SetUp持续失败，阻塞容器启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: app (ContainerCreating) | 确认容器处于挂起等待状态 |
| 2 | K8s Event | Kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 明确挂载失败的直接原因为依赖对象缺失 |
| 3 | K8s State | Kubernetes | `pod.phase`: Pending | 确认 Pod 处于调度后、容器未启动的阶段 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (reason=ContainerCreating) | 监控指标佐证 Pod 持续处于等待状态 |

**证据分析：**
Kubernetes 事件 (证据 2) 明确指出 `ConfigMap unavailable-config` 不存在导致挂载失败，这是阻塞 Pod 进入 `Running` 状态的根本原因；K8s 状态 (证据 1、3) 与 Metric 指标 (证据 4) 一致确认了容器长期处于 `ContainerCreating` 挂起状态。日志与追踪维度因容器未启动而无法采集，但 K8s 层面的事实已完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 定义引用了不存在的 ConfigMap 'unavailable-config' → Kubelet 挂载卷 (MountVolume.SetUp) 持续失败 → 容器无法初始化 (ContainerCreating) → 用户可见 Pod 卡在 Pending 状态且未 Ready
```

### 根因结论

已确认根因：Pod yaml 中 volume 'input' 引用的 ConfigMap 'unavailable-config' 不存在。
该缺陷导致 `MountVolume.SetUp` 操作不断重试失败，直接阻塞了容器启动流程。相关现象（`FailedMount` 事件、`ContainerCreating` 状态）由 K8s 事件 (证据 2) 及状态 (证据 1、3) 和 Prometheus 监控 (证据 4) 交叉验证确证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.9s
├─ 并发证据采集: 65.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 65.3s (Evidence 56.4s, RCA 8.7s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed
