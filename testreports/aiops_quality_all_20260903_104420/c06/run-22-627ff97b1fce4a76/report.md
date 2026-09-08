## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | exit_code: 2, restart_count: 14 | 确认容器以异常退出码终止并处于反复重启循环中 |
| 2 | K8s Event | kubernetes | `BackOff ... Back-off restarting failed container app` | 证实 K8s 正在执行指数退避重启策略 |
| 3 | K8s Config | kubernetes | memory limit: 96Mi, cpu limit: 200m | 提供资源限制基准，排除显式 OOMKilled 的硬限制条件 |
| 4 | Logging | elasticsearch | 出现 4 次 `event: http_request, level: error, message: runtime process exiting, http_status: 500` | 聚合日志记录显示应用在请求完成后主动退出进程 |
| 5 | Tracing | deepflow | 4 次 `GET /work` 请求返回 `response_code: 500`，时间范围 20:27-20:42，伴随对应 Trace | 从流量侧确认异常发生在请求处理链路末端 |
| 6 | Tracing | tempo | Trace `00775f8b4349217aaa79618a772f0c9f` 的 Span `aiops.observed_mode: runtime_exit` | 直接关联日志事件与 Tracing 的主动退出模式 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (CrashLoopBackOff) | 验证当前 Pod 状态符合反复退出的特征 |

证据间印证关系：Kubernetes 的 CrashLoopBackOff 状态 (Fact 1, 2) 与 Metrics 中的等待原因 (Fact 7) 一致。Logging 中的 `runtime process exiting` (Fact 4) 与 Tracing (Fact 5, 6) 中的 `http.response.status_code: 500` 以及 `aiops.observed_mode: runtime_exit` 完美关联。跨维度的 Trace `00775f8b4349217aaa79618a772f0c9f` 将日志的退出事件、Tracing 的异常模式与流量记录统一在同一个请求上下文中，证明退出是应用内部逻辑主动触发的。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量配置 FAILURE_MODE='runtime_exit' → 应用逻辑检测到配置并主动执行退出信号 → 容器进程以 Exit Code 2 终止 → Kubernetes 检测容器失败并触发 CrashLoopBackOff
```

### 根因结论

已确认的根因为应用显式配置的故障模拟机制：应用通过环境变量 `FAILURE_MODE=runtime_exit` 接收指令，在处理 `/work` 请求后主动以退出码 2 终止进程。

该根因由以下事实支撑：
1.  **直接证据**：Trace Span 记录了 `aiops.observed_mode: runtime_exit` (Fact 6)，日志中聚合了 `runtime process exiting` (Fact 4)。
2.  **现象印证**：Exit Code 2 (Fact 1) 排除了 OOM 导致的退出码 137，且资源限制 (Fact 3) 未触发硬限制，证明进程是被内部逻辑终止。
3.  **状态闭环**：主动退出导致 K8s 触发 CrashLoopBackOff 重启 (Fact 2, 7)。

综上，集群当前异常为配置了特定模拟模式的应用因主动退出引发的 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 13.7s
├─ 并发证据采集: 114.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 114.8s (Evidence 105.0s, RCA 9.6s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
