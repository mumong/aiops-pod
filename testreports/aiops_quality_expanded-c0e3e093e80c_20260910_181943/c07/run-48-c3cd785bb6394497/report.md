## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 应用启动或初始化时缺少必要配置（CONFIG_MISSING），导致进程以非零退出码终止，进而引发 kubelet 无限重启及 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 9m10s (x332 over 83m) kubelet Back-off restarting failed container app in pod workload-dff5cbc6b-sjvxl` | 证明应用经历长周期的无限重启，处于 CrashLoopBackOff 状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `exit_code: 78` | 确认容器以非零退出码 78 终止，是重启的直接原因 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi`, `resource_request.memory: 24Mi` | 排除内存超限（OOM）作为故障根因的可能性 |
| 4 | Logging | Elasticsearch | `pattern: {event: http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work}`, `occurrence_count: 8`, `time_range: 21:34 - 21:50` | 日志明确记录应用层配置缺失错误，且连续发生，解释异常终止的业务逻辑原因 |
| 5 | Tracing | Deepflow | `HTTP GET /work 响应 code=500`, `src_ip: 172.16.104.8 -> dst_ip: 172.16.104.63`, `occurrence_count: 9` | 从流量层面印证 500 错误，将应用异常与特定网络请求关联 |
| 6 | Tracing | Tempo | `span: "GET /work"`, `attributes: aiops.observed_mode=config_missing_exit, http.response.status_code=500`, `trace_id: 35171f43b5d98aebd6019469374b813c` | 提供 Trace ID 关联，明确观测到 `config_missing_exit` 模式，与日志证据一致 |

**证据关联与印证：**
日志中捕获的 `CONFIG_MISSING` 错误（证据 4）解释了容器以退出码 78 异常终止（证据 2）的业务原因；Tempo 追踪中的 `config_missing_exit` 观测模式（证据 6）与日志和流量异常（证据 5）在逻辑上完全闭环，共同指向配置问题导致应用无法启动。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动/初始化时缺少必要配置 (事实 4, 6) → 应用抛出异常并返回 HTTP 500 (事实 4, 5, 6) → 进程以非零退出码 78 终止 (事实 2) → kubelet 触发无限重启并进入 CrashLoopBackOff (事实 1, 3)
```

### 根因结论

已确认根因为：**应用启动或初始化阶段缺失必要的运行配置（`CONFIG_MISSING`）**。

这一缺失导致应用在请求处理时抛出错误并退出（退出码 78），从而触发了 Kubernetes 的重启策略，表现为持续的 `CrashLoopBackOff`。该结论由应用日志中的 `CONFIG_MISSING` 报错（事实 4）、追踪数据中的 `config_missing_exit` 模式（事实 6）以及 Kubernetes 的异常终止状态（事实 2）共同证实。内存资源配置（事实 3）排除了资源耗尽的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.7s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 45.3s (Evidence 38.8s, RCA 6.4s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
