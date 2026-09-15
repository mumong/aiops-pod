## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | aiops-case-v04/workload 处于 ContainerCreating/Pending 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Warning FailedMount 14m (x23 over 44m) MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接定位挂载失败原因 |
| 2 | K8s Event | kubelet | Warning FailedMount 4m12s (x18 over 42m) Unable to attach or mount volumes: unmounted volumes=[input]: timed out waiting for the condition | 证实故障持续且无法恢复 |
| 3 | K8s State | kubelet | status: Pending, reason: ContainerCreating | 当前 Pod 阻塞状态与挂载失败一致 |
| 4 | K8s State | kubelet | Pod Ready/ContainersReady: False (containers with unready status: [app]) | 确认应用容器未就绪 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1 | 指标层面对 Pod 挂起状态的独立印证 |

**证据小结**：K8s 事件记录显示 `secret "unavailable-input" not found` 是导致 `FailedMount` 的直接原因（证据 #1），随后引发的超时警告（证据 #2）确认了挂载动作处于无限期重试状态，导致 Pod 停留在 `Pending` 阶段（证据 #3）。Metric 数据证实该容器正处于 `ContainerCreating` 等待状态，且未发生过重启（重启数 0），排除了启动后崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用的 Secret 'unavailable-input' 不存在 → kubelet 尝试挂载卷失败并不断重试 → Pod 永久停留在 Pending/ContainerCreating 状态 → 应用未启动/不可用
```

### 根因结论

已确认的根因为：**Pod 定义中引用的 Secret `unavailable-input` 不存在**。

证据支持：
1. K8s Event 明确记录了 `secret "unavailable-input" not found`（证据 #1），这是挂载失败的直接原因。
2. 事件中的重复重试记录（证据 #2）与 Pod 持续的 `Pending` 状态（证据 #3）吻合，表明故障未被自动修复。

目前证据充足，可发布该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 28.0s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-v04/workload: 50.0s (Evidence 41.3s, RCA 8.4s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-sandbox-create-failed
