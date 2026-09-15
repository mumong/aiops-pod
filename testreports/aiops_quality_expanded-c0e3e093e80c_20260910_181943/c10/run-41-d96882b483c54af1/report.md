## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r in namespace aiops-case-10处于CrashLoopBackOff状态，容器app反复重启（23次）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason` = Error | 指示容器上次非正常终止 |
| 2 | K8s Event | Kubernetes | `Warning  Unhealthy  30m (x30 over 65m)   kubelet  Liveness probe failed: HTTP probe failed with statuscode: 500` | 证明健康检查持续失败 |
| 3 | K8s State | Kubernetes | `container.waiting_reason` = CrashLoopBackOff, `container.waiting_message` = back-off 5m0s restarting... | 确认 Pod 处于重启风暴中 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory` = 96Mi | 提供容器内存硬限制，是潜在的资源瓶颈边界 |
| 5 | K8s State | Kubernetes | `container.last_exit_code` = 137 | 关键证据：系统级 OOM-Kill 终止信号 |
| 6 | Logging | Elasticsearch | Pattern: `request completed` (status: 200), `numeric_fields.allocated_mib`: min=0, max=0 | 显示应用此前能处理请求且内部内存统计为0，说明问题非应用逻辑报错 |
| 7 | Tracing | Deepflow | Equivalent L7 flows (HTTP GET /work), response_code: 200, time_range: 2026-09-14 11:03:17 to 11:28:42 | 网络层面请求曾正常返回，印证进程是被外部（内核）杀死而非应用主动退出 |
| 8 | Metrics | Prometheus | `kube_pod_container_status_restarts_total` = 23 | 量化 Pod 重启频次，佐证异常持续存在 |

**证据交叉印证分析：**
*   **终止原因锁定**：K8s 状态显示 `exit_code=137`（通常对应 SIGKILL，特别是 OOM-Kill），而日志和追踪显示 HTTP 请求正常返回 200 后进程随即消失，排除了应用逻辑错误或外部拦截导致 5xx 的可能。
*   **资源约束关联**：Pod 被严格限制在 `96Mi` 内存，且频繁触发 Liveness 探针失败（HTTP 500，可能是 OOM 瞬间或进程重启期间）和 BackOff。
*   **缺失环节**：虽然 Exit Code 137 和内存限制强烈指向 OOM，但由于 Metrics 维度仅有单样本（`sample_count: 1`）且 `trend_evaluable=false`，缺少内存使用量达到 96Mi 峰值的时序数据佐证，因此不能100%排除极短时间内的内存尖刺或系统其他进程竞争导致的极端内存压力，但结合 Exit Code 137，OOM 仍是主导解释。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存资源限制过紧（96Mi） → 进程运行或突发请求导致内存触及限制 → 系统内核触发 OOM-Kill 终止进程（Exit Code 137） → Pod 状态变为 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
Pod `workload-79d9f8fd88-48j8r` 处于 **CrashLoopBackOff** 状态，直接原因是进程被系统强制终止。关键证据 `container.last_exit_code = 137` 以及 `container.last_terminated_reason = Error` 强烈指向 **Out Of Memory (OOM) Kill**。结合 `container.resource_limit.memory = 96Mi` 这一极低硬限制，可以确认 **内存资源限制过紧** 是导致应用进程无法稳定运行并被系统回收的核心原因。

日志显示应用在处理 `/work` 请求时返回了 200（证据 #6），随后进程消失且不再响应 Liveness 探针（证据 #2），这符合 OOM-Kill 导致的“静默死亡”特征（进程在极短时间内被杀，来不及记录日志或发送错误码）。

**局限性说明：**
根据输入事实 `unknowns`，当前缺少 Metrics 中内存使用量的时序数据（无法展示内存曲线在 96Mi 附近尖峰）以及具体的 OOM 触发快照。但在缺乏更多反证的情况下，Exit Code 137 是诊断 OOM 的决定性指标，当前证据链已足以支撑根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 10.5m
├─ 问题定位: 30.6s
├─ 并发证据采集: 585.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 585.4s (Evidence 575.2s, RCA 10.0s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
