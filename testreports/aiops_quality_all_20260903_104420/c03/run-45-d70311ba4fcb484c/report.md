## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod 引用了不存在的 ConfigMap 'unavailable-config' (Optional=false)，导致 kubelet 在 MountVolume.SetUp 阶段持续失败，Pod 卡在 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` phase: `Pending`; condition: `ContainersReady=False` (ContainersNotReady) | 确认为持续异常组，未进入运行态 |
| 2 | K8s Event | kubernetes | `FailedMount` (x50): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接定位挂载阶段失败，根因为 ConfigMap 缺失 |
| 3 | K8s Event | kubernetes | `FailedMount` (x31): `Unable to attach or mount volumes: unmounted volumes=[input]...` | 辅助说明挂载持续失败的时间跨度 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 验证当前等待原因为 ContainerCreating，与事件状态一致 |

**证据印证说明**：
Kubernetes Event (事实 2) 明确指出因引用不存在的 ConfigMap `unavailable-config` 导致挂载失败，该机制直接阻碍容器启动。Kubernetes State (事实 1) 与 Metric (事实 4) 分别确认了 Pod 处于 `Pending` 状态以及等待原因为 `ContainerCreating`，与事件描述完全一致，证据链闭环。

## 🎯 根因分析 · g1

### 因果链

```text
引用不存在的 ConfigMap 'unavailable-config' (Optional=false) → kubelet MountVolume.SetUp 阶段失败 → 容器启动条件不满足，进入 ContainerCreating 等待 → Pod 持续处于 Pending 状态，无法提供服务
```

### 根因结论

已确认根因为 Pod 配置中引用了不存在的 ConfigMap `unavailable-config` 且该挂载操作非可选（Optional=false），导致 kubelet 无法完成卷挂载，进而使 Pod 卡在 `Pending/ContainerCreating` 状态。该结论由 K8s Event 中的 `FailedMount` 错误原文直接支撑，并与 Pod 状态及等待指标一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 32.5s
├─ 并发证据采集: 45.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 45.1s (Evidence 36.4s, RCA 8.5s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
