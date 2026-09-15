## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | app容器启动失败，执行python3 /opt/aiops/server.py时发生内部错误(退出码2)导致CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认应用持续重启，Pod 无法就绪 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error`；`container.last_exit_code`: `2` | 确认最近一次异常由进程退出码 2 导致 |
| 3 | K8s Event | Kubernetes | `BackOff  99s (x475 over 106m)` | 证实故障已持续约 106 分钟，进入指数退避阶段 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory`: `96Mi`；`resource_request.cpu`: `20m` | 提供资源配置基线，排除显而易见的 OOMKilled 或 CPU 节流（状态不符） |
| 5 | Logging | Elasticsearch | `runtime process exiting` (http_status: 500, path: `/work`, 4条记录, trace_ids: `19429b...`, `04b45d...`) | 捕捉到应用层面的内部错误与异常终止信号 |
| 6 | Tracing | Deepflow | `GET /work` response_code: `500` (occurrence_count: 3, trace_ids: `a8998d...`) | 网络层流量证实了 HTTP 500 错误，与日志的 500 状态码相互印证 |
| 7 | Tracing | Deepflow | `GET /work` response_code: `200` (occurrence_count: 5, trace_ids: `21cff4...`) | 提供对比基线，证明 `/work` 接口在早期能正常响应，问题属于应用内部执行故障而非全链路不可达 |

**证据印证说明：**
1. Kubernetes 的 `Error` 退出码 `2` (证据#2) 与 Logging (证据#5) 的 `runtime process exiting` 结合，直接锁定了进程非正常退出。
2. Tracing (证据#6) 的 HTTP 500 响应与 Logging (证据#5) 中的 500 状态码一致，证明应用在收到请求后执行到了崩溃点。
3. K8s Event (证据#3) 记录了长期的退避重启，说明这是一个持续存在的内部错误，而非偶发或配置问题。

## 🎯 根因分析 · g1

### 因果链

```text
app容器启动失败，执行python3 /opt/aiops/server.py时发生内部错误(退出码2) → 进程异常终止 → Kubelet 检测到容器退出码2 → CrashLoopBackOff
```

### 根因结论

已确认的根因为 **应用容器内部执行错误**（具体表现为 `python3 /opt/aiops/server.py` 执行时发生内部错误，导致进程以退出码 2 终止）。

*   **直接证据**：Kubernetes 状态显示容器终止原因为 `Error`，最后一次退出码为 `2`（证据#2）。
*   **应用层面证据**：日志捕获到 `runtime process exiting` 事件（证据#5），Tracing 记录了伴随的 HTTP 500 错误（证据#6），证实应用在运行过程中遭遇了内部崩溃。
*   **故障现状**：由于退出码非 137 (OOMKilled) 或 1 (正常停止)，而是 2，说明是应用代码、依赖缺失或配置错误导致的内部异常。目前证据已充分证实容器因内部错误反复崩溃，符合 CrashLoopBackOff 特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.4s
├─ 并发证据采集: 51.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 51.5s (Evidence 45.1s, RCA 6.3s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
