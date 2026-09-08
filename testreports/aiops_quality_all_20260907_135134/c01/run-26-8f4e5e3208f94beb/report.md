## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，持续未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | 3 个节点均不匹配 Pod 的节点亲和/选择器；抢占不可用 | 解释调度失败原因，确证调度器判定 |
| 2 | K8s Config | `container.resource_request.cpu` | `5m` | 资源请求量极低，非资源不足导致 |
| 3 | K8s Event | `FailedScheduling` | `Warning ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指向标签选择器匹配失败 |

Pod 在 PodScheduled 条件中明确提示“节点未匹配选择器”，结合极低的资源请求量（CPU 5m），排除资源争抢，确证失败原因为标签选择器不匹配。Metric 仅展示 Pending 状态，与 K8s Event 状态一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector: aiops.lab/unavailable=true → 集群中无节点匹配该标签选择器 → 调度器判定 0/3 nodes are available 并拒绝调度 → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 配置了标签选择器 `nodeSelector: aiops.lab/unavailable=true`，但集群中所有节点均未设置该标签（证据 #1、#3）。该选择器条件无法满足导致调度器始终无法分配节点，表现为 Pod 持续 Pending（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 55.6s
├─ 问题定位: 14.6s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 35.4s (Evidence 27.5s, RCA 7.8s)
└─ 汇总总结: 5.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
