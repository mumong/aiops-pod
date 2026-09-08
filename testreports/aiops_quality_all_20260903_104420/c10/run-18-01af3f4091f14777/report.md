## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Environment variable FAILURE_MODE is set to 'liveness_fail', causing the application's /health endpoint to return HTTP 500, which triggers liveness probe failures and subsequent container kills (OOM/signal 137). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x17) | 直接触发容器重启机制的事实依据 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error` | 证实容器非正常终止 |
| 3 | K8s Event | Kubernetes | `Back-off restarting failed container` (x176 over 49m) | 证实故障已形成 CrashLoop 模式 |
| 4 | Logging | Elasticsearch | `pattern: {path: "/work", http_status: 200}` (8次) | 证明应用主业务逻辑运行正常，隔离故障范围至健康检查端点 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1 (CrashLoopBackOff)` | 佐证 Pod 当前处于等待重启状态 |
| 6 | Tracing | Tempo | `span: GET /work` 且 `attributes.aiops.observed_mode: liveness_fail` | 确认容器在运行期间确实处于故意失败的模式配置中 |

**证据关联说明：**
Kubernetes 的 Liveness Probe 失败记录与 Prometheus 的 CrashLoopBackOff 状态直接对应；日志证明主业务正常（200），而 Tracing 数据中的 `aiops.observed_mode: liveness_fail` 与 K8s 探针返回的 500 状态在逻辑上完全一致，证实是特定环境配置导致了探针失败。

## 🎯 根因分析 · g1

### 因果链

```text
Config/Env: FAILURE_MODE=liveness_fail → 健康端点返回 HTTP 500 → 容器探针失败被杀 (Exit 137) → 进入 CrashLoopBackOff
```

### 根因结论

已确认的根因为：环境变量 `FAILURE_MODE` 被设置为 `'liveness_fail'`，导致应用的 `/health` 端点故意返回 HTTP 500 错误。由于 Kubernetes Liveness Probe 依赖该端点，探针连续失败触发了容器强制终止机制（表现为 Exit Code 137 和 Terminated Reason Error），进而导致 Pod 进入 CrashLoopBackOff 状态。日志与 Tracing 数据证实应用主体运行正常，进一步排除了资源不足或代码崩溃等其他可能。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 16.0s
├─ 并发证据采集: 561.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 561.0s (Evidence 551.6s, RCA 9.3s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-notready-probe-failed
