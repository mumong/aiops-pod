## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 4m30s (x202 over 49m) kubelet Back-off restarting failed container app` | 证实 Pod 经历长时间的失败重启周期，直接关联 `CrashLoopBackOff` 现象 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error` | 提供明确的异常状态分类，确认为应用层崩溃而非调度或资源不足 |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 78` | 提供终止退出码，表明应用主动以非标准码退出，需结合应用逻辑分析 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (labels: `reason: Error`) = `1` | 从监控指标侧面印证容器终止原因归类为 Error |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (container: app) = `14` | 提供具体的重启次数，量化故障的持续性 |
| 6 | Logging | Elasticsearch | 日志模式 `event: http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work` (重复 8 次) | **核心证据**：直接暴露应用启动/自检阶段的错误原因为“配置缺失” |
| 7 | Tracing | Tempo | Span: `GET /work`, `status_code: 500`, `aiops.observed_mode: config_missing_exit`, trace_id: `65684c8c074b2b13bde640e742613caa` | 提供完整的调用链路，将 HTTP 请求、错误代码与 `config_missing_exit` 诊断模式绑定 |
| 8 | Tracing | Deepflow | L7 Flow: 9 次 `GET /work` 请求至 `172.16.104.15` 均返回 500 (含 trace_id `65684c8c074b2b13bde640e742613caa`) | 证明外部或内部对 `/work` 端点的探测/请求持续失败，触发健康检查失败导致重启 |

**证据关联与印证：**
Kubernetes 事件与指标（#1, #2, #4）共同锁定了 `CrashLoopBackOff` 状态；日志中的 `CONFIG_MISSING` 错误模式（#6）精确解释了退出码 78（#3）背后的业务逻辑原因；Trace 链路（#7, #8）则通过具体的 trace_id 将网络请求失败（500）与日志中的错误模式在同一个请求上下文中关联起来，证实了应用因配置缺失导致启动检查失败，进而触发了 K8s 的重启机制。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 应用启动或自检时返回 HTTP 500 (Exit Code 78) → 容器终止触发重启策略 → Pod 陷入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：** 应用启动依赖的配置缺失（`CONFIG_MISSING`）。

**依据：**
- 日志层面：连续 8 次记录显示 `http_request` 失败，错误原因为 `CONFIG_MISSING`，并伴随 `http_status: 500`（证据 #6）。
- 追踪层面：Trace 数据显示请求 `/work` 返回 500，且应用内部观测模式明确标记为 `config_missing_exit`，该行为与日志高度一致（证据 #7, #8）。
- 状态层面：上述业务层错误导致容器以退出码 78 终止，Kubernetes 健康检查失败后执行重启，最终表现为 `CrashLoopBackOff`（证据 #1, #2, #3）。

**未确认事项：**
- 具体的缺失配置文件名称或路径（输入事实中 `unknowns` 明确列出此信息缺失）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 26.6s
├─ 并发证据采集: 106.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 106.9s (Evidence 99.9s, RCA 6.8s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
