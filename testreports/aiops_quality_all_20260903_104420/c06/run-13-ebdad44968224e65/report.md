## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 环境配置 FAILURE_MODE=runtime_exit 指示应用模拟运行时异常退出行为 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-9e306e72a1a0) | `container.last_terminated_reason`: Error | 确认容器最近一次终止的根因类型为通用错误，指向进程异常 |
| 2 | K8s State | kubernetes (fact-4706701e610e) | `container.last_exit_code`: 2 | 提供具体的非零退出码，验证应用层异常退出机制 |
| 3 | K8s Event | kubernetes (fact-fbba4f3ec221) | `Warning BackOff ... 2m6s (x133 over 31m)` | 描述 Pod 进入 CrashLoopBackOff 状态及重启频率激增的宏观现象 |
| 4 | Metric | prometheus (fact-e8918da2578a) | `kube_pod_container_status_restarts_total`: 10 | 独立验证容器已重启 10 次，与 K8s 状态一致，作为异常持续性的量化证据 |
| 5 | Logging | elasticsearch (fact-521de38f63f2) | pattern: `runtime process exiting`, http_status: 500 | 从应用日志侧确认进程主动退出行为，直接关联至配置模拟的故障现象 |
| 6 | Tracing | tempo (fact-1fa56ecc0bcc) | trace_id: `0adf17e5b0a9aca15ff758c1e1232579`, span_name: `GET /work`, attributes: `aiops.observed_mode: runtime_exit` | 提供 Trace 维度的决定性证据，`aiops.observed_mode` 标签直接锁定退出原因为预期的故障模式配置 |

**证据说明**：
- 证据 2 (K8s Exit Code: 2) 与 证据 5 (日志: runtime process exiting) 互相印证，排除了 OOMKilled (退出码 137) 等系统级原因，确认为应用进程主动退出。
- 证据 6 (Trace 模式: runtime_exit) 为决定性上下文证据，直接解释了退出原因，并与 证据 1 和 证据 4 共同勾勒出“配置导致异常退出 -> 触发重启策略 -> 进入 BackOff 状态”的完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
环境配置 FAILURE_MODE=runtime_exit → 应用检测故障模式并主动终止进程 (exit_code 2) → Kubernetes 触发重启策略导致 CrashLoopBackOff → 应用进程周期性非正常退出 (runtime_exit)
```

### 根因结论

已确认根因为环境配置变量 `FAILURE_MODE` 设置为 `runtime_exit`。该配置指示应用逻辑模拟运行时异常退出行为，导致容器进程以退出码 2 主动终止。Kubernetes 的重启策略不断尝试拉起容器，但容器因相同的配置再次快速退出，最终演变为 `CrashLoopBackOff` 状态。

Trace 中的 `aiops.observed_mode: runtime_exit` 标签与日志中的 `runtime process exiting` 模式形成了闭环证据，证实此 CrashLoopBackOff 是由应用内预期的故障模式配置驱动的，而非底层的系统资源故障或意外的代码 Bug。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 20.0s
├─ 并发证据采集: 82.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 82.2s (Evidence 75.9s, RCA 6.1s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- 未调用 Runbook
