## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，持续无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.aiops-case-v02/workload.status` | status: Pending, phase: Pending | 确认 Pod 尚未被调度 |
| 2 | K8s Event | `default-scheduler` | `Warning FailedScheduling` (fact-82f4daeee961, fact-8da3ae3bd907): `0/3 nodes are available: 3 Insufficient memory` | 提供调度失败的直接错误原因及时间跨度 |
| 3 | K8s State | `pod.aiops-case-v02/workload.condition` | `PodScheduled=False`, reason: `Unschedulable`, message: `3 Insufficient memory` | 固化当前调度器的最终判断结果 |
| 4 | K8s Config | `container.app` | `resource_request.memory=1Pi`, `resource_limit.memory=1Pi` | 确认 Pod 的资源请求/限制存在且量级异常巨大 |
| 5 | Metric | `prometheus` (kube-state-metrics) | `phase="Pending"`, value=1 (fact-55bdf412e458) | 监控层证实 Pod 仍处于 Pending 阶段，排除 Failed |

**证据印证说明：**
Pod 的 Pending 状态（证据 #1、#5）与调度器的 `Insufficient memory` 报错（证据 #2、#3）在时间上和状态上完全匹配。Pod 声明的 `1Pi` 内存资源（证据 #4）从物理层面解释了为何集群中任意节点（0/3）都无法满足其调度需求。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 声明了 1Pi 的内存 requests/limits (K8s Config) → 调度器在所有节点资源检查中失败 (K8s Event/State) → 3个节点均报告 Insufficient memory 且无抢占者 (K8s Event) → Pod 持续处于 Pending 状态，无法启动 (K8s State/Metric)
```

### 根因结论

已确认根因为：Pod `aiops-case-v02/workload` 声明了极度不合理的内存资源量 `1Pi`（远超常规集群容量），导致 Kubernetes 调度器在所有可用节点上均因 `Insufficient memory` 拒绝调度，且因无足够内存的节点可被抢占，Pod 陷入 `Pending` 状态。

支持这一结论的事实包括：
1. 调度器在 19 分钟周期内两次报出 `Insufficient memory` 错误，表明该问题非瞬时波动 (事实 #2, #3)。
2. Pod 的 `resource_request.memory` 和 `resource_limit.memory` 均为 `1Pi` (事实 #4)，构成了直接的拒绝依据。
3. 监控数据仅反映其 Pending 状态 (事实 #5)，无证据表明其进入了 Running 或 Failed 状态，确认故障停留在调度环节。

---

## 📊 性能统计

```text
├─ 总耗时: 58.7s
├─ 问题定位: 15.0s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-v02/workload: 33.9s (Evidence 24.6s, RCA 9.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
