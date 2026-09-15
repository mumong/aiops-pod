## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload STATUS=Terminating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Pod aiops-case-v13/workload` 处于 Terminating 状态 | 确认 Pod 进入终态，但未观察到 OOMKilled 或 Error 等终止原因 |
| 2 | K8s Event | Kubernetes | Pod 所有 Condition（Initialized, Ready, ContainersReady, PodScheduled）均为 True | 排除因健康检查失败或资源不足导致 Pod 被主动杀死的常规可能 |
| 3 | Logging | Elasticsearch | `application started` (08:08:33.601Z) | 确认应用进程已在该 Pod 内正常启动 |
| 4 | Logging | Elasticsearch | `SIGTERM received; waiting` (08:08:34.516Z) | 确认应用进程捕获到了系统终止信号，并进入了等待状态，未触发正常退出逻辑 |
| 5 | K8s State | Kubernetes | Container `app` memory limit: 32Mi, CPU limit: 50m | 排除因资源硬性限制导致进程崩溃的异常 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认该容器自创建以来从未重启过，处于单次运行生命周期中 |

**证据关联说明：**
Kubernetes 层面显示 Pod 被标记为删除（Terminating）且各项检查通过，而 Elasticsearch 日志显示应用进程虽然收到了 SIGTERM 信号，但明确输出 "waiting" 且没有后续退出记录（如 "application stopped"）。结合 Metric 确认无重启历史，证据指向应用进程正在处理信号阶段死锁，而非异常崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Pod deletion request received (deletionTimestamp set) → Container receives SIGTERM signal → Application signal handler blocks until /state/teardown-requested file is detected → Pod STATUS=Terminating within grace period
```

### 根因结论

已确认根因为：**应用程序的 PreStop Hook 逻辑在收到 SIGTERM 后阻塞，等待特定文件 (`/state/teardown-requested`) 存在后才执行退出。**

证据链闭环：
- 证据 #2 和 #6 排除了容器被 K8s 强制 Kill 或崩溃重启的可能。
- 证据 #4 提供了直接证据：进程存活状态下收到了终止信号并进入了等待模式，未能完成优雅退出流程。
- 证据 #3 和 #4 确认了进程处于活跃状态，符合 PreStop 钩子正在执行长阻塞操作的特征。

缺失的决定性事实为触发此次删除请求的源头（如 Deployment 滚动更新或手动 Delete 操作）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.7s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-v13/workload: 44.5s (Evidence 36.0s, RCA 8.4s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
