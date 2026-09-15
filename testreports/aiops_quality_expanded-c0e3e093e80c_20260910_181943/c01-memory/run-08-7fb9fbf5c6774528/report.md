## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 直接指示调度器因集群内存不足而拒绝调度，且无法触发抢占 |
| 2 | K8s Config | kubernetes | `container.app` 声明 `resource_limit.memory`: **1Pi** | 根因证据：该资源声明远超常规集群规模，是导致节点资源评估失败的直接原因 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v02/workload` 状态为 `Pending`，条件 `PodScheduled` 为 `False`，原因 `Unschedulable` | 确认了异常状态，与 Event 中的 `FailedScheduling` 互为印证 |

**证据分析：**
K8s 事件与 Pod 状态共同确认了集群处于 `Pending` 且不可调度状态，调度器明确指出所有 3 个节点均因 `Insufficient memory` 无法接纳该 Pod。K8s 配置事实显示该容器的内存上限（`resource_limit`）被错误声明为 **1Pi**。结合调度器的判断逻辑（调度失败且无受害者可供抢占），该异常事实直接导致了调度失败。由于容器从未启动，Logging 与 Tracing 维度不可用（`not_applicable`），当前基于 K8s 状态的证据已足以闭环。

## 🎯 根因分析 · g1

### 因果链

```text
容器资源声明不合理 (memory limit=1Pi) → 调度器评估节点资源不足 (3 Insufficient memory) → 调度失败 (FailedScheduling, 无可用节点) → Pod 状态: Pending
```

### 根因结论

**已确认根因**：Pod `aiops-case-v02/workload` 的容器 `app` 声明的 `memory limit` 为 **1Pi**（证据 #2）。
该资源声明严重超出集群所有节点的可分配内存上限，导致 `default-scheduler` 在资源评估阶段判定 `0/3` 节点可用（证据 #1、#3）。由于资源声明不合理，集群中不存在足以容纳该 Pod 的资源槽位，因此 `preemption` 机制也未能找到任何受害者（`No preemption victims found`），最终导致 Pod 持续处于 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.5s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-v02/workload: 39.8s (Evidence 32.3s, RCA 7.4s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
