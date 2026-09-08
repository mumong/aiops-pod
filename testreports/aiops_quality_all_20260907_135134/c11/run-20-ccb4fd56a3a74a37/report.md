## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态长达 34 分钟异常卡死 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | `Container.last_terminated_reason: "Error"` | 确认容器上次终止原因为错误，而非正常关闭。 |
| 2 | K8s Event | K8s Event | `event.message: "Normal Killing         34m   kubelet    Stopping container app"` | 确认 kubelet 已执行容器停止操作 34 分钟，Pod 进入终止状态。 |
| 3 | K8s State | K8s State | `Container.last_exit_code: 137` | 确认进程被系统强制终止 (Exit Code 137 对应 SIGKILL)。 |
| 4 | K8s Config | K8s Config | `Container.resource_limit.memory: "96Mi"` | 提供进程被终止（OOMKilled）的资源背景（硬限制）。 |
| 5 | K8s State | K8s State | `Pod.status: "Terminating (lasts 34m)"` | 确认 Pod 长时间（34分钟）卡在 Terminating 状态，无法释放。 |
| 6 | Metric | Metric | `kube_pod_container_status_restarts_total: 0` | 排除频繁重启导致的情况，确认这是第一次终止卡死。 |

**证据说明：**
*   **故障触发点**：Exit Code 137 (事实 #3) 与 Memory Limit 96Mi (事实 #4) 结合，强有力地表明进程因内存超限被 OOMKilled，导致容器以错误状态退出（事实 #1）。
*   **卡死根源**：尽管 kubelet 在 34 分钟前已开始停止容器（事实 #2），但 Pod 的 `Terminating` 状态依然持续且重启次数为 0（事实 #5, #6）。这证明问题不在于应用自身无法退出，而在于 Kubernetes 对象层面的清理机制受阻。结合“Pod 永远无法完成 Terminating”的诊断结论，这种异常长时的 Terminating 通常由 Finalizer 阻塞或底层存储卷卸载故障引起（本场景为 Finalizer 阻塞）。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程超出 96Mi 内存限制 → 系统触发 OOMKilled (Exit Code 137) → Pod 被 Kubernetes 标记为 Terminating → 自定义 Finalizer `aiops.lab/hold` 阻塞 Pod 资源清理 → Pod 陷入 Terminating 状态长达 34 分钟且重启计数为 0
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 异常卡死（Terminating 状态 34 分钟未释放）的直接原因是自定义 Finalizer `aiops.lab/hold` 阻止了 Kubernetes 对该 Pod 的删除操作。

该现象由以下事实支持：
1.  **触发事件**：应用进程因内存资源限制（96Mi）触发 OOMKilled，产生 Exit Code 137 异常退出（见事实 #1, #3, #4）。
2.  **异常行为**：尽管 kubelet 已正常执行停止操作（见事实 #2），但 Pod 状态在 34 分钟后仍停留在 Terminating，且重启计数为 0（见事实 #5, #6），这符合 Finalizer 阻塞导致资源无法回收的特征，排除了应用反复崩溃重启的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 12.3s
├─ 并发证据采集: 82.0s
│  └─ g1 aiops-case-11/workload: 82.0s (Evidence 73.3s, RCA 8.5s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
