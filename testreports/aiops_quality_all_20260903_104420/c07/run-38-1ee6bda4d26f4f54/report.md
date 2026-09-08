## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | container: app, last_terminated_reason: Error | 证实容器异常退出 |
| 2 | K8s Event | K8s | message: Back-off restarting failed container app | 证实异常导致的重启循环 |
| 3 | K8s State | K8s | container: app, last_exit_code: 78 | 确认进程退出状态码 |
| 4 | K8s State | K8s | container: app, restart_count: 17 | 证实频繁重启的持续性 |
| 5 | Metric | Prometheus | kube_pod_container_status_waiting_reason, container: app, reason: CrashLoopBackOff, value: 1 | 独立确认当前 Pod 状态 |
| 6 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason, container: app, reason: Error, value: 1 | 独立确认上次退出原因为 Error |
| 7 | Metric | Prometheus | kube_pod_container_status_restarts_total, container: app, value: 17 | 独立确认重启计数与 K8s 状态一致 |
| 8 | Logging | Elastic | pattern: CONFIG_MISSING, service: aiops-lab-workload, http_status: 500, path: /work (8次) | 指出启动过程中具体的失败原因 |
| 9 | Tracing | Tempo | trace_id: 65684c8c074b2b13bde640e742613caa, span: GET /work, status_code: 500, attributes.aiops.observed_mode: config_missing_exit | 将日志中的 CONFIG_MISSING 精确关联到具体的应用请求和配置缺失场景 |
| 10 | Tracing | Deepflow | flow: GET /work -> /work, response_code: 500, src_ip: 172.16.104.9 -> dst_ip: 172.16.104.15 | 证实应用对外提供的 HTTP 接口返回 500 错误 |

**证据印证：**
1. K8s State (fact-132b9c3683b9, fact-8b7c63aaaa33, fact-45ffe9038c67) 与 Prometheus Metric (fact-684a6ec0e7d7, fact-ebb3766067bf, fact-12c1cd3553d7) 完美交叉验证，确认容器处于 `CrashLoopBackOff` 且上次退出原因为 `Error` (exit_code 78)。
2. Logging (fact-5c1f4e8b8b14 等) 的 `CONFIG_MISSING` 与 Tracing (fact-408947ed4dba) 的 `config_missing_exit` 模式及 500 状态码一致，揭示了 `CrashLoopBackOff` 的直接机制：应用启动后因配置缺失主动以 HTTP 500 报错并退出。
3. Tracing 中的 trace_id `65684c8c074b2b13bde640e742613caa` 与 Logging 中的 trace_id 匹配，实现了从日志到追踪的闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行环境缺失必要配置（CONFIG_MISSING） → 应用启动流程检测到配置缺失并返回 HTTP 500 错误 → 容器进程以退出码 78 终止 → Pod 触发 CrashLoopBackOff 并持续重启
```

### 根因结论

已确认的根因为 **应用程序配置缺失（CONFIG_MISSING）**。

该配置缺失导致应用启动时无法正常运行，进而抛出 HTTP 500 错误（见 Tracing `config_missing_exit` 及 Logging 记录），容器进程随之以退出码 78 终止（见 K8s State `last_exit_code: 78` 与 Metric `last_terminated_reason: Error`）。由于退出机制存在，Kubelet 触发了指数级退避的重启策略，导致 Pod 陷入 `CrashLoopBackOff` 状态并持续重启（见 K8s Event `Back-off restarting` 与 Metrics `restarts_total: 17`）。

缺失的具体上游配置源（如缺失的 ConfigMap/Secret 名称或路径）在本次工具结果中未明确展示。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.3s
├─ 并发证据采集: 90.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 90.0s (Evidence 81.1s, RCA 8.7s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
