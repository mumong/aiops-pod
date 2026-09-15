## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，持续 FailedScheduling。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending` (fact-id: fact-dea0d6ce3c7c) | 确认当前异常实体处于等待调度的停滞状态 |
| 2 | K8s State | kubernetes | `pod.condition: PodScheduled=False`, reason `Unschedulable` (fact-id: fact-d087031fd1df) | 明确容器调度失败的底层条件 |
| 3 | K8s Event | kubernetes | `FailedScheduling`, 报错 `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` (fact-id: fact-1453056a396f) | 直接定位到调度失败原因是引用的 PVC 资源不存在 |
| 4 | Metric | prometheus | `kube_pod_status_phase` = `1` (`phase: Pending`) (fact-id: fact-a83fe9cb6046) | 从时序数据侧面印证 Pod 持续处于 Pending 阶段，且无 Completed/Succeeded 样本 |

**证据分析**：
K8s 维度提供了最直接的根因证据（事实 #2 与 #3），明确指出调度器在预检查阶段因为找不到名为 `unavailable-claim` 的 PVC 而无法将 Pod 分配到任何节点（0/3 nodes available）。Metrics 维度（事实 #4）确认了这一状态并非短暂的过渡态，而是在观测窗口内持续存在。Logging 和 Tracing 维度均为 `not_applicable`，因为 Pod 处于 Pending 状态且未绑定到节点，无法启动容器产生应用日志与流量追踪数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 PVC 'unavailable-claim' → 调度器在预检查阶段发现 Volume 绑定失败 → Pod 被判定为 Unschedulable (0/3 nodes available) → Pod 持续处于 Pending 状态，未启动
```

### 根因结论

已确认的根因为 **Pod Spec 中声明引用的 PersistentVolumeClaim 'unavailable-claim' 在当前命名空间（aiops-case-v03）中不存在**。

这一配置缺陷导致 K8s 调度器在调度前无法完成 Volume 绑定检查，从而判定所有 3 个节点均无法满足调度条件，直接导致 Pod 卡死在 Pending 状态（证据 #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.3s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-v03/workload: 45.0s (Evidence 37.1s, RCA 7.9s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable, pod-volume-mount-failed, pod-config-error
