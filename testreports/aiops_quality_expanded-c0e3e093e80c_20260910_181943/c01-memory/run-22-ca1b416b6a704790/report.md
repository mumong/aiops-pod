## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod资源请求配置了不切实际的内存上限（1Pi），导致调度器判定所有集群节点内存不足而无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 26m (x2 over 31m) default-scheduler 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (fact_id: fact-1a9267cb797f, fact_id: fact-6eecc090cb04) | 核心证据。Schedular 明确报告所有 3 个节点均“内存不足”，且因资源请求过大无抢占对象。 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory: 1Pi` (fact_id: fact-6bac71a7ac54) | 核心证据。Pod 申请了 1 PiB 内存，该数值远超集群常规容量，直接导致调度评估失败。 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 1Pi` (fact_id: fact-47726a3167f3) | 上下文。硬限制同样配置了 1 PiB，进一步印证这是不切实际的资源配置。 |
| 4 | K8s State | kubernetes | `Pod condition: type=PodScheduled, status=False, reason=Unschedulable` (fact_id: fact-35a2de8b278b) | 症状确认。状态持续表明调度器判定该 Pod 不可调度。 |
| 5 | Metric | prometheus | `kube_pod_status_phase=1` (fact_id: fact-5e630443ec03) | 佐证。Metric 显示 Pod 维持在 Pending 状态。 |

**证据说明：**
证据 #1 (Event) 和 #4 (State) 共同证实了 Pod 处于“不可调度”状态。#1 明确将“Insufficient memory”列为所有节点的失败原因，#2 (#6bac71a7ac54) 提供了直接的解释：1 PiB 的内存请求导致了这一结果。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1 PiB 内存请求 → 调度器评估所有节点内存不足 → 调度失败 (Unschedulable) → Pod 状态卡在 Pending
```

### 根因结论

**已确认的根因：**
Pod (`aiops-case-v02/workload`) 的内存资源请求 (`resource_request.memory`) 被错误配置为 `1Pi` (fact_id: fact-6bac71a7ac54)，该值远超集群节点的物理内存容量。这导致 Kubernetes 调度器判定集群中所有 3 个节点均不满足资源要求（证据 #1, #4），从而无法调度该 Pod。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 15.6s
├─ 并发证据采集: 33.3s
│  └─ g1 aiops-case-v02/workload: 33.3s (Evidence 29.6s, RCA 3.6s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
