## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload (aiops-case-v03) 处于 Pending 状态，无法调度至任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | `Pending` (fact_id: `fact-314e339bc2a5`) | 确认 Pod 未进入运行状态 |
| 2 | K8s Event | Scheduler Warning | `FailedScheduling ... persistentvolumeclaim "unavailable-claim" not found.` (fact_id: `fact-24542d6ea72d`) | 揭示 Pod 无法调度的直接原因：PVC 缺失 |
| 3 | K8s Event | Scheduler Warning | `FailedScheduling ... persistentvolumeclaim "unavailable-claim" not found.` (fact_id: `fact-d7ab7f60cbb0`) | 确认该 PVC 缺失问题在调度窗口期 (5m31s) 内持续存在 |
| 4 | Metric | Pod Status | `kube_pod_status_phase{phase="Pending"} = 1` (fact_id: `fact-febbd6d4ceed`) | 验证 Pod 处于 Pending 状态的实时指标 |

**证据关联说明**：
K8s Event 事实 (`#2`, `#3`) 提供了完整的调度拒绝理由，明确指出由于找不到 `unavailable-claim` PVC 导致调度失败。Metric 事实 (`#4`) 与 K8s 状态 (`#1`) 相互印证，表明该 Pod 在查询时刻仍维持在 `Pending` 状态，未因重试或其他机制恢复。由于 Pod 未能调度启动，Logging 和 Tracing 维度无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Volume 引用不存在的 PVC -> Scheduler 依赖校验失败 -> 返回 FailedScheduling 事件 -> Pod 状态为 Pending
```

### 根因结论

已确认根因：Pod `aiops-case-v03/workload` 的定义中引用了一个名为 `unavailable-claim` 的 PersistentVolumeClaim，但该 PVC 在集群中不存在。Kubernetes Scheduler 在调度过程中发现该存储依赖无法满足，因此将 Pod 标记为 `Unschedulable` 并持续生成 `FailedScheduling` 事件，导致 Pod 始终处于 `Pending` 状态。证据 `#2` (Event) 和 `#4` (Metric) 支持此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.6s
├─ 并发证据采集: 38.7s
│  └─ g1 aiops-case-v03/workload: 38.7s (Evidence 29.4s, RCA 9.3s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
