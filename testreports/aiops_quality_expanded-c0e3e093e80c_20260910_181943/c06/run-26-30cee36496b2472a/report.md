## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，kubelet 持续 Back-off 重启容器 app |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (fact-034738a7f04c) | 确认容器进程异常终止状态 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (fact-5523153f6714) | 解释 CrashLoopBackOff 现象的直接原因 |
| 3 | K8s Config | Kubernetes | `resource_request.memory: 24Mi`, `container.resource_limit.memory: 96Mi` (fact-87c13499ef33, fact-d0b08b84911b) | 排除 OOMKilled，确认资源限制宽松 |
| 4 | Logging | Elasticsearch | `pattern: "runtime process exiting"`, `http_status: 500` (fact-252eebff744f) | 确认应用层发生致命错误导致主动退出 |
| 5 | Tracing | Tempo | `http.response.status_code: 500`, `aiops.observed_mode: runtime_exit` (fact-13fcc0fac632) | 关联日志，确认请求处理阶段崩溃 |
| 6 | Tracing | Deepflow | `response_code: 500` (fact-26d949a3c83b) | 网络流证实应用返回 500 错误 |

**证据印证：**
1. 容器状态 (`fact-034738a7f04c`) 显示 `Error`，结合日志 (`fact-252eebff744f`) 中的 `"runtime process exiting"`，证实进程因应用层错误而非系统级资源耗尽而终止。
2. 追踪数据 (`fact-13fcc0fac632`) 与日志 (`fact-252eebff744f`) 在同一个 `/work` 请求路径上互相印证，均指向 HTTP 500 及 runtime 退出模式，锁定了故障发生的触发时机。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 GET /work 请求时抛出致命异常 → 容器进程记录 runtime process exiting 并返回 HTTP 500 → 进程以 exit code 2 异常终止 → Kubernetes 重启策略触发 BackOff 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：** 应用进程在处理 `/work` 请求时发生未捕获的运行时错误（Runtime Error），导致进程以 `exit code 2` 主动退出。

**证据支撑：**
*   **K8s 层面**：容器状态记录 `terminated_reason: Error` (`fact-034738a7f04c`)，事件流显示 `Back-off restarting failed container` (`fact-5523153f6714`)，重启计数已达 15 次 (`fact-5b2198a7b2c7`)，确认了应用不断重启的现象。
*   **日志层面**：明确捕捉到 `"runtime process exiting"` 模式 (`fact-252eebff744f`)，排除了 OOM（内存限制宽松，且日志中无 OOMKilled 提示）或健康检查超时的可能。
*   **追踪层面**：Span 数据显示在 `/work` 端点处理期间出现 `http.response.status_code: 500` 且 `observed_mode: runtime_exit` (`fact-13fcc0fac632`)，直接关联了网络请求与应用崩溃。

**不确定性：**
*   日志中未完整打印具体的 Python 异常堆栈（如 `ValueError`、`KeyError` 等） (`unknowns`)，因此无法确定具体的代码逻辑错误类型，仅能确认是应用内部运行时的致命异常。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 16.2s
├─ 并发证据采集: 111.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 111.7s (Evidence 97.4s, RCA 14.1s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
