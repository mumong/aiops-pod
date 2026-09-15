## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，应用因配置缺失导致启动失败并崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-dff5cbc6b-sjvxl` 状态 `Running`，但容器 `app` 处于 `CrashLoopBackOff`，重启次数 5 次，Exit Code 78 | 确认应用启动即崩溃，且退出码异常 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (105s x10 over 4m11s) | 确认容器启动失败触发了 K8s 的重启退避机制 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: CrashLoopBackOff); `kube_pod_container_status_last_terminated_reason` = 1 (reason: Error) | 从监控指标层面佐证了崩溃循环和 Error 终止状态 |
| 4 | Logging | Elasticsearch | 错误模式：`CONFIG_MISSING` (HTTP 500, path: /work)；时间范围 2026-09-10T20:30:17Z 至 2026-09-10T20:33:45Z，共出现 8 次 | 核心错误日志，直接定位到应用因配置缺失而崩溃的业务原因 |
| 5 | Tracing | Tempo | Trace ID `a358165e4c5df7b2882c057473693f30`：应用属性 `aiops.observed_mode: config_missing_exit`，响应状态 500 | 追踪链路确认了 `config_missing_exit` 的具体模式，与日志事实一致 |

**证据印证说明：**
- **K8s 状态与日志印证**：K8s 报告 Exit Code 78（通常非标准 0/1/137），结合日志中明确的 `CONFIG_MISSING` 和 `config_missing_exit` 模式，说明应用是主动因缺少依赖配置而强制退出。
- **多源时间一致性**：日志和追踪均发生在 20:30 至 20:33 时间窗口内，与 K8s BackOff 事件发生时间（105s over 4m11s）吻合，证明崩溃发生在同一轮启动周期中。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动依赖特定配置项但未找到 (CONFIG_MISSING) → 应用以退出码 78 主动退出 → Kubernetes 检测到容器非正常退出并重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用因启动时缺失必需配置（返回 `CONFIG_MISSING` 错误及退出码 78）而崩溃**。

- **支撑证据**：
  1. 日志与追踪明确展示了业务层级的错误模式：`CONFIG_MISSING` 和 `aiops.observed_mode: config_missing_exit` (证据 #4, #5)。
  2. Kubernetes 状态证实了崩溃结果：容器反复启动失败，Exit Code 为 78，最终触发 K8s 的 `CrashLoopBackOff` (证据 #1, #2, #3)。
- **缺失信息**：
  由于无法获取上一次崩溃瞬间的完整业务堆栈日志（采集限制），且未见 ConfigMap 内容，具体缺失的配置项 Key 名及 `ConfigMap 'workload-code'` 的确切内容仍为未知 (unknowns)，但这不影响判定“配置缺失导致启动失败”这一根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.9s
├─ 并发证据采集: 69.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 69.6s (Evidence 60.4s, RCA 9.0s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
