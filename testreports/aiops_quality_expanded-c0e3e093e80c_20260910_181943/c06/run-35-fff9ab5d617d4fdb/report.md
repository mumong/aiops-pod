## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8持续处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app ...` (x315 over 74m) | 确认 Pod 处于 CrashLoopBackOff 状态，且已重启 19 次 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认等待原因与事件描述一致 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 确认容器最后一次异常退出，由应用层终止 |
| 4 | Metric | prometheus | `container_memory_usage_bytes`: 3.71 MiB (18:38:22) → 3.72 MiB (18:43:37) | 证明 CrashLoopBackOff 期间内存未越界（limit 96Mi），排除 OOMKill |
| 5 | Logging | elasticsearch | `request completed` (HTTP 200) 19:20-19:35；随后 `runtime process exiting` (HTTP 500) 19:20-19:41 | 日志显示服务在正常响应 200 后，开始出现处理失败并返回 500 的记录 |
| 6 | Tracing | deepflow | L7 Flow: `GET /work` → 500, 耗时 4.4-5.7 ms (19:30-19:46) | 追踪了应用返回 500 错误的具体时刻，与日志结束时间吻合 |
| 7 | Tracing | tempo | Span `GET /work` (trace: 9db0ebec...): `aiops.observed_mode: runtime_exit` | 结合 `runtime_exit` 标签，佐证了进程在收到 500 后主动退出的行为 |

证据链表明：Pod 因应用异常不断重启（事实 1-3）。重启期间应用内存使用极低（事实 4），排除资源限制问题。日志显示服务在一段时间内响应正常（200），随后在处理 `/work` 请求时开始出现异常并返回 500，且伴随进程退出（事实 5-7）。Tracing 中的 `runtime_exit` 模式进一步证实了这是应用代码层面的主动终止。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理 /work 请求时未捕获异常 → 返回 HTTP 500 并执行退出命令 → 容器以 exitCode=2 终止 → K8s 触发重试策略导致 CrashLoopBackOff
```

### 根因结论

已确认的根因是 **应用代码在处理 `/work` 请求时发生未捕获运行时异常**。
*   证据 5、6、7 一致表明应用在处理特定 HTTP 请求时返回 500 错误，并且该行为伴随着进程的主动终止（`exitCode=2` 和 `runtime_exit` 观察）。
*   证据 3 提供了直接的终止代码 `exitCode=2`，证明非 OOMKill。
*   证据 4 排除了内存不足导致的系统级 Kill。
*   目前的证据足以确定根本原因是应用层的逻辑缺陷或异常，导致进程不断崩溃重启。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 25.4s
├─ 并发证据采集: 90.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 90.1s (Evidence 81.1s, RCA 8.9s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
