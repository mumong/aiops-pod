## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload (aiops-case-v04) stuck in ContainerCreating/Pending state for >49m |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接指向缺失的 Secret 导致挂载失败，支撑根因核心事实 |
| 2 | K8s Event | kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input] | 确认挂载尝试失败的状态，证实卷依赖未就绪 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: "ContainerCreating", `pod.status`: "Pending" | 确认为启动阻塞状态，排除了启动后崩溃等其他场景 |
| 4 | K8s State | kubernetes | `pod.condition`: `ContainersNotReady` (containers with unready status: [app]), `restart_count`: 0 | 确认容器从未成功运行过，排除了运行时 OOM 等重启问题 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 1 (reason: `ContainerCreating`) | 外部验证了 Kubernetes 内部状态，佐证 Pod 持续处于等待挂载阶段 |

证据 1-2 明确指出 `secret "unavailable-input" not found`，这与证据 3 的 `ContainerCreating` 状态完全吻合。由于 `restart_count` 为 0（证据 4），说明问题存在于初始化挂载阶段，而非应用运行后。Metric 证据 5 与 K8s 内部状态一致，排除了监控滞后或误报的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 Secret 'unavailable-input' → Kubelet 挂载卷失败 (FailedMount) → Pod 无法创建容器 (ContainerCreating) → Pod 卡在 Pending 状态 >49m
```

### 根因结论

**已确认根因：** Pod `aiops-case-v04/workload` 的卷定义引用了命名空间 `aiops-case-v04` 下不存在的 Secret `unavailable-input`。

**证据支撑：**
- K8s 事件 `fact-111632955826` 和 `fact-0ce78f421bb7` 明确记录了 `secret "unavailable-input" not found` 的 `FailedMount` 错误。
- K8s 状态 `fact-293d3c47960d` 确认容器处于 `ContainerCreating` 状态。
- Metric `fact-5d82e60ac3ca` 独立佐证了等待原因为 `ContainerCreating`。

**结论：** 根本原因是配置错误（引用了不存在的 Secret），导致存储卷无法挂载，Pod 无法进入运行状态。关于该 Secret 为何未被创建的后续原因（如流水线遗漏或手动错误）证据不足，但不影响当前故障的根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.7s
├─ 并发证据采集: 40.5s
│  └─ g1 aiops-case-v04/workload: 40.5s (Evidence 31.1s, RCA 9.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
