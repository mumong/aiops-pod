## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Application internal unhandled error during HTTP request handling causes immediate process termination (exitCode=2) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认应用当前处于重启循环状态 |
| 2 | K8s Event | Kubernetes | BackOff: `back-off 5m0s restarting failed container=app pod=workload-7679bcf76-w9s9c_aiops-case-06` | 确认 kubelet 因应用反复异常退出而主动延长重启间隔 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason`: Error, `container.last_exit_code`: 2, `restart_count`: 24 | 确认应用进程非正常退出且退出码固定为 2 |
| 4 | Logging | Elasticsearch | Pattern: `http_request` 500 `runtime process exiting` on `/work`, trace_id: `9e40de7904911dfd27f6b9430ff5b674` | 捕获到请求处理阶段进程立即崩溃的直接证据 |
| 5 | Tracing | Deepflow | L7 Flow: HTTP GET `/work` response_code: `500`, trace_id: `005d9f0d3504d3557ff340b304fd9609` | 独立网络层面确认 `/work` 请求返回 500 且无应用层成功响应 |
| 6 | Tracing | Tempo | Span: `GET /work` response_code: `200` (正常), trace_id: `160828fdbc068f8fae2f2c59ecad1f1b` | 证明同一服务下其他请求正常，排除集群网络或入口故障 |

**证据印证说明**：
Kubernetes 层显示容器因 Exit Code 2 反复重启（#3, #1），而 Logging 与 Tracing 层（#4, #5）在相同的 `/work` 请求路径上，一致记录了进程崩溃和 500 错误，直接解释了重启原因。正常请求的 200 响应（#6）排除了基础设施层面的故障。

## 🎯 根因分析 · g1

### 因果链

```text
HTTP 请求处理时应用内部未捕获异常 → 进程立即退出 (exitCode=2) → 容器状态 CrashLoopBackOff → 用户访问 /work 持续收到 500
```

### 根因结论

已确认根因为**应用内部未捕获异常导致进程在请求处理期间崩溃**。
应用在处理 `/work` 请求时因内部错误立即终止（Logging #4），这直接导致容器退出码为 2 且不断重启（K8s #3）。该根因得到网络层独立观测（Tracing #5）的支持，且正常流量的存在排除了环境或网络故障（Tracing #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 14.6s
├─ 并发证据采集: 92.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 92.1s (Evidence 84.6s, RCA 7.3s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled, pod-imagepull-failed
