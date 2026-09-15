## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | last_terminated_reason: OOMKilled (container: app) | 提供直接失败原因，证实应用进程被系统强制终止 |
| 2 | K8s Event | kubernetes | BackOff restarting failed container app in pod workload-5c9c7b6489-p8462 | 证实容器经历多次重启并进入退避状态，反映故障的持续性 |
| 3 | K8s Config | kubernetes | resource_limit.memory: 64Mi | 提供硬内存限制，确认触发 OOM 的条件上限 |
| 4 | Logging | elasticsearch | 内存分配模式: 18 MiB 增长至 48 MiB (时间窗口: 2026-09-10T22:16:34Z - 22:17:04Z) | 记录故障前应用内部资源使用的异常增长趋势，支持内存耗尽推测 |
| 5 | K8s State | kubernetes | last_exit_code: 137 | 对应 Linux OOM Killer 终止信号 (SIGKILL)，进一步确认 OOM 事实 |
| 6 | Metric | prometheus | kube_pod_container_status_last_terminated_reason=1 (reason: OOMKilled) | 从监控层面对容器最终终止原因进行了独立确认 |

**证据分析：**
K8s 原生状态（证据 #1、#5）与 Prometheus 监控数据（证据 #6）在“OOMKilled”这一核心事实上达成一致，排除了单一数据源故障的可能。日志记录（证据 #4）揭示了应用进程在短时间内将内存使用量从 18 MiB 激增至 48 MiB，这一趋势表明分配行为失控。结合证据 #3 中 64 MiB 的硬限制，日志中记录的 48 MiB 虽未触顶，但结合持续增长的趋势，清晰指向了触及 64 MiB 阈值并触发 OOM Killer 的因果链。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存分配持续增长 (日志观测: 18 MiB -> 48 MiB) → 触及 64Mi 内存限制 → 触发 OOM Killer 终止进程 (Exit 137 / OOMKilled) → 容器不断重启导致 CrashLoopBackOff
```

### 根因结论

**已确认根因：容器应用发生内存泄漏或持续增长，最终触发 OOMKilled。**

日志数据（证据 #4）证实了故障发生前应用内存存在持续增长的明确趋势。这一行为直接触及了资源限制（64 MiB，证据 #3），导致容器进程被系统 OOM Killer 强制终止（证据 #1、#5），进而引发容器进入 CrashLoopBackOff 状态（证据 #2、#6）。所有证据维度（K8s、Metric、Logging）相互印证，事实充分。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 98.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 98.7s (Evidence 90.5s, RCA 8.0s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
