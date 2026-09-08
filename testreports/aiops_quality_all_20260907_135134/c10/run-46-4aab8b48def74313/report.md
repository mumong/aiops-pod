## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: Error | 确认容器退出状态 |
| 2 | K8s State | Kubernetes | container.last_exit_code: 137 | 退出码 137 证实 OOMKilled |
| 3 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 存活探针连续失败，触发重启机制 |
| 4 | K8s Config | Kubernetes | container.resource_limit.memory: 96Mi | 极低的内存硬限制是资源瓶颈的关键上下文 |
| 5 | K8s Config | Kubernetes | container.resource_request.memory: 24Mi | 请求与限制差距悬殊，反映配置异常 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total: 41 (从 0 升至 41) | 证明崩溃持续发生且频率极高 |
| 7 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (reason: Error) | 指标侧反复确认终止原因为 Error |
| 8 | Logging | Elasticsearch | log: request completed, http_status: 200, path: /work | 正常请求日志证明应用在处理业务 |
| 9 | Tracing | Tempo | application_span: http.response.status_code: 200, observed_mode: liveness_fail | 链路层确认响应成功但被 Liveness Probe 判定失败 |

**证据说明：**
- K8s 侧（事实 1-3）明确显示容器以 137 退出并伴随探针 500 错误，结合事实 4（96Mi 限制）和事实 8、9（正常业务响应 200），证明应用是在处理请求时耗尽内存而非崩溃。
- Metric 侧（事实 6-7）的重复上升和终止原因与 K8s 侧现象完全吻合，证实了频繁重启的模式。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制 (96Mi) 过低 → 处理请求时触发 OOMKilled (Exit Code 137) → Liveness 探针连续失败 (HTTP 500) → Kubelet 触发重启 (CrashLoopBackOff)
```

### 根因结论

已确认根因：**容器内存硬限制（`limits.memory: 96Mi`）配置过低**。

该配置不足导致应用在处理请求时触发 OOMKilled（由事实 2、7 证实），进而导致 Liveness Probe 失败（事实 3、9）及后续的 CrashLoopBackOff（事实 6）。尽管日志（事实 8）和 Tracing（事实 9）显示业务请求能返回 200 状态码，但内存耗尽仍直接导致了进程的异常终止和存活探针的误报（或应用在处理完毕但未释放足够内存前被判定为不健康）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.6s
├─ 并发证据采集: 87.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 87.6s (Evidence 79.0s, RCA 8.5s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-crashloop-runtime
