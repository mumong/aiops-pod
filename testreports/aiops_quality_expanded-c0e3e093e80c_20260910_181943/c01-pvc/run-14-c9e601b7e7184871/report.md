## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `workload` 的 Spec 中定义了引用名为 `unavailable-claim` 的 PersistentVolumeClaim (PVC) 的 Volume，但该 PVC 在命名空间 `aiops-case-v03` 中不存在。这导致 default-scheduler 在调度阶段因无法绑定 PVC 而判定 0/3 节点可用，抛出 `FailedScheduling` 事件，Pod 因此卡在 Pending 状态且无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `fact-238d5a2710f2`: `FailedScheduling`, message=`0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 确认调度器因找不到指定 PVC 而判定所有 3 个节点不可用。 |
| 2 | K8s State | Kubernetes | `fact-afdb9a28b397`: Pod `workload` 状态 `PodScheduled=False`, reason=`Unschedulable`, message=`...persistentvolumeclaim "unavailable-claim" not found.` | 提供 Pod 级别的最终调度失败证据，与事件事实一致。 |
| 3 | Metric | Prometheus | `fact-1efda3a6e053`: `kube_pod_status_phase` 在 phase=`Failed` 的标签下值为 `0`。 | 确认 Pod 未发生 CrashLoopBackOff 等容器运行期故障，排除了容器内错误导致状态异常的可能。 |

证据间逻辑一致：K8s 事件与 Pod 状态在 `persistentvolumeclaim "unavailable-claim" not found` 这一错误信息上相互印证，共同指向调度失败；Metrics 提供的负面观测排除了容器运行层面的其他异常可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Spec 定义引用不存在的 PVC `unavailable-claim` → Scheduler 无法绑定 PVC 判定 0/3 节点可用 → Pod 持续处于 Unschedulable 状态 → Pod 卡在 Pending 状态
```

### 根因结论

已确认的根因为 Pod `workload` 的 Spec 中定义了引用名为 `unavailable-claim` 的 PVC，但该 PVC 在命名空间 `aiops-case-v03` 中不存在（证据 #1, #2）。这导致 `default-scheduler` 在调度阶段因无法绑定 PVC 而判定无可用节点，抛出 `FailedScheduling` 事件，使得 Pod 最终维持在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 59.0s
├─ 问题定位: 21.9s
├─ 并发证据采集: 29.9s
│  └─ g1 aiops-case-v03/workload: 29.9s (Evidence 22.1s, RCA 7.7s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
