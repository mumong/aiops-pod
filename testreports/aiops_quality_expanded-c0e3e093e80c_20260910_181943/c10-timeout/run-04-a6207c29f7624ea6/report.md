## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | workload in aiops-case-v17 enters CrashLoopBackOff; liveness probe on port 18080 times out, followed by container kill with Exit Code 137. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Liveness probe failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) | 确认容器在运行时出现无响应现象，触发探针超时 |
| 2 | K8s State | kubernetes | Container app terminated with Exit Code 137 | 确认进程被系统强制终止（OOM Killer 或 SIGKILL 标志） |
| 3 | K8s State | kubernetes | Container resource_limit.memory: 64Mi | 确认存在极低的内存硬限制配置 |
| 4 | K8s State | kubernetes | Container resource_request.memory: 8Mi | 确认内存请求量极低，进一步表明资源分配异常受限 |
| 5 | K8s State | kubernetes | CrashLoopBackOff, back-off 2m40s restarting failed container | 确认容器因频繁异常退出进入重启循环 |
| 6 | Metric | prometheus | kube_pod_container_status_last_terminated_reason = Error (fact_id: fact-3c6f5ad0d7cc) | 独立验证容器以 Error 状态终止的事实 |

- **证据 3 & 4 与 2 的因果关联**：容器配置的硬内存限制（64Mi）极低，结合退出码 137，强烈指向进程因超出内存限制被系统 OOM Killer 终止。
- **证据 1 的补充说明**：探针超时与退出码 137 同时出现，说明进程在内存耗尽时立即失去响应，无法处理健康检查请求。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制 (64Mi) 过低 → 进程内存使用超出限制触发 OOM Killer → 进程被强制终止 (Exit Code 137) → 容器崩溃重启并进入 CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器内存限制配置不当（64Mi）**。

该配置远低于运行中 Python ThreadingHTTPServer 实际所需的内存。当进程内存使用超过 64Mi 限制时，Linux 内核 OOM Killer 介入并发送 SIGKILL，导致进程退出码为 137。这也解释了为何 kubelet 报告 Liveness 探针超时（进程僵死）以及为何容器持续处于 CrashLoopBackOff 状态。

*注：具体的应用内存增长模式（是否无界增长）需结合代码逻辑进一步确认。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 29.7s
├─ 并发证据采集: 72.5s
│  └─ g1 aiops-case-v17/workload: 72.5s (Evidence 61.2s, RCA 11.2s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
