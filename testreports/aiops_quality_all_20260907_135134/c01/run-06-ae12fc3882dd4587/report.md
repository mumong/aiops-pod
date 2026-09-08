## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (持续出现, 间隔 15m/9m) | 确认 Pod 因亲和性/选择器不匹配导致调度器判定集群无可用节点 |
| 2 | K8s State | kubernetes | `pod.status`: "Pending" | 确认 Pod 处于不可运行状态 |
| 3 | K8s Config | kubernetes | `resource_request.cpu`: 5m, `resource_request.memory`: 8Mi, `resource_limit.cpu`: 50m, `resource_limit.memory`: 32Mi | 提供 Pod 资源需求上下文（极低） |
| 4 | Metric | prometheus | `kube_pod_status_phase` (Pending): 1 | 验证当前 Pod 处于 Pending 阶段 |

**证据说明：**
K8s 事件（证据 #1）直接指出 3 个节点均未匹配 Pod 的 Node Affinity/Selector，这与 Pod 维持 Pending 状态（证据 #2, #4）的现象一致。虽然资源请求极低（证据 #3），通常不会导致全集群资源不足，但事件明确指向“不匹配”，排除了资源耗尽作为主要原因。由于 Pod 未启动，Logging 和 Tracing 维度不适用（输入已声明 `not_applicable`）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 NodeSelector/NodeAffinity (aiops.lab/unavailable=true，事实中未展示具体标签值，仅展示不匹配现象) → 集群节点均不具备该标签或语义不匹配 → Scheduler 判定 0/3 节点可用，持续触发 FailedScheduling → Pod 保持 Pending 状态
```

### 根因结论

**证据不足**。
当前证据明确显示 Pod 因“未匹配 Pod's node affinity/selector”而被调度器拒绝（证据 #1）。然而，输入事实中**缺失具体的 NodeSelector 或 NodeAffinity 配置字段内容**，无法直接展示导致不匹配的那个具体标签或选择器规则。因此，虽然可以确定是亲和性配置导致的问题，但无法在报告中精确引用导致该失败的具体配置键值。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 21.4s
├─ 并发证据采集: 547.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 547.8s (Evidence 540.9s, RCA 6.8s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
