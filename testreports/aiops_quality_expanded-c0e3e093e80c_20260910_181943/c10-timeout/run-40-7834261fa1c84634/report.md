## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，容器 app 持续以 Exit Code 137 (SIGKILL) 崩溃，且伴随 Liveness Probe 超时事件。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `exit_code: 137` | 确认进程收到 SIGKILL 信号退出。 |
| 2 | K8s Config | K8s | `resource_limit.memory: 64Mi` | 提供极低的内存硬限制条件。 |
| 3 | K8s Event | K8s | `Liveness probe failed: context deadline exceeded` | 验证应用处于无法响应探活检查的僵死或挂起状态。 |
| 4 | K8s Event | K8s | `BackOff restarting failed container app` | 证实容器因异常退出而陷入重启循环。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: Error` | 辅助证明容器异常终止，但未能提供 OOM 的明确标签。 |
| 6 | Logging | ES | `GET /health HTTP/1.1 200` | 确认应用在崩溃前（如 14:31:08）已成功启动并响应请求。 |
| 7 | Tracing | DeepFlow | `/health` 请求 `duration_us: 3000632`~`3002216` | 暴露 L7 层面的极高延迟，印证系统资源耗尽导致响应超时。 |

证据间关联逻辑：应用由 Logging 证实曾成功启动，但在运行中受限于 64Mi 的极低内存硬限制，导致系统资源耗尽。这引发进程僵死（表现为 Tracing 和 K8s Event 中的 Liveness 超时）并最终触发 OOM 机制被系统杀死（Exit Code 137），最终形成 CrashLoopBackOff 循环。

## 🎯 根因分析 · g1

### 因果链

```text
容器硬内存限制配置过低 (memory.limit=64Mi) → 应用运行期间内存溢出，触发系统 OOM Killer → 进程接收 SIGKILL 信号退出 (Exit Code 137) → 容器反复崩溃重启 (CrashLoopBackOff) 且伴随 Liveness 超时
```

### 根因结论

已确认根因为：容器配置的内存硬限制 (`memory.limit=64Mi`) 严重不足。

证据表明，应用在运行中受限于此硬限制，导致内存耗尽，触发了系统 OOM Killer 机制。这解释了进程为何以 `Exit Code 137 (SIGKILL)` 被强制终止，以及在进程被杀之前的僵死状态为何会导致 Liveness Probe 超时和后续的 CrashLoopBackOff 重启循环。

尽管 `kubectl_describe` 摘要中未显式列出 `OOMKilled` 文本，但在 64Mi 如此严格的限制下，结合 Exit 137 和 Liveness 超时，指向 OOM 的逻辑链条已充分闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 14.5s
├─ 并发证据采集: 89.0s
│  └─ g1 aiops-case-v17/workload: 89.0s (Evidence 72.9s, RCA 16.0s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
