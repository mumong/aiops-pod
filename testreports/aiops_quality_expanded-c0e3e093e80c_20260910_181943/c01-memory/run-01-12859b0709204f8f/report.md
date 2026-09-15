## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 的容器 `app` 配置了极端不切实际的内存限制 `1Pi`（且请求量等同），导致集群内所有 3 个可用节点的剩余内存均无法满足该调度条件，从而触发 FailedScheduling 事件，使 Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v02/workload` 状态为 `Pending` | 确认为持续调度失败的直接症状 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling 80s ... 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` | 直接指明集群内所有 3 个节点均无足够内存进行分配，且无可用抢占目标 |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存限制 `resource_limit.memory` 为 `1Pi` | 构成调度失败的直接约束条件，远超常规节点物理内存上限 |
| 4 | K8s Config | Kubernetes | 容器 `app` 内存请求 `resource_request.memory` 为 `1Pi` | 证实调度器按 `1Pi` 大小进行资源预留，导致所有节点匹配失败 |
| 5 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` 值为 `1` (当前观测) | 确认 Pod 目前仍处于 Pending 阶段，未见进入 Running 或 CrashLoopBackOff 状态 |

证据表明，集群调度失败是由 Pod 配置中极端不切实际的 `1Pi` 内存资源请求直接引起的。该限制导致调度器在所有节点上查找失败，并伴随明确的 `Insufficient memory` 警告。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 中定义资源 requests/limits.memory: 1Pi → 调度器校验发现集群 3 个节点均无此量级可用内存 → 调度失败 (FailedScheduling) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod `aiops-case-v02/workload` 的容器 `app` 配置了 `1Pi` 的内存限制与请求（证据编号 3、4）。这一数值在真实计算环境中远超物理节点的可用容量，导致调度器无法在集群内的任何节点（共 3 个）上满足其分配条件（证据编号 2），从而使 Pod 持续卡在 `Pending` 状态（证据编号 1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 42.4s
├─ 并发证据采集: 32.7s
│  └─ g1 aiops-case-v02/workload: 32.7s (Evidence 26.2s, RCA 6.4s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
