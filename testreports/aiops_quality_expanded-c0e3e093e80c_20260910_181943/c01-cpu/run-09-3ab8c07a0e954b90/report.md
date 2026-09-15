## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，持续未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v01/workload` 状态 `Pending`，Phase `Pending`（fact-39cbfac33468, fact-c76cbb7ecdc0） | 确认为待调度异常状态 |
| 2 | K8s Event | kubernetes | `FailedScheduling` 事件：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found`（fact-53a04700f885） | 直接说明调度器因资源不足及无抢占对象而失败 |
| 3 | K8s State | kubernetes | Pod 条件 `PodScheduled` 为 `False`，原因 `Unschedulable`（fact-1a50e684d633） | 确认 Pod 被标记为不可调度 |
| 4 | K8s Config | kubernetes | 容器 `app` 请求 `cpu: 100k`（fact-283c15204413） | 提供引发资源竞争的请求资源量级 |
| 5 | K8s Config | kubernetes | 容器 `app` 限制 `cpu: 100k`（fact-4fe116eb9be2） | 确认 CPU 为硬限制边界 |
| 6 | Metric | prometheus | `kube_pod_status_phase` 中 `Pending` 状态值为 `1`（fact-67dde83c8279） | 外部指标印证 Pod 处于等待状态 |

**证据分析：**
Kubernetes 的事件（#2）和状态（#3）直接指向了 `Insufficient cpu` 且无抢占空间，这是导致 Pod 进入 `Pending`（#1, #6）状态的直接原因。配置的 CPU 请求量（#4）作为引发资源压力的上下文，与调度器的失败原因一致。

## 🎯 根因分析 · g1

### 因果链

```text
集群 3 个节点 CPU 资源耗尽 (Insufficient cpu) → 调度器无法满足 Pod 资源请求且无预emption 对象 → Pod 状态标记为 Unschedulable (Pending) → 容器未启动
```

### 根因结论

已确认根因为**集群节点 CPU 资源耗尽**。

证据链（#2, #3）明确显示 `default-scheduler` 无法在集群的 3 个可用节点中找到满足 `cpu` 请求的资源，且因无预emption 对象（`No preemption victims found`）而无法调度。Pod 因此被永久标记为 `Unschedulable`（#3），导致容器无法分配资源启动（#1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 25.4s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-v01/workload: 39.5s (Evidence 33.0s, RCA 6.4s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
