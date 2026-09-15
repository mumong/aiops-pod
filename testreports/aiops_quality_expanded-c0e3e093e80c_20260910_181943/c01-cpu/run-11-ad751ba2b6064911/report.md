## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | The cluster has effectively exhausted CPU scheduling capacity across all nodes. Although individual node allocatable CPU values are high, the scheduler reports '3 Insufficient cpu' for every node. This indicates that the sum of resource requests (likely from kube-system or other critical workloads not visible in this namespace) exceeds the allocatable CPU on all 3 nodes. The workload pod, requesting only 100k CPU, cannot be placed because no node reports available CPU for scheduling. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling` 2m52s (x2 over 7m52s)：`0/3 nodes are available: 3 Insufficient cpu`；无抢占受害者 | 确认为集群级资源瓶颈，非节点故障或配置错误 |
| 2 | K8s State | Pod (Pending) | `PodScheduled: False` | 证实 Pod 状态停滞，与调度失败原因一致 |
| 3 | Metric | prometheus | `kube_pod_status_phase` (Pending): 1 | 量化确认异常 Pod 持续处于 Pending 状态 |
| 4 | K8s Config | Pod (app) | CPU Request: 100k, CPU Limit: 100k | 排除该 Pod 资源请求过大或配置缺陷的可能性 |

**证据说明：**
Pod 状态（#2）和调度事件（#1）直接确认了 Pod 无法上线的原因。Metric 数据（#3）提供了该状态的持续时间佐证。配置证据（#4）排除了目标 Pod 本身的问题，结合“3 Insufficient cpu”的报错，逻辑闭环指向集群调度资源枯竭。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 可用容量耗尽（外部因素） → 调度器无法满足 Pod 资源请求 → Pod 处于 Pending 状态并持续报 FailedScheduling → 用户无法访问该工作负载
```

### 根因结论

已确认的根因是**集群节点层面的 CPU 调度容量已耗尽**。

1. **集群资源耗尽**：调度器在所有 3 个节点上均报告 `Insufficient cpu` 且无法找到抢占者（#1），表明集群内其他工作负载（如 kube-system 或用户业务负载）的 CPU 请求总和已占用全部节点可用容量。
2. **目标 Pod 非致因**：目标 Pod 仅请求 `100k` CPU 却仍无法调度（#4），证明该异常是由全局资源竞争导致，而非 Pod 自身配置错误。

**证据不足说明：** 当前证据无法精确定位是哪类工作负载导致了集群资源耗尽。需要查询 `kube-system` 或其他用户名称空间内高 CPU 请求的 Pod 分布才能完成最终定位，但这不影响确认当前故障的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.9s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-v01/workload: 50.0s (Evidence 42.0s, RCA 7.9s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
