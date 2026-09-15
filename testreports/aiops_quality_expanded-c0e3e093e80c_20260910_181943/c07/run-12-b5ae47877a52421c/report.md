## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态（重启9次），容器 app 连续以 Exit Code 78 错误退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Back-off restarting failed container app` (x88 over 24m) | 确认 Pod 处于频繁重启循环状态 |
| 2 | K8s State | K8s | `waiting_reason: CrashLoopBackOff` | 确认当前 Pod 状态及 K8s 对异常的处理机制 |
| 3 | K8s State | K8s | `container.last_terminated_reason: Error`, `exit_code: 78` | 确认容器异常退出的直接原因和退出码 |
| 4 | K8s State | K8s | `restart_count: 9` | 提供异常持续发生的量化证据 |
| 5 | Logging | elasticsearch | `CONFIG_MISSING` (pattern: http_request, 500, path: /work, 8 occurrences) | 直接暴露应用层异常原因：配置项缺失导致请求处理失败 |
| 6 | Tracing | tempo | `span: GET /work`, `status_code: 500`, `aiops.observed_mode: config_missing_exit` | 追踪应用层处理流程，确认是应用逻辑主动退出而非被 K8s 或 OOM 杀死 |

**证据分析：**
K8s 状态事实（事实 1、2、3、4）证实了 Pod 处于 CrashLoopBackOff 循环，且容器以非零退出码 78 终止。日志事实（事实 5）明确指出了导致异常的直接业务原因是 `CONFIG_MISSING`。追踪事实（事实 6）与日志相互印证，显示应用在处理 `/work` 请求时主动返回 500 错误并进入 `config_missing_exit` 模式。所有证据链闭合，指向应用逻辑异常导致的主动退出，排除了资源耗尽（OOM）或外部网络故障的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (ENV: FAILURE_MODE=config_missing_exit) → 应用逻辑主动返回 HTTP 500 (message: CONFIG_MISSING) → 应用进程以 Exit Code 78 终止 → Kubernetes 检测到非零退出码并触发 CrashLoopBackOff
```

### 根因结论

已确认的根因是应用因配置项缺失（日志明确输出 `CONFIG_MISSING`）在处理 HTTP 请求时主动抛出错误并退出。

1.  **应用异常触发：** 应用程序在处理 `GET /work` 请求时，因检测到关键配置项缺失，主动返回 `HTTP 500` 错误，并记录 `CONFIG_MISSING` 日志（参考证据 #5, #6）。
2.  **进程退出：** 应用逻辑在抛出错误后，主动以 `Exit Code 78` 终止进程（参考证据 #3）。
3.  **K8s 重启循环：** Kubernetes 监控到容器非正常退出，根据重启策略不断尝试重启容器，但由于配置问题未解决，容器反复启动后再次失败，导致 Pod 状态变为 `CrashLoopBackOff`（参考证据 #1, #2, #4）。

**缺失信息：**
日志和追踪仅显示了 `CONFIG_MISSING` 这一通用错误，未能提供具体缺失的配置项名称，这是当前唯一未确认的细节（参考诊断报告中的 unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 22.2s
├─ 并发证据采集: 137.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 137.9s (Evidence 127.4s, RCA 10.2s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
