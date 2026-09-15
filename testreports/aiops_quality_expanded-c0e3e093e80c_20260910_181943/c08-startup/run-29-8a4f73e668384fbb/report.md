## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Container memory allocation (256Mi) significantly exceeds the configured memory limit (64Mi), triggering the Linux OOM killer (Exit Code 137) which causes the CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: OOMKilled`, `container.last_exit_code: 137` | 确认应用进程因资源限制被系统强制杀死并进入重启循环。 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi`, `container.resource_request.memory: 8Mi` | 确认 Pod 的内存硬限制为 64Mi，且请求量远低于限制。 |
| 3 | K8s Event | kubernetes | `BackOff  4m13s (x372 over 84m)` | 证实 CrashLoopBackOff 状态已在集群中持续运行 84 分钟，重启次数达 372 次以上。 |
| 4 | Logging | elasticsearch | `log.message: startup allocation 256Mi` | 提供直接证据，表明容器内应用进程启动时尝试分配 256Mi 内存，远超 Pod 限制。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason {reason="CrashLoopBackOff"} = 1`<br>`kube_pod_container_status_restarts_total = 21` | 从监控系统确认当前容器处于等待状态及历史重启累计数。 |

**证据分析：**
Kubernetes 状态证实了 OOMKilled 与 Exit Code 137 的致命错误，这与 Prometheus 监控中持续的 CrashLoopBackOff 状态一致。关键的逻辑闭环在于：应用进程试图分配 256Mi 内存（Log 事实），而 Pod 仅配置了 64Mi 的硬性内存上限（Config 事实），这种 4 倍的差异直接解释了为何 Linux 内核 OOM Killer 介入并终止了容器。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动分配 256Mi (Log 事实) → 超过 Pod 64Mi 硬限制 (K8s Config 事实) → 触发内核 OOM Killer (Exit Code 137) → 容器 CrashLoopBackOff (K8s State)
```

### 根因结论

已确认的根因是 **容器资源配置严重不匹配**。容器内的应用进程在启动时需要申请 256Mi 内存（见证据 #4），但这显著超出了 Kubernetes Pod 配置的 `64Mi` 内存硬限制（见证据 #2）。这种资源超配导致 Linux 内核触发 OOM Killer 机制强制终止了容器（见证据 #1 和 #3），进而导致 Kubernetes 不断尝试重启应用，最终表现为 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.3s
├─ 并发证据采集: 37.7s
│  └─ g1 aiops-case-v15/workload: 37.7s (Evidence 30.4s, RCA 7.1s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
