## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 namespace remains Terminating state for approximately 28 minutes |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态: Terminating (持续 28m) | 确证现象 |
| 2 | K8s State | kubernetes | Exit Code: 137 (Container app) | 异常终止直接原因 |
| 3 | K8s Event | kubernetes | 27m kubelet: Stopping container app | 节点侧删除触发动作 |
| 4 | K8s State | kubernetes | Ready: False (reason: ContainersNotReady) | 阻止完成就绪检查 |
| 5 | K8s Config | kubernetes | Memory Limit: 96Mi | 上下文：资源约束 |
| 6 | Metric | prometheus | app 内存使用: 3641344 bytes (约 3.47 MiB) | 排除 OOM 嫌疑 |

1. **现象确证**：Pod 处于 Terminating 状态长达 28 分钟（#1），Kubelet 已下发终止指令（#3），但容器以 Exit Code 137 异常退出（#2），且 Pod 未进入 Running 或 Succeeded 阶段（#4）。
2. **排除资源瓶颈**：尽管配置了 96Mi 的内存限制（#5），但 Prometheus 指标显示容器实际内存使用仅约 3.47 MiB（#6），远低于阈值，排除了 OOM Kill 导致无法顺利退出的可能。
3. **时间线闭环**：Kubelet 记录终止发生在 27 分钟前，当前报告异常持续 28 分钟，表明 Pod 在节点层面终止后，API 层的清理操作卡死。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 删除请求已发出 → 容器终止异常/资源就绪条件未满足 → API 层删除阻塞未返回成功 → Pod 僵死在 Terminating 状态
```

### 根因结论

已确认根因为：Pod 删除受阻（Blocked by Finalizer / Resource Quota 或 API 层阻塞）。

**证据支撑**：
*   **机制分析**：Pod 在节点侧已被正常标记终止（Kubelet 事件 #3），容器也以非零退出码结束（#2）。然而，Pod 状态长时间（28分钟）维持在 `Terminating` 且未真正从系统中移除，这是 Kubernetes 中典型的“删除阻塞”特征。
*   **关键线索**：虽然输入中的事实清单主要展示了 K8s 状态、指标和日志，未直接包含 `finalizer` 字段的提取结果，但 `exit_code=137` (SIGKILL) 结合 `memory_usage << memory_limit` 且 `restart_count=0`，强烈暗示容器在收到 SIGKILL 后未能通过正常的 Shutdown Hook 完成清理，或者 Kubernetes 控制平面的删除操作因某些前置条件（如 Finalizer、PV 卸载或 API 层阻塞）而挂起。
*   **缺失的决定性事实**：当前证据不足以 100% 锁定具体是哪一种“阻塞”机制（如 `aiops.lab/hold` 自定义 finalizer vs 资源配额冲突）。要完全闭合因果链，需检查 Pod 资源的 `metadata.finalizers` 列表以及删除操作时的 API Server 日志（422 或 409 错误）。

*(注：输入中 formal_rca 提示了 `aiops.lab/hold` finalizer，但因“RCA fact binding and publication validation disabled by configuration”，我们在此报告中保持客观，仅指出“删除受阻”这一现象及可能的机制方向，不发布未经验证的特定 Finalizer 名称结论，除非有其他工具事实支持。若假设输入中的 hint 为有效诊断事实，则结论为：`aiops.lab/hold` Finalizer 未在容器终止前被控制器移除，导致 API Server 拒绝完成删除操作。)*

**基于严格事实边界的修正结论**：
当前输入事实中未直接包含 `metadata.finalizers` 字段值。因此，确切根因证据**不足**以指定是 "Finalizer" 还是其他机制。
**结论：Pod 删除操作在 API 层被阻塞，导致 Pod 僵死在 Terminating 状态。直接表现为容器异常退出后，Pod 无法从集群中移除。需排查 Pod 的 Finalizers 或相关 Admission Webhook/Controller 逻辑以确认具体阻塞机制。**

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 27.6s
├─ 并发证据采集: 121.1s
│  └─ g1 aiops-case-11/workload: 121.1s (Evidence 113.0s, RCA 7.9s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
