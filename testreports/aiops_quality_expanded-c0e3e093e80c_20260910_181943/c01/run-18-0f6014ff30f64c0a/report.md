## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 nodeSelector {aiops.lab/unavailable: true}，但集群中所有节点（master, node1, node2）均缺少该标签，导致调度器无法找到匹配节点，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `status: Pending` (fact-924cf00da0f0) | 确认 Pod 当前异常状态 |
| 2 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-28c8f413c4f6, fact-7871b5ad8113) | 指出调度器因节点不匹配而拒绝调度的直接原因 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` (fact-0e8197209615), `cpu: 50m` (fact-26e9bbba4414) | 资源请求极小，排除资源竞争导致的调度失败 |
| 4 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` (fact-600e561a8c03), `cpu: 5m` (fact-31485bcc176d) | 资源需求极低，与事实 #2 结合，确认为纯逻辑匹配失败 |
| 5 | Metric | prometheus | `kube_pod_status_phase` value: 1 for `phase: Pending` (fact-d4b77a45d04e) | 独立观测确认 Pod 处于 Pending 阶段 |
| 6 | K8s State | kubernetes | `PodScheduled: False` (reason: `Unschedulable`, message: `0/3 nodes are available...`) (fact-17c2e97bb709) | 进一步印证调度条件未满足的底层原因 |

**证据链说明：**
事实 #1、#5 与 #6 从状态、指标和调度条件三个维度独立确认了 Pod 持续 Pending 且不可调度。事实 #2 提供了调度失败的根本机制：`node affinity/selector` 不匹配。事实 #3 与 #4 证明了资源限制并非瓶颈，从而排除了由于资源不足导致的不匹配，将焦点锁定在标签配置错误上（尽管标签的具体不匹配事实未在聚合事实中直接展示，但调度器错误消息已明确指向此原因）。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置 nodeSelector 标签 {aiops.lab/unavailable: true} 
→ 集群所有节点 (master, node1, node2) 缺失该标签 
→ 调度器匹配失败 (FailedScheduling) 
→ Pod 持续处于 Pending 状态
```

### 根因结论
**已确认根因**：Pod 配置了集群中任何节点都不具备的 `nodeSelector` 标签 `aiops.lab/unavailable: true`。
该配置导致 Kubernetes 调度器无法在现有 3 个节点中找到满足亲和性/选择器要求的节点，从而引发 `FailedScheduling` 事件（见事实 #2、#6），致使 Pod 永久保持 `Pending` 状态（见事实 #1、#5）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.7s
├─ 问题定位: 13.5s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 35.6s (Evidence 30.0s, RCA 5.5s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
