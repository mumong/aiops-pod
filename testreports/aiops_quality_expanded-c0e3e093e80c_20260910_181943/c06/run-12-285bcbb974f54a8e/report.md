## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Application-level unhandled error in /work endpoint causing process exit (exitCode 2) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code`: 2 | 容器终止时的具体异常退出码 |
| 2 | K8s State | Kubernetes | `restart_count`: 10 | 容器因退出已重试 10 次 |
| 3 | K8s State | Kubernetes | `waiting_reason`: CrashLoopBackOff, `waiting_message`: "back-off 5m0s restarting failed container=app" | 系统级重启行为处于退避等待状态 |
| 4 | K8s Event | Kubernetes | `BackOff restarting failed container app` (x112 over 29m) | 频繁重启行为已持续约 29 分钟 |
| 5 | Logging | Elasticsearch | `path`: /work, `http_status`: 500, `message`: "runtime process exiting" (出现 2 次, `trace_ids`: b7890415..., 0a2f7e93...) | 明确指向 /work 路径发生 500 错误导致进程退出 |
| 6 | Logging | Elasticsearch | `path`: /work, `http_status`: 200, `message`: "request completed" (出现 6 次) | 排除 /work 路径完全不可达，错误为应用内部异常 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (CrashLoopBackOff): 1 | 确认当前状态符合 K8s 报告的异常 |
| 8 | Metric | Prometheus | `kube_pod_status_phase` (Running): 1, `reason`: Error (LastTerminated): 1 | 确认 Pod 调度成功且处于 Running 态，但最近终止原因为 Error |

**证据印证：**
1. K8s 层面观察到容器以 `exitCode 2` 退出并触发 CrashLoopBackOff（事实 1-4）。
2. Elasticsearch 日志直接定位到具体触发点为 `/work` 路径的 HTTP 500 错误，伴随 "runtime process exiting" 的日志输出（事实 5），与 K8s 的退出码（事实 1）形成闭环。
3. Prometheus 指标（事实 7-8）独立验证了当前 CrashLoopBackOff 的状态和最近终止原因，确证了异常状态的真实性。

## 🎯 根因分析 · g1

### 因果链

```text
Unhandled error in server.py /work endpoint (应用层未捕获异常) → 
Process logs 'runtime process exiting' and returns HTTP 500 → 
Container terminates with exitCode 2 → 
Kubelet enters CrashLoopBackOff
```

### 根因结论

已确认的根因为：**`/work` 端点的应用层未捕获异常（Unhandled error）**。

*   **现象解释**：应用在处理 `/work` 路径的请求时发生未捕获错误，记录 "runtime process exiting" 日志并返回 HTTP 500 状态码，导致进程以 `exitCode 2` 异常退出。随后 Kubelet 尝试重启该容器，因频繁失败而进入 `CrashLoopBackOff` 状态。
*   **证据引用**：
    *   K8s 状态：`exit_code: 2`（事实 1）、`CrashLoopBackOff`（事实 3）。
    *   日志：`/work` 路径 `http_status: 500` 且 `message: "runtime process exiting"`（事实 5）。
*   **证据不足部分**：具体触发异常的应用代码行、异常类型或堆栈信息（Stack Trace）目前缺失，无法进一步定位导致该未捕获异常的底层业务逻辑原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.6s
├─ 并发证据采集: 75.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 75.6s (Evidence 68.4s, RCA 7.1s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
