## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，启动后收到外部请求 GET /work 时返回 500 错误并主动退出进程（ExitCode=2） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running`, `container.status: CrashLoopBackOff`, `container.exit_code: 2` (fact-1415b64b3419, fact-a547dd8cc7e6, fact-e9caf7054e13) | 确认 Pod 实例存活但容器进程已异常终止，处于重启振荡状态。 |
| 2 | K8s Event | Kubernetes | `BackOff` 警告，触发频率 `x134 over 33m` (fact-fe919ac5a382) | 证实进程反复崩溃已被 Kubelet 观察并实施指数退避重启策略。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 标签 `CrashLoopBackOff` 值为 1 (fact-604258a2f0fb) | 监控系统侧交叉印证容器当前正等待重启。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 标签 `Error` 值为 1 (fact-5d7743e97077) | 确认上一轮容器终止原因为应用层 Error 而非资源超限 (OOMKilled)。 |
| 5 | Logging | Elasticsearch | HTTP 500 错误日志模式：`message="runtime process exiting"`, `http_status=500`, `path="/work"` (fact_ids: fact-93d4535d3918, fact-252eebff744f, fact-81fad94edaf5) | 直接暴露异常发生时的应用层状态码及“进程退出”的关键动作。 |
| 6 | Tracing | DeepFlow | L7 Flow: `GET /work` 返回 `response_code: 500`, `duration: 4196-4847us`, `trace_ids: 6b940021b18df312738422d71af62239` (fact_ids: fact-26d949a3c83b, fact-874f2165c2b0) | 在流量层锁定导致 500 响应的具体请求路径及耗时。 |
| 7 | Tracing | Tempo | Span: `GET /work` 属性 `aiops.observed_mode: runtime_exit` (fact-31b0e51382df, trace_id: 6b940021b18df312738422d71af62239) | 追踪数据确认异常是由运行时退出触发，与日志记录的模式吻合。 |

**证据链说明：**
Kubernetes 状态与指标共同确认了 CrashLoopBackOff 现象及 Error 退出码（证据 1-4）。日志中的 `runtime process exiting` 500 错误（证据 5）与 Trace 中特定请求 `6b940021b18df312738422d71af62239` 的 500 响应及 `runtime_exit` 模式（证据 6-7）通过 Trace ID 实现了闭环关联，证实崩溃是由单次请求处理失败直接触发的。

## 🎯 根因分析 · g1

### 因果链

```text
外部请求 GET /work (Trace ID: 6b940021b18df312738422d71af62239) → 服务端执行逻辑发生内部异常 → 进程记录 "runtime process exiting" 并调用退出(ExitCode=2) → 触发 Kubelet 重启机制导致 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
应用服务在处理 `/work` 路径时发生了未捕获的内部运行时错误（Internal Error）。

**证据支撑：**
*   流量追踪（证据 6-7）显示针对 `/work` 的请求返回了 HTTP 500，且 Span 属性明确标记为 `runtime_exit`。
*   应用日志（证据 5）在同一时间段记录了针对 `/work` 的 500 错误及“runtime process exiting”消息，直接对应了 ExitCode=2 的退出行为。
*   K8s 状态（证据 1）确认了该退出行为导致了容器被终止并进入重启循环。

**局限性：**
具体引发该内部异常的 Python 堆栈跟踪（Stack Trace）或异常类型因日志截断不可见，但足以确认为应用代码逻辑缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 18.3s
├─ 并发证据采集: 69.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 69.5s (Evidence 55.7s, RCA 13.6s)
└─ 汇总总结: 15.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
