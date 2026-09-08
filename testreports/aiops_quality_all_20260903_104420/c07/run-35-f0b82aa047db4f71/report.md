## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-kmfxx_aiops-case-07` | 确认 Pod 正处于由 CrashLoopBackOff 触发的重启退避阶段 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `exit_code: 78` | 确认容器以 Error 退出，且退出码 78 符合应用内部逻辑终止特征 |
| 3 | K8s Config | Kubernetes | `resource_request.cpu: 20m`, `resource_limit.cpu: 200m`, `resource_limit.memory: 96Mi` | 提供资源环境上下文，确认非资源配额引发的 OOMKilled |
| 4 | Logging | Elasticsearch | `pattern: CONFIG_MISSING, http_status: 500, path: /work` (发生 8 次, `68f3f90b...` 等 Trace ID 关联) | 提供直接根因证据：应用因配置缺失抛出 500 错误 |
| 5 | Tracing | Tempo | `attributes: {http.response.status_code: 500, aiops.observed_mode: config_missing_exit}, trace_id: 65684c8c...` | 确认日志中 `CONFIG_MISSING` 的具体 HTTP 请求链路和观测模式 |
| 6 | Tracing | Deepflow | `request_resource: /work, response_code: 500, src_ip: 172.16.104.9, dst_ip: 172.16.104.15` (发生 10 次, 跨 7 个 Trace ID) | 提供 L7 网络层面的独立观测，证实目标 Pod 对 `/work` 路由持续返回 500 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 16` (采样 1 个, 趋势不可评估) | 量化确认当前容器已重启 16 次 |

证据分析：
1. **现象一致性**：Metric 中记录的 16 次重启与 K8s Event 中 `BackOff` 现象高度吻合，证实该 Pod 存在高频重启的持续性故障。
2. **根因锁定**：Logging 维度中聚合的 `CONFIG_MISSING` 模式直接指向根因，且该模式与 Tracing 维度中 `aiops.observed_mode: config_missing_exit` 及 `status_code: 500` 在时间窗口（14:31 至 14:57）和业务路由（`/work`）上完全重叠，相互印证。
3. **故障定界**：K8s State 确认退出码 78 且资源限制正常（非内存溢出），排除了基础设施资源问题，将故障严格定界为应用层逻辑异常。

## 🎯 根因分析 · g1

### 因果链

```text
Application configuration missing → HTTP request /work returns 500 error → Container process crashes (exit_code: 78) → CrashLoopBackOff (restarted 16 times)
```

### 根因结论

已确认根因为 **应用配置缺失 (Application Config Missing)**。

该根因由日志（Logging）中的 `CONFIG_MISSING` 错误模式及追踪（Tracing）中的 `config_missing_exit` 观测模式直接证实，说明应用程序在启动或处理 `/work` 请求时因关键配置缺失而主动抛出 500 错误并退出。K8s 事件与指标数据（Metric）中的连续重启行为（Restart 16 次）是该异常退出导致的直接后果。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 17.8s
├─ 并发证据采集: 91.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 91.0s (Evidence 82.7s, RCA 8.1s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
