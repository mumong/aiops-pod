## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 定义中引用了不存在的 PersistentVolumeClaim (PVC) 'unavailable-claim'，导致 Kubernetes 调度器因无法绑定存储卷而持续将 Pod 保持在 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 25m default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 直接表明调度失败的具体原因为找不到指定的 PVC，且持续发生。 |
| 2 | K8s State | kubernetes | `PodScheduled condition: status=False, reason=Unschedulable, message: persistentvolumeclaim "unavailable-claim" not found.` | 证实 Pod 状态长期处于 `Unschedulable`，与事件记录的故障机制一致。 |
| 3 | K8s State | kubernetes | `Pod phase: Pending` | 确认 Pod 尚未被调度，物理资源未分配，解释了为何无法采集日志。 |
| 4 | K8s Config | kubernetes | `container resource_limits: cpu=50m, memory=32Mi` | 作为上下文证据，排除因 CPU 或内存资源不足导致调度失败的可能性。 |
| 5 | Metric | prometheus | `kube_pod_status_phase[phase=PendTime]=1` | 从指标侧佐证 Pod 当前处于 Pending 状态，未发现 Failed 状态的计数（`phase=Failed` 值为 0）。 |

当前调度失败的根本原因由 K8s 事件明确指向：缺少 PVC `unavailable-claim`。由于 Pod 卡在调度阶段，`logging` 与 `tracing` 维度均因容器未启动而无法采集（`pod_ip` 为空），这与 Pod 长期处于 `Pending` 状态的事实一致，未产生额外阻碍。

## 🎯 根因分析 · g1

### 因果链
```text
应用定义引用不存在的 PVC 'unavailable-claim' → Kubernetes 调度器无法绑定存储卷 → Pod 调度失败 (Unschedulable) → Pod 保持 Pending 状态，持续拒绝调度
```

### 根因结论
已确认的根因为：应用 Pod 定义中引用了一个在当前集群中不存在的 `PersistentVolumeClaim`（名为 `unavailable-claim`）。
证据表明，Kubernetes 调度器（default-scheduler）因无法找到该 PVC，明确拒绝了 Pod 的调度请求（`FailedScheduling`），导致 Pod 无法分配节点，从而一直处于 `Pending` 状态。证据支持（事实 1、事实 2）充分证实了这一机制。

---

## 📊 性能统计

```text
├─ 总耗时: 54.4s
├─ 问题定位: 17.1s
├─ 并发证据采集: 29.4s
│  └─ g1 aiops-case-v03/workload: 29.4s (Evidence 24.4s, RCA 5.0s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
