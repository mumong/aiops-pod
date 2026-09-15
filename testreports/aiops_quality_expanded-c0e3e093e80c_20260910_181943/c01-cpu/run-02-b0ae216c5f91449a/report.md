## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态且无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling 103s default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod. | 确认调度失败及具体原因 |
| 2 | K8s State | kubernetes | PodScheduled=False, message="0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod." (2026-09-11T05:28:07Z) | 记录 Pod 调度状态失败的确切事实 |
| 3 | K8s State | kubernetes | phase="Pending" (Pod phase), status="Pending" (Diagnosis) | 确认 Pod 处于不可调度的最终状态 |
| 4 | K8s Config | kubernetes | container.app.cpu_request="100k", container.app.memory_request="8Mi" | 确定调度失败的资源需求上下文 |

**证据分析：**
Kubernetes 事件 (事实 1) 与 Pod 状态条件 (事实 2) 高度一致，共同指向 `Insufficient cpu` 和 `No preemption victims found` 两个核心约束。这表明集群不仅资源不足，且无法通过抢占释放资源。资源配置 (事实 4) 提供了需求端的数据，与事件中的原因相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有可用节点 CPU 资源耗尽 → 调度器拒绝调度且无抢占候选人 → Pod 处于 Pending 状态 (PodScheduled=False) → 用户可见 Pod 未运行
```

### 根因结论

已确认的根因是：**集群所有可用节点的 CPU 资源均已耗尽，且不存在可被抢占的 Pod 来释放资源**。

具体依据如下：
1.  **资源耗尽**：调度器报告 `0/3 nodes are available: 3 Insufficient cpu`，表明集群内所有节点均无法提供 Pod 所需的 CPU 资源（至少为 100k，见事实 4）。
2.  **无法动态调节**：报告 `No preemption victims found for incoming pod`，说明在当前集群状态下，没有优先级较低的 Pod 可以被抢占以腾出资源，导致 Pod 陷入永久 Pending 状态。

该结论由 Kubernetes 事件 (事实 1) 和 Pod 状态 (事实 2) 直接支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 58.6s
├─ 问题定位: 18.2s
├─ 并发证据采集: 31.9s
│  └─ g1 aiops-case-v01/workload: 31.9s (Evidence 23.8s, RCA 7.9s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
