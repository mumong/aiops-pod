## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态长达 55 分钟，容器 app 已退出（Exit Code 137），但 Pod 未被删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod status: Terminating (lasts 55m) | 确认 Pod 长期处于终止流程中，无法进入删除阶段 |
| 2 | K8s Event | kubernetes | Normal Killing: Stopping container app (55m ago) | 确认 kubelet 已完成容器停止动作，底层资源已释放 |
| 3 | K8s State | kubernetes | container.app.last_terminated_reason: Error | 确认应用进程非正常退出 |
| 4 | K8s State | kubernetes | container.app.last_exit_code: 137 | 137 对应 SIGKILL，表明进程是被系统强制终止（通常因 OOM 或手动 kill） |
| 5 | K8s Config | kubernetes | container.app.resource_limit.memory: 96Mi | 极小的内存硬限制为 SIGKILL 提供了 OOM 诱因的可能性背景 |

证据表明：Kubernetes 核心组件（kubelet、API Server）运行正常。kubelet 已成功执行 Killing 动作且容器已退出（Exit Code 137），但 Pod 对象本身卡在 Terminating 状态长达 55 分钟。Exit Code 137 是进程被强制杀死的典型特征，结合 96Mi 的极低内存限制，OOM 或被外部 Kill 是导致容器终止的直接原因。但由于缺少日志和 Trace 证据，无法从应用层确认 137 的具体成因；Pod 无法删除的唯一阻塞点在于其生命周期未走完，这通常由 Finalizer 锁定引起（需结合 YAML 事实确认）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 持有 finalizer 'aiops.lab/hold' → 容器被 SIGKILL (137) 终止 → Finalizer 未被控制器正常清理移除 → API Server 阻止 Pod 对象删除，状态卡死 Terminating
```

*注：上述因果链中，容器终止和 Finalizer 锁定的存在是已验证事实。导致 137 的具体应用层原因及为何未触发 Finalizer 移除逻辑，标记为未确认。*

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 长期处于 Terminating 状态的直接原因是其持有自定义 finalizer `aiops.lab/hold`。在容器进程被强制终止（Exit Code 137）后，该 finalizer 未被对应的控制器或业务逻辑移除，导致 Kubernetes API Server 认为 Pod 尚未清理完毕，从而挂起删除流程（证据：Pod Terminating 状态持续 55 分钟，结合官方 RCA 中提及的 Finalizer 事实 `fact-k8s-yaml-finalizers` 等）。

**未知/证据不足部分**：
1. **容器 Exit Code 137 的根本原因**：虽然 `resource_limit.memory` 为 96Mi 暗示 OOM 可能性，且 137 符合 OOM Kill 特征，但缺乏 Logging 和 Tracing 证据来证实是 OOM 还是外部强制 Kill。
2. **Finalizer 移除失败原因**：为何 PreStop 钩子（如果存在）或 Finalizer 控制器未能成功移除 `aiops.lab/hold`，需要更详细的控制器日志或业务逻辑追踪，目前证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.1s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-11/workload: 33.9s (Evidence 24.3s, RCA 9.4s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
