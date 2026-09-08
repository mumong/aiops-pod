## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error, `container.waiting_reason`: CrashLoopBackOff, `container.last_exit_code`: 78, `container.restart_count`: 13 | 确认应用进程异常退出且 kubelet 处于重启退避循环中 |
| 2 | K8s Event | kubernetes | `BackOff` Warning: "Back-off restarting failed container app... (x179 over 43m)" | 佐证重启循环已持续近一小时，系统正在抑制频繁重启 |
| 3 | Logging | elasticsearch | 模式 `CONFIG_MISSING`, `http_status: 500`, `path: /work`, `first: 2026-09-03T14:16:05` | 直接显示应用因配置缺失报错并返回 500 |
| 4 | Tracing | deepflow/tempo | `http.request.method: GET`, `http.response.status_code: 500`, `aiops.observed_mode: config_missing_exit`, `span.trace_id: 9e99fbd922a97ca99308339b3fbad526` | 追踪调用链确认应用内部逻辑因缺少配置而主动终止，状态码与日志一致 |

证据印证说明：
Kubernetes 的 `CrashLoopBackOff` 状态和退出码 78 表明容器异常终止；日志中的 `CONFIG_MISSING` 模式与追踪中的 `aiops.observed_mode: config_missing_exit` 相互印证，确认了导致应用退出的直接机制是缺少关键配置。

## 🎯 根因分析 · g1

### 因果链

```text
Application configuration missing (CONFIG_MISSING) → 应用进程报错退出 (exit code 78) → Kubelet 触发重启退避 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因：应用程序因缺失关键配置（日志与追踪均记录 `CONFIG_MISSING` 错误且观察模式为 `config_missing_exit`）导致进程以退出码 78 退出。该异常触发了 kubelet 的持续重启行为，最终表现为 Pod 状态 `CrashLoopBackOff`。

目前缺乏关于“具体缺失哪个环境变量或配置文件”的确切事实（unknowns），但现有 Kubernetes 状态、日志错误原文与追踪指标已充分支撑“配置缺失导致应用崩溃重启”这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.9s
├─ 并发证据采集: 63.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 63.9s (Evidence 56.1s, RCA 7.6s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
