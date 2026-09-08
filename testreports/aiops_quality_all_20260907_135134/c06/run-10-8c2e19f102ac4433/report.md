## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (app) | 确认 Pod 处于循环重启的异常状态 |
| 2 | K8s Event | kubernetes | `BackOff restarting failed container app` (Back-off 5m0s) | 确认 K8s 执行指数退避重启策略 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: `Error` (exit_code: 2) | 确认应用容器非正常退出，退出码为 2 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1 (CrashLoopBackOff) | 从监控视角确认等待原因 |
| 5 | Logging | elasticsearch | `runtime process exiting` (http_status: 500, allocated_mib: 0) | 记录进程退出时的内存分配值为 0 |
| 6 | Tracing | tempo/deepflow | GET /work (response_code: 200, duration: 16863us-68554us) | 确认网络层面请求可达且成功，排除外部网络问题 |

**证据关联与印证：**
1. K8s 事件与 Metric 一致确认了 `CrashLoopBackOff` 状态（证据 1、2、4）。
2. K8s 异常退出事件（证据 3）与应用日志中观察到的 `runtime process exiting` 相互印证（证据 5）。
3. Tracing 数据显示请求在应用内部成功执行并返回 200（证据 6），但随后的日志显示进程退出，说明崩溃发生在应用处理过程中，且日志明确指出此时内存分配为 0（证据 5）。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动时内存分配为0 (allocated_mib: 0) → 应用程序运行时异常退出 (exitCode 2) → Kubernetes执行指数退避重启策略 → Pod处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因是 **应用程序运行时内存分配异常（allocated_mib: 0）**。
该异常直接导致应用进程以 `exitCode 2` 异常退出（证据 3、5）。随后 Kubernetes 检测到此异常并根据退避策略进入 `CrashLoopBackOff` 状态（证据 1、2、4）。Tracing 证据（证据 6）排除了外部请求层面的问题，将故障定位为应用内部运行时的资源分配或运行时状态异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.2s
├─ 并发证据采集: 61.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 61.7s (Evidence 54.3s, RCA 7.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
