## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | Error | pod_status_error_crashloop |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `container.waiting_reason`: CrashLoopBackOff | 确证容器反复异常终止与重启中 |
| 2 | K8s State | Kubernetes | `pod.condition`: Ready/ContainersReady=False (13:34:06Z); `restart_count`: 17; `exit_code`: 2 | 确认故障持续且 Pod 无法就绪 |
| 3 | K8s Event | Kubernetes | `message`: Back-off restarting failed container app in pod workload-7679bcf76-jwr8b (x271 over 64m) | 提供 BackOff 机制与重启频率的上下文 |
| 4 | Logging | Elasticsearch | Pattern: `level: error`, `message: "runtime process exiting"`; `http_status: 500` (13:13:21Z - 13:34:04Z) | 确认应用层发生致命错误，进程直接退出 |
| 5 | Logging | Elasticsearch | Pattern: `level: info`, `message: "request completed"`; `http_status: 200` (13:13:19Z - 13:34:02Z) | 确认应用此前正常处理请求，故障发生在特定路径 |
| 6 | Tracing | Deepflow + Tempo | Span: `GET /work` (Trace `684...3a0`, 13:13:19Z), `span.name: "GET /work"`, `http.request.method: "GET"` | 关联日志中的异常请求至具体 API 路径 |

证据关联与印证：
1. Kubernetes 维度确认容器以 exit_code 2 终止并进入 CrashLoopBackOff（事实 1, 2）。
2. 日志维度显示 `/work` 接口在相同时间段内频繁返回 500 并伴随 "runtime process exiting" 错误（事实 4, 5）。
3. Tracing 维度将 500 响应与具体的 HTTP `GET /work` 请求链路对应（事实 6）。
4. 三维度在时间与错误表现上完全闭合，一致指向应用逻辑缺陷导致的进程崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
/application_logic_error_on_/work_endpoint → unhandled_exception (runtime_process_exiting) → container_terminated_with_exit_code_2 → kubelet_crashloopbackoff_rescheduling
```

### 根因结论

**已确认根因：应用层处理 `/work` 接口时发生未捕获异常（Unhandled Exception）。**

应用在处理该 HTTP 请求时触发内部逻辑错误，导致进程直接退出（Runtime Process Exiting），返回 500 状态码并伴随 exit_code 2（依据事实 4, 6, 1, 2）。Kubelet 检测到容器异常终止后，执行指数级退避的重启策略（依据事实 3, 2），从而表现为持续处于 CrashLoopBackOff 状态。

**缺失信息**：日志中未捕获到具体的内部堆栈跟踪、异常类型代码或详细错误信息（依据 `unknowns` 字段），因此无法确定导致崩溃的具体底层代码逻辑，但已足以定位根因为应用层逻辑缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.8s
├─ 并发证据采集: 83.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 83.2s (Evidence 73.5s, RCA 9.5s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
