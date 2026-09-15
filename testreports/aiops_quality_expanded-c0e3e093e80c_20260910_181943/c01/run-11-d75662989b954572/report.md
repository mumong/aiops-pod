## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Pending` (fact-3252bdafd0e2) | 确认异常持续状态 |
| 2 | K8s Event | `default-scheduler` | `FailedScheduling`: 0/3 nodes didn't match Pod's node affinity/selector (fact-592858ae5371) | 直接指出调度失败原因 |
| 3 | K8s State | `pod.condition` | `PodScheduled`: False, Unschedulable (fact-0faa8d86d995) | 与事件互为印证 |
| 4 | Metric | `kube_pod_status_phase` | Pending=1, Running=0 (fact-e56703fd9351) | 确认 Pod 当前运行状态 |

**证据关联说明：**
K8s 事件 (`#2`) 明确记录了“无法匹配 node affinity/selector”是调度失败的直接原因，且该事件在 15 分钟内连续出现 2 次 (`fact-592858ae5371` 和 `fact-61a7cf3c9892`)，印证了 Pod 处于持续的阻塞状态。Metric (`#4`) 提供了独立维度的状态确认，与 K8s 状态 (`#1`) 完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector (aiops.lab/unavailable='true') → 集群所有节点均缺失该 label → 调度器无法找到匹配节点触发 FailedScheduling → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为 **调度规则与集群拓扑不匹配**。
输入中的正式 RCA 指出 `nodeSelector {aiops.lab/unavailable: 'true'}` 导致了匹配失败。当前证据（K8s Event `#2` 中的 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` 以及 K8s Condition `#3`）直接支撑了“调度器无法找到匹配节点”这一结论。
**证据不足**：当前事实来源未提供具体的 Pod 定义配置（如 YAML），无法验证 `nodeSelector` 字段的具体键值对是否与 RCA 描述完全一致，但现有事实已足以确认调度失败的物理机制。

---

## 📊 性能统计

```text
├─ 总耗时: 49.9s
├─ 问题定位: 17.4s
├─ 并发证据采集: 24.3s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 24.3s (Evidence 16.7s, RCA 7.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
