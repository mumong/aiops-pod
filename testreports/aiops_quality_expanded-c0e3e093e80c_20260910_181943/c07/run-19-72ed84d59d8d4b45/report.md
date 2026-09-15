## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Back-off restarting failed container app in pod workload-dff5cbc6b-sjvxl (BackOff, x155 over 35m) | 确认 Pod 处于高频重启状态 |
| 2 | K8s State | Kubernetes | exit_code: 78, reason: Error | 确认容器异常终止的具体退出码及状态 |
| 3 | Logging | Elasticsearch | CONFIG_MISSING (HTTP 500, path=/work, service=aiops-lab-workload, 8 occurrences) | 直接定位异常原因为配置缺失 |
| 4 | Tracing | Tempo | Span GET /work (status_code: 500, aiops.observed_mode: config_missing_exit) | 关联日志与 Trace，确认应用内部处理机制 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total: 11 (sample_count: 1) | 辅助确认 Pod 已被重启 11 次 |
| 6 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (reason: Error) | 辅助确认最近一次终止原因为 Error |

**证据分析：**
1. **Kubernetes** 的 `BackOff` 事件和 `exit_code: 78` 证实了异常终止现象及重启循环的触发。
2. **Logging** 和 **Tracing** 提供了直接的业务层归因：应用在处理 `/work` 请求时，因 `CONFIG_MISSING` 记录 500 错误，并以 `config_missing_exit` 模式退出。
3. **Metric** 证实了重启次数和错误状态，与 K8s 状态及 Log/Trace 的异常记录一致。

## 🎯 根因分析 · g1

### 因果链
```text
应用缺少必需配置(CONFIG_MISSING) → HTTP 请求处理异常 → 进程以 exitCode=78 退出 → Pod CrashLoopBackOff 重启
```

### 根因结论
已确认的根因是：容器内应用在处理 HTTP 请求时因**缺少必需配置**（`CONFIG_MISSING`），导致应用以退出码 **78** 异常终止，进而触发 Kubernetes 的 CrashLoopBackOff 重启循环。
*   **依据**：Log 明确输出 `CONFIG_MISSING` 错误 (证据 #3)，Trace 确认 `aiops.observed_mode: config_missing_exit` (证据 #4)，K8s 状态记录 `exit_code: 78` (证据 #2)。
*   **未知因素**：目前证据仅证明“缺少配置”，但无法确定配置缺失的具体原因（是 ConfigMap 内容缺失、键名不匹配还是挂载路径错误），也缺乏应用侧期望读取的具体配置文件或环境变量名称的证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.4s
├─ 并发证据采集: 70.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 70.1s (Evidence 61.9s, RCA 8.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
