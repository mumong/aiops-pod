## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error (fact-id: fact-3037c75bad3e) | 确认容器异常退出的直接事实 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff (fact-id: fact-e2170751e8da) | 确认 K8s 处于重启循环状态 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 2 (fact-id: fact-0f5f142f8341) | 提供进程退出的具体代码，指向运行时崩溃 |
| 4 | K8s Event | kubernetes | `BackOff` 事件: "Back-off restarting failed container app..." (fact-id: fact-80b2a0f980ba) | 证实 K8s 调度器在检测到连续重启后进入退避 |
| 5 | Logging | elasticsearch | `runtime process exiting` 错误日志 (HTTP 500, path: `/work`) (fact-id: fact-778e3ba9615a 等) | 直接记录应用逻辑错误与进程终止的对应关系 |
| 6 | Tracing | deepflow+tempo | `GET /work` 请求返回 HTTP 500，Span 属性 `aiops.observed_mode`: runtime_exit (fact-id: fact-1fa56ecc0bcc) | 链路追踪与日志 trace_id 一致，验证了 500 错误由运行时退出导致 |

上述证据表明应用服务在处理 `/work` 请求时发生了未捕获的异常，导致返回 HTTP 500 并使 Python 进程以退出码 2 终止。Kubernetes 检测到该异常后，依据重启策略不断尝试恢复，从而形成了 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /work 端点存在运行时逻辑错误 → 处理请求返回 HTTP 500 并触发进程崩溃 → 容器退出码 2，Kubernetes 检测到重启失败并进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用代码在处理 `/work` 端点请求时发生了未捕获的内部运行时错误。

该错误直接导致了两个后果：
1. 请求处理失败并返回 HTTP 500（证据来源：Logging #5, Tracing #6）。
2. Python 进程因崩溃以退出码 2 终止（证据来源：Logging #5, K8s State #3）。

Kubernetes 依据重启策略不断尝试重启该容器，但由于底层应用逻辑错误未被解决，导致容器反复崩溃，最终 K8s 状态进入 CrashLoopBackOff（证据来源：K8s State #1, #2, #4）。

**局限性**：当前证据无法确定导致上述错误的**具体代码级异常类型**（如特定 Python 模块的 ValueError 或 KeyError）以及完整的**异常堆栈跟踪（Stack Trace）**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 21.4s
├─ 并发证据采集: 74.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 74.2s (Evidence 62.4s, RCA 11.7s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
