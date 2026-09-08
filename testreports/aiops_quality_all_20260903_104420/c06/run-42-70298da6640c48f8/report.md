## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff，容器 app 崩溃退出并反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container last terminated reason: "Error" | 确认容器异常终止状态 (fact-7e8c6e869d8d) |
| 2 | K8s State | Kubernetes | container last exit code: 2 (fact-5fc26966d8fa) | 确认进程存在非正常退出 (fact-5fc26966d8fa) |
| 3 | K8s Event | Kubernetes | Warning BackOff 100s (x474 over 106m), restarting failed container | 确认 K8s 正在按策略反复重启失败容器 (fact-fdb7e161965d) |
| 4 | Logging | Elasticsearch | repeated_log_pattern: event="http_request", level="error", message="runtime process exiting", http_status=500, path="/work", trace_ids=["005d9f0d3504d3557ff340b304fd9609", "83ac4ea940a445d1f077cc1d9a9e0e8b", "22fa8919bffd2b6bfa494eebb80ffd68", "a3ec8d4abdf31fbc6a0a80dfb6d9cad3", "3e8d7fa2e67393d6eb6fecf68126720d", "83b3251ce25b45b31926d73555d66d8a"], time_range: 2026-09-03T13:14:18 - 13:40:34 | 日志明确记录进程在执行 /work 时发生异常退出，提供关键时间窗口 (fact-6efb8c4ef276) |
| 5 | Tracing | Deepflow | l7_flow aggregation: GET /work, response_code=500, trace_ids=["005d9f0d3504d3557ff340b304fd9609", "3e8d7fa2e67393d6eb6fecf68126720d", "83b3251ce25b45b31926d73555d66d8a"], src_ip=172.16.104.21, dst_ip=172.16.104.17 | L7 流量记录证实 /work 接口返回 500 状态码，与日志 trace_id 一致，确认是服务内部处理导致崩溃 (fact-7cc922125280) |
| 6 | K8s Config | Kubernetes | resource_request.memory: 24Mi, resource_limit.memory: 96Mi | 排除因内存超限 (OOMKilled) 导致退出的可能性 (fact-1f76d10a18f1) |

证据说明：
1. 日志与追踪高度关联：Deepflow 中的 L7 Flow 记录了特定 trace_ids（如 `005d9f...`）在 `/work` 端点上返回了 500 状态码，而这些 trace_ids 与日志中 `runtime process exiting` 的记录完全重合。
2. 排除资源限制：Pod 的内存 request 为 24Mi，limit 为 96Mi，且 K8s 异常原因为 `Error` 而非 `OOMKilled`，配合 `exit_code: 2` 可判断是应用层面的逻辑崩溃，而非基础设施限制。
3. 崩溃循环证据：K8s 事件 `BackOff` 显示 `x474 over 106m`，说明自 13:14 左右第一次出现错误后，Pod 已处于长时间的重启崩溃循环中。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码或运行时环境缺陷 → 在执行 /work 接口任务时进程异常退出 (exit_code 2) → Kubelet 捕获 Error 状态并尝试重启 → Pod 进入 CrashLoopBackOff，用户请求返回 500
```

### 根因结论

已确认的根因为 **应用进程在执行 `/work` 业务逻辑时发生致命异常（runtime process exiting）导致 exit code 2**。

这一根因由以下事实共同印证：
1. **直接证据**：Kubernetes 状态明确记录 `last_terminated_reason: Error` 和 `last_exit_code: 2`（证据 #1, #2）。
2. **触发路径**：Elasticsearch 日志和 Deepflow 追踪均记录了 `GET /work` 操作伴随 `error` 级别日志 `runtime process exiting` 以及 `response_code=500`（证据 #4, #5）。两者通过相同的 `trace_ids` 完美关联，确认是特定请求触发了崩溃。
3. **结果表现**：K8s 事件 `BackOff` 证实了这种崩溃是反复发生的，导致 Pod 无法稳定运行（证据 #3）。

**缺失的决定性事实**：日志和追踪仅提供了高层的 `runtime process exiting` 和 HTTP 500 状态，**未包含具体的 Python 堆栈跟踪、异常类型（如 ValueError, ConnectionError 等）或错误详情**。因此，无法确定具体的代码缺陷（如空指针、依赖缺失或配置错误），这需要通过查看 Pod 退出前的完整 stderr/stdout 日志或应用代码来进一步定位。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 32.8s
├─ 并发证据采集: 64.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 64.4s (Evidence 54.2s, RCA 10.0s)
└─ 汇总总结: 18.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
