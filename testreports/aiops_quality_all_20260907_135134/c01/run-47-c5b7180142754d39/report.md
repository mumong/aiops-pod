## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 调度策略配置为 `node_selector: aiops.lab/unavailable=true`，强制要求调度至标记为‘不可用’的节点；但集群内 3 个节点（master, node1, node2）均处于 Ready 状态且均缺失该标签，导致调度器无法找到匹配节点（FailedScheduling），Pod 持续 Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 2m55s (x13 over 62m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | **核心证据**：重复性调度失败事件，明确指示调度器因节点亲和性/选择器匹配失败而放弃调度，且已持续超过 1 小时。 |
| 2 | K8s State | kubernetes | `Pod status: Pending` | **现象**：确认容器处于调度等待阶段，未进入运行时（No Running/PodStarted）。 |
| 3 | K8s Config | kubernetes | `container: app, resource_request.cpu: 5m` | **排除资源瓶颈**：请求资源（CPU 5m）极低，非 CPU 资源不足导致。 |
| 4 | K8s Config | kubernetes | `container: app, resource_request.memory: 8Mi` | **排除资源瓶颈**：请求资源（内存 8Mi）极低，非内存资源不足导致。 |
| 5 | Metric | prometheus | `kube_pod_status_phase=1 (Pending)` | **外部印证**：监控指标确认 Pod 目前仍处于 Pending 状态。 |
| 6 | Metric | prometheus | `kube_pod_status_phase=0 (Failed)` | **排除异常崩溃**：Failed 计数为 0，证明 Pod 未被调度器拒绝后标记为失败，而是持续等待。 |

**证据互证说明：**
K8s Event (`#1`) 中的错误消息 `3 node(s) didn't match Pod's node affinity/selector` 是调度失败的直接归因。结合 K8s Config (`#3`, `#4`) 中极低的资源请求，可以逻辑推断调度失败并非由于集群节点缺乏足够的 CPU/内存资源，而是由非资源因素（即选择器标签匹配问题）引起。K8s State (`#2`) 和 Metrics (`#5`) 证实了 Pod 的状态与调度事件的时间线一致（长时 Pending 且未转为 Failed）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 node_selector: aiops.lab/unavailable=true → 调度器在集群内搜索带有该标签的节点 → 集群中所有 3 个可用节点（master, node1, node2）均缺失该标签 → 导致 FailedScheduling 事件持续触发 → 用户可见 Pod 状态持续为 Pending，服务不可用
```

### 根因结论

**已确认的根因：**
Pod 调度策略存在标签配置不匹配。Pod 被强制要求调度至标签为 `aiops.lab/unavailable=true` 的节点，而当前集群内所有节点（master, node1, node2）均处于 Ready 状态但**均不包含该标签**。调度器因无法找到满足亲和性要求的节点，导致 Pod 被永久挂起（Pending）(`fact-e32a8dfa9048`)。

**说明：**
尽管该标签名称为 `unavailable`（不可用），看起来可能是有意用于模拟场景（`unknowns`），但基于现有工具事实，其直接后果是导致调度约束无法满足，从而引起服务不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.1s
├─ 并发证据采集: 37.0s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 37.0s (Evidence 30.7s, RCA 6.2s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
