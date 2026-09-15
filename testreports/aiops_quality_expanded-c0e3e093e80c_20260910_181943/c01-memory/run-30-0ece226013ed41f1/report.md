## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | aiops-case-v02/workload处于Pending状态，无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` (fact-718be613e731, fact-7f7f60a02e69) | 直接展示调度器在 3 个节点上均因内存不足而调度失败，且无预emption 空间 |
| 2 | K8s Config | kubernetes | 容器 `app` 内存请求 `resource_request.memory` 为 `1Pi` (fact-51b652aa35c9) | 揭示 Pod 申请了极其庞大的内存资源，远超物理节点容量，是引发资源耗尽的根本原因 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v02/workload` 状态为 `Pending` (fact-1ad2de9481c5) | 确认 Pod 处于未调度状态，印证了调度失败的持续后果 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 显示 `Pending` 状态值为 1，且无 `Succeeded` 记录 (fact-c0ef18188030, fact-2e7f1231fbbd) | 通过监控指标确认 Pod 的 Pending 状态是持续存在的现实事实 |

**证据分析：**
K8s 事件与指标一致证实了 Pod 持续处于 Pending 状态且无法调度（#1, #3, #4）。K8s 配置事实揭示了调度失败的直接约束原因：容器配置了 `1Pi` 的内存请求（#2），这直接导致集群所有可用节点均无法满足资源需求（#1 中的 Insufficient memory）。由于 Pod 未启动，Logging 与 Tracing 维度被物理限制为不可用，故依赖 K8s 状态与资源配置事实完成诊断闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置了不切实际的资源限制（memory: 1Pi） → 集群所有可用节点物理内存均远小于1Pi → 调度器执行FailedScheduling，报告3 Insufficient memory且无法抢占 → Pod保持Pending状态，持续拒绝调度
```

### 根因结论

已确认根因为 Pod 配置了不合理且超出物理集群容量的资源限制。
容器 `app` 声明的内存请求（`resource_request.memory`）高达 `1Pi`（事实 #2），这一资源需求量远远超过了集群内任意单个节点的实际物理内存容量。因此，调度器在尝试放置 Pod 时，判定所有 3 个节点均因 `Insufficient memory` 而无法满足要求。同时，由于没有任何节点能够运行该 Pod，也就无法触发有效的抢占（Preemption）机制来释放资源，最终导致 Pod 陷入长期的 `Pending` 状态（事实 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 32.2s
├─ 并发证据采集: 46.9s
│  └─ g1 aiops-case-v02/workload: 46.9s (Evidence 40.4s, RCA 6.4s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable, pod-volume-mount-failed
