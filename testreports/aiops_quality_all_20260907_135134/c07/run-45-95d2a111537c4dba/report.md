## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason: Error` | 确认容器非正常退出，且未返回 OOMKilled 等常见系统级原因 |
| 2 | K8s State | Kubernetes | `exit_code: 78` | 提供程序级退出码，通常指示应用逻辑错误或配置缺失 |
| 3 | K8s Event | Kubernetes | `Warning BackOff 7m44s (x377 over 92m) kubelet Back-off restarting failed container app` | 确认已进入严重重启循环，且持续较长时间（92分钟） |
| 4 | Logging | Elasticsearch | `http_request, level: error, message: CONFIG_MISSING, path: /work, service: aiops-lab-workload` (发生 8 次) | 直接证明应用逻辑在启动或处理请求时遇到配置缺失并报错 |
| 5 | Tracing | Tempo | `GET /work, status_code: 500, attributes.aiobserved_mode: config_missing_exit` | 关联日志模式，证实应用在处理 /work 请求时主动返回 500 并进入 `config_missing_exit` 模式 |
| 6 | Metric | Prometheus | `restart_count: 22` (单样本，无趋势) | 量化 Pod 的崩溃重启频率，佐证 K8s Event 中的频繁重启现象 |

日志与链路证据高度一致：日志显示应用检测到 `CONFIG_MISSING` 错误，Tracing 确认该应用在处理 `/work` 请求时主动返回 500 状态码并设定 `config_missing_exit` 模式，导致应用进程以 `exitCode=78` 终止。K8s 状态与事件证实这种进程级的异常退出触发了 Kubernetes 的 CrashLoopBackOff 机制。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动时检测到关键配置缺失（CONFIG_MISSING） → 应用进程抛出错误并返回 HTTP 500，随后以 exitCode=78 终止 → Kubernetes 检测到容器异常退出并触发 CrashLoopBackOff 状态 → Pod 持续处于重启循环中，无法就绪
```

### 根因结论

**已确认根因**：Pod 内 `workload-dff5cbc6b-fkzvn` 的 `app` 容器因应用层检测到**关键配置缺失**（`CONFIG_MISSING`）而导致启动或请求处理失败。具体表现为应用在检测到该错误后，主动以 `exitCode=78` 退出进程，Kubernetes 进而触发重启策略（CrashLoopBackOff）[证据 1, 2, 3, 4, 5, 6]。

**未知项**：具体缺失的配置变量名称、ConfigMap 字段，以及该配置缺失的根本技术原因（例如配置未正确挂载、Secret 权限不足或代码逻辑误判）目前证据不足，无法进一步确诊。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 23.6s
├─ 并发证据采集: 61.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 61.1s (Evidence 52.3s, RCA 8.6s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
