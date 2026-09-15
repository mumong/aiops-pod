## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 引用了不存在的 PersistentVolumeClaim 'unavailable-claim'，导致调度器无法绑定存储卷，Pod 持续处于 Pending/Unschedulable 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `PodScheduled` 条件为 `False`，原因 `Unschedulable`，消息 `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接确认 Pod 因 PVC 缺失被调度器拒绝 |
| 2 | K8s State | kubernetes | `phase: Pending` | 确认 Pod 长期处于不可用状态 |
| 3 | K8s State | kubernetes | `container: app`，`cpu_request: 5m`，`memory_request: 8Mi` | 提供资源上下文，排除资源不足导致的调度失败 |

```text
PVC 'unavailable-claim' 不存在 → 调度器无法满足存储绑定要求 → Pod 持续 Pending → 集群无法提供该工作负载
```

- **证据印证**：K8s 的 `PodScheduled` 异常消息（#1）明确指出了根本原因是 `persistentvolumeclaim "unavailable-claim" not found`。
- **逻辑排他**：集群存在 3 个可用节点，且容器请求资源（5m CPU, 8Mi 内存）极低（#3），排除了节点资源耗尽或溢出导致的 `Unschedulable`。
- **限制说明**：因容器未能启动，日志（Logging）和链路追踪（Tracing）维度均无数据，但 K8s 控制平面状态已构成完整证据链。

## 🎯 根因分析 · g1

### 根因结论

**根因**：Pod 定义引用了不存在的 PersistentVolumeClaim `unavailable-claim`。

**分析说明**：
K8s 调度器在尝试绑定存储卷时发现 PVC `unavailable-claim` 不存在，导致无法满足调度条件，进而将 Pod 的 `PodScheduled` 状态置为 `False` 并保持在 `Pending` 状态。这一事实由 K8s 控制平面反馈的错误消息（#1）直接确认。

---

## 📊 性能统计

```text
├─ 总耗时: 59.5s
├─ 问题定位: 14.2s
├─ 并发证据采集: 38.5s
│  └─ g1 aiops-case-v03/workload: 38.5s (Evidence 33.2s, RCA 5.1s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
