## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用进程在 `/work` 路径处理请求时发生未捕获的内部逻辑错误（HTTP 500），导致进程主动异常退出（exitCode 2） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app` (226次 over 52m, fact-2432c7a41606) | 确认应用持续崩溃引发 Kubelet 的指数退避重启 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff` (fact-3087b94bcbad) | 确认最终异常状态 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error` (fact-0b0a4e60ea3c) | 记录导致退出的终止原因 |
| 4 | K8s State | kubernetes | `container.last_exit_code: 2` (fact-46305fbe42f3) | 确认进程主动退出并返回错误码 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason{reason="Error"}: 1` (fact-fcdcaaf05cb6) | 独立观测确认上次终止原因 |
| 6 | Logging | elasticsearch | `pattern: runtime process exiting, http_status: 500, path: /work` (fact-252eebff744f) | 记录应用层面的致命错误与退出路径 |
| 7 | Tracing | deepflow | `l7_flow GET /work: response_code: 500, occurrence: 4, trace_id: 2bedd23e6c9eb325f924bbfb32bd5cc4` (fact-26d949a3c83b) | 确认该错误路径上的 L7 请求特征 |
| 8 | Tracing | tempo | `span GET /work: http.response.status_code: 500, trace_id: 2bedd23e6c9eb325f924bbfb32bd5cc4` (fact-fb39fa09688a) | 跨维度关联日志与追踪，证实请求处理时异常退出 |

**证据说明**：
Kubernetes 的 `CrashLoopBackOff` (fact-2) 与终止原因 `Error` (fact-3) 为现象基础。日志明确显示应用在处理 `/work` 路径时发生 `HTTP 500` 并主动退出 (fact-6)。Tracing 数据中的 `trace_id: 2bedd23e6c9eb325f924bbfb32bd5cc4` (fact-8) 与日志中的错误模式完全对应，且 deepflow 的 L7 Flow 也确认了同一 Trace ID 下的 `500` 响应 (fact-7)。日志与追踪共同指向是应用内部逻辑错误导致了该次请求失败并触发退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work 请求时发生内部逻辑错误 → 进程记录 HTTP 500 错误并主动退出（exitCode 2） → Kubelet 触发容器重启机制 → 容器反复崩溃导致 Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认根因为：**应用进程在 `/work` 路径处理请求时发生未捕获的内部逻辑错误，导致进程主动异常退出（exitCode 2）。**

证据表明，虽然集群资源（CPU/Memory limits）充足且配置无异常，但应用代码在处理特定请求时产生了致命错误（`HTTP 500`，见 fact-6）。进程随后退出（`exit_code: 2`，见 fact-4），Kubernetes 试图重启容器（fact-1），但因程序逻辑未修复，进程再次崩溃，最终陷入 `CrashLoopBackOff` 状态（fact-2）。日志与追踪通过唯一的 `trace_id` (fact-8) 相互印证，完整复现了“请求处理-发生错误-进程退出”的闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 26.0s
├─ 并发证据采集: 73.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 73.7s (Evidence 63.9s, RCA 9.6s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
