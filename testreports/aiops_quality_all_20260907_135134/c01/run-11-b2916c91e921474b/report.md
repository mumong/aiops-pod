## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 持续处于 Pending 状态，未能调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod condition: `PodScheduled=False, reason=Unschedulable`, message: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-635cd15c282b) | 提供直接的失败机制说明 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling 20m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-8807dc7ed2c6) | 确认调度器判定无匹配节点 |
| 3 | Metric | prometheus | `kube_pod_status_phase` 为 `Pending: 1, Failed: 0` (fact-841d72ed69c2) | 印证 Pod 持续保持 Pending 状态 |

Kubernetes 状态（#1）与事件（#2）共同指向同一结论：调度器因节点亲和性/选择器不匹配判定 0/3 节点可用。Metric 数据（#3）从外部观测角度佐证了 Pod 一直停留在 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
未确认的 Pod nodeSelector 定义 → 集群节点缺乏对应标签 → 调度器判定不匹配 → Pod 持续 Pending
```

### 根因结论

**证据不足。**
目前 K8s 事件与状态（#1, #2）明确排除了资源不足（CPU/Memory 等）的可能性，且未发现 Taint/Toleration 导致的排斥。这证实了 Pod 配置了某种节点亲和性/选择器，导致集群中所有节点都无法匹配。然而，事实数据中缺失该 Pod 的 `nodeSelector` 或 `affinity` 配置字段（未提供完整 Pod YAML）。在无法获取配置原文的情况下，只能推断是“未展示的配置导致节点选择器不匹配”，不能确认具体的标签键值要求。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.1s
├─ 并发证据采集: 37.1s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 37.1s (Evidence 27.6s, RCA 9.4s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
