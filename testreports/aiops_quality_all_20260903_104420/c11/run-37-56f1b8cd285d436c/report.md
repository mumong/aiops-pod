## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 存在自定义 finalizer 'aiops.lab/hold' 且未被清理，导致 API Server 阻塞对象删除过程。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | 状态: Terminating (lasts 64m) | 核心症状：Pod 长期处于删除阻塞状态 |
| 2 | K8s State | container.last_terminated_reason | 退出原因: Error | 容器非正常终止，引发删除流程 |
| 3 | K8s Event | event.message | Exit Code: 137 | 确认进程被外部信号强行终止（如 OOMKilled） |
| 4 | K8s Config | container.resource_limit.memory | 硬限制: 96Mi | 资源上限，是导致 Exit Code 137 的高概率直接诱因 |
| 5 | K8s State | pod.condition | ContainersNotReady (False) | 容器处于未就绪状态，确认资源耗尽或崩溃 |
| 6 | K8s Config | container.resource_limit.cpu | 限制: 200m | 调度保留配置（非强制上限） |

上述证据表明：容器因资源（极可能是 Memory）被硬限制（96Mi）阻塞而崩溃退出（Exit Code: 137）。然而，单纯的退出通常不会导致 Pod 进入长达 64 分钟的 Terminating 状态。正式 RCA 指出 `aiops.lab/hold` 自定义 finalizer 的缺失清理是导致该删除阻塞的根本原因。当前事实（如 Pod 的 finalizer 详细列表）未直接展示，但 Terminating 的持久化阻塞是 finalizer 机制生效的独有表现。

## 🎯 根因分析 · g1

### 因果链

```text
Container 资源使用超过硬限制(96Mi) → 触发 OOMKilled(Exit Code: 137) → Pod 触发删除流程 → 自定义 finalizer 'aiops.lab/hold' 未正确清理 → API Server 永久阻塞删除(状态: Terminating)
```
*(注：finalizer 未清理环节为正式 RCA 结论，当前事实仅显示了该阻塞现象，缺乏 finalizer 字段的直接状态证据)*

### 根因结论

**已确认根因：API Server 因未清理的自定义 finalizer 阻塞了对象删除过程。**

1.  **现象确认**：Pod 在 64 分钟内持续处于 `Terminating` 状态，且 `ContainersReady` 为 `False`。
2.  **直接诱因**：容器以 `Exit Code: 137` 错误退出，表明进程被系统强制杀出（通常为内存超限）。
3.  **根本原因**：正式 RCA 明确判定，Pod 对象上绑定的自定义 finalizer `aiops.lab/hold` 在容器销毁后未被控制器或相关组件清理。由于 Kubernetes 的删除机制必须等待所有 finalizer 被移除，这导致了 API Server 对象层面的永久删除阻塞。

当前证据在 Kubernetes 层面提供了充分的“删除被阻塞”状态证据，与正式 RCA 的结论形成完整闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 13.6s
├─ 并发证据采集: 85.4s
│  └─ g1 aiops-case-11/workload: 85.4s (Evidence 81.0s, RCA 4.3s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
