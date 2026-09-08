## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用容器启动后无法检测到必要的配置，导致执行 `/work` 逻辑时抛出 `CONFIG_MISSING` 错误并退出，退出码 78 触发 kubelet 的 CrashLoopBackOff 重启机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-kmfxx` (3m, x134 over 32m) | 确认应用容器 `app` 已进入 `CrashLoopBackOff` 循环 |
| 2 | K8s State | kubernetes | `last_terminated_reason`: `Error`, `last_exit_code`: `78`, `restart_count`: `11` | 提供退出码 78 这一导致重启的直接原因 |
| 3 | Logging | elasticsearch | 错误模式：`CONFIG_MISSING` 在 `GET /work` 时抛出，日志时间窗 2026-09-03 14:05 至 14:31 | 揭示导致退出的应用逻辑根因为“配置缺失” |
| 4 | Tracing (Flow) | deepflow | L7 Flow `GET /work` 返回 HTTP 500，`172.16.104.9` -> `172.16.104.15`，关联 TraceID：`afd42312ee...`, `9e99fbd9...` | 外部观测到服务不可用且返回 500，与日志错误码一致 |
| 5 | Tracing (Span) | tempo | Span `GET /work` (TraceID: `9e99fbd9...`)，属性 `aiops.observed_mode: config_missing_exit` | 链路内部确认退出是由于配置缺失模式触发 |

证据通过多个维度相互印证：Kubernetes 报告的 78 退出码和 CrashLoopBackOff 状态由 Elasticsearch 日志中的 `CONFIG_MISSING` 错误解释；Tracing 的 Flow 确认了请求层面的 500 响应，而 Tempo Span 进一步将具体的应用行为锁定为 `config_missing_exit` 模式。时间线（14:05-14:31）与 K8s 事件的持续时间（32m）吻合，排除了时序错乱的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺少必要配置 (CONFIG_MISSING) → /work 接口处理失败 (HTTP 500) → 退出码 78 → kubelet CrashLoopBackOff 重启
```

### 根因结论

已确认根因为**应用启动后检测到必要的配置缺失**，导致其在执行 `/work` 逻辑时抛出 `CONFIG_MISSING` 错误并返回 HTTP 500。该逻辑路径以退出码 78 终止，进而触发 kubelet 的 CrashLoopBackOff 重启机制。

此结论由以下独立事实支撑：
- **K8s 状态 (Fact 1, 2)**：证实了容器因 `Error` 状态以 `78` 退出码反复重启。
- **Logging (Fact 3)**：明确指出失败原因是 `CONFIG_MISSING` 且发生在 `/work` 路径上。
- **Tracing (Fact 4, 5)**：从外部流量 (Flow 500) 到内部执行模式 (Span `config_missing_exit`) 均闭环验证了配置缺失导致的处理失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.4s
├─ 并发证据采集: 60.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 60.0s (Evidence 54.3s, RCA 5.5s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
