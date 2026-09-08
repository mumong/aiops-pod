## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | Elasticsearch | 模式 `http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work`，出现 8 次，关联 trace_ids 含 `424df37443b75963abf97aed7762eb01` 等 | 核心证据：证明应用存在且正在响应请求，但检测到关键配置缺失并返回 500 错误 |
| 2 | Tracing | DeepFlow | HTTP GET /work 返回 500，9 次等效 Flow，Trace IDs 与日志一致（如 `424df37443b75963abf97aed7762eb01`） | 辅助证据：确认异常行为发生在 L7 应用层，非网络或底层基础设施问题 |
| 3 | Tracing | Tempo | Span `GET /work`，Attribute `aiops.observed_mode: config_missing_exit`，Trace ID `da9999ae734835080b2f252e105e1ce7` | 辅助证据：直接标记应用因配置缺失而终止的模式，与日志和 Flow 相互印证 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 当前值为 5 | 症状证据：证实容器经历多次重启，与 CrashLoopBackOff 现象一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 为 `Error`，`kube_pod_container_status_waiting_reason` 为 `CrashLoopBackOff` | 症状证据：确认最近一次退出原因非 OOM 或被杀，且当前处于等待重试状态 |

**证据关联说明：**
日志中的 500 错误和 Tracing 中的 `config_missing_exit` 标记表明应用因自身逻辑（检查配置失败）主动退出；Metric 的 `restarts_total=5` 和 `CrashLoopBackOff` 状态证实了该异常退出导致容器反复重启。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行环境配置缺失 → 应用启动后检查配置并返回 500 CONFIG_MISSING → 容器进程异常退出 → CrashLoopBackOff
```

### 根因结论

已确认根因为**应用启动时检测到配置缺失（CONFIG_MISSING）**。应用启动后尝试执行工作路径 `/work` 相关的逻辑，发现必要配置缺失，随即记录错误日志并返回 HTTP 500 状态码，随后进程主动异常退出。Kubernetes 重启策略导致容器在退出后进入重启计数，最终因频繁重启进入 `CrashLoopBackOff` 状态。证据链通过 Elasticsearch 的日志模式（Fact #1）、DeepFlow/Tempo 的流量和 Span 数据（Fact #2, #3）以及 Prometheus 的重启指标（Fact #4, #5）得到充分印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 35.3s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 30.6s (Evidence 22.8s, RCA 7.6s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
