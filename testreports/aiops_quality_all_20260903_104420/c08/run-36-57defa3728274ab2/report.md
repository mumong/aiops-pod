## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | workload-5c9c7b6489-fl85h in aiops-case-08 is stuck in CrashLoopBackOff with OOMKilled exit code 137. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 退出码 137 (OOMKilled) | 确认进程被系统强制终止 |
| 2 | K8s Config | kubernetes | 内存硬限制 `resource_limit.memory`: 64Mi | 提供导致 OOM 的资源约束基准 |
| 3 | K8s Event | kubernetes | BackOff 重启 415 次，原因 OOMKilled/CrashLoopBackOff | 确认 OOM 已导致应用陷入反复崩溃循环 |
| 4 | Logging | elasticsearch | `/work` 日志 "memory allocation advanced"，`allocated_mib` 在 10 至 42 MiB 间上升 | 确认内存消耗随请求递增（+2 MiB/请求） |
| 5 | K8s State | kubernetes | 容器重启计数 `restart_count`: 22 | 量化崩溃频率，佐证故障持续性和严重性 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` = "OOMKilled" (fact-40c3f832b78c) | 指标层面确认最后终止原因为 OOM |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 12 -> 22 (fact-413c0fa42611) | 指标层面确认重启行为呈上升趋势 |

**证据分析：**
日志中 `/work` 路径的内存分配数据（从 10 到 42 MiB）直接展示了应用存在的内存泄漏模式。该持续增长的趋势解释了为何在 64MiB 的硬限制下会发生 OOMKilled（事实 1, 2）。Kubernetes 事件与指标数据（事实 3, 6, 7）均一致确认了 OOM 现象及随之而来的重启行为，证实了根因。

## 🎯 根因分析 · g1

### 因果链

```text
HTTP /work 接口存在内存泄漏（每次请求增加 2 MiB） → 容器内存持续增长并最终超出硬限制(64MiB) → OOMKilled 进程终止 → CrashLoopBackOff
```

### 根因结论

已确认根因为：`/work` HTTP 接口的代码存在内存泄漏。

应用代码在处理 `/work` 请求时存在内存分配累积，根据日志证据（事实 4），内存占用随请求线性上升。由于容器的硬内存限制仅为 64MiB（事实 2），累积的内存使用量（最高观察到 42 MiB，接近限制）最终导致触发了操作系统级别的 OOM Killer，以退出码 137 终止容器进程（事实 1）。这一机制导致容器频繁重启，最终被 Kubelet 标记为 CrashLoopBackOff（事实 3, 7）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.5s
├─ 并发证据采集: 68.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 68.9s (Evidence 59.1s, RCA 9.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
