## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群所有可用节点CPU资源不足导致调度器无法为Pod分配节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `PodScheduled` 状态为 `False`，原因 `Unschedulable`，详细报错 `0/3 nodes are available: 3 Insufficient cpu` | 直接症状：集群 3 个可用节点均因 CPU 资源耗尽而无法调度该 Pod |
| 2 | K8s Config | Kubernetes | 容器 `app` 申请 `cpu=100k`，硬限制 `cpu=100k` | 上下文：Pod 所需的资源规格较小（0.1核），但集群已无法满足 |
| 3 | K8s Event | Kubernetes | `FailedScheduling` (14m x12 over 69m) `3 No preemption victims found for incoming pod.` | 过程证据：调度器已尝试运行近 1 小时并 12 次失败，且因无高占用 Pod 可抢占，调度彻底失败 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 | 现状确认：Pod 持续处于 Pending 状态，且该指标不可计算趋势 |

证据说明：
1. **现象与原因互为印证**：K8s 事件（#3）与 Pod 条件状态（#1）共同确认了 Pod 卡死在 Pending 状态是由于集群层面的 CPU 资源分配失败。
2. **资源对比**：尽管 Pod 申请的 CPU 极低（#2），但 3 个节点全量报错 `Insufficient cpu`（#1），表明故障根源在于节点资源整体枯竭，而非单 Pod 需求过高。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点整体 CPU 资源耗尽 → 调度器无法分配节点并无可抢占目标 → 3 个可用节点均拒绝分配 → Pod 状态变更为 Pending
```

### 根因结论

已确认的根因是：**集群所有可用节点 CPU 资源不足导致调度器无法为 Pod 分配节点**。

证据支持：
- Pod 因 `3 Insufficient cpu` 被 3 个节点同时拒绝，且触发 `FailedScheduling` 事件（#1, #3）。
- 调度器明确告知 `No preemption victims found`（#3），说明集群处于资源满负荷状态。
- Pod 持续处于 Pending 状态（#4）与调度失败的结论一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.4s
├─ 并发证据采集: 36.9s
│  └─ g1 aiops-case-v01/workload: 36.9s (Evidence 32.2s, RCA 4.6s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
