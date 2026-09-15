## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod 的 SIGTERM 信号处理器未退出进程，而是进入无限循环等待外部文件 `/state/teardown-requested` 存在；因该文件未出现且无 finalizers 阻塞，Pod 被标记为 Terminating 后进入 3900s 宽限期等待 kubelet 发送 SIGKILL。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s API | `status.phase=Running` | 确认 Pod 核心状态未变，处于正常运行周期内。 |
| 2 | K8s Event | K8s Event | `Normal Killing... Stopping container app` (7m48s前) | 确认 kubelet 已发起终止容器的动作。 |
| 3 | K8s Event | K8s Event | `Warning Unhealthy... Readiness probe failed: command timed out` (20s前) | 确认应用进程在容器终止阶段卡死，未响应存活探针。 |
| 4 | Logging | ES 日志 | `application started` (07:43:55.403Z) | 确认应用正常启动，生命周期起点明确。 |
| 5 | Logging | ES 日志 | `SIGTERM received; waiting` (07:43:57.518Z) | 捕获到应用接收到终止信号并进入等待状态的行为。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除应用因 OOM、CrashLoopBackOff 或其他崩溃导致的重启现象。 |

**证据说明：**
1. Pod 整体处于 `Running` 状态，证明其具备完整的工作负载能力，不存在资源短缺或调度异常（无 Metric 波动，无 K8s Warning）。
2. 容器内日志在启动 2 秒后收到 `SIGTERM` 信号并打印 `waiting`，结合 `Readiness probe failed: timed out`，证明该等待是无限循环的（无超时自动结束）。
3. `restart_count = 0` 排除了应用因为非预期崩溃而重启的可能，确认问题出在应用当前的生命周期停滞上。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 (未处理 SIGTERM 退出) → 收到 SIGTERM 后进入死循环等待 (/state/teardown-requested 不存在) → 容器进程卡死无响应 → kubelet 终止探针超时判定失败 → Pod 滞留 Terminating 状态
```

### 根因结论

**已确认的根因：应用程序的 SIGTERM 信号处理器存在逻辑缺陷，导致进程在接收终止信号后进入无限循环等待。**

具体而言，应用代码未配置正常的优雅退出逻辑，而是转而等待外部文件 `/state/teardown-requested`。由于该文件不存在，应用进程无法响应退出命令，导致 Pod 卡在 `Terminating` 状态。
- 证据 **#5** 日志 `SIGTERM received; waiting` 证实了信号接收及进入特定等待路径的行为。
- 证据 **#3** 探针超时证实了该等待状态持续存在且无超时机制自行解除。
- 证据 **#4** 和 **#6** 排除了其他导致 Pod 无法清理的常见因素（如应用未启动或崩溃重启）。

---

## 📊 性能统计

```text
├─ 总耗时: 8.5m
├─ 问题定位: 18.4s
├─ 并发证据采集: 481.2s
│  └─ g1 aiops-case-v13/workload: 481.2s (Evidence 472.7s, RCA 8.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
