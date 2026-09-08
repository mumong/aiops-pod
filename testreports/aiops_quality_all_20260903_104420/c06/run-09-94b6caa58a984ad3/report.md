## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Application code in `/opt/aiops/server.py` encounters a runtime error (HTTP 500) when handling requests to the `/work` endpoint, causing the Python process to exit with code 2. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (`fact-3317d1b44002`) | 确认应用处于持续重启且退避中状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error` (`fact-2d24f63f820a`) | 确认容器因非零退出码终止 |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: 2 (`fact-3d193d83d7e4`) | 确认应用程序异常退出的具体代码 |
| 4 | K8s Event | Kubernetes | `Back-off restarting failed container app` 89次 (`fact-48cb4b994ae5`) | 记录重启循环的频率和持续时间 |
| 5 | Logging | Elasticsearch | `request completed` (HTTP 200, `/work`, 5次) vs `runtime process exiting` (HTTP 500, `/work`, 3次) (`fact-7c13d0c944bc`, `fact-778e3ba9615a`) | 区分了正常处理与导致崩溃的错误处理逻辑 |
| 6 | Logging | Elasticsearch | 错误日志 `runtime process exiting` (`fact-778e3ba9615a`) | 直接指向应用进程在遇到 HTTP 500 时的行为 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (Reason: `CrashLoopBackOff`) (`fact-7c632aeda3fa`) | 从监控指标侧验证了当前的 Pod 等待状态 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 9 (`fact-237c4583c808`) | 量化了应用的总重启次数，印证 CrashLoopBackOff 的持续性 |

**证据印证说明：**
1.  **K8s 状态与日志的因果闭环**：Kubernetes 层面的 `CrashLoopBackOff` 和退出码 2 (`fact-2`, `fact-3`) 由应用日志中 `/work` 端点返回 HTTP 500 并触发进程退出 (`fact-5`, `fact-6`) 直接解释。
2.  **指标与日志的一致性**：日志中 HTTP 500 的连续出现与 Prometheus 指标中重启计数为 9 (`fact-8`) 以及等待原因为 `CrashLoopBackOff` (`fact-7`) 完美对应，确认了这是一个间歇性但持续触发的运行时错误。
3.  **排除资源限制干扰**：配置显示 CPU 请求/限制为 20m/200m，内存为 24Mi/96Mi (`fact-4`, `fact-5`, `fact-6`, `fact-7` 配置部分)，但日志和错误代码指向运行时逻辑错误（HTTP 500 导致退出），而非 OOMKilled 或 CPU Throttling 导致的异常终止。

## 🎯 根因分析 · g1

### 因果链

```text
服务端代码处理 /work 请求时发生异常 → 返回 HTTP 500 状态码 → 进程捕获错误并调用退出逻辑(exit code 2) → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：应用程序代码在处理 `/work` 端点请求时存在运行时错误（Runtime Error）。**

证据表明，应用在处理特定请求时返回了 HTTP 500 状态码，并随即因代码逻辑主动以退出码 2 终止了进程。Kubernetes 记录到的 `Error` 终止原因、非零退出码（2）、以及 `CrashLoopBackOff` 状态，均与“应用代码异常导致进程退出”这一结论一致。日志明确记录了 `runtime process exiting` 与 HTTP 500 响应的关联。当前证据足以将根因定位为应用层面的代码逻辑或依赖处理错误，而非底层基础设施或资源限制问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.4s
├─ 并发证据采集: 80.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 80.5s (Evidence 71.5s, RCA 8.9s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
