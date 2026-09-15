## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload 持续处于 ContainerCreating 状态，未进入 Running 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` 62s-15m (累计 x43)：MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接锁定根因为 Secret 缺失导致挂载阻塞 |
| 2 | K8s State | kubernetes | Pod Phase: Pending; Container Waiting Reason: ContainerCreating | 确认 Pod 卡在启动初期，未进入业务运行阶段 |
| 3 | K8s Config | kubernetes | Container 'app' Resource Requests: memory=8Mi, cpu=5m | 排除因资源请求过大导致的调度失败（Pending） |
| 4 | K8s State | kubernetes | Pod Conditions: Initialized=True, PodScheduled=True, Ready=False (ContainersNotReady) | 排除调度与 Init 阻塞，证实问题出在容器卷挂载环节 |
| 5 | K8s Config | kubernetes | Container 'app' Resource Limits: memory=32Mi, cpu=50m | 确认资源约束合法，非硬限制导致 OOMKilled |
| 6 | K8s State | kubernetes | Container 'app' Restart Count: 0 | 证实容器从未成功拉起过，故障自始发即持续 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason` {reason="ContainerCreating", container="app"} = 1 | 独立观测印证 Kubernetes API 的状态快照 |
| 8 | Metric | prometheus | `kube_pod_status_phase` {phase="Pending"} = 1; `restart_total` = 0 | 进一步排除 OOMKilled 或 CrashLoopBackOff 等运行时故障 |

**证据综合说明：**
Kubernetes 事件（证据 1）是判定根因的决定性证据，明确指出了 Volume 'input' 因 Secret 'unavailable-input' 不存在而挂载失败。状态（证据 2）与指标（证据 7）相互印证了“ContainerCreating”这一停滞状态。配置（证据 3, 5）排除了资源压力，而重启计数（证据 6, 8）为 0 的事实进一步确认了 Pod 未能跨过启动阶段，排除了启动后崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间缺失 Secret 'unavailable-input' → kubelet 挂载 Volume 'input' 失败 → Pod 阻塞在 ContainerCreating 阶段 → 用户不可见应用服务
```

### 根因结论

已确认根因：Pod `aiops-case-v04/workload` 的 Spec 中引用了名为 `input` 的 Volume，该 Volume 指向 Secret `unavailable-input`。由于该 Secret 在 `aiops-case-v04` 命名空间中不存在，且未标记为 Optional，导致 kubelet 在执行 `MountVolume.SetUp` 时持续报错（见证据 1），从而永久阻塞容器启动流程。现有事实已足以形成完整闭环，无需更多维度的补充证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 29.1s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-v04/workload: 35.9s (Evidence 28.1s, RCA 7.7s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed
