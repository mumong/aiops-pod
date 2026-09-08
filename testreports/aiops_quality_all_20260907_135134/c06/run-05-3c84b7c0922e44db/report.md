## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | 容器应用启动后在 '/work' 请求处理过程中触发未捕获异常（日志显示 'runtime process exiting'），导致进程以退出码 2 终止，Kubelet 持续重启失败引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `reason: "Error"`, `exit_code: 2`, `restart_count: 6` | 确证应用进程异常终止且 Kubelet 处于重启循环中 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (持续 10m, x44) | 展示重启行为导致 Pod 进入 CrashLoopBackOff 状态 |
| 3 | Logging | Elasticsearch | `error` 级别日志 `runtime process exiting` 伴随 `path: "/work"`, `http_status: 500` | 直接指出崩溃发生在处理 `/work` 请求时的应用运行时阶段 |
| 4 | Tracing | Deepflow/Tempo | HTTP Flow 显示 `request_resource: "/work"`, `response_code: 500`, `trace_ids`: `["fa50465f8c4433915f35a0b33797defd", "a43b4fd787e1275d85970e6dd3bde0f0"]` | 关联日志中的错误请求，证实该特定接口调用的失败与进程终止高度一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason="Error"`, `kube_pod_container_status_restarts_total=6` | 外部指标数据与 Kubernetes 状态确认重启与错误状态 |

证据表明 Pod 进入 CrashLoopBackOff 并非由资源不足（资源 Request 24Mi/20m，Limit 96Mi/200m）或网络插件（Calico）引发。日志 `runtime process exiting` 与追踪系统 `/work` 路径上的 500 错误共同指向应用内部逻辑在特定请求处理时发生未捕获异常并退出（exit code 2）。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑错误/未捕获异常 → 进程收到退出信号并终止 (exit_code=2) → Kubelet 重启策略触发频繁重启 (restarts=6) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：**容器应用在处理 `/work` 接口请求时发生未捕获异常（runtime process exiting），导致进程以退出码 2 终止。**

该根因由以下事实充分支撑：
1.  **Kubernetes 状态**确认了进程退出码为 2 且已触发 6 次重启（`fact-b091e6289788`、`fact-e19289c2c44b`）。
2.  **日志证据**明确捕捉到 `runtime process exiting` 错误且发生在 `/work` 路径（`fact-266ef80f4fbc` 等）。
3.  **追踪数据**将上述错误日志与具体的 HTTP 500 响应进行了关联（`fact-0bb56c36f3d0`、`fact-089f2d40d83c`）。

**缺失事实**：日志摘要中未展示具体的异常堆栈（Traceback），因此无法进一步定位具体的代码行或异常类型（`unknowns` 中已标注）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.8s
├─ 并发证据采集: 66.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 66.3s (Evidence 58.3s, RCA 7.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
