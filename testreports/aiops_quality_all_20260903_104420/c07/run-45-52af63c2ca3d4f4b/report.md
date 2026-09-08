## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用因关键配置缺失（CONFIG_MISSING）在启动及处理请求时抛出错误并退出（Exit Code 78），导致容器进入 CrashLoopBackOff 重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `app` 容器 `last_terminated_reason`: Error | 确认容器异常终止的直接原因 |
| 2 | K8s Event | kubernetes | `Warning BackOff` 22s (x357 over 80m) kubelet Back-off restarting failed container app | 描述因持续退出导致的指数退避重启现象 |
| 3 | K8s State | kubernetes | `app` 容器 `last_exit_code`: 78 | 确认进程以特定非零码终止，关联应用逻辑错误 |
| 4 | Logging | elasticsearch | 模式 `CONFIG_MISSING` 出现 8 次 (trace_ids: `8c7b...`, `ce81...` 等)，时间窗口 `14:52:38` 至 `15:18:40`，返回 HTTP 500 | 捕获应用层因配置缺失返回 500 错误的业务根因 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}` 当前值为 1 | 实时反映 Pod 处于等待重启状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值为 19 | 量化重启频次 |
| 7 | Tracing | deepflow | HTTP GET `/work` 返回 500 错误共 11 次，对应 trace_ids: `6ded...`, `e669...` 等 | 关联日志确认应用对特定请求抛出错误 |
| 8 | Tracing | tempo | Span `GET /work` (trace_id: `5ef67866f348c5aa93ff865f603c2cdc`), `aiops.observed_mode`: `config_missing_exit` | 通过 Trace ID 关联日志与日志中的 trace_id，锁定单次调用失败为配置缺失导致 |

**证据说明：**
1. **Kubernetes 层面与 Metric**：证实了容器因 `Error` 退出并处于 `CrashLoopBackOff` 状态的客观事实，重启次数（Metric: 19, K8s: 20）相互印证。
2. **Logging 与 Tracing 关联**：日志捕获了多次 `CONFIG_MISSING` 错误，Tracing 捕获了等价的 500 响应。
3. **根因锁定**：Trace ID `5ef678...` 在 Logging 和 Tracing 中均存在，日志明确标记 `CONFIG_MISSING`，Trace Span 中记录 `observed_mode: config_missing_exit`，直接指向配置缺失是导致 Exit Code 78 的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
运行时配置项缺失 → 应用抛出 CONFIG_MISSING 并返回 HTTP 500 (Exit Code 78) → 进程终止 → Kubelet 触发 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用因依赖的特定配置项（关键配置缺失，具体名称未知）导致启动或处理请求失败，以退出码 78 异常终止，进而引发 CrashLoopBackOff 重启循环。
- **证据**：日志聚合 `CONFIG_MISSING`（证据 #4）与 Trace Span `config_missing_exit`（证据 #8）一致；K8s 状态显示退出码为 78（证据 #3）及 BackOff 事件（证据 #2）。
- **缺失事实**：尚未确定缺失的具体配置项名称（如 ConfigMap key 或环境变量名）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 27.5s
├─ 并发证据采集: 75.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 75.9s (Evidence 66.2s, RCA 9.5s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
