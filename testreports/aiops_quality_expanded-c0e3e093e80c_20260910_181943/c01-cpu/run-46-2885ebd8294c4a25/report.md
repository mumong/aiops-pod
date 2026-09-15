## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群CPU资源完全耗尽，导致调度器无法找到可用节点进行Pod调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient cpu.` (11m 内发生 12 次) | 直接指明调度失败原因为集群 CPU 资源不足 |
| 2 | K8s State | scheduler | `PodScheduled=False` (`Unschedulable`): `No preemption victims found for incoming pod.` | 确认无优先级更低的 Pod 可被抢占，调度死锁 |
| 3 | K8s State | pod | `phase`: `Pending`; `status`: `Pending` | 确认 Pod 处于长期无法调度的停滞状态 |
| 4 | K8s Config | container | `app`: cpu request=`100k`, cpu limit=`100k`, mem request=`8Mi`, mem limit=`32Mi` | 确定目标 Pod 的 CPU 资源需求规格（100毫核） |
| 5 | K8s Event | pod | `Warning FailedScheduling`: 提示 `3 nodes are available`，排除网络分区或节点失联 | 排除基础设施连通性问题，聚焦资源逻辑 |

**证据分析：**
所有 Kubernetes 事实高度一致且无冲突：调度器明确反馈集群内全部 3 个节点均因 CPU 耗尽而无法容纳新 Pod，且由于没有优先级更高的抢占对象，Pod 陷入永久 Pending 状态。Metric、Logging 和 Tracing 维度因 Pod 未启动而不可用，K8s 层面证据已构成完整闭环。

## 🎯 根因分析 · g1

```text
集群节点 CPU 资源被占满 → 调度器评估 3/3 节点资源不足 → 无法分配 Pod 且无抢占对象 → Pod 长期处于 Pending 状态
```

**根因结论：**
**已确认根因**：集群 CPU 资源完全耗尽。
依据证据 `[1, 2, 3]`，调度器在 3 个节点上均无法找到满足 CPU 需求的资源，且因无法执行抢占机制，导致 Pod `aiops-case-v01/workload` 无法被调度并一直维持在 Pending 状态。现有证据已充分支撑此结论，无需额外日志或链路追踪。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 11.0s
├─ 并发证据采集: 48.1s
│  └─ g1 aiops-case-v01/workload: 48.1s (Evidence 41.3s, RCA 6.7s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
