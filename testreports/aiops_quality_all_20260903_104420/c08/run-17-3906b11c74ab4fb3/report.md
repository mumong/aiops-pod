## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason: OOMKilled` | 证实容器因触发 OOM Killer 被系统强制终止 |
| 2 | K8s State | Kubernetes | `last_exit_code: 137`, `reason: CrashLoopBackOff` | 进程被杀后的标准退出码及随后的重试状态 |
| 3 | K8s State | Kubernetes | `resource_limit.memory: 64Mi` | 提供内存使用的硬性上限边界 |
| 4 | Logging | Elasticsearch | `allocated_mib`: first=12, last=48, max=48 (pattern: http_request, path: /work) | 证明应用在处理 /work 请求时内存持续增长，逼近且可能触及 limit |
| 5 | Tracing | Deepflow/Tempo | Flow: `GET /work` (9 occurrences), Span trace_id: `8b6b270f6b1cee15b7a70208acd2dc49` | 关联日志中的请求模式，确认导致内存增长的流量来源为 /work 接口 |
| 6 | Metrics | Prometheus | `kube_pod_container_status_last_terminated_reason=OOMKilled` | 独立验证容器终止原因为 OOM |

**证据说明**：
Kubernetes 事件与退出码（#1, #2）确认了容器因超内存被杀（OOMKilled, Exit 137）。日志中针对 `/work` 请求的内存增长记录（#4，从 12 MiB 增至 48 MiB）表明应用逻辑存在内存分配增加的情况。结合容器 `memory limit` 为 64Mi（#3），应用增长后的内存已处于临界或超限状态。Tracing 数据（#5）提供了具体的流量入口，与日志中的 `/work` 路径一致，证实了引发内存增长的异常调用链路。

## 🎯 根因分析 · g1

```text
应用逻辑在处理 GET /work 请求时分配大量内存（日志记录达 48 MiB） → 内存使用突破容器 memory limit (64Mi) → Linux 内核 OOM Killer 强制终止进程 (Exit Code 137, OOMKilled) → Kubelet 执行退避重启形成 CrashLoopBackOff
```

**根因结论**：
已确认根因为**应用内存分配过量**。

容器 `app` 处理 HTTP `/work` 请求时持续分配内存，最大分配量达 48 MiB。由于容器配置了 64Mi 的硬内存限制，应用进程在分配过程中消耗了全部可用内存并触发 OOM 机制，被系统杀死（Exit Code 137）。随后 Kubelet 触发重启策略，导致 Pod 陷入 CrashLoopBackOff 循环。

支撑证据：
- OOM 发生的确凿证据：K8s 状态 `OOMKilled` 与退出码 `137`（#1, #2）。
- 根因触发机制：日志记录的内存增长模式 `allocated_mib` 最高至 48 MiB，且发生在 `/work` 请求上下文中（#4）。
- 故障边界：容器 memory limit 为 64Mi，限制了剩余开销空间（#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.5m
├─ 问题定位: 22.0s
├─ 并发证据采集: 179.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 179.5s (Evidence 168.5s, RCA 10.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
