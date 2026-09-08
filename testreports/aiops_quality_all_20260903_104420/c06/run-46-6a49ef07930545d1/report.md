## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod `workload-7679bcf76-w9s9c` 处于 `CrashLoopBackOff` 状态，容器 `app` 反复以退出码 `2` 崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 3m56s (x497 over 113m) kubelet Back-off restarting failed container app` | 证实容器已长时间高频重启，处于持续不可用状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 2` | 确认进程非 OOM（非 137）终止，而是内部错误退出 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 提供资源约束背景，结合日志确认非内存溢出 |
| 4 | Logging | Elasticsearch | `event: http_request`, `level: error`, `message: runtime process exiting`, `http_status: 500`, `path: /work` | 核心证据：应用在处理特定请求时崩溃，并伴随 HTTP 500 错误 |
| 5 | Logging | Elasticsearch | `numeric_fields.allocated_mib`: min/max/first/last 均为 `0.0` | 证实崩溃前无内存分配增长，排除应用内存泄漏或突发占用导致 OOM 的可能 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 26 | 量化重启次数，与 K8s 观测到的 `x497` 事件记录相互印证 |
| 7 | Tracing | Deepflow | Flow: `GET /work`, `response_code: 500`, `occurrence_count: 4` | 网络层面观测到对应错误请求，与日志中的 `http_status: 500` 对齐 |
| 8 | Tracing | Tempo | Span: `GET /work`, `trace_id: 44d82bffd1cff720d7ba7f132cc91772`, `http.response.status_code: 200` | 提供成功请求对照，证明应用并非整体不可用，仅在特定场景下失败 |

**证据互证说明：**
K8s 状态与日志高度一致：`Container` 状态显示 `CrashLoopBackOff` 且退出码为 2，对应日志中出现的 `runtime process exiting` 及 `http_status: 500`。日志中 `allocated_mib` 均为 0 且容器内存上限为 96Mi，排除了因超出内存限制（OOMKilled）导致的强制终止，进一步锁定了“应用代码逻辑/运行时环境导致的不正常退出”。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码或配置缺陷导致运行时异常 → 处理 /work 请求时抛出未捕获错误 (exit_code: 2) → 容器进程非正常终止 (CrashLoopBackOff) → Pod 状态 CrashLoopBackOff，业务报错 500
```

### 根因结论

已确认的根因是 **应用代码或配置缺陷导致的运行时异常**。

*   **证据支撑**：
    1.  容器每次崩溃前的日志均明确显示 `runtime process exiting` 且伴随 HTTP 500 错误（见证据 #4, #7）。
    2.  容器退出码为 2，非标准的 OOMKilled 退出码（137）。
    3.  内存监控数据显示 `allocated_mib` 始终为 0，且内存限制（96Mi）与崩溃无直接关联，排除了资源不足引发的崩溃（见证据 #3, #5）。
*   **未确认细节**：虽然确定是应用内部运行时错误，但缺乏具体的异常堆栈（Traceback），无法定位具体的代码分支或底层异常类型（如 `KeyError` 等）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 21.9s
├─ 并发证据采集: 71.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 71.5s (Evidence 59.7s, RCA 11.6s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
