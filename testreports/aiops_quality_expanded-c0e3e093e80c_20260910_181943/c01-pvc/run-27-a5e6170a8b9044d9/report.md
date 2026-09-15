## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 持续 Pending 且未被调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (fact-459a337e49d4, fact-9532c6708169) | 直接指出调度失败原因：引用的 PVC 不存在 |
| 2 | K8s Config | kubernetes | `container "app" requests cpu=5m, memory=8Mi` (fact-08e811fe4d22) | 排除因资源请求过高导致无法调度 |
| 3 | K8s Config | kubernetes | `container "app" limits cpu=50m, memory=32Mi` (fact-750f1b5985a8) | 排除因资源限制配置错误导致无法调度 |
| 4 | K8s State | kubernetes | `Pod status: Pending` (fact-88ad87baed3c) | 确认 Pod 处于未调度状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase=1, phase="Pending"` (fact-686ef8689f7b) | 监控确认 Pod 持续处于 Pending 状态 |

K8s Event 明确指出因 PVC 缺失导致 FailedScheduling；Metric 数据从监控维度佐证了 Pod 持续 Pending 的客观状态；资源请求和限制配置极低，进一步排除了资源不足的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 PersistentVolumeClaim 'unavailable-claim' → 调度器校验阶段检测到 PVC 依赖缺失 → default-scheduler 触发 FailedScheduling 事件并拒绝调度 → Pod 保持 Pending 状态且无节点分配
```

### 根因结论

已确认的根因是：Pod `aiops-case-v03/workload` 的规格中定义了 `persistentvolumeclaim "unavailable-claim"` 作为卷依赖，但该 PVC 在当前集群命名空间中并不存在。这导致 `default-scheduler` 在调度前验证阶段发现依赖无法满足，从而拒绝将该 Pod 调度到任何节点，表现为持续 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 28.8s
├─ 并发证据采集: 47.7s
│  └─ g1 aiops-case-v03/workload: 47.7s (Evidence 39.6s, RCA 8.0s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
