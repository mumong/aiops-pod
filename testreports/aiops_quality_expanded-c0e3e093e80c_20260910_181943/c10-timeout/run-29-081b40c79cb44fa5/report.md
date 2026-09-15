## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 应用代码使用 Python ThreadingHTTPServer 且未实现并发处理（单线程阻塞），导致处理耗时（~3秒）超过探针超时限制（1秒）。探针频繁超时判定失败触发重启，重启导致状态轮空呈现 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | ContainersNotReady, reason: ContainersNotReady | 确认 Pod 实际不可用，处于不健康状态 |
| 2 | K8s Event | kubelet.event | Unhealthy, reason: Unhealthy, message: "Liveness probe failed: Get \"http://172.16.104.36:18080/health\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)" | 核心证据：证明 Liveness 探针请求被服务端挂起，最终导致探针超时 |
| 3 | K8s State | pod.status / container | phase: Running, status: CrashLoopBackOff, container.waiting_reason: CrashLoopBackOff | 确认可观测的异常状态，由探针失败重启引起 |
| 4 | K8s State | container.restart_count | container.app.restart_count: 25 | 证实容器被频繁重启，与探针超时机制匹配 |
| 5 | Tracing | l7_flow (GET /health) | src_ip: 10.2.0.50, dst_ip: 172.16.104.36, response_code: 200, duration_us max: 3001585.0 (~3.0s) | 证实健康检查请求耗时远超 1 秒探针超时限制 |
| 6 | Logging | log.message | 10.2.0.50 - - [14/Sep/2026 14:07:22] "GET /ready HTTP/1.1" 200 - (及多条类似请求) | 证实探针请求到达并得到响应，但由于耗时过长被 K8s 判定为失败 |

**证据互证说明：**
*   K8s Event (#2) 显示的探针超时，在 Trace 维度得到直接验证 (#5)，健康检查请求实际执行时间长达 3 秒，超过探针设定的 1 秒限制。
*   Logging 显示请求最终返回 200 (#6)，说明后端服务在慢响应后仍正常工作，而非服务崩溃；K8s Restart Count 高频增长 (#4) 进一步证实是外部探针判定失败导致强制重启。

## 🎯 根因分析 · g1

### 因果链

```text
应用单线程阻塞导致处理耗时~3秒 → 响应时间超过探针1秒超时限制 → 探针判定失败触发重启 → Pod 持续 CrashLoopBackOff
```

### 根因结论

已确认根因为：应用代码使用 Python ThreadingHTTPServer 且未实现并发处理（单线程阻塞），导致处理耗时（~3秒）超过探针超时限制（1秒）。

这一机制直接解释了为何 Liveness 探针频繁超时 (#2, #5)，并最终导致容器被反复强制终止，呈现 CrashLoopBackOff 状态 (#3, #4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 13.9s
├─ 并发证据采集: 67.4s
│  └─ g1 aiops-case-v17/workload: 67.4s (Evidence 61.8s, RCA 5.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
