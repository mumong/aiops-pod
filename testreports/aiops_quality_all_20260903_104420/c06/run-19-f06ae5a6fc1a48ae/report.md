## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | Running | Runtime error in application logic at endpoint /work |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload-7679bcf76-w9s9c...` (x178 over 43m) | 确认应用进程存在严重退出异常并触发系统重启机制 |
| 2 | K8s State | Kubernetes | `reason: Error`, `exit_code: 2` | 确认终止原因非 OOM 杀除，属应用层错误退出 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi` | 提供应用资源硬限制上下文，辅助排除内存超限假设 |
| 4 | Logging | Elasticsearch | `runtime process exiting`, `http_status: 500`, `path: /work`, `trace_id: 491a5553286b708f2be0016438a15c3f` | 锁定具体触发路径为 `/work` 端点返回 500 错误导致进程终止 |
| 5 | Tracing | Deepflow | `GET /work` `response_code: 500` `trace_id: 491a5553286b708f2be0016438a15c3f` | 与日志 trace_id 一致，网络层观测确认返回 500 状态码 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: "Error"`, `restart_total: 13` | 持续复现的异常重启状态统计佐证 |
| 7 | Tracing | Tempo | `GET /work` `http.response.status_code: 200`, `trace_id: 97a75c073642b491e78d960ba0ad27a4` | 确认 `/work` 端点同时存在正常处理情况，排除全量服务不可用 |

证据显示应用进程因 `/work` 端点引发内部运行时错误（exit code 2）而终止。Deepflow 中的 500 流量日志与 Elasticsearch 中的 `runtime process exiting` 日志存在 trace_id (491a5553286b708f2be0016438a15c3f) 的直接关联。同时存在成功返回 200 的同类请求，证实故障表现为该端点特定的应用逻辑异常而非整体服务宕机。

## 🎯 根因分析 · g1

### 因果链
```text
Application code logic error at endpoint /work → Endpoint returns HTTP 500 and triggers 'runtime process exiting' → Container process exits with Error code (non-OOM) → Kubernetes restart policy triggers CrashLoopBackOff
```

### 根因结论
**已确认的根因**：应用程序在 `/work` 端点的逻辑错误导致进程运行时退出（Runtime error / exit code 2）。
**证据支撑**：
1. **直接证据**：Elasticsearch 日志显示路径 `/work` 在返回 500 状态码时进程退出（fact-6063d42ebb93）；Deepflow 流量记录同步验证该端点返回 500 错误（fact-23b0ab486279）。
2. **辅助证据**：Pod 重启计数器（fact-7389fec40fa8）及 K8s 事件（fact-5c3f8ca5d253）记录了多次因非 OOM 异常（exit code 2）导致的 CrashLoopBackOff。
3. **排除假设**：应用存在资源硬限制 96Mi，但退出机制明确为“Error”而非 OOMKilled，排除因内存耗尽导致的系统级强杀进程。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 21.9s
├─ 并发证据采集: 98.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 98.0s (Evidence 89.0s, RCA 8.9s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-oomkilled
