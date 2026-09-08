## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in namespace aiops-case-01 remains in Pending status due to scheduling failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector..." | 直接证明调度失败原因是节点亲和性/选择器不匹配 |
| 2 | K8s State | kubernetes | Pod status: Pending | 确认 Pod 始终未调度成功 |
| 3 | K8s Config | kubernetes | resource_request.cpu: 5m, memory: 8Mi | 资源请求值极低，说明资源充足，排除资源不足导致的调度失败 |
| 4 | K8s Config | kubernetes | resource_limit.cpu: 50m, memory: 32Mi | 确认资源限制值 |

**证据关联说明：**
- 事件 1 明确指出现象为 "didn't match Pod's node affinity/selector"，直接指向非资源类的调度约束问题。
- 状态 2 佐证 Pod 持续处于 Pending 状态，符合调度失败的典型表现。
- 配置 3 和 4 证实 Pod 的资源请求非常低，排除了因资源不足（No Resources）导致 3 个节点均不可用的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 包含 NodeSelector 约束 'aiops.lab/unavailable=true' → 调度器检查集群中 3 个节点，发现无节点满足该标签约束 → 调度器返回 '0/3 nodes are available' 并持续触发 FailedScheduling 事件 → Pod 保持在 Pending 状态
```

### 根因结论

已确认的根因为 **NodeSelector 约束 'aiops.lab/unavailable=true' 与集群节点标签不匹配**。
该约束指定了 Pod 只能运行在带有 `aiops.lab/unavailable=true` 标签的节点上，但集群当前仅有的 3 个节点（master, node1, node2）均无此标签，导致调度器无法为 Pod 分配任何节点，从而使其长期处于 Pending 状态。
这一结论由 K8s Event 中明确指出的 "didn't match Pod's node affinity/selector" 以及 K8s State 中的 Pending 状态直接支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.1s
├─ 并发证据采集: 48.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 48.8s (Evidence 40.2s, RCA 8.4s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
