## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 137` | 进程被强制终止的明确信号 |
| 2 | K8s State | Kubernetes | `reason: OOMKilled` | 指出 137 终止码的直接原因为内存超限 |
| 3 | K8s State | Kubernetes | `waiting_reason: CrashLoopBackOff`, `restart_count: 24` | 应用因 OOM 持续退出，当前陷入反复重启的故障循环 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` | 容器当前内存硬限制极低，极易触发 OOM |
| 5 | K8s Config | Kubernetes | `container.resource_request.memory: 24Mi` | 调度预留量仅为 24Mi，与实际运行状态无关联 |
| 6 | Logging | Elasticsearch | 日志模式：`memory allocation advanced`, 路径 `/work`, `allocated_mib` 变化 (first: 14, last: 46) | 日志证实应用正在执行无界的内存分配，且在短时间内内存需求从 14Mi 激增至 46Mi |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = `1` (reason: OOMKilled), `kube_pod_container_status_restarts_total` = `24` | 指标独立确认了 OOM 状态与持续重启的事实 |

**证据分析：**
Kubernetes 的 Event 和 State 记录了容器因 `OOMKilled` 被杀并触发 `CrashLoopBackOff` 的事实。Elasticsearch 日志中的 `allocated_mib` 数值变化（14 → 46）直接揭示了应用自身的内存分配模式，解释了为何在仅有 64Mi 限制的极低水位下会频繁越界。Prometheus 指标作为独立观测维度，确认了这一异常状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
应用执行无界内存分配（日志模式确认内存持续上升） → 容器实际内存占用突破硬限制（64Mi） → 触发 OOMKilled (Exit Code 137) → Kubernetes 自动重启机制导致 CrashLoopBackOff
```

### 根因结论

**已确认根因：** 容器 `app` 因未受控的内存分配导致内存使用量逼近并超过 64Mi 的硬限制，被系统 OOM Killer 强制终止。

*   **证据支持：** 日志维度显示应用不断进行内存分配（`allocated_mib` 从 14Mi 涨至 46Mi）；K8s 维度明确记录终止原因为 `OOMKilled` 且退出码为 137；由于应用重启策略，反复的 OOM 触发了当前的 `CrashLoopBackOff` 现象。
*   **结论引用：** 见证据项 2 (OOMKilled), 4 (64Mi 限制), 6 (内存增长日志), 1 (137退出码)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.3s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 51.1s (Evidence 43.8s, RCA 7.1s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
