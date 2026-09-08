## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态，未能被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `phase: Pending`, `condition: Unschedulable` (`pod.phase`, `pod.condition`) | 确认 Pod 持续处于未调度状态 |
| 2 | K8s Event | `kubernetes` | `Warning FailedScheduling` (7m32s) `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 提供调度失败的精确原因，指出节点亲和性/选择器不匹配 |
| 3 | K8s Config | `kubernetes` | `container.resource_request.cpu: 5m`, `memory: 8Mi` | 排除资源不足导致调度失败的常见原因（资源极低） |

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的节点选择器标签 (nodeSelector: aiops.lab/unavailable=true) → 集群所有节点不包含该标签 → 调度器判定 0/3 节点可用 (FailedScheduling) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 Pod 配置了不存在的节点选择器标签 (`aiops.lab/unavailable=true`)。根据证据 #2 的 `FailedScheduling` 事件，集群内 3 个节点均无法满足该亲和性/选择器要求，导致 Pod 无法分配节点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.5s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 46.2s (Evidence 36.9s, RCA 9.1s)
└─ 汇总总结: 5.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
