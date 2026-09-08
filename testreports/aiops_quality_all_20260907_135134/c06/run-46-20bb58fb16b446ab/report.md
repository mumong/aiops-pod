## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Application process terminates with exit code 2 triggered by a 500 error response during /work request processing, causing persistent container restarts. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit code: 2 | 确认容器因错误退出 |
| 2 | K8s Event | kubernetes | BackOff restarting failed container app | 确认集群级重启机制触发 |
| 3 | Logging | elasticsearch | http_request error: http_status=500, path=/work, message="runtime process exiting" (3次, 14:00-14:21) | 直接指向 500 错误及进程退出行为 |
| 4 | Tracing | deepflow | HTTP GET /work response_code=500 (4次, 172.16.104.59 -> 52) | 从流量侧验证了 500 错误的产生和分布 |
| 5 | Metric | prometheus | kube_pod_container_status_last_terminated_reason="Error", value=1 (7次, 稳定) | 长期持续处于 Error 状态 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total=26 (6-26次) | 反映重启的累积量级 |

**证据关系说明**：
- **K8s Event (行 2)** 与 **K8s State (行 1)** 相互印证，确认了 Pod 的 CrashLoopBackOff 状态与退出码 2 之间的因果关系。
- **Logging (行 3)** 与 **Tracing (行 4)** 一致确认了异常的直接原因：在处理 `/work` 请求时触发 HTTP 500 错误，并伴随 "runtime process exiting" 日志，证实了进程级别的终止。
- **Metric (行 5, 6)** 在时间跨度上（7次观测）持续记录了该终止原因和重启行为，排除了瞬时抖动，确认为持续的故障模式。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑触发 /work 请求 HTTP 500 错误 → 进程记录 "runtime process exiting" 并返回 Exit Code 2 → K8s 执行 Container Restart → CrashLoopBackOff
```

### 根因结论

**已确认的根因：应用层在处理 `/work` 请求时返回了 HTTP 500 错误，进而触发了进程的致命退出（Exit Code 2）。**

具体而言，证据表明应用代码中发生了导致 500 错误的异常，并在随后的逻辑中执行了进程退出操作：
1. **流量/追踪证据**：Deepflow 聚合流数据显示针对 `/work` 的 HTTP GET 请求出现了 500 响应码（`response_code: 500`）。
2. **日志证据**：ES 日志明确记录了关联的 "runtime process exiting" 事件，且附带了 `http_status: 500` 和 `path: /work` 上下文。
3. **K8s 状态证据**：Pod 处于 CrashLoopBackOff，容器最后一次终止原因为 `Error`（Exit Code 2），重启次数已累积至 26 次以上。

这一链式反应导致应用不断重启并持续报错，形成了当前的集群异常状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.9s
├─ 并发证据采集: 57.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 57.6s (Evidence 51.0s, RCA 6.5s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
