## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | {'message': 'Annotations:      cni.projectcalico.org/containerID: 4fe3fccc7e7cf5eb12ef7ae6a7cda8fbaa042ce7c3cbb0356b6d2f5b214d97a2'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-7679bcf76-w9s9c` 状态 `Running`，但 App 容器 `restart_count: 11`，最后一次 `exit_code: 2` | 确认为应用进程内部崩溃导致反复重启，而非调度或启动失败 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (持续 35m) | 确认 Kubelet 检测到容器异常退出且重启策略已触发限流退避 |
| 3 | K8s Config | Kubernetes | App 容器资源限制 `memory: 96Mi` (硬限制)，请求 `memory: 24Mi` | 提供资源消耗基准，用于评估是否存在 OOM 可能（需结合日志确认） |
| 4 | Logging | Elasticsearch | `http_request` 错误日志：`message: "runtime process exiting"`, `http_status: 500`, `path: "/work"` | 直接证据：应用在处理 /work 请求时主动退出，无堆栈或 OOM 信号 |
| 5 | Tracing | Tempo/Span | TraceID `97a75c07...` (关联成功日志)：`http.response.status_code: 200`, `aiops.observed_mode: runtime_exit` | 辅助证据：在部分成功请求的 Trace 中观测到 `runtime_exit` 状态，证明是进程级异常 |
| 6 | Tracing | Deepflow/Flow | 5 次 `GET /work` 流量聚合，`response_code: 500`，TraceID 与错误日志一致（如 `491a...`, `5ece...`） | 关联证据：L7 层面明确观察到 500 错误，且流量时间范围与日志匹配 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: "Error"` (单点样本) | 验证容器以 Error 状态终止，与 K8s 事件原因一致 |

**证据综合说明：**
K8s 状态显示容器反复退出（exit_code 2），日志与 Tracing 明确指向应用进程在处理 `/work` 路径时主动抛出内部错误并退出（`runtime process exiting`）。虽然内存硬限制为 96Mi，但日志和 Trace 中未出现 OOM 信号，而是表现为应用层崩溃。由于缺乏堆栈跟踪，进程退出的具体代码级原因（Bug 或资源耗尽）仍无法通过现有数据确诊。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程在处理 /work 请求时发生运行时错误 → 抛出内部错误导致进程非正常退出 (exit_code: 2) → Kubelet 检测到容器终止并重启 → 触发 CrashLoopBackOff
```

### 根因结论

**已确认现象**：Pod `workload-7679bcf76-w9s9c` 因应用进程在 HTTP 处理 `/work` 期间发生运行时错误而频繁崩溃退出。日志 (`runtime process exiting`) 和 Tracing (`aiops.observed_mode: runtime_exit`) 与 K8s 容器的 `exit_code: 2` 及 `BackOff` 事件相互印证，确定了应用层主动退出的直接失败机制。

**结论：证据不足**。
当前数据不足以定位“导致运行时错误的具体机制”。日志中未提供堆栈跟踪、异常详情或内存泄漏迹象（无 OOM 信号），无法区分是代码逻辑缺陷、未捕获异常还是特定数据导致的崩溃。需补充应用日志中的异常堆栈（Stack Trace）或更详细的内存/CPU 监控指标以进一步确诊。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 21.1s
├─ 并发证据采集: 100.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 100.3s (Evidence 86.9s, RCA 13.2s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
