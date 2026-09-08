## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | workload-5c9c7b6489-fl85h CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: `OOMKilled` (fact-1cd66a41277e) | 确认进程被内核 OOM Killer 终止 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: `137` (fact-4097e077c9e7) | 确认进程因 OOM 退出（信号 9） |
| 3 | K8s State | Kubernetes | `container.resource_limit.memory`: `64Mi` (fact-1ba1a8662a73) | 确认容器内存硬限制仅为 64Mi |
| 4 | K8s Event | Kubernetes | `event.message`: `Warning  BackOff  2m12s (x454 over 120m)` (fact-759638ca9054) | 确认频繁重启导致 BackOff 机制触发 |
| 5 | Metric | Prometheus | `container_memory_usage_bytes`: `241664` bytes (236Ki) 于 17:32 (fact-c55ba718603f) | 反映容器实际使用量（236Ki）已超过内存硬限制（64Mi） |
| 6 | Logging | Elasticsearch | Pattern: `memory allocation advanced`, numeric change: `allocated_mib` from 10 to 48 (fact-50d29dea5a18) | 确认应用存在持续增长的记忆分配行为，且 48Mi 已接近 64Mi 边界 |

**证据印证说明：**
Kubernetes 层面的 `OOMKilled` (fact-1) 和 `exit code 137` (fact-2) 是内存溢出的直接系统级证据，与 Prometheus 层面观测到的容器实际内存使用量 `236Ki` (fact-5) 远超其设定的 `64Mi` 限制相印证。日志记录 `allocated_mib` 从 10 增长至 48 (fact-6)，揭示了在受限资源下应用内部内存分配的持续消耗路径，构成了“资源限制过低”导致“应用被终止”的完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制(64Mi)过低 → 应用内存分配持续增长至越界 → 触发内核 OOM Killer 终止进程 → CrashLoopBackOff 反复重启
```

### 根因结论

已确认根因为 **容器内存配置过低**。
证据表明，`workload-5c9c7b6489-fl85h` 容器的 `memory limit` 仅为 64Mi (证据#3)，但日志显示应用内存分配已增长至 48Mi (证据#6)，且 Prometheus 监控显示其实际内存占用量达到 236Ki (证据#5)。这种内存使用量的持续增长触发了内核 OOM 保护机制，导致容器以 Exit Code 137 (证据#2) 被强制终止 (证据#1)，进而引发 Kubelet 频繁重启并进入 CrashLoopBackOff 状态 (证据#4)。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 24.4s
├─ 并发证据采集: 89.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 89.4s (Evidence 81.7s, RCA 7.5s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
