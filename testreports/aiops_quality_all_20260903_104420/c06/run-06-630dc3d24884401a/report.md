## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 应用工作进程在处理 /work 接口时发生内部错误（返回 HTTP 500），导致 Python 进程异常退出（exitCode=2）并进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 最后一次终止原因为 `Error`（fact-4d46a2acaea8） | 确认进程崩溃退出，指向运行时内部错误 |
| 2 | K8s State | Kubernetes | 容器 `app` 退出码为 2（fact-b3a778f3c14c） | 对应 Python 进程异常终止（SIGABRT 或 RuntimeError）的典型退出码 |
| 3 | K8s Event | Kubernetes | `BackOff` 事件，持续 11 分钟内触发 43 次（fact-5a457a611600） | 证实 Pod 处于 CrashLoopBackOff 循环重启状态 |
| 4 | Metric | Prometheus | 容器重启总数 6 次（fact-e00010ad82e4），状态为 CrashLoopBackOff（fact-2e0f86fa4f8c） | 独立于 K8s 指标确认重启频率和当前异常状态 |
| 5 | Logging | Elasticsearch | 4 次 HTTP 请求报错 `500`，日志模式为 `runtime process exiting`，路径 `/work`（fact-778e3ba9615a 等） | 直接揭示崩溃前触发内部错误的业务请求路径 |
| 6 | Tracing | Tempo | Trace `0adf17e5b0a9aca15ff758c1e1232579` 显示 `GET /work` 返回 500 且模式为 `runtime_exit`（fact-1fa56ecc0bcc） | 关联日志中相同 trace_id，证明 HTTP 请求直接触发了运行时退出机制 |

**证据关联说明：**
日志与追踪系统互相印证：Tempo 中的 `runtime_exit` 模式与日志中的 `runtime process exiting` 一致，且 Trace ID 匹配，证明应用在处理 `/work` 接口时发生内部错误导致 Python 进程崩溃。Kubernetes 的 `Error` 终止状态和退出码 2 提供了容器层面的直接证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部错误（触发 /work 接口） → 返回 HTTP 500 → Python 进程异常退出（Exit Code 2） → CrashLoopBackOff
```

### 根因结论

**已确认根因：** 应用在处理 `/work` 接口时发生内部错误（返回 HTTP 500），导致 Python 工作进程异常退出。

*   **直接证据引用：** 
    *   日志显示在 `2026-09-03 11:54:41` 至 `12:00:57` 期间，多次发生 `runtime process exiting` 伴随 `HTTP 500`（证据 #5）。
    *   追踪链路 `0adf17e5b0a9aca15ff758c1e1232579` 证实 `GET /work` 请求触发 `runtime_exit` 模式（证据 #6）。
    *   Kubernetes 层面记录 `Error` 终止原因和 `Exit Code 2`（证据 #1, #2），并伴随频繁的 `BackOff` 重启事件（证据 #3）。

*   **机制分析：** 应用代码在处理 `/work` 路径时抛出未捕获异常或显式调用退出，导致 Python 进程终止。Kubernetes 检测到容器非正常退出后，触发重启策略，由于连续失败进入 `CrashLoopBackOff` 状态（证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 16.0s
├─ 并发证据采集: 107.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 107.7s (Evidence 100.1s, RCA 7.4s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
