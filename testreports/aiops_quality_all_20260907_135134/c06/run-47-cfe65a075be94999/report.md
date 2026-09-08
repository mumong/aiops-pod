## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，应用容器反复以 Exit Code 2 异常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态 `Running`，但 `ContainersReady=False`，等待原因 `CrashLoopBackOff` (`fact-f21d01a0efe8`) | 确认异常表现，容器处于重启循环中 |
| 2 | K8s State | Kubernetes | 容器最后一次终止原因 `Error`，退出码 `2` (`fact-3a423f15d6f3`, `fact-0a6d6ef62867`) | 确认应用进程因错误强制退出，且非 OOMKilled |
| 3 | K8s Event | Kubernetes | `BackOff 2m22s (x522 over 117m) ... Back-off restarting failed container app` (`fact-24562d257ef8`) | 证实重启行为已持续约 117 分钟，频率高且稳定 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `CrashLoopBackOff` (1)；`restart_total` = 27 (`fact-78482818effc`, `fact-7c295731da01`) | 独立指标确认了 K8s 观测到的重启状态 |
| 5 | Logging | Elasticsearch | 模式：`event: http_request`, `level: error`, `message: runtime process exiting`，`http_status: 500`，`path: /work`，`allocated_mib: 0` (`fact-8ea49a9106c1` 等) | 定位崩溃时间点，显示进程在收到 HTTP 请求后直接退出，内存使用为 0 |
| 6 | Tracing | Tempo/Deepflow | HTTP Flow 聚合：`GET /work` 返回 `500`，耗时 5.2-5.9ms (`fact-9ebeecabfc1a` 等)；对应 Span `GET /work` 状态 `200` 但属性含 `runtime_exit` (`fact-24b762a1cf33`) | 确认 `/work` 接口触发了服务端崩溃，部分调用链路在应用层崩溃前返回 200（可能为异步或中间件层） |

证据间印证关系：
- **K8s 状态与日志关联**：K8s 记录的 `exit_code=2` 与日志中的 `runtime process exiting` 互相印证，表明是应用进程内部发生的致命错误导致崩溃。
- **资源使用情况**：日志显示 `allocated_mib=0` 且 K8s 退出码非 `OOMKilled`，结合 Metric 中 `restart_total` 的持续增长，排除了常规内存超限导致的重启，指向应用逻辑或运行时层面的崩溃。

## 🎯 根因分析 · g1

### 因果链
```text
应用未捕获的致命异常（如段错误或运行时崩溃） → 进程强制终止 (Exit Code 2) → K8s 执行 CrashLoopBackOff 策略 → Pod 持续重启并返回 500/崩溃
```

### 根因结论
已确认根因为**应用主进程在处理 `/work` 请求时发生未捕获的致命异常**。

- **确认事实**：
  1. **直接症状**：Pod 处于 `CrashLoopBackOff` 状态，重启次数达 27 次以上，退出码固定为 `2`（`fact-f21d01a0efe8`, `fact-3a423f15d6f3`）。
  2. **崩溃机制**：日志明确显示 `runtime process exiting`，且伴随 `http_status: 500`（`fact-8ea49a9106c1`）。
  3. **触发条件**：Tracing 和 Logging 均指向 `/work` 端点（`fact-24b762a1cf33`, `fact-9ebeecabfc1a`）。

- **缺失环节（证据不足部分）**：
  - 由于日志仅输出 `runtime process exiting` 而无具体的 Traceback（Stack Trace），无法确定具体的编程语言异常类型（如 Python 的 Uncaught Exception 或 C/C++ 的 Segfault）。
  - 虽然内存显示为 0，但无法完全排除极短时间内的内存尖峰未被监控捕捉（`unknowns` 字段），不过鉴于退出码非 OOM 类型，此可能性较低。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.0s
├─ 并发证据采集: 59.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 59.3s (Evidence 49.0s, RCA 10.2s)
└─ 汇总总结: 15.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
