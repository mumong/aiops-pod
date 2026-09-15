## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 持续处于 Pending 状态，节点分配为 <none>。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`：0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found. | 确认调度器因 PVC 缺失拒绝调度 |
| 2 | K8s Config | kubernetes | Pod Spec 中引用 PVC `unavailable-claim` | 锁定导致调度的配置依赖项 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v03/workload` 状态 `Pending` | 确认故障当前状态为无法调度 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase=Pending) 值为 1；`kube_pod_status_phase` (phase=Failed) 值为 0 | 验证 Pod 处于调度阻塞阶段，未进入运行失败状态 |

K8s 事件明确指出调度失败的原因为 PVC `unavailable-claim` 未找到，直接印证了 Pod 配置中对不存在 PVC 的引用（证据 2）。Metric 数据显示 Pod 停留在 Pending 阶段（证据 4），与事件记录的原因和 Pod 状态（证据 3）完全一致，排除了容器运行时故障的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 PVC 'unavailable-claim' → default-scheduler 发现 Volume 依赖缺失 → 触发 FailedScheduling 事件 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod Spec 中引用了不存在的 PersistentVolumeClaim 'unavailable-claim’**（依据证据 2、1）。由于 PVC 缺失，`default-scheduler` 无法进行卷绑定与调度决策，导致 Pod 无法分配节点并长时间保持在 `Pending` 状态（依据证据 3、4）。现有证据链完整，无需补充其他维度信息。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.6s
├─ 并发证据采集: 45.7s
│  └─ g1 aiops-case-v03/workload: 45.7s (Evidence 36.6s, RCA 9.0s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
