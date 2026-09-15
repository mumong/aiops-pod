## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `workload` 的 YAML 定义中引用了名为 `unavailable-claim` 的 PersistentVolumeClaim (PVC)，但该 PVC 在当前 namespace `aiops-case-v03` 中不存在。由于调度器无法找到并绑定该卷，导致 Pod 持续处于 `Pending` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Pending (事实 ID: `fact-74915b10b31d`) | 确认 Pod 运行状态处于挂起阶段，未进入 Running |
| 2 | K8s State | kubernetes | `pod.condition`: PodScheduled=False, Reason=Unschedulable (事实 ID: `fact-c2392f1b2055`) | 明确调度器判定 Pod 无法被调度，给出具体失败原因 |
| 3 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found (事实 ID: `fact-1bb7d194925a`) | 直接定位到具体的失败实体：PVC `unavailable-claim` 在当前 Namespace 中缺失 |
| 4 | K8s Config | kubernetes | `resource_limit.memory`: 32Mi, `resource_request.memory`: 8Mi, `resource_limit.cpu`: 50m, `resource_request.cpu`: 5m (事实 ID: `fact-044aee04cbf3` 至 `fact-c9808da780ae`) | 确认计算资源请求合理且远低于集群容量，排除资源不足导致的调度失败 |
| 5 | Metric | prometheus | `kube_pod_status_phase` (Pending): 1 (事实 ID: `fact-3194a2f223b5`) | 通过 Prometheus 监控数据独立印证 Pod 持续处于 Pending 状态 |

**证据关联说明：**
K8s State 中的 `Unschedulable` 失败条件与 `FailedScheduling` 事件共同指向了同一阻塞机制：调度器无法解析 Pod 定义中的 PVC 依赖（事实 2 与 3）。资源配置事实（4）排除了节点资源竞争的可能性。Metric 观测结果（5）与 K8s 内部状态（1）在时间范围内高度一致，确认了异常状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
引用了不存在的 PVC "unavailable-claim" → 调度器无法完成卷绑定 → 调度失败 (Scheduling Failed) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod `workload` 的 YAML 定义中引用了一个在当前 Namespace `aiops-case-v03` 中不存在的 PersistentVolumeClaim（即 `unavailable-claim`）。由于调度器在尝试绑定该卷时无法找到对应的 PVC 对象，导致 Pod 被判定为 `Unschedulable`，从而一直停留在 `Pending` 状态，无法被调度到任何节点上。

---

## 📊 性能统计

```text
├─ 总耗时: 59.6s
├─ 问题定位: 16.2s
├─ 并发证据采集: 34.1s
│  └─ g1 aiops-case-v03/workload: 34.1s (Evidence 28.4s, RCA 5.6s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
