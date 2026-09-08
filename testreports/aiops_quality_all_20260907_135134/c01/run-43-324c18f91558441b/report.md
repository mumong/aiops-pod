## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod的nodeSelector要求aiops.lab/unavailable=true，但集群中所有节点均不满足该标签，导致调度器无法匹配任何可用节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase: Pending` (fact-84cb6ce6cfb4) | 确认 Pod 处于挂起状态，未进入运行阶段。 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-6b8e4297f2fa) | 明确指示调度失败的原因是节点标签不匹配。 |
| 3 | K8s State | kubernetes | `PodScheduled: False`, `reason: Unschedulable`: `3 Preemption is not helpful for scheduling.` (fact-9461bff3ed31) | 进一步证实由于资源限制或节点条件不足，且抢占无法解决该调度问题。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 中 `Pending=1` (fact-3d52beda2b38) | 提供独立指标源佐证 Pod 持续处于 Pending 状态。 |
| 5 | K8s Config | kubernetes | `resource_request.memory: 8Mi`, `resource_request.cpu: 5m` (fact-27edf5aa617f, fact-7eb551d627d2) | 说明 Pod 对资源的需求极小，排除因资源不足导致的调度失败。 |

**证据关联说明：**
事实 1、2、3、4 从状态、事件和指标三个维度互相印证，确认 Pod 因调度器无法匹配节点而处于 `Pending` 状态。事实 5 排除了资源配额（Request）作为阻塞因素，结合事实 2 中的明确报错信息，将原因锁定为节点选择器（Node Selector）不匹配。事实 4 提供了来自 Prometheus 的客观数据支持。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector: aiops.lab/unavailable=true → 调度器检查集群节点标签 → 所有 3 个节点均缺少该标签 → 无法分配节点（Unschedulable） → 现象：Pod 状态为 Pending，调度事件 FailedScheduling
```

### 根因结论

**已确认的根因：** Pod 的调度策略与集群实际节点标签不匹配。

Pod 的 `nodeSelector` 强制要求节点必须拥有标签 `aiops.lab/unavailable=true`。然而，集群中全部 3 个节点均不满足此条件。由于 Pod 的资源请求量（CPU 5m, Memory 8Mi）非常小，资源本身不是瓶颈（证据 5），且抢占机制无法解决标签缺失问题（证据 3）。

该结论得到 K8s 事件（证据 2）、K8s 状态（证据 1）、K8s 条件（证据 3）以及 Prometheus 指标（证据 4）的交叉验证支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.6s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 41.7s (Evidence 35.1s, RCA 6.5s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
