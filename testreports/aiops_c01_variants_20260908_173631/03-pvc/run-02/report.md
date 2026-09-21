## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，未被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 直接原因：调度器因 PVC 不存在而拒绝调度。 |
| 2 | K8s State | kubernetes | `PodScheduled`: `False`, reason=`Unschedulable` | 症状确认：Pod 处于 Pending 状态，调度器明确判定为不可调度。 |
| 3 | K8s Config | kubernetes | container: `app` 资源请求 `memory=8Mi`, `cpu=5m` | 排除资源不足：Pod 资源需求极低，集群资源不是导致调度的阻碍。 |
| 4 | K8s Config | kubernetes | container: `app` 资源限制 `memory=32Mi`, `cpu=50m` | 上下文参考：Pod 内存限制设置较低，但当前状态并非 OOM。 |
| 5 | Metric | prometheus | `kube_pod_status_phase` (Pending): `1` (样本数: 1) | 状态映射：Kubernetes 指标确认 Pod 持续处于 Pending 阶段。 |

**证据分析**：
K8s Event (Fact 1) 与 K8s State (Fact 2) 高度印证，明确指出了调度失败的直接原因是 PVC "unavailable-claim" 不存在。K8s Config (Fact 3, 4) 中的资源请求极小，结合 Metric (Fact 5) 的 Pending 状态，进一步排除了 CPU 或内存资源耗尽导致调度的可能性。日志和 Tracing 维度因 Pod 未启动而无数据，但不影响基于调度器侧事实的结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 声明挂载不存在的 PVC 'unavailable-claim' → default-scheduler 校验 PVC 绑定状态失败 → 调度器触发 FailedScheduling 事件并拒绝调度 → Pod 保持 Pending 状态且 nodeName 为 None
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v03/workload` 的 Pod Spec 中引用了名为 `unavailable-claim` 的 PersistentVolumeClaim，但该 PVC 在 `aiops-case-v03` 命名空间内不存在。这导致 `default-scheduler` 在调度阶段校验依赖失败，从而将 Pod 保持在 `Pending` 状态。

**证据引用**：
- Kubernetes Event 直接报错 `persistentvolumeclaim "unavailable-claim" not found`（见证据 #1）。
- Kubernetes State 确认 Pod 因 `Unschedulable` 条件被调度器拒绝（见证据 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 30.0s
├─ 并发证据采集: 31.4s
│  └─ g1 aiops-case-v03/workload: 31.4s (Evidence 24.2s, RCA 7.0s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
