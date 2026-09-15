## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，容器反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `last_terminated_reason: Error`, `last_exit_code: 2` | 直接证实容器应用层异常退出 |
| 2 | K8s Event | kubernetes | `Warning BackOff 80s (x338 over 76m)`: Back-off restarting failed container app | 证实已触发 K8s 指数退避重启，导致 CrashLoopBackOff |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total: 19` (7 → 19) | 证实 Pod 在采样期内持续处于重启循环中 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason: 1` (reason="Error") | 独立数据源确认最后终止原因为 Error，与 K8s State 一致 |
| 5 | Logging | elasticsearch | `runtime process exiting` (error, 500) | 日志记录进程强制退出行为，但无详细堆栈 |
| 6 | Tracing | deepflow+tempo | `GET /work` (200) ↔ `runtime process exiting` (500) | 日志与 Trace 关联（如 `4fb6...`），确认 HTTP 响应 500 后进程终止 |

**证据关联说明：**
K8s State 中的 `exit_code: 2` 与 Metric 中的 `terminated_reason: Error` 互相印证了容器异常退出的核心事实。Logging 中的 `runtime process exiting` 和 Tracing 中的 HTTP 500 响应，从应用层面锁定了导致进程崩溃的具体请求链路；但日志仅记录退出事实，缺乏堆栈信息，无法直接解释退出原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程发生内部错误 (Exit Code 2) → Kubernetes 检测到容器终止并尝试重启 → 容器反复崩溃，触发 Back-off 重试限制 → Pod 状态变为 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用进程因内部错误异常退出（Exit Code 2），触发 Kubernetes 的重启机制，最终导致 Pod 进入 CrashLoopBackOff 状态。

*   **证据支持**：K8s 状态与 Metric 均确认最后终止原因为 `Error` 且退出码为 `2`（证据 #1, #2, #4）；日志记录了进程退出的行为（证据 #5）。
*   **未确认因素**：具体的应用代码错误堆栈或业务逻辑缺陷（如配置错误、依赖缺失）未能在日志中找到对应记录（证据 #5 无详细堆栈），目前证据不足以定位导致 `Exit Code 2` 的具体业务代码原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 13.3s
├─ 并发证据采集: 57.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 57.2s (Evidence 49.0s, RCA 8.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
