## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器 app 反复以 Exit Code 2 退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-7679bcf76-w9s9c` | 确认应用进程反复异常退出 |
| 2 | K8s State | kubernetes | `container.app.exit_code: 2`, `container.app.restart_count: 25` | 确认进程以非零状态码强制退出，已发生 25 次重启 |
| 3 | K8s State | kubernetes | `container.app.reason: Error`, `container.app.waiting_reason: CrashLoopBackOff` | 确认 Pod 处于崩溃循环状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total: 25` | 独立确认容器重启次数 |
| 5 | K8s Config | kubernetes | `container.app.resource_limit.memory: 96Mi` | 确认容器硬内存限制 |
| 6 | Logging | elasticsearch | `pattern: runtime process exiting`, `http_status: 500`, `path: /work`, `first: 13:14:18.003Z` | 确认应用在处理 /work 请求时记录内部错误并退出进程 |
| 7 | Tracing | deepflow | `flow: GET /work -> 500`, `src_ip: 172.16.104.21`, `dst_ip: 172.16.104.17` | 证实网络流量确实在 /work 端点返回了 500 错误 |

上述证据形成了闭环：Tracing 与 Logging 的 `trace_id` 均包含 `44d82bffd1cff720d7ba7f132cc91772`，该 Trace 同时对应日志中的 `request completed (200)` 和 Tracing 中的 `span: 200`，但日志聚合与 Deepflow 流量聚合同时也记录了 `GET /work` 的 `500` 错误与 `runtime process exiting`。Kubernetes 的 Event 与 Container State 确证了进程退出后触发了 CrashLoopBackOff。资源限制（96Mi）在此处为上下文背景，未显示 OOM Kill 迹象，因此直接证据指向应用逻辑异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在 /work 端点处理 HTTP GET 请求时发生内部异常 → 应用记录 runtime process exiting (500 Error) 并强制退出 (Exit Code 2) → Kubernetes 检测到容器非零退出码并触发重启策略 → Pod 陷入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用服务在处理 `/work` 请求时发生内部错误（表现为 HTTP 500 及 `runtime process exiting`），导致进程以 Exit Code 2 强制退出，触发 Kubernetes 的重启策略进而陷入 CrashLoopBackOff（证据：fact-6efb8c4ef276, fact-7cc922125280, fact-10e04d0281e5, fact-135430e47f58）。

**未确认细节**：
1. 导致 `/work` 请求返回 500 的具体 Python 异常堆栈或代码级故障点（缺少完整日志上下文）。
2. 是否存在导致 500 错误的周期性输入模式或特定触发参数。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 19.1s
├─ 并发证据采集: 86.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 86.9s (Evidence 77.3s, RCA 9.4s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled
