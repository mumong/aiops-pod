## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，容器 app 持续以 exit code 2 崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (`fact-4dcd65091ac1`) | 确认 Pod 处于重启循环状态 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (持续 60m, x270) (`fact-d5ed51325c42`) | 证实 Kubelet 正在持续按指数退避重启 |
| 3 | K8s State | Kubernetes | `last_terminated_reason`: `Error`; `exit_code`: 2 (`fact-09290e0821bf`, `fact-7f2f6f0f7759`) | 确认进程因内部错误主动以 2 退出 |
| 4 | Logging | Elasticsearch | `error` 级别日志：`"runtime process exiting"`, 路径 `/work` (`fact-1b5987cca1f8` 等) | 直接记录运行时异常退出的事实 |
| 5 | K8s Config | Kubernetes | 资源限制：内存 96Mi, CPU 200m (`fact-2d85cb2367f5`, `fact-47ff747a92cf`) | 提供异常发生的资源上下文 |
| 6 | Metric | Prometheus | `restart_count`: 16 (`fact-82c54b1c2e57`) | 量化重启频率，与 K8s 状态一致 |
| 7 | K8s State | Kubernetes | `restart_count`: 16 (`fact-7c27e573fd96`) | 独立来源证实重启计数 |

**证据说明**：
日志 (证据 4) 确认应用进程因内部原因执行退出逻辑，K8s 状态 (证据 3) 证实该退出表现为 `exit code 2` 而非 OOMKill 或信号强制终止。两者结合锁定了根因为应用层内部异常。同时，Metric (证据 6) 和 K8s 状态 (证据 7) 在重启次数上完全一致，佐证了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码内部抛出未捕获异常 → 记录 "runtime process exiting" 并终止 → 容器进程以 exit code 2 退出 → Kubelet 触发 Back-off 重启策略导致 CrashLoopBackOff
```

### 根因结论

已确认的根因是**应用代码内部抛出未捕获异常导致运行时进程直接退出**。

这一结论由以下事实闭环支撑：
1.  **应用层直接记录**：日志明确捕获了 `runtime process exiting` 错误模式 (`fact-1b5987cca1f8`)，排除了 Kubernetes 层面的强制杀除（如 OOMKill 无相关事件）。
2.  **状态与退出码匹配**：K8s 状态显示 `last_terminated_reason` 为 `Error` 且 `exit_code` 为 2 (`fact-09290e0821bf`)，这通常对应应用程序主动报错退出的状态码，与日志信息完全吻合。
3.  **循环机制**：由于退出非外部资源限制导致（且资源限制仅 96Mi 并非极小），Kubelet 按照默认策略不断重启该容器，从而形成了持续的 `CrashLoopBackOff` 状态 (`fact-4dcd65091ac1`)。

缺失的决定性事实包括未捕获异常的具体代码堆栈和具体的触发数据，但这不影响确认“应用代码异常退出”这一根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.8s
├─ 并发证据采集: 65.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 65.1s (Evidence 54.4s, RCA 10.6s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
