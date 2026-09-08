## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod被自定义finalizer 'aiops.lab/hold' 阻塞，尽管容器因OOM killed（exitCode=137）终止，但finalizer阻止了Pod进入Terminated状态，导致处于Terminating Stuck。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.condition`: Ready=False (ContainersNotReady); `container.last_terminated_reason`: Error; `container.last_exit_code`: 137 (E137) | 确认容器因 OOM Kill 崩溃终止且 Pod 处于不可用状态 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_request.memory`: 24Mi | 容器内存硬限制极低（96Mi），构成 OOM 高风险背景 |
| 3 | K8s State | Kubernetes | `fact-f9207a33d024`: `container.last_exit_code` 为 137; `fact-29d591deb0e5`: `container.resource_limit.memory` 为 96Mi | 直接关联 SIGKILL 信号与低内存限制事实 |
| 4 | Logging | Elasticsearch | `log.message` 模式 `request completed` 持续成功；`allocated_mib`: first 0, last 0 | 显示崩溃前业务流量正常处理，内存分配量始终为 0 |
| 5 | Tracing | Deepflow/Tempo | `GET /work` 耗时 3.6ms-19.6ms, HTTP 200, trace_ids 与日志匹配 | 验证业务逻辑本身未发生异常耗时或报错 |
| 6 | K8s State | Kubernetes | `diagnostic_status`: "Terminating" (诊断描述提及) | 指出 Pod 虽崩溃但资源对象卡在清理阶段，未真正销毁 |

**证据小结**：Kubernetes 状态与日志、链路显示应用运行正常但容器发生异常终止（OOM Kill）。虽然 exitCode 137 指向 OOM，但 `allocated_mib` 为 0 且内存限制极低，OOM 是合理的崩溃原因。然而，决定当前系统不可用（Terminating Stuck）的关键矛盾在于：Pod 对象因 `aiops.lab/hold` Finalizer 未清除而被 API Server 阻止进入 Terminated 状态，导致集群层面呈现“僵死”而非“崩溃重试”。

## 🎯 根因分析 · g1

```text
容器内存限制过低(96Mi) → OOM Killer终止进程(exitCode=137) → Finalizer 'aiops.lab/hold' 阻止对象销毁 → Pod对象卡在 Terminating 状态，资源无法回收，集群呈现 Terminating Stuck
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 处于 **Terminating Stuck** 状态，根本原因在于存在自定义 Finalizer **`aiops.lab/hold`** 且未被清理。

*   **现象解释**：虽然容器因内存限制过低（96Mi）触发了 OOM Kill（退出码 137），但 Kubernetes 的 Garbage Collection 机制无法移除该 Pod 对象，因为 Finalizer `aiops.lab/hold` 仍然挂载在 Pod 的 `metadata.finalizers` 中。这导致 Pod 即使已经崩溃，其资源对象仍保留在 API Server 中并显示为 Terminating，阻碍了集群资源的完全回收。
*   **引用证据**：
    *   容器崩溃事实：`exit_code=137` 和 `container.last_terminated_reason=Error` (证据 #1)。
    *   状态卡住事实：诊断信息中明确指出 `Pod被自定义finalizer 'aiops.lab/hold' 阻塞...导致处于Terminating Stuck` (证据 #6)。

**未确认因素**：
*   谁设置了 `aiops.lab/hold` Finalizer 及其未清理的具体触发原因。
*   导致容器收到 SIGKILL (exitCode=137) 的具体触发源（虽然 96Mi 限制极低，指向 OOM，但 `allocated_mib` 始终为 0，需进一步确认是否被外部强制干预）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 15.3s
├─ 并发证据采集: 86.3s
│  └─ g1 aiops-case-11/workload: 86.3s (Evidence 78.7s, RCA 7.5s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
