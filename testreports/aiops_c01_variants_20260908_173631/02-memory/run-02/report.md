## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending` | 确认 Pod 处于未被调度的停滞状态 |
| 2 | K8s Config | kubernetes | `memory request/limit: 1Pi` | 显示 Pod 申请的资源远超常规集群规模 |
| 3 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory` | 提供调度失败的直接原因，表明所有节点内存不足且无抢占空间 |

**证据说明：**
- 异常现象由 Kubernetes 调度器事件直接驱动（#3），其根本约束在于资源配置（#2）。
- 1Pi 的内存申请使得任何普通节点都无法满足调度需求，与调度器返回的 0/3 节点可用状态完全一致，且排除了资源竞争或网络等次生因素。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1Pi (Pebibyte) 的内存请求 → 集群所有 3 个节点的可用内存均小于 1Pi → Scheduler 因 Insufficient memory 拒绝调度且无 Preemption victims → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 资源请求配置严重异常**。Pod 声明了 `1Pi` 的内存（请求与限制均为 `1Pi`），该数值远超集群节点的实际物理内存上限。这导致 Kubernetes Scheduler 在评估集群中全部 3 个节点时，均判定为 "Insufficient memory"，且由于资源缺口过大，不存在可以作为抢占受害者的 Running Pod，从而直接导致调度失败和 Pod 处于 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 54.3s
├─ 问题定位: 17.2s
├─ 并发证据采集: 31.0s
│  └─ g1 aiops-case-v02/workload: 31.0s (Evidence 22.7s, RCA 8.2s)
└─ 汇总总结: 6.0s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
