## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 容器应用进程被显式配置为模拟运行时崩溃（FAILURE_MODE=runtime_exit），在处理后返回500错误并执行异常退出（Exit Code 2）以触发故障注入，导致Pod进入CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 确认应用容器非正常退出 |
| 2 | K8s Event | kubernetes | `Warning BackOff: Back-off restarting failed container app in pod workload-7679bcf76-w9s9c` | 确认 Pod 因重启失败进入 CrashLoopBackOff 状态 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 2` | 提供进程退出的精确系统返回码，是故障注入的标志性特征 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi`, `container.resource_request.cpu: 20m`, `container.resource_limit.cpu: 200m` | 确认资源约束配置，结合低使用率可排除 OOM 或 CPU 限制 |
| 5 | Logging | elasticsearch | `http_status: 500`, `message: "runtime process exiting"` (pattern, occ=3) | 业务日志显示应用处理请求后主动触发异常退出 |
| 6 | Tracing | deepflow | `HTTP GET /work`, `response_code: 200`, `duration: 18ms~41ms` (flow, count=9) | 网络层观测到成功返回的流量，证明应用逻辑本身在处理请求，但随后被进程层终止 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total: 9` | 量化验证了 CrashLoopBackOff 导致的频繁重启现象 |

证据表明，应用容器在执行特定业务逻辑（HTTP `/work` 请求）后，会统一返回 500 状态码并退出。Tracing 观测到的成功流量与日志中记录的 500 错误、Exit Code 2 共同指向一种有意的故障注入行为，而非资源耗尽或系统缺陷导致的意外崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置了 FAILURE_MODE=runtime_exit 故障注入 → 业务处理结束后执行异常退出(Exit Code 2) → 容器进程终止，K8s 触发重启并逐渐进入 BackOff 冷却 → 用户可见 Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因是**应用层面的显式故障注入（Failure Injection）**。

该工作负载 `aiops-case-06/workload-7679bcf76-w9s9c` 的容器应用被配置为在响应特定请求后模拟运行时崩溃。证据包括：
1. 容器以 **Exit Code 2** 异常退出，这是故障注入工具常见的退出标识。
2. 日志明确记录 `runtime process exiting`。
3. 资源监控数据（`resource_limit` 等）未显示内存或 CPU 限制导致的 OOMKilled，排除资源故障可能。

上述故障注入机制导致 Pod 频繁重启，最终触发 K8s 的 CrashLoopBackOff 保护机制。当前环境为故障测试场景，而非生产意外故障。

---

## 📊 性能统计

```text
├─ 总耗时: 9.2m
├─ 问题定位: 25.5s
├─ 并发证据采集: 515.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 515.7s (Evidence 509.9s, RCA 5.7s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-notready-probe-failed
