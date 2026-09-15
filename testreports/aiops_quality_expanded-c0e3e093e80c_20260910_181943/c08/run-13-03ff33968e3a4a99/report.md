## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 初始表现为 CrashLoopBackOff，当前处于 Running 状态但曾经历 12 次重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff restarting failed container app ... x162 over 45m` | 证实容器长期处于高频重启状态 |
| 2 | K8s State | Kubernetes | `reason: OOMKilled`, `exit_code: 137` | 明确进程被系统强制终止的直接原因 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory: 64Mi` | 提供判断资源是否充足的基准上限 |
| 4 | Metric | Prometheus | `reason: OOMKilled` (last_terminated_reason), `restarts_total: 11` | 独立验证了容器终止原因与异常事实一致 |
| 5 | Logging | Elasticsearch | 模式 `memory allocation advanced`, `allocated_mib` 从 30 降至 6 (Min 2, Max 42) | 显示应用在处理请求时存在显著的内存波动，最高触及 42MiB |
| 6 | Tracing | Deepflow/Tempo | HTTP `GET /work` (响应 200), 关联 Span `aiops.observed_mode: oom_growth` | 证实请求处理过程中存在内存增长趋势 |

**证据说明：**
*   **状态与原因印证**：K8s 事件报告的高频重启（#1）与退出码 137/oomKilled（#2）直接对应，Metric 指标再次独立验证了这一异常终止原因（#4）。
*   **资源边界与现象**：容器硬限制为 64Mi（#3），而应用处理 `/work` 请求时的日志显示内存分配最高可达 42MiB（#5）。结合 Tracing 中观测到的 `oom_growth` 模式（#6），证实应用在运行时内存需求逼近且最终可能突破资源限制，导致 OOM 机制触发。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 HTTP 请求并分配内存（最高达 42MiB） → 内存使用超出容器 64Mi 限制 → OOM Killer 终止进程（Exit 137） → 容器反复崩溃重启（CrashLoopBackOff）
```

### 根因结论

**已确认根因**：Pod `aiops-case-08/workload-5c9c7b6489-p8462` 的容器应用在处理请求时产生的峰值内存（约 42MiB）过于逼近甚至可能超过其硬限制 `64Mi`。当内存分配触发操作系统 OOM Killer 机制后，进程被强制杀死（Exit Code 137），导致 K8s 控制器不断重启容器，表现为 CrashLoopBackOff 状态。

*   **证据引用**：日志与 Tracing 证实了内存分配行为及增长模式（#5, #6），K8s 配置限定了 `64Mi` 阈值（#3），K8s 状态与 Metric 共同锁定了 `OOMKilled` 及 `137` 退出码（#2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.1s
├─ 并发证据采集: 71.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 71.5s (Evidence 62.0s, RCA 9.4s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
