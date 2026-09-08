## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | ConfigMap `workload-code` 配置缺失或环境变量未设置，导致 `server.py` 运行时触发 `config_missing_exit` 逻辑并返回 HTTP 500 后以 exit code 78 主动退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Reason: CrashLoopBackOff` | 确认容器持续退出并进入重启退避状态 |
| 2 | K8s State | K8s Event | `message: "ConfigMap workload-code configuration missing or environment variable not set..."` | 直接记录异常现象与初步推断原因 |
| 3 | K8s State | K8s Event | `exit_code: 78` | 提供具体的进程退出码，指向主动退出行为 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason{reason="Error"} = 1` | 佐证容器最后一次终止原因为 Error |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} = 1` | 佐证容器当前处于等待重启状态 |
| 6 | Logging | Elasticsearch | `pattern: {event: "http_request", level: "error", message: "CONFIG_MISSING", http_status: 500}` | 应用层日志记录到具体的配置缺失错误，导致 HTTP 500 响应 |
| 7 | Tracing | Tempo | `trace_id: 435ddc9f7062bac6badf52854f8152a6`, `aiops.observed_mode: "config_missing_exit"`, `http.response.status_code: 500` | 通过 Trace 上下文直接关联应用模式为 `config_missing_exit`，确认配置缺失触发 500 状态码 |

**证据说明：**
1. K8s 层显示的 `CrashLoopBackOff` 状态与 Metric 层的 `CrashLoopBackOff` 和 `Error` 状态完全一致，确认了容器无法稳定运行的现象。
2. 日志中的 `CONFIG_MISSING` 模式与 Tracing 中 `aiops.observed_mode: "config_missing_exit"` 相互印证，确立了“配置缺失”是导致应用行为的核心机制。
3. 容器以 exit code 78 退出且伴随 HTTP 500 响应，是应用层发现配置缺失后主动终止并返回错误码的直接证据。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `workload-code` 配置缺失或环境变量未设置 → `server.py` 触发 `config_missing_exit` 逻辑 → 返回 HTTP 500 并以 exit code 78 主动退出 → 容器 CrashLoopBackOff
```

### 根因结论

已确认的根因是 **ConfigMap `workload-code` 配置缺失或环境变量未设置**。

这一原因导致应用在运行时触发 `config_missing_exit` 逻辑，具体表现为：
1. 应用检测到配置缺失后，返回 HTTP 500 错误（证据 #6 日志模式、证据 #7 Trace 状态码）。
2. 应用随后以 exit code 78 主动终止进程（证据 #3 退出码）。
3. 这种非预期的主动退出导致 Kubernetes 将其标记为 Error，并因频繁重启进入 CrashLoopBackOff 状态（证据 #1 K8s 状态、证据 #4 Metric 状态）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.6s
├─ 并发证据采集: 98.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 98.7s (Evidence 90.7s, RCA 7.9s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-config-error, pod-oomkilled
