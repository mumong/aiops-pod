## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod 的启动命令包含 SIGTERM 信号处理逻辑，收到终止信号后进入无限循环等待 '/state/teardown-requested' 文件存在，导致容器无法优雅退出并长时间处于 Terminating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase` = Running (fact-323a99250e17); `termination` stuck 状态 | 确认 Pod 当前实际处于 Running 阶段，而非正常退出后的 Completed/Error |
| 2 | K8s Event | Kubernetes | `pod.condition`: Initialized, PodScheduled, Ready, ContainersReady 均为 True (fact-1e28a41baab6) | 容器状态健康，非 OOMKilled 或 CrashLoopBackOff 等系统级终止 |
| 3 | Logging | Elasticsearch | "SIGTERM received; waiting" (fact-1ba56e1076da); "application started" (fact-e53ccf97c7f2) | 证明应用收到了 SIGTERM 信号并开始处理，但未记录退出日志 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-27668b3c2217) | 确认应用未发生异常重启，排除了资源不足导致的崩溃 |
| 5 | K8s Config | Kubernetes | `memory.request=8Mi`, `memory.limit=32Mi`, `cpu.request=5m`, `cpu.limit=50m` (fact-0ce050a0c115) | 资源请求与限制配置极低，进一步印证非资源不足引起的异常 |

**证据关联分析：**
日志 (3) 明确记录了应用层收到 SIGTERM 后进入等待，而 K8s 状态 (1, 2) 显示容器依然处于 Running 且就绪。结合 Metric (4) 中重启次数为 0 的事实，证实问题并非由于系统强制杀死容器（SIGKILL），而是应用层在收到 SIGTERM 后进入了死循环或长时间挂起，导致优雅退出逻辑失效。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程处理 SIGTERM 信号 → 等待 '/state/teardown-requested' 文件触发(死循环) → 容器未正常退出(K8s 保持 Running) → Pod 处于 Terminating 状态但长时间卡住
```

### 根因结论

已确认的根因：Pod 中的应用程序包含对 SIGTERM 信号的不正确处理逻辑。根据日志证据 (3)，应用收到终止信号后进入等待特定文件 (`/state/teardown-requested`) 存在的逻辑，但由于该文件可能从未出现，导致进程无限期挂起。K8s 虽然向容器发送了 SIGTERM，但由于进程未响应退出，容器保持在 Running 状态，导致 Pod 无法完成终止流程（证据 1, 2, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.0s
├─ 并发证据采集: 64.0s
│  └─ g1 aiops-case-v13/workload: 64.0s (Evidence 58.1s, RCA 5.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
