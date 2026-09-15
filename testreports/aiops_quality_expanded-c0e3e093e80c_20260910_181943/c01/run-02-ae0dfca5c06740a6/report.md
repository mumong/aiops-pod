## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，未能调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-4b8a5eab96ae, fact-ffbb5b9b65bd) | 直接原因：调度器明确报告集群中 3 个节点均未通过亲和性/选择器检查。 |
| 2 | K8s State | kubernetes | `Pod status: Pending` (fact-6b832a573684) | 最终现象：Pod 未能分配 Node 资源，维持等待状态。 |
| 3 | Metric | prometheus | `kube_pod_status_phase { phase="Pending" } = 1` (fact-c830e0c3b5a7) | 确认 Pod 处于 Pending 阶段的事实，无 Running 实例。 |
| 4 | K8s Config | kubernetes | `resource_request.cpu: 5m`, `resource_request.memory: 8Mi`, `resource_limit.cpu: 50m`, `resource_limit.memory: 32Mi` (fact-d63ca8d77b66, fact-9c090c43f738, fact-0e4851918040, fact-480a4367f7da) | 资源需求极低，排除资源耗尽导致调度的可能性。 |

Pod 处于 Pending 状态且无法调度。虽然集群中存在节点（事实 1 提及 3 个节点），但调度器日志（事实 1）明确指出节点不满足 Pod 的亲和性/选择器要求。资源请求（事实 4）极低，排除了 CPU/Memory 资源不足的问题，因此判定调度失败的根源在于标签不匹配。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了 'node_selectors: aiops.lab/unavailable=true' → 集群节点不具备该标签导致选择器不匹配 → 调度器执行 FailedScheduling (0/3 nodes) → Pod 保持 Pending 状态
```

### 根因结论

**已确认根因**：Pod 的调度策略与集群节点配置不匹配。
Pod Spec 中指定的节点选择器标签 `aiops.lab/unavailable=true` 在集群现有节点上不存在，导致调度器无法将 Pod 绑定到任何节点，从而引发 `FailedScheduling` 事件。证据链清晰：K8s 事件明确指出了亲和性/选择器不匹配（事实 1），而 Kubernetes 配置事实（事实 4）证实资源需求量极小，进一步排除了资源不足的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 16.2s
├─ 并发证据采集: 555.7s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 555.7s (Evidence 547.2s, RCA 8.5s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
