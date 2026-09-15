## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，持续重启退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 50s (x112 over 25m) kubelet Back-off restarting failed container app` | 确认容器崩溃触发了 Kubernetes 的指数退避重启策略（证据支撑 CrashLoopBackOff 状态）。 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 2` | 确认容器是以错误状态码 2 异常退出的，这是应用层崩溃的直接表现。 |
| 3 | Logging | elasticsearch | `runtime process exiting`, `http_status: 500`, 关联 trace `0a2f7e93d108d5996daca00874df4884` | 证实应用进程在收到请求后主动终止，并记录了明确的退出信息，属于应用内部错误导致。 |
| 4 | Metrics | prometheus | `kube_pod_container_status_last_terminated_reason: 1` (reason=Error), `kube_pod_container_status_waiting_reason: 1` (reason=CrashLoopBackOff) | 独立验证了容器的退出原因为 Error，且当前处于等待重启的 BackOff 阶段。 |

**证据关联说明：**
Kubernetes 事件的 BackOff 警告与 Metrics 状态完全印证了 Pod 处于持续重启失败中。日志 `runtime process exiting` 为 K8s 中 Exit Code 2 提供了具体原因解释（应用主动退出而非被 OOMKilled 等外部强制结束）。目前仅能确认是应用进程内部异常退出，但缺乏代码堆栈或详细的 Trace 数据。

## 🎯 根因分析 · g1

```text
应用进程内部异常 (Exit Code 2) → 应用进程主动终止 (runtime process exiting) → 容器重启触发 BackOff 策略 → Pod 处于 CrashLoopBackOff 状态
```

**根因结论：**
已确认根因为：**应用进程 runtime 异常退出**。
Pod `workload-7679bcf76-n5vp8` 的应用容器 `app` 持续崩溃退出（Exit Code 2），触发 Kubernetes 指数退避重启机制，导致 Pod 处于 `CrashLoopBackOff` 状态。
- 证据 `fact-1809f157bb19` (exit_code 2) 与 `fact-7f29f52b1580` (日志 "runtime process exiting") 共同指向应用代码层或运行时的具体异常。
- 缺失决定性事实：具体的应用内部异常堆栈信息，以及对应 trace_id `0a2f7e93d108d5996daca00874df4884` 的完整链路失败点，阻碍了对具体代码逻辑或输入导致崩溃的精确定位。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.2s
├─ 并发证据采集: 85.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 85.9s (Evidence 76.5s, RCA 9.3s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
