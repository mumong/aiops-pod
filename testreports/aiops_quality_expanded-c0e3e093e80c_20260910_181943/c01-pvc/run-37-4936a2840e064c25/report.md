## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload in aiops-case-v03 is stuck in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`：`0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (fact-bd0cb553af80) | 直接表明调度器因找不到 PVC 而拒绝调度 |
| 2 | K8s State | kubernetes | Pod `aiops-case-v03/workload` 当前状态为 `Pending` (fact-9f5c641fd6b8) | 证实 Pod 处于停滞状态，未进入 Running 阶段 |
| 3 | Metric | prometheus | `kube_pod_status_phase` 值为 1 (Pending)，无 Failed 或 Running 样本 (fact-16d09fa0c748) | 从指标侧确认 Pod 持续停留在 Pending 阶段 |

## 🎯 根因分析 · g1

### 因果链

```text
PVC 'unavailable-claim' 不存在于 namespace aiops-case-v03 → 调度器无法完成卷绑定 → Pod 无法分配节点，维持在 Pending 状态 → 用户观察到 Pod 停滞且收到 FailedScheduling 警告事件
```

### 根因结论

**已确认的根因：Pod 引用了不存在的 PersistentVolumeClaim (`unavailable-claim`)。**

事实证据显示，Pod `aiops-case-v03/workload` 在调度过程中因 `persistentvolumeclaim "unavailable-claim" not found` 被 `default-scheduler` 拒绝调度（证据 #1）。Pod 的状态维持在 `Pending` 且无任何节点可供分配（证据 #2, 证据 #3），这符合因 PVC 缺失导致调度失败的典型行为。由于 Pod 未启动，日志和追踪数据不可用，当前 Kubernetes 事件与状态事实足以支持该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 51.0s
├─ 问题定位: 16.6s
├─ 并发证据采集: 28.0s
│  └─ g1 aiops-case-v03/workload: 28.0s (Evidence 21.2s, RCA 6.8s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
