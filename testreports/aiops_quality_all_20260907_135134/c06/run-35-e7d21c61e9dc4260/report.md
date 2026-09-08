## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod `aiops-case-06/workload-7679bcf76-jwr8b` 处于 `CrashLoopBackOff` 状态，重启次数23次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | 容器 `app` 退出码 2，状态 `CrashLoopBackOff` (fact-2cceca337954, fact-d19fef324bcc) | 描述直接症状 |
| 2 | K8s Event | K8s | `Back-off restarting failed container app` (fact-2eb7259d048d) | 描述重启行为 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 23 (fact-a5e4902e8e85) | 量化重启次数 |
| 4 | Logging | Elasticsearch | `http_request`, 500, `runtime process exiting`, path `/work` (fact-1e0bcbeae073) | 捕捉进程退出的确切日志和原因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = Error (fact-859caa6595c2) | 确认容器以 Error 退出 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = CrashLoopBackOff (fact-af0d6432c6a3) | 确认容器处于崩溃等待状态 |

**证据链分析**：
Metric 维度（#3, #5, #6）直接证实了容器经历了 23 次重启且最终停留在崩溃等待状态。Kubernetes 维度（#1, #2）展示了具体的 Pod 状态与 Kubelet 的退避重启事件。日志维度（#4）提供了最关键的机制解释，明确了 `http_status: 500` 后进程打印 `runtime process exiting` 并终止，这完美解释了 K8s 观测到的 `Exit Code 2` 和 `CrashLoopBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑缺陷 (处理 /work 路径) → HTTP 返回 500 并主动调用退出 → 容器进程以 exitCode 2 终止 → 触发 Kubelet BackOff 重启，Pod CrashLoopBackOff
```

### 根因结论

已确认根因为**应用服务逻辑缺陷导致进程主动崩溃退出**。

应用服务在处理 HTTP 请求（特别是 `/work` 路径）时发生了内部异常，导致返回 HTTP 500 状态码。随后，应用进程触发了主动退出机制（日志显示 `runtime process exiting`），以 `Exit Code 2` 终止。Kubernetes 检测到该异常退出后，依据重启策略不断尝试重启容器，最终因频繁重启进入 `CrashLoopBackOff` 状态（证据 #1, #4, #5）。

具体导致 500 错误的业务逻辑原因（如配置缺失或代码 Bug）目前证据不足，无法直接确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.5s
├─ 并发证据采集: 72.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 72.7s (Evidence 59.9s, RCA 12.6s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
