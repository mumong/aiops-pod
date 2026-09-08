## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIP: 172.16.104.52/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认 Pod 处于重启失败状态 |
| 2 | K8s Event | kubernetes | `event.message`: Back-off 5m0s restarting failed container app | 证实重启间隔拉大，应用持续崩溃 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error | 确认容器最后一次终止原因为通用错误 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: 2 | 提供进程退出的确切退出码 |
| 5 | Logging | elasticsearch | `http_request`: path=/work status=500, message="runtime process exiting", trace_ids: [f564ba67b5e2494bb283993304f3fa1b, ...] | 记录导致进程退出的具体 HTTP 异常请求 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (reason=Error) | 指标侧确认容器最后一次终止为错误状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 25 | 量化应用已重启次数，确认处于不稳定状态 |
| 8 | Tracing | deepflow | `l7_flow`: GET /work status_code=500, src_ip=172.16.104.59 -> dst_ip=172.16.104.52 | 网络层面复现 500 请求路径 |
| 9 | Tracing | tempo | `application_span`: trace_id=130bdd4836bc750bcf687e89b717aebe, status=200 | 确认应用并非完全宕机，具备正常响应能力 |

**证据说明**：
- 编号 1-4 的 Kubernetes 状态与编号 5-6 的日志/指标互相印证，确认应用进程因异常退出 (Exit Code 2) 导致重启失败。
- 编号 5 与编号 8 分别通过日志流和网络流量流，共同锁定了导致崩溃的直接操作是访问 `/work` 接口。
- 编号 9 的存在排除了网络不通或应用完全挂死的可能性，限定了故障范围在应用代码执行层面。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码未捕获异常 → HTTP 500 响应 → runtime process exiting → CrashLoopBackOff
```

### 根因结论

现有证据足以确认根因：应用在处理 `/work` 接口时发生内部错误（返回 500），导致主进程以退出码 2 强制终止，进而触发 Kubernetes 的重启机制并因连续失败进入 CrashLoopBackOff 状态。

然而，关于**根本原因的细节（Root Cause）**，证据不足：
- 导致 500 错误的 **具体 Python 异常类型或堆栈** 缺失：日志虽捕获了“runtime process exiting”，但未提供导致退出的具体代码行或异常信息。
- 关键追踪链路 **完整性不足**：尽管有 Trace ID `f564ba67b5e2494bb283993304f3fa1b` 关联到 500 错误，但该链路的详细上下文未获取（受限于采集范围或配置），无法定位具体是哪段代码逻辑触发了异常。
- **触发来源不明**：无法从当前证据中确定触发 `/work` 请求的来源是外部流量还是内部探针。

因此，只能确认“未处理异常导致进程退出”为直接原因，具体代码级根因需补充日志堆栈或完整链路追踪数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.2s
├─ 并发证据采集: 73.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 73.7s (Evidence 61.7s, RCA 11.8s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
