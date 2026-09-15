## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，持续被调度器拒绝 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` (x11) | `FailedScheduling ... persistentvolumeclaim "unavailable-claim" not found.` (`fact-c6db384e2c0d`, `fact-d23550c49569`) | 确认 Pod 持续被调度器拒绝，直接归因于 PVC 缺失。 |
| 2 | K8s State | `pod.phase` | `Pending` (`fact-6c199204e9cd`) | 确认 Pod 未进入运行态，处于等待调度的阻塞状态。 |
| 3 | K8s State | `pod.condition` | `PodScheduled: False (Unschedulable)` (`fact-697c3f3fe589`) | 验证 Pod 的调度状态标记，表明 3 个节点均无法调度。 |
| 4 | Metric | `kube_pod_status_phase` | `1` (Pending) (`fact-2dcd29b366c7`) | 通过 Prometheus 指标独立确认 Pod 持续处于 Pending 阶段。 |
| 5 | K8s Config | `resource_request/limit` | CPU 请求 5m/限制 50m, 内存 8Mi/限制 32Mi (`fact-08c321b3ffc2` 等) | 排除资源配额超限导致的调度失败，确认问题不在算力。 |

证据表明 Pod 被调度器拒绝的唯一原因是 PVC 缺失（事实 1），指标（事实 4）确认该状态持续存在，且资源请求配置（事实 5）极低，排除了资源不足的可能性。

## 🎯 根因分析 · g1

```text
PVC 'unavailable-claim' 在当前 namespace 中不存在 → 调度器无法绑定 Volume → Pod 标记为 Unschedulable 并持续 Pending → 用户可见 Pod 状态卡死在 Pending
```

### 根因结论

已确认根因为**依赖的 PVC 'unavailable-claim' 缺失**（见证据 #1）。调度器因找不到指定的卷而拒绝调度，导致 Pod 状态持续为 Pending。Pod 资源请求极低且状态指标一致，进一步排除了集群资源耗尽等其他可能性，故障点明确指向 PVC 引用错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 25.9s
├─ 并发证据采集: 27.4s
│  └─ g1 aiops-case-v03/workload: 27.4s (Evidence 21.2s, RCA 6.0s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
