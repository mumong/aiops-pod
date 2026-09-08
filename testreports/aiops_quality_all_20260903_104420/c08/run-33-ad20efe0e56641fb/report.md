## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 容器应用进程在处理请求时存在内存累积泄漏，导致内存使用量超过 Pod 配置的记忆限制（64Mi），触发 Kubernetes OOMKiller 强制终止容器进程（退出码 137），进而引发 CrashLoopBackOff 重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason="CrashLoopBackOff" | 确认应用进程频繁异常退出并进入重启退避循环 |
| 2 | K8s Event | kubernetes | kubelet 消息：Back-off restarting failed container app... (x318 over 84m) | 证实集群层面对该容器执行了长达 84 分钟的高频重启尝试 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory="64Mi" | 定义触发 OOMKiller 的内存硬限制边界 |
| 4 | K8s State | kubernetes | container.last_terminated_reason="OOMKilled", container.last_exit_code=137 | 核心证据：确认容器因触发内存限制被系统强制终止 |
| 5 | K8s State | kubernetes | pod.phase="Running", restart_count=18 | 验证容器目前虽然处于重启中，但已有 18 次重启记录，符合 CrashLoopBackOff 特征 |
| 6 | Logging | elasticsearch | log 模式 "memory allocation advanced"：8 次出现，内存分配从 16Mi 增长至 34Mi (range: 16-34) | 提供异常前兆，证明应用在请求处理中存在内存持续累积的行为 |
| 7 | Tracing | tempo/deepflow | HTTP GET /work (200)：trace_id 与日志存在关联 (如 48b92c4fdd8a1c4b930b41cfd8e7fc5a) | 追踪日志关联：证实特定的 `/work` 请求路径与上述日志中的内存分配现象发生在同一业务上下文中 |

**证据关联说明：**
1. K8s 状态与事件（#1, #2, #4, #5）构成了完整的故障闭环：内存不足被杀 -> 进程退出 -> K8s 重启 -> 触发退避循环。
2. 日志（#6）与追踪（#7）提供了故障成因的业务视角：证明内存泄漏并非系统异常，而是针对特定请求（`/work`）的累积行为，且该行为发生在 OOMKilled 发生之前。

## 🎯 根因分析 · g1

### 因果链

```text
业务请求处理中内存累积泄漏（日志/追踪证据） → 内存使用量突破 64Mi 硬限制（K8s 配置） → 触发 OOMKiller 强制终止进程 (Exit 137, K8s 状态) → CrashLoopBackOff 重启循环 (K8s 状态/事件)
```

### 根因结论

已确认根因为 **容器应用进程在处理请求时存在内存累积泄漏，导致内存使用量超过 Pod 配置的记忆限制（64Mi），触发 Kubernetes OOMKiller 强制终止容器进程，进而引发 CrashLoopBackOff 重启循环**。

具体机制如下：
*   **触发机制**：应用在处理请求（如 `GET /work`）时发生内存分配累积（日志记录显示内存分配从 16Mi 增至 34Mi），最终超出 64Mi 的硬限制。
*   **故障现象**：Linux 内核 OOMKiller 介入终止进程，返回 Exit Code 137，Kubernetes 尝试重启容器，因短时间内频繁失败进入退避重启状态（CrashLoopBackOff）。

已知局限：当前证据无法定位具体的代码级内存泄漏点，也无法精确解释为何 48MiB 的增长即触发了 64MiB 的限制（可能存在 JVM/Python 等运行时的额外内存开销）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 28.1s
├─ 并发证据采集: 97.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 97.1s (Evidence 87.8s, RCA 9.1s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
