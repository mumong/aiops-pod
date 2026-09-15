## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload (aiops-case-v03) is in Pending state; scheduler repeatedly fails to schedule. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod status | `Pending` | 确认 Pod 未能被调度，停留在等待状态。 |
| 2 | K8s Event | scheduler events | `FailedScheduling 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接指示调度器因找不到指定的 PVC 而失败。 |
| 3 | Metric | kube_pod_status_phase | `Pending: 1` (single sample) | 从监控侧验证 Pod 当前确处于 Pending 状态。 |

调度器日志明确指出“persistentvolumeclaim 'unavailable-claim' not found”，这是导致 Pod 无法调度至任何节点的唯一阻塞原因，监控数据进一步印证了该状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
PVC 'unavailable-claim' 不存在于 namespace 'aiops-case-v03' 中 → 调度器无法绑定 Volume，拒绝调度 → Pod 状态持续为 Pending，触发 FailedScheduling 事件 → 用户无法访问该工作负载
```

### 根因结论

根因确认为：Pod `workload` 引用了一个在命名空间 `aiops-case-v03` 中不存在的 PersistentVolumeClaim `unavailable-claim`。
这一配置错误直接导致 Kubernetes 调度器无法完成卷绑定步骤，从而反复抛出 `FailedScheduling` 事件，使 Pod 永远处于 Pending 状态。证据链完整且闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 58.2s
├─ 问题定位: 19.8s
├─ 并发证据采集: 33.1s
│  └─ g1 aiops-case-v03/workload: 33.1s (Evidence 26.5s, RCA 6.5s)
└─ 汇总总结: 5.3s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
