## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 定义的 Volume 引用了不存在的 PersistentVolumeClaim (PVC) 'unavailable-claim'，导致调度器无法绑定存储资源，从而拒绝调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling ... persistentvolumeclaim "unavailable-claim" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (fact-019420983424) | 确认集群调度器无法找到 PVC 资源，直接拒绝 Pod 调度。 |
| 2 | K8s State | kubernetes | `PodScheduled`: status `False`, reason `Unschedulable`, message 同上 (fact-8cc70533a4ee) | 确认 Pod 实际状态被调度器标记为不可调度。 |
| 3 | K8s State | kubernetes | pod.phase: `Pending`, pod.status: `Pending` (fact-042ea1094708, fact-6aa61aa1db6b) | 确认 Pod 处于长期 Pending 状态，未进入运行阶段。 |
| 4 | Metric | prometheus | `kube_pod_status_phase`: phase `Pending` value `1`, phase `Unknown` value `0` (fact-9515d2fa48ec, fact-1a6e6902cdf1) | 指标数据与 Pod 真实状态一致，确认无其他隐藏的运行中实例。 |

**证据关联说明：**
K8s Event 中的具体报错信息（fact-1）精确解释了 K8s State 中 Pod 处于 `Unschedulable` 和 `Pending` 状态（fact-2, fact-3）的底层原因。Metric 数据（fact-4）在维度上完全印证了 Pod 当前的停滞状态，排除了 Pod 处于 CrashLoop 或 Unknown 状态的可能性。Logging 与 Tracing 维度因 Pod 未启动而物理不可达，不产生冲突证据。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义 Volume 引用不存在的 PVC 'unavailable-claim' → 调度器无法绑定存储资源 → 调度器返回 FailedScheduling → Pod 持续 Pending 且状态为 Unschedulable
```

### 根因结论
**已确认的根因：** 异常组 `g1` 中 `aiops-case-v03/workload` 的调度失败是由资源定义缺失引起的。

**证据支撑：**
1. **K8s Event (fact-1)** 与 **Pod Condition (fact-2)** 明确显示调度器因 `persistentvolumeclaim "unavailable-claim" not found` 而拒绝调度，且集群中没有抢占受害者（No preemption victims），排除了节点资源不足或抢占导致的失败。
2. **Pod State (fact-3)** 和 **Metric (fact-4)** 确认 Pod 因此长期停留在 `Pending` 状态，未进入任何运行或故障重启阶段。
3. 该结论直接对应 K8s 调度器的标准行为逻辑，证据充分且无冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 54.1s
├─ 问题定位: 18.2s
├─ 并发证据采集: 26.0s
│  └─ g1 aiops-case-v03/workload: 26.0s (Evidence 21.6s, RCA 4.3s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
