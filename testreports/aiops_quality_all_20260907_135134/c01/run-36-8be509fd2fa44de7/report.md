## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 定义了 `nodeSelector: {aiops.lab/unavailable: 'true'}`，但集群中所有节点（master, node1, node2）均为 Ready 状态且不包含该标签，导致调度器因无法满足亲和性/选择器条件而判定 0/3 节点匹配。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-434ce1d5a30c) | 直接确认调度失败原因：节点不匹配 |
| 2 | K8s State | Pod | `Pending` 状态，`PodScheduled` 条件为 `False` (fact-32368ce4a8cc) | 确认 Pod 处于无法被调度的阻塞状态 |
| 3 | K8s State | Pod | 诊断上下文指出定义了 `nodeSelector: {aiops.lab/unavailable: 'true'}` (fact-66e6dc771b97) | 指出导致调度的配置约束 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 显示 `Pending` 状态值为 1 (fact-63e724b792e9) | 从监控维度证实 Pod 持续处于 Pending 状态 |

**证据说明：**
Kubernetes 事件与 Pod 状态一致表明调度器因无法满足亲和性/选择器条件而判定 0/3 节点匹配。监控数据证实了 Pod 持续处于 Pending 状态。资源请求（5m/8Mi）和限制（50m/32Mi）配置过低，与调度失败无关。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了 `nodeSelector: {aiops.lab/unavailable: 'true'}` → 调度器无法找到包含该标签的节点 → FailedScheduling (0/3 nodes matched) → Pod 处于 Pending 状态
```

### 根因结论

**已确认根因**：Pod 的 `nodeSelector` 要求节点拥有 `aiops.lab/unavailable: 'true'` 标签，但集群中所有节点（master, node1, node2）均未设置该标签，导致调度器因无法满足选择器条件而判定 0/3 节点匹配，Pod 无法被调度。

**引用证据**：
- 调度器事件明确指出 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`（证据 #1）
- Pod 状态为 `Pending` 且 `PodScheduled` 条件为 `False`（证据 #2）
- 诊断上下文指出 Pod 定义了 `nodeSelector: {aiops.lab/unavailable: 'true'}`（证据 #3）
- 监控数据证实 Pod 持续处于 `Pending` 状态（证据 #4）

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.1s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 39.2s (Evidence 33.9s, RCA 5.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
