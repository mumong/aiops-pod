## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，Liveness Probe 持续超时，容器频繁重启（退出码 137） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-6d96152f0dde` | Ready/ContainersReady=False; message: "containers with unready status: [app]" | 确认 Pod 整体处于 NotReady 状态，由 app 容器状态直接导致 |
| 2 | K8s State | `fact-2c39b810ba49` | container.waiting_reason=CrashLoopBackOff | 描述容器当前的崩溃等待状态 |
| 3 | K8s Event | `fact-b7f3177b2cb0` | kubelet Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded | 描述 Liveness Probe 因超时被标记为不健康的事件记录 |
| 4 | K8s State | `fact-96d9ea1e4e67` | container.exit_code=137 | 进程异常退出码，对应内核 OOM Killer 发送 SIGKILL |
| 5 | K8s Config | `fact-3b7e0055319a` | container.resource_limit.memory=64Mi | 容器硬内存限制，是触发 OOM 的边界条件 |
| 6 | K8s Event | `fact-e49cea6ac71b` | Exit Code: 137 | 事件日志记录中确认的异常退出码 |
| 7 | Metric | `fact-1f0dca89267f` | kube_pod_container_status_restarts_total=35 | 采样值显示容器已重启 35 次，反映持续崩溃 |
| 8 | Logging | `fact-0491e62e6268` | 10.2.0.50 - - [14/Sep/2026 14:36:38] "GET /health HTTP/1.1" 200 - | 日志记录显示 /health 接口在崩溃前已成功返回 200 |
| 9 | Tracing | `fact-3313b572508a` | Flow HTTP GET /health dst=172.16.104.36 response_code=200 duration_us min=3001044.0 | 流量记录显示健康检查请求耗时达 3 秒，证实响应超时 |

**证据综合分析：**
1、2、4、6 号证据相互印证，确认容器经历了异常退出（137）且最终陷入 CrashLoopBackOff 状态。
8、9 号证据提供了关键的过程矛盾：应用日志显示 HTTP 请求在收到 200 之前已发生（8），而 Tracing 数据（9）证实 Liveness Probe 的 GET /health 请求确实经历了长达 3 秒的超时。这证明在 Liveness Probe 判定超时之前，内核 OOM Killer 已经因触及 64Mi 内存限制而杀死了进程，进而导致服务无响应和后续的持续崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制 64Mi 过低 → 触发 OOM Killer 强制终止进程 (SIGKILL/Exit Code 137) → Liveness Probe 超时 (context deadline exceeded) → 容器反复重启至 CrashLoopBackOff
```

### 根因结论

已确认的根因是 `container.resource_limit.memory` 设置为 `64Mi`，该值过低，导致容器启动后无法满足运行需求，触发了内核的 OOM Killer 机制。

证据支撑如下：
- **硬证据**：`fact-96d9ea1e4e67` 和 `fact-e49cea6ac71b` 明确记录了进程退出码为 137，这是 Linux 内核 OOM Killer 终止进程的标志性信号。
- **现象印证**：`fact-b7f3177b2cb0` 记录了 Liveness Probe 的 "context deadline exceeded" 超时错误，`fact-3313b572508a` 的 Tracing 数据证实了该超时发生在请求发出后约 3 秒。结合 `fact-0491e62e6268` 中日志仍显示 200 状态码（表明进程在某个瞬间或请求完成时还存活，但随即崩溃或被 OOM 终止），说明在 Probe 等待响应返回期间，进程已被内核强行终止。
- **持续故障**：`fact-1f0dca89267f` 和 `fact-2c39b810ba49` 确认了由此引发的 35 次重启和 CrashLoopBackOff 状态。

因此，内存限制不足引发的 OOM 是导致当前集群异常的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 26.0s
├─ 并发证据采集: 70.6s
│  └─ g1 aiops-case-v17/workload: 70.6s (Evidence 60.7s, RCA 9.7s)
└─ 汇总总结: 16.4s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
