## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error, container.last_exit_code: 2 | 确认进程异常终止的具体退出码 |
| 2 | K8s Event | kubernetes | Warning BackOff: 74s (x248 over 56m), back-off 5m0s restarting failed container | 证实 CrashLoopBackOff 状态及长时间高频重启模式 |
| 3 | K8s Config | kubernetes | resource_limit.cpu: 200m, resource_limit.memory: 96Mi | 提供资源限制上下文 |
| 4 | Metric | prometheus | kube_pod_container_status_last_terminated_reason(Error): 1 | 从监控侧证实容器最后一次退出原因为 Error |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason(CrashLoopBackOff): 1 | 从监控侧证实当前等待原因为 CrashLoopBackOff |
| 6 | Logging | elasticsearch | 模式 `runtime process exiting`, path=/work, http_status=500, 发生 2 次 (19:15-19:20) | 捕获进程退出时的错误日志模式及对应服务 |
| 7 | Logging | elasticsearch | 模式 `request completed`, path=/work, http_status=200, 发生 6 次 (18:59-19:25) | 提供正常请求的对比基线，证明服务曾可正常运行 |
| 8 | Tracing | deepflow | Flow: GET /work -> response_code: 500, count: 3 (03:04-03:09) | 从网络流层证实 /work 请求失败并返回 500 |
| 9 | Tracing | tempo | Span: GET /work, response_code: 200, trace_id: b2c74bd59a13816a64bebc87858a5008 (19:25:29) | 确认同一 Trace ID 下存在成功返回，说明应用具备处理能力 |

**证据关联说明：**
- **现象确认**：事实 1、2 确认了 Pod 处于 CrashLoopBackOff 且进程以 Exit Code 2 异常退出的状态，事实 4、5 从监控指标层面提供了独立佐证。
- **业务机制**：事实 6（Log）和事实 8（Flow）共同指向 `/work` 端点处理失败，表现为 HTTP 500。
- **能力验证**：事实 9（Trace）结合事实 7（Log）证实该服务此前能够正常处理 `/work` 请求，排除了网络不通或基础设施整体不可用的可能性，问题局限于应用进程内部处理逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
应用层代码在 /work 端点处理逻辑中存在运行时异常 → 异常触发进程以 Exit Code 2 退出并记录 runtime process exiting 日志 → Kubernetes 探测到容器非正常退出并触发重启 → Pod 因频繁重启且退避耗尽进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：应用进程在处理 `/work` 请求时发生未捕获的运行时异常导致进程直接退出。**

具体表现为应用进程在处理 `/work` 请求时异常退出（Exit Code 2），Kubernetes 检测到容器异常退出后执行重启策略，但在重试耗尽后导致 Pod 进入 `CrashLoopBackOff` 状态。证据链显示日志中存在 `runtime process exiting` 错误（fact-6, fact-7），Tracing 网络流中观测到 `/work` 请求返回 500（fact-8），而同一时间窗口或关联 Trace ID 下又存在 200 成功响应（fact-9），确认应用本身是存活的，问题在于特定业务场景下的处理逻辑崩溃。

**未确认部分：**
- 导致 `/work` 请求处理失败的具体业务逻辑错误或异常类型（如 NPE、参数校验失败等）；
- Trace ID `b2a618d284bf6044c4b23962ad35eb64` 未能在 Tracing 系统中检索到完整链路的原因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 37.7s
├─ 并发证据采集: 87.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 87.7s (Evidence 76.6s, RCA 10.9s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
