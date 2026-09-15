## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod 'workload' in 'aiops-case-v01' is stuck in 'Pending' status with no node assigned. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling 5m12s (x12 over 60m) default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 确立核心故障现象：调度器在 3 个节点上均因 CPU 不足且无抢占目标而持续拒绝 |
| 2 | K8s Config | kubernetes | CPU request=100k, limit=100k; Memory request=8Mi, limit=32Mi | 证明该 Pod 资源请求极低，调度拒绝并非由该 Pod 的资源量级导致 |
| 3 | K8s State | kubernetes | `status: Pending` | 确认 Pod 当前停滞在未分配节点状态，未进入运行阶段 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 中 Pending 值为 1 (1 sample); Running 值为 0 (1 sample) | 独立确认集群内该 Pod 处于 Pending 阶段，且没有 Running 状态的 Pod 可供调度器进行资源抢占 |

证据表显示，K8s Event 记录了持续 60 分钟的调度失败，根本原因为 `Insufficient cpu` 且 `No preemption victims`。Metric 数据佐证了该 Pod 长期保持 Pending 状态。Pod 自身的资源请求极低（100k CPU），与调度器反馈的集群整体 CPU 不足形成对比，说明集群内部资源处于极度饱和状态。

## 🎯 根因分析 · g1

### 因果链
```text
集群节点 CPU 资源耗尽 → 调度器因 Insufficient cpu 拒绝所有节点 → 无运行中的 Pod 可供抢占 → Pod 永久处于 Pending 状态
```

### 根因结论
已确认的根因是 **集群整体 CPU 资源枯竭，且缺乏可抢占的冗余 Pod**。
集群内全部 3 个节点均处于 CPU 资源耗尽状态，导致调度器无法为该 Pod 分配任何节点。更关键的是，系统中没有任何正在运行的 Pod（Metric 显示 Running 为 0），使得调度器的抢占机制失效（`No preemption victims found`）。
该 Pod 自身仅请求 100k CPU 和 8Mi 内存，其被拒纯粹是由于集群资源分配已无剩余。虽然存在高 CPU 消耗的负载导致了此僵局，但缺乏具体的负载标识，无法进一步指向具体的业务应用。

---

## 📊 性能统计

```text
├─ 总耗时: 53.1s
├─ 问题定位: 17.8s
├─ 并发证据采集: 26.8s
│  └─ g1 aiops-case-v01/workload: 26.8s (Evidence 18.8s, RCA 7.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
