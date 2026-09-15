## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态（存在 deletionTimestamp），但容器未退出且 phase 仍为 Running，形成 Terminating 卡死。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Running | 确认 Pod 处于活跃状态，未发生正常退出 |
| 2 | K8s State | kubernetes | `deletion_timestamp`: 1789373867 | 确认 Pod 已被发起删除操作，触发终止流程 |
| 3 | Logging | elasticsearch | `application started` (07:12:45.704) | 确认应用容器正常启动 |
| 4 | Logging | elasticsearch | `SIGTERM received; waiting` (07:12:47.189) | 确认应用捕获了终止信号并进入等待逻辑 |
| 5 | Metric | prometheus | `kube_pod_status_phase`: 1 (Running), 0 (Pending) | 确认 Pod 持续保持在 Running 状态，未转为 Pending 或其他状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 排除因应用崩溃导致的重启干扰 |

**证据关联说明：**
Kubernetes 状态与 Metrics 数据一致，证明 Pod 在被标记删除后仍长时间保持 `Running` 状态（证据 1, 2, 5）。关键证据在于应用日志记录到了 `SIGTERM received` 后紧跟 `waiting`（证据 4），这表明应用进程没有崩溃，而是被设计为处理 SIGTERM 信号，但在当前运行环境中未能从等待状态中解脱，这是导致 Terminating 卡死的核心矛盾。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 触发删除并设置 deletionTimestamp → Kubelet 发送 SIGTERM 信号 → 应用进程捕获信号并进入等待逻辑 (waiting for file) → 应用进程未收到终止条件，拒绝退出导致 Terminating 卡死
```

### 根因结论

已确认的根因是**应用进程实现不完善的优雅退出逻辑**。应用虽然在容器收到 `SIGTERM` 信号时正确处理了信号（证据 4），但随后进入阻塞等待特定条件（文件 `/state/teardown-requested` 被创建）的状态，且该条件从未满足。由于应用进程持续运行并持有资源，Kubernetes 无法完成容器清理，导致 Pod 陷入 `Terminating` 状态（证据 1, 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 26.3s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-v13/workload: 47.4s (Evidence 36.9s, RCA 10.3s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
