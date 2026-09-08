## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | Unschedulable (0/3 nodes didn't match affinity/selector) | 确证 Pod 停留在 Pending 的直接原因 |
| 2 | K8s Event | event.message | FailedScheduling 23m (x7 over 53m) | 提供异常持续时长与频率，排除瞬时抖动 |
| 3 | K8s Config | container.resource_request | CPU: 5m, Memory: 8Mi | 排除常规资源容量（CPU/内存）不足的可能性 |

1. **K8s State 与 Event 相互印证**：Pod 的 `Unschedulable` 状态直接对应 `FailedScheduling` 事件，明确故障点是调度失败而非运行异常。
2. **排除资源瓶颈**：`resource_request` 仅为 `5m` CPU 和 `8Mi` 内存，属极小值；结合事件指出是 "didn't match ... selector" 而非资源不足，将故障范围收窄至拓扑/标签匹配问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了 nodeSelector: aiops.lab/unavailable=true → 集群 3 个节点均无匹配该标签 → 调度器触发 FailedScheduling → Pod 持续处于 Pending 状态
```

### 根因结论

根因已确认：Pod 配置了不满足当前集群拓扑的节点选择器（`aiops.lab/unavailable=true`）。

*   **因果关联**：所有 3 个节点均未匹配该标签（证据 #1, #2），导致调度器无法找到可用节点，引发 Pod 挂起。
*   **排他性**：由于资源请求极低（证据 #3），排除资源耗尽或容量不足等其他调度失败场景。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.9s
├─ 并发证据采集: 44.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 44.8s (Evidence 37.4s, RCA 7.3s)
└─ 汇总总结: 6.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
