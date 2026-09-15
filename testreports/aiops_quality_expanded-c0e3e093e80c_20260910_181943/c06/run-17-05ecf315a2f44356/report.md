## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用代码在处理 /work 接口时发生运行时错误（Runtime Error），导致进程主动终止（Exit Code 2）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 4m29s (x157 over 39m) kubelet Back-off restarting failed container app in pod workload-7679bcf76-n5vp8` | 确认可见现象：因重启失败导致的 CrashLoopBackOff 状态，持续异常 39 分钟 |
| 2 | K8s State | Kubernetes | `exit_code: 2` | 核心证据：容器以退出码 2 终止，指示应用进程主动报错退出，而非 OOM 等系统级原因 |
| 3 | Logging | Elasticsearch | `http_status: 500`, `path: /work`, `event: http_request`, `message: runtime process exiting` (2 次记录) | 机制证据：在 `/work` 接口路径上观察到 500 错误，并伴随“进程退出”的日志信息 |
| 4 | Tracing | Deepflow (L7 Flow) | `GET /work` -> `response_code: 500`, `duration_us: 3883 ~ 4623` | 网络与性能佐证：网络层面观察到对 `/work` 的 500 响应，响应极快，符合应用内部异常拦截特征 |
| 5 | Tracing | Tempo (Application Span) | `trace_id: 650e7da7b4dc0e95768ebc5720a2260e`, `http.route: /work`, `aiops.observed_mode: runtime_exit` | 链路上下文关联：Trace ID 证实了该请求触发了应用侧的 `runtime_exit` 观察模式，与 Log 日志时间窗口吻合 |

证据间高度一致：日志记录了 `/work` 路径上的 500 错误及进程退出信息，Trace 数据（Flow 与 Span）在网络层和应用层双向验证了该请求返回 500 且触发了运行时退出逻辑。Kubernetes 的 `exit_code: 2` 直接映射了进程终止行为，进而导致 Pod 处于 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 路径触发未捕获的运行时异常 → 进程处理异常（返回 HTTP 500）并主动终止 (exit code 2) → K8s 检测到进程非正常退出并触发 CrashLoopBackOff 重启策略 → 应用表现为反复重启且对外报错
```

### 根因结论

**已确认的根因**：
应用代码在 `/work` 接口处理过程中发生运行时错误（Runtime Error），导致进程主动异常退出（Exit Code 2），进而触发 Kubernetes 的重启保护机制进入 CrashLoopBackOff 状态。

**支撑证据**：
- **Exit Code 2** (`fact-250c574c735a`)：容器进程以错误码 2 终止，属于典型的应用层主动崩溃。
- **日志与追踪** (`fact-569fa85cf878`, `fact-12f288de85c9`)：日志显示请求 `/work` 时发生 500 错误及 `runtime process exiting`；Trace 记录确认该请求模式下的 `runtime_exit` 行为。
- **Pod 状态** (`fact-adf70875d980`)：直接呈现因反复退出引发的 `CrashLoopBackOff` 现象。

**待澄清的未知项**：
导致 Runtime Error 的具体业务逻辑原因（代码堆栈/Stack Trace）及确定性触发条件目前缺失。现有日志仅记录了“进程退出”及 HTTP 500，未包含详细堆栈信息。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.0s
├─ 并发证据采集: 81.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 81.9s (Evidence 73.2s, RCA 8.5s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
