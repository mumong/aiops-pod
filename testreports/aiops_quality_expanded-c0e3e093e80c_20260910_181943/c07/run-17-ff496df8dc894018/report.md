## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 应用容器 (app) 因关键配置缺失(CONFIG_MISSING)触发主动退出(Exit Code 78)，导致 Kubernetes 触发 CrashLoopBackOff 重启机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container=app, exit_code=78 | 容器异常退出代码 |
| 2 | K8s State | Kubernetes | container=app, reason=CrashLoopBackOff | 重启循环状态确认 |
| 3 | K8s Event | Kubernetes | Back-off restarting failed container app | 异常状态的事件日志 |
| 4 | Logging | Elasticsearch | pattern: CONFIG_MISSING (occurrences: 8, time_range: 2026-09-10T20:33:45Z ~ 2026-09-10T20:57:35Z) | 应用侧日志确认根因 |
| 5 | Metric | Prometheus | kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}=1 | 指标状态佐证 |

**证据关联：** 日志事实 (#4) 明确指出应用内部发生 `CONFIG_MISSING` 错误，结合 K8s 状态事实 (#1) 中的 Exit Code 78，证实应用因自身逻辑主动退出。该退出触发了 K8s 的重启机制，导致 K8s Event (#3) 和 Metric (#5) 均反映为 `CrashLoopBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
关键配置缺失(CONFIG_MISSING) → 应用主动退出(Exit Code 78) → K8s CrashLoopBackOff → 容器无法就绪
```

### 根因结论

**已确认的根因：** 应用容器内的关键配置缺失（`CONFIG_MISSING`）。
根据日志证据（#4），应用服务在 `2026-09-10T20:33:45Z` 至 `2026-09-10T20:57:35Z` 期间多次发生 `CONFIG_MISSING` 错误并返回 HTTP 500。应用进程在检测到该错误后，主动以退出码 78（通常表示配置或环境错误）终止（#1），导致 Kubernetes 的容器重启回退机制被触发，使 Pod 长期处于 `CrashLoopBackOff` 状态（#2, #3, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.5s
├─ 并发证据采集: 75.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 75.7s (Evidence 69.2s, RCA 6.3s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
