## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason=CrashLoopBackOff`; `container.last_terminated_reason=Error`; `container.last_exit_code=78` | 确认容器因应用错误退出且 K8s 正在执行重启退避 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `first=15.0, last=21.0` (观测窗口持续上升); `kube_pod_container_status_last_terminated_reason(reason="Error")=1` | 证实重启频率高且终止原因固定为 Error，排除了瞬时抖动 |
| 3 | Logging | elasticsearch | 模式 `CONFIG_MISSING` (HTTP 500, path=/work) 重复 8 次; `trace_ids` 包含 `5ef67866f348c5aa93ff865f603c2cdc` | 提供具体崩溃根因，确认应用因配置缺失主动报错退出 |
| 4 | Tracing | deepflow+tempo | Flow `GET /work` 响应 500 (Src: 172.16.104.9, Dst: 172.16.104.15); Span 属性 `aiops.observed_mode=config_missing_exit`, 关联 Trace `5ef67866f348c5aa93ff865f603c2cdc` | 与日志 Trace ID 一致，闭环验证应用逻辑处理了 HTTP 500 后进程退出 |

日志中的错误模式（`CONFIG_MISSING` 导致 HTTP 500）直接解释了 K8s 观测到的 `Exit Code 78`（通常为非零应用退出码），且 Metric 显示重启计数持续攀升，证实崩溃为应用内部逻辑异常而非资源限制导致。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺少关键配置项 → 处理 /work 请求时抛出 CONFIG_MISSING (HTTP 500) → 应用以退出码 78 终止 → CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因为**应用程序代码逻辑缺陷或环境配置缺失**。
应用在处理请求时因检测到缺失配置而主动抛出 `CONFIG_MISSING` 错误并返回 HTTP 500，随后进程以退出码 78 终止 [[3, 4]]。Kubernetes 检测到该非零退出码并触发重启，由于重启频繁（21 次）且原因一致，状态演进为 `CrashLoopBackOff` [[1, 2]]。该结论由日志、Tracing 和 K8s 状态事实完全支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.7s
├─ 并发证据采集: 63.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 63.8s (Evidence 55.1s, RCA 8.5s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
