## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | Error | 应用代码在处理 '/work' 路径时触发未捕获的致命错误（runtime process exiting），导致进程以退出码 2 主动终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload-7679bcf76-jwr8b_aiops-case-06` (fact-0be56f63da0d, fact-19b1c47c5492) | 确认容器反复被系统终止并重启的异常状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (fact-0c2653a12d3e)；`container.last_exit_code: 2` (fact-5ba748ff4559) | 明确退出原因为 Error，且退出码为 2（通常指应用逻辑错误） |
| 3 | Logging | Elasticsearch | `runtime process exiting` (fact-266ef80f4fbc)；`request completed` (fact-b8cf83ec3df6)；路径均为 `/work` | 捕捉到导致终止的精确应用级致命错误日志，并确认该异常发生在处理 `/work` 路径时 |
| 4 | Tracing | Tempo | `GET /work` 返回 200，`aiops.observed_mode: runtime_exit` (fact-16c1065d8223) | 证明在应用进程异常终止前，该请求在应用层已返回成功，说明是请求处理完成后的后置致命错误 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` 在 299008.0 ~ 438272.0 之间波动 (fact-25a62d0217cc) | 证明容器运行期间内存处于正常水平，排除内存溢出导致被 OOMKilled 的可能 |

上述证据相互印证：K8s 报告异常终止与退出码 2，Elasticsearch 日志精准定位到处理 `/work` 路径时的 `runtime process exiting` 异常，Tempo 追踪进一步确认了在请求成功返回后应用层发生了非预期的运行时退出，而 Metrics 监控则排除了资源耗尽（如 OOM）的外部因素。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 → 处理 '/work' 路径时触发未捕获致命错误 → 进程以 exit code 2 主动退出 → 触发 K8s BackOff 重启并处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：应用代码在处理 `/work` 路径时触发了未捕获的致命错误（导致 `runtime process exiting`），从而以非零退出码 2 主动终止进程。

该结论由以下事实支撑：
- **退出特征匹配**：K8s 容器状态显示终止原因为 Error，退出码为 2，与代码层面的主动退出行为一致，且 Metrics 证明不存在 OOMKilled 现象。
- **精准业务定位**：Elasticsearch 日志直接记录了 `runtime process exiting`，且该事件集中在 `/work` 路径的上下文中。
- **时序与流程印证**：Tempo 追踪表明应用在处理该请求时已成功返回 HTTP 200，这意味着崩溃发生在响应返回后的后续代码执行路径中，证实了是代码内部异常导致了进程的意外退出。

---

## 📊 性能统计

```text
├─ 总耗时: 4.2m
├─ 问题定位: 15.3s
├─ 并发证据采集: 224.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 224.1s (Evidence 216.0s, RCA 7.9s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-config-error, pod-crashloop-runtime, pod-imagepull-failed
