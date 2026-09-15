## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating 状态，持续约 13 分钟未能进入 Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-dfbd7fc3530f) | 确认 Pod 卡在 ContainerCreating 的直接错误原因是 ConfigMap key 引用错误 |
| 2 | K8s State | kubernetes | `container.waiting_reason = ContainerCreating` (fact-0f2d6b693566) | 确认 Pod 处于等待挂载阶段 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason[reason="ContainerCreating"] = 1` (fact-50416def0e55) | 独立验证了 Kubernetes 状态，显示等待状态持续 |
| 4 | K8s Event | kubelet | `FailedMount` 事件，持续时间 2m16s 并在 11 分钟内出现 5 次 (fact-dd3ea33c4318) | 确认挂载失败是持续性错误，并非瞬时波动 |
| 5 | K8s State | kubernetes | `pod.phase = Pending` (fact-4d0b40eabe3f) | 确认 Pod 尚未被调度到实际运行状态 |

**证据说明**：
- 编号 1 和 2 直接指出了故障的机制与现象：ConfigMap 中缺少 `unavailable-key` 导致挂载失败，Pod 因此卡在 ContainerCreating 状态。
- 编号 3 通过 Prometheus 指标独立验证了编号 2 中描述的等待状态，增强了该现象的可信度。
- 编号 4 提供了故障的时间分布，表明该挂载失败并非偶发，而是持续发生的阻塞错误。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失 key 'unavailable-key' → Volume 'input' 挂载配置引用不存在的 key → kubelet MountVolume.SetUp 失败 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因是 **Pod 的 Volume 'input' 挂载配置引用了一个不存在的 ConfigMap key**。

具体而言，Pod 配置试图从 ConfigMap `workload-input` 中读取 key `unavailable-key` 挂载为 Volume `input`，但该 key 在 ConfigMap 中不存在。这导致 kubelet 在执行 `MountVolume.SetUp` 时失败，无法完成卷挂载，进而阻止了容器 `app` 的启动。该结论由 kubelet 的 `FailedMount` 事件日志（fact-dfbd7fc3530f）直接证实，并与 Pod 持续处于 `ContainerCreating` 状态的 Kubernetes 状态（fact-0f2d6b693566）及对应 Metric（fact-50416def0e55）完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 42.6s
├─ 并发证据采集: 33.5s
│  └─ g1 aiops-case-v05/workload: 33.5s (Evidence 26.6s, RCA 6.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
