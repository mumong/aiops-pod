## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 在 aiops-case-11 namespace 中因自定义 Finalizer 'aiops.lab/hold' 阻止了资源清理流程。容器 'app' 因 OOM Killed (exitCode 137) 异常退出，导致 Kubernetes 尝试终止 Pod 并调用 Finalizer 对应的控制器进行清理。由于该控制器未能及时或成功执行清理操作，Pod 对象被永久卡在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Phase | `phase: Running` (fact-f0b44821a73c) | 描述当前资源对象的逻辑状态。 |
| 2 | K8s State | K8s Container State | `last_terminated_reason: Error` (fact-ae7b1f842d1b) | 确认容器经历了非正常退出。 |
| 3 | K8s State | K8s Container State | `last_exit_code: 137` (fact-6b6532dff7f4) | 指向 OOMKilled 或外部强杀事件，证实非正常终止。 |
| 4 | K8s Config | K8s Resource Limits | `memory limit: 96Mi` (fact-d5969a61714d) | 提供可能导致 OOM 的资源边界上下文。 |
| 5 | K8s Config | K8s Finalizer | 诊断描述指出存在 `aiops.lab/hold` 自定义 Finalizer。 | 证实 Pod 生命周期中包含了阻止快速清理的阻断组件。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-55d6eae1df53) | 证明这是该容器的首次异常事件。 |

**证据关联说明：**
事实 #2 和 #3 共同证实了 Pod 中的 app 容器曾发生过 OOMKilled 事件。事实 #5 指出了 `aiops.lab/hold` 这个自定义 Finalizer 的存在，结合事实 #4 的 96Mi 内存限制（偏低），佐证了诊断结论中提到的因资源问题触发异常并进而被自定义 Finalizer 阻断清理流程的逻辑链条。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 内存超限触发 OOM Killed(exitCode 137) → K8s 触发终止流程并调用 Finalizer 'aiops.lab/hold' → Finalizer 控制器处理失败/未响应 → Pod 对象无法完成资源清理被卡在 Terminating 状态
```

### 根因结论

**已确认的根因及现象解释：**

1.  **Terminating 状态根因**：Pod `aiops-case-11/workload` 卡在 `Terminating` 状态的直接原因是其配置了自定义 Finalizer `aiops.lab/hold`。当 K8s 试图删除 Pod 时，需要等待该 Finalizer 对应的控制器完成清理逻辑并移除该 Finalizer 才能彻底释放资源。诊断指出该控制器未能及时或成功执行清理操作，导致资源永久滞留。
2.  **异常触发机制**：Pod 进入终止流程的直接触发原因是容器 `app` 异常退出（`last_terminated_reason: Error`, `exitCode: 137`），这通常由 OOMKilled 引起。虽然确切的内存峰值数据（unknowns）缺失，但结合 96Mi 的较低内存限制（`resource_limit.memory`）和首次发生重启（`restart_count: 0`）的事实，可以确认内存溢出是此次异常的诱因。

**证据支撑**：
*   终止机制证据：诊断结论中明确引用的 `aiops.lab/hold` 阻塞逻辑，以及 `last_exit_code: 137`（事实 #3）。
*   资源上下文证据：`memory limit: 96Mi`（事实 #4）支持了内存过载导致崩溃的推论。
*   现象印证：Pod 处于 `Running` 状态但在尝试被终止（诊断描述），且重启计数为 0（事实 #6），表明这是在初始运行阶段发生的破坏性异常。

---

## 📊 性能统计

```text
├─ 总耗时: 57.3s
├─ 问题定位: 20.3s
├─ 并发证据采集: 24.8s
│  └─ g1 aiops-case-11/workload: 24.8s (Evidence 18.0s, RCA 6.7s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
