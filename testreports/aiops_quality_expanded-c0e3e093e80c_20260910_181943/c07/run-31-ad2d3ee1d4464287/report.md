## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Container 'app' repeatedly fails to start due to 'CONFIG_MISSING' error, causing exit code 78 and CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，最后终止原因 `Error`，退出码 `78`，重启次数 `15` | 确认应用层崩溃及循环重启现象 |
| 2 | K8s Event | Kubernetes | Warning `BackOff`: `back-off 5m0s restarting failed container=app` (61s x242 over 55m) | 证实重启行为持续且被 K8s 控制 |
| 3 | Logging | Elasticsearch | 错误日志模式 `CONFIG_MISSING` (HTTP 500)，关联 `trace_id` `55c07e8b117659114ccbae9c7f582db0` 等，时间窗 `2026-09-10T20:57:33Z` 至 `21:23:49Z` | 提供应用层启动/运行失败的具体业务错误 |
| 4 | Tracing | Tempo | Span `GET /work`，状态码 `500`，属性 `aiops.observed_mode=config_missing_exit`，`trace_id` `55c07e8b117659114ccbae9c7f582db0` | 交叉印证日志中的 `trace_id`，确认错误源于特定 HTTP 请求处理 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (CrashLoopBackOff), `last_terminated_reason=1` (Error), `restart_total=15` | 指标数据与 K8s 事件和状态完全一致 |

**证据互证说明：**
日志中观察到的 `CONFIG_MISSING` 业务错误（事实 #3）与 Trace 中记录的 `aiops.observed_mode=config_missing_exit`（事实 #4）及相同的 `trace_id` 形成了完整的链路闭环，证明容器内应用因配置缺失主动返回错误并终止（退出码 78）。这种应用层逻辑错误直接触发了 Kubernetes 的重启机制，进而导致 `CrashLoopBackOff` 状态（事实 #1、#2、#5）。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 应用启动失败/处理请求报错退出 (Exit Code 78) → Kubernetes 重启容器 (CrashLoopBackOff) → Pod 持续不可用
```

### 根因结论

已确认根因为容器 `app` 内的应用因检测到 `CONFIG_MISSING` 错误（HTTP 500）而主动终止进程（Exit Code 78）。日志证据（#3）和链路追踪证据（#4）一致证实了这一应用层行为，该行为直接导致了 Kubernetes 层面的 `CrashLoopBackOff` 异常（#1, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.3s
├─ 并发证据采集: 54.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 54.9s (Evidence 46.9s, RCA 7.8s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
