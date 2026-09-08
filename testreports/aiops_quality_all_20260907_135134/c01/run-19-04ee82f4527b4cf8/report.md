## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 配置了 NodeSelector `aiops.lab/unavailable: true`，但集群中所有节点均缺少该 Label，导致调度器在所有节点上判定不匹配从而拒绝调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` (fact-37ead9747ba1) | `Pending` | 确认 Pod 未处于运行状态 |
| 2 | K8s Event | `FailedScheduling` (fact-272645668b67) | `3 node(s) didn't match Pod's node affinity/selector` | 直接指出调度失败原因为节点匹配失败 |
| 3 | K8s Config | `NodeSelector` (diagnosis context) | `aiops.lab/unavailable: true` | 提供调度规则的具体约束条件 |
| 4 | Metric | `kube_pod_status_phase` (fact-97aea081bffe) | `1` (phase: Pending) | 独立于 K8s 状态数据的时序采样印证，确认处于 Pending 阶段 |

**证据说明**：
1. K8s Event (证据 2) 中的错误信息明确指向 `node affinity/selector` 不匹配，直接排除了资源不足或节点不可用的常见原因。
2. 结合诊断上下文中提取的 `NodeSelector` (证据 3) 与 Event 的报错内容，形成了完整的逻辑闭环：特定的调度标签缺失导致了 Event 中描述的匹配失败，从而引起证据 1 和 4 所示的 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
NodeSelector 约束 `aiops.lab/unavailable: true` 未被任何节点满足 → 
Scheduler 判定所有节点不匹配 (0/3 nodes) → 
调度器拒绝放置 Pod 并触发 FailedScheduling 事件 → 
Pod 保持 Pending 状态
```

### 根因结论

已确认根因为 **Pod 调度规则配置错误导致无可用节点**。

具体而言，该 Pod 配置了节点选择器标签 `aiops.lab/unavailable: true`，但集群内现有的 3 个节点均未携带此标签。这种硬性的匹配规则冲突导致 `default-scheduler` 无法找到任何符合条件的节点，进而产生 `FailedScheduling` 警告，使 Pod 一直处于 `Pending` 状态。

**引用证据**：
- 证据 2 (`FailedScheduling` 事件) 确认了调度的失败原因。
- 证据 1 & 3 (`Pending` 状态及 `NodeSelector` 配置) 确认了问题的直接表现与触发条件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.9s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 33.9s (Evidence 29.1s, RCA 4.6s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
