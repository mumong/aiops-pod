## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in namespace aiops-case-01 remains in Pending state with FailedScheduling events |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling: 3 node(s) didn't match Pod's node affinity/selector | 确认调度失败直接原因为节点亲和性/选择器不匹配 |
| 2 | K8s Config | kubernetes | resourceRequest: cpu=5m, memory=8Mi | 排除资源容量不足，确认请求量极小 |
| 3 | K8s State | kubernetes | pod.status: Pending, condition: Unschedulable | 确认 Pod 卡在调度阶段，无法被分配节点 |
| 4 | Metric | prometheus | kube_pod_status_phase: 1 (Pending), 0 (Unknown) | 确认当前集群中该 Pod 处于 Pending 状态，无未知异常 |

**证据印证：**
事实 1、2、3 与 4 互相印证，确认了 Pod 由于调度失败停留在 Pending 状态，且并非因为资源不足（事实 2），而是调度器无法找到匹配节点（事实 1）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的标签约束 (nodeSelector: aiops.lab/unavailable: true) → 所有 3 个集群节点均不满足亲和性条件 → 调度器拒绝所有节点 → Pod 持续处于 Pending 状态并产生 FailedScheduling 事件
```

### 根因结论

已确认根因为 **Pod 的 `nodeSelector` 约束 `aiops.lab/unavailable: true` 与集群实际节点标签不匹配**。

证据编号 1 明确指出调度器因“没有节点匹配 Pod 的节点亲和性/选择器”而拒绝所有节点。结合证据编号 2 可知，集群中有 3 个节点可用，且 Pod 资源请求极低（5m CPU），因此节点缺失并非由于资源耗尽，而是纯粹由标签匹配规则导致。

---

## 📊 性能统计

```text
├─ 总耗时: 58.6s
├─ 问题定位: 18.1s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 33.8s (Evidence 27.0s, RCA 6.7s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
