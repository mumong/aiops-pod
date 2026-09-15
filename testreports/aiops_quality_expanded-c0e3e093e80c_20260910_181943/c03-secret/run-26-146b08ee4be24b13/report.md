## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 Pending/ContainerCreating 状态，应用容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` (x23 over 40m): `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 直接证明 Pod 因找不到指定 Secret 导致挂载失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason` 为 `ContainerCreating` | 证实容器因等待挂载卷而处于卡住状态 |
| 3 | K8s State | kubernetes | `pod.phase` 为 `Pending`，`Ready` 为 `False` (ContainersNotReady) | 确认 Pod 整体调度完成但无法进入运行阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `ContainerCreating`, container: `app`) | 独立观测到 app 容器持续处于等待挂载状态 |
| 5 | K8s Config | kubernetes | `volume` 未设置为 `optional`，且 Pod 定义引用名为 `input` 的 volume | 结合 K8s Event，确定 Secret 缺失导致挂载失败是硬性阻塞点 |

**证据说明：**
Kubernetes 的 Event (`fact-67253c0867d1`) 明确指出了失败原因是 Secret `unavailable-input` 不存在，且没有标记为 `optional`。状态事实 (`fact-7a0f7de39d16`, `fact-95dafa65cd6f`) 与 Metric (`fact-9b380c06aecb`) 均证实该 Pod 持续处于 `ContainerCreating`/`Pending` 状态且未发生过重启（`restart_count=0`），这与挂载失败导致的启动前阻塞特征完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 Secret 'unavailable-input' 且未设为 optional → kubelet 执行 MountVolume.SetUp 失败 → Pod 无法挂载卷 'input' → 状态卡在 Pending/ContainerCreating
```

### 根因结论

已确认根因为 **配置错误**：Pod `aiops-case-v04/workload` 的 Volume 定义引用了 Secret `unavailable-input`，但该 Secret 在 `aiops-case-v04` 命名空间中不存在，且该 Volume 未配置为 `optional: true`。

根据 K8s Event (`fact-67253c0867d1`)，kubelet 明确报告 `secret "unavailable-input" not found` 导致 `MountVolume.SetUp failed`。由于该错误发生在容器启动前的挂载阶段，Pod 无法向前推进，导致处于 `Pending` 和 `ContainerCreating` 状态。证据链闭环，无需补充。

---

## 📊 性能统计

```text
├─ 总耗时: 57.1s
├─ 问题定位: 13.6s
├─ 并发证据采集: 34.1s
│  └─ g1 aiops-case-v04/workload: 34.1s (Evidence 27.0s, RCA 7.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed, pod-imagepull-failed
