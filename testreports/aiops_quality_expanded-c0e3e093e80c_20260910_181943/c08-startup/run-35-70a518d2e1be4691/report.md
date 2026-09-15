## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod 容器配置 memory.limit (64Mi) 远低于应用启动代码实际分配的内存大小 (256Mi)，导致 Linux OOM Killer 强制终止容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-7e7619675bdc` | container: app, reason: OOMKilled | 确认进程被系统强制终止的直接原因 |
| 2 | K8s Config | `fact-a3e14f6dfab3` | container: app, memory limit: 64Mi | 展示容器可用的内存硬上限 |
| 3 | Logging | `fact-016ce27a1965` | 2026-09-14T10:49:20.610Z, message: startup allocation 256Mi | 暴露应用实际启动时申请的内存远超容器限制 |
| 4 | K8s State | `fact-e9fc2d6ed606` | container: app, exit code: 137 | 佐证进程因 OOM 信号异常退出 |
| 5 | Metric | `fact-641f1300d25a` | 2026-09-14T10:58:26.424Z, reason: OOMKilled (last_terminated_reason) | Prometheus 记录印证了最后一次终止事件的性质 |
| 6 | K8s Config | `fact-30a013696531` | container: app, memory request: 8Mi | 展示请求量极低，凸显 64Mi Limit 与 256Mi 实际需求的巨大反差 |

Kubernetes 状态和事件明确记录容器处于 `CrashLoopBackOff`，最后一次终止原因为 `OOMKilled`，进程退出码为 137（对应 SIGKILL）。日志在容器启动阶段（10:49:20）明确记录了分配 256Mi 内存的行为，而 Kubernetes 配置（64Mi Limit）严重低于该数值。Metric 数据作为补充，确认了 OOMKilled 的状态。

## 🎯 根因分析 · g1

```text
容器配置 memory.limit (64Mi) 远低于应用启动实际申请量 (256Mi) → Linux OOM Killer 机制介入 → 应用进程被强制终止 (Exit Code: 137) → Pod 进入 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因**：容器资源限制（Memory Limit）配置过低导致容器持续被内核 OOM Killer 终止。

具体表现为：在 Pod `aiops-case-v15/workload` 的 `app` 容器中，Kubernetes 配置的内存硬限制为 **64Mi** (`fact-a3e14f6dfab3`)。然而，应用启动日志显示其实际初始分配的内存高达 **256Mi** (`fact-016ce27a1965`)。由于 64Mi 的内存上限远低于 256Mi 的需求，Linux 内核触发了 OOM Killer 并强制杀死了 `app` 进程（`reason: OOMKilled`, `exit_code: 137`，见 `fact-7e7619675bdc`, `fact-e9fc2d6ed606`）。Kubernetes 随后按策略不断重启该容器，导致现象表现为 `CrashLoopBackOff` (`fact-b3f5be5923e5`) 和大量的 BackOff 事件 (`fact-4aaa28c170ca`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.0s
├─ 并发证据采集: 69.6s
│  └─ g1 aiops-case-v15/workload: 69.6s (Evidence 63.2s, RCA 6.1s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-oomkilled, pod-crashloop-runtime
