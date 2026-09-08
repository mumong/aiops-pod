## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff，app 容器因处理 /work 请求时产生 500 错误并退出（exit code 2）而不断重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `CrashLoopBackOff` (fact-4a129d56e7a1) | 确认 Pod 持续重启且正在退避，是集群层面的主要可见状态。 |
| 2 | K8s State | `container.last_terminated_reason` | `Error` (fact-2a7c646cf12d) | 提供上一次容器终止的直接原因。 |
| 3 | K8s State | `container.last_exit_code` | `2` (fact-501e598a688a) | 证实进程异常终止（通常表示运行时错误或程序显式报错退出）。 |
| 4 | K8s Event | `BackOff` 事件 | `Back-off restarting failed container app` (fact-995bd02741c1) | 验证 K8s 正在根据退避策略处理失败的重启。 |
| 5 | Logging | `runtime process exiting` | `http_status 500` on `/work` (fact-046b66b804fc) | 揭示容器退出前的业务上下文，指出应用在收到 500 错误后主动退出。 |
| 6 | Metric | `kube_pod_container_status_last_terminated_reason` | `1` (Error) (fact-8af9dd40ee1b) | 独立验证了 K8s 层面的终止状态。 |
| 7 | Metric | `kube_pod_container_status_restarts_total` | `19` (fact-5d8b7dcf691b) | 量化重启频率，说明该问题已持续一段时间。 |
| 8 | Tracing | L7 Flow (Deepflow) | `GET /work` -> `500` 错误流 (fact-2bd0b7048628) | 证实外部流量确实收到了 500 响应，与日志中的错误码完全吻合。 |

**证据分析：**
*   **状态闭环：** `K8s State` (fact-1, 2, 3) 和 `Metric` (fact-6) 一致确认了容器以 Error 状态终止且频繁重启。
*   **根因指向：** `Logging` (fact-5) 和 `Tracing` (fact-8) 在逻辑上紧密关联，日志记录了应用内部在 `/work` 路径发生 500 错误并触发 `runtime process exiting`，而 `Tracing` 证实了 500 状态码真实发生。
*   **现象映射：** `K8s Event` (fact-4) 解释了为什么容器虽然频繁重启（`Metric` fact-7 显示 19 次），但 Pod 始终处于 `CrashLoopBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链
```text
业务代码处理 /work 请求时发生未捕获异常 (日志: http_status 500) → 进程执行退出逻辑 (日志: runtime process exiting) → 容器退出并返回非零状态码 (K8s: exit_code 2) → K8s 重启策略触发 (K8s: CrashLoopBackOff)
```

### 根因结论
**已确认的根因：** 应用业务逻辑在处理 `/work` 路径请求时发生异常，导致进程主动异常退出，进而触发 Kubernetes 的 CrashLoopBackOff 机制。

该结论由以下证据相互印证支持：
1.  **直接证据：** `K8s State` 明确记录容器以 `exit_code 2` 退出且原因为 `Error`（证据 #2, #3）。
2.  **上下文证据：** `Logging` 明确指出容器在发生 `http_status 500` 后执行了 `runtime process exiting`（证据 #5），直接关联了 500 错误与进程终止。
3.  **佐证证据：** `Tracing` 观测到针对 `/work` 的 `500` 错误流（证据 #8），确认了错误码的真实性。

**证据不足的部分：** 导致 `/work` 路径下产生 `http_status 500` 的具体内部代码逻辑、异常堆栈或依赖错误原因未在日志或追踪中记录（日志模式显示“未包含详细堆栈”），目前仅能确认是应用内部运行时错误导致退出。

---

## 📊 性能统计

```text
├─ 总耗时: 10.3m
├─ 问题定位: 37.0s
├─ 并发证据采集: 564.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 564.8s (Evidence 552.2s, RCA 12.4s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
