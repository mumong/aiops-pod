## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c处于CrashLoopBackOff状态，无法就绪 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `CrashLoopBackOff`; `container.last_terminated_reason: Error`; `restart_count: 10`; `exit_code: 2` | 确认 Pod 应用容器因错误退出并持续重启 |
| 2 | K8s Config | K8s | `resource_request.memory: 24Mi`; `resource_limit.memory: 96Mi` | 提供应用资源限制上下文，非 0 值表明资源非极度紧缺 |
| 3 | Logging | ES | `pattern: "runtime process exiting"`; `error log path=/work http_status=500`; `allocated_mib min/max: 0.0`; 发生 4 次 | 显示应用在 `/work` 路径请求处理期间发生内部错误导致进程退出，且退出前内存使用为 0 |
| 4 | Tracing | Deepflow/Tempo | `GET /work` 成功响应 200 的 Flow/SPAN 9 次；`GET /work` 响应 500 的 Flow/SPAN 2 次，关联 trace_id `1177dab7b64a1e5b24692ffc4375aaf6` | 确认应用可运行，但在特定请求路径上返回错误状态码，与日志中 500 错误一致 |

**证据交叉印证：**
*   **日志与跟踪一致**：Deepflow 中 2 个返回 HTTP 500 的流量均关联到 trace_id，与 Elasticsearch 日志中记录 HTTP 500 状态码及 `runtime process exiting` 模式完全吻合（如 `fact-1177dab7b64a1e5b24692ffc4375aaf6` 关联），证明 HTTP 错误导致进程异常终止。
*   **K8s 与 Metrics 一致**：Kubernetes 报告 `CrashLoopBackOff`、终止原因 `Error` 和重启次数 10 次；Prometheus 指标 `kube_pod_container_status_restarts_total: 10`、`reason: Error`、`waiting_reason: CrashLoopBackOff` 均精确对应。
*   **资源使用情况**：日志中的 `allocated_mib` 为 0，且资源请求/限制均非 0 值，排除 OOM 或极端资源限制导致的直接崩溃，支持“内部未捕获异常或应用逻辑错误”作为直接原因的推断。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑异常或运行时错误（未确认具体代码） → 进程调用exit(2)退出并记录error日志 → K8s检测到容器非0退出码(Exit Code 2) → Pod进入CrashLoopBackOff状态，无法就绪
```

### 根因结论

**已确认根因：** 容器内应用 `app` 在处理 `/work` 路径的 HTTP 请求时，因内部错误（如未捕获异常或显式调用 `exit(2)`）导致进程异常退出。

**证据支撑：**
1.  **K8s 状态明确**：Pod `workload-7679bcf76-w9s9c` 处于 `CrashLoopBackOff` 状态，容器终止原因为 `Error`，重启 10 次，退出码为 `2`（事实编号 1）。
2.  **日志与跟踪直接关联**：Elasticsearch 日志显示 4 次 `runtime process exiting` 错误，均关联 HTTP 请求 `path=/work` 且 `http_status=500`（事实编号 3）。Deepflow 流量日志显示 2 次 `GET /work` 返回 `response_code=500`，且 Trace ID `1177dab7b64a1e5b24692ffc4375aaf6` 同时在日志和跟踪中出现，形成闭环（事实编号 4）。
3.  **排除资源问题**：应用内存使用量为 0，且非极低资源限制，使得 OOM 等外部资源驱逐可能性极低，指向应用内部逻辑或代码问题。

**不足与未知：**
*   缺乏具体的应用代码堆栈（Traceback），无法确定引发 `exit(2)` 的确切代码行或业务逻辑。
*   Exit Code 2 的具体应用语义定义未知（通常表示通用错误，但可能因应用而异）。
*   尽管有证据表明是内部错误，但具体导致“未捕获异常”的代码路径尚未明确（符合正式 RCA 中的 `unknowns`）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 30.9s
├─ 并发证据采集: 78.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 78.8s (Evidence 69.8s, RCA 8.8s)
└─ 汇总总结: 15.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
