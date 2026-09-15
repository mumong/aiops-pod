## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，调度失败 (Unschedulable)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling  6m53s (x13 over 66m)  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认调度失败的直接触发原因：亲和性/选择器不匹配。 |
| 2 | K8s State | kubernetes | `pod.condition: PodScheduled=False, reason=Unschedulable, message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 从 Pod 状态层面证实调度器因无法匹配节点而拒绝调度。 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu: 5m, container.resource_request.memory: 8Mi` | 确认资源请求极小，排除因资源不足导致的调度失败，佐证是拓扑约束问题。 |
| 4 | K8s Config | kubernetes | `Pod 定义包含 NodeSelector aiops.lab/unavailable=true` | 提供了导致亲和性不匹配的具体配置依据，证实节点标签缺失是根本原因。 |

**证据关联分析：**
事件 `fact-916178c32667` 与 Pod 状态 `fact-4e8f57462b77` 均明确指向 `node affinity/selector` 不匹配，且均显示 3/3 节点不满足条件；结合配置事实 `aiops.lab/unavailable=true`，直接确认了因标签缺失导致的调度死锁。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 NodeSelector `aiops.lab/unavailable=true` → 集群 3 个节点均未匹配该 NodeSelector 约束 → 调度器触发 FailedScheduling 事件且预抢占无效 → Pod 保持 Pending 状态且 nodeName 为 <none>
```

### 根因结论

已确认根因为 **Pod 配置了 NodeSelector `aiops.lab/unavailable=true`，但集群所有 3 个节点均不包含此标签**。
这一配置约束导致调度器无法找到任何满足条件的节点（证据 `fact-916178c32667`, `fact-4e8f57462b77`, `aiops.lab/unavailable=true`），从而持续处于 Unschedulable 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 26.2s
├─ 并发证据采集: 34.1s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 34.1s (Evidence 24.6s, RCA 9.4s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
