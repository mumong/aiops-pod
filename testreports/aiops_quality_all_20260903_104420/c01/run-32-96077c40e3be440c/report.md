## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，处于 Unschedulable |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `status: Pending`, `pod.condition.PodScheduled: False` | 确认 Pod 处于 Pending 状态且未调度 |
| 2 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 直接指示调度失败原因为节点选择器不匹配 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi`, `container.resource_request.memory: 8Mi`, `container.resource_limit.cpu: 50m`, `container.resource_request.cpu: 5m` | 确认 Pod 资源请求极小，排除资源配额不足导致 Pending |
| 4 | K8s Event | kubernetes | `message`: `Preemption is not helpful for scheduling` | 证实集群无资源可抢占，且调度失败非资源争抢导致 |

现有证据一致指向 **节点亲和性/选择器配置** 问题。K8s Event 明确显示集群中 3 个节点均不满足该 Pod 的 `node affinity/selector` 条件，且因请求资源极低（8Mi/5m）且无可用资源可抢占，直接排除了资源不足的可能性。Logging 与 Tracing 因容器未启动而无法获取，属于预期现象，不影响当前结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的节点标签匹配规则 → 调度器无法找到满足条件的节点 → FailedScheduling 事件触发 → Pod 持续处于 Pending (Unschedulable) 状态
```

### 根因结论

已确认根因为 **Pod 节点选择器（Node Affinity/Selector）与集群节点标签不匹配**。
证据编号 1、2 与 3 形成闭环：虽然 Pod 的资源请求非常小（编号 3），但调度器在检查所有 3 个节点时均因标签不匹配而拒绝调度（编号 2），且预抢占机制也无效（编号 2），最终导致 Pod 保持在 Pending 状态（编号 1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.7s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 47.4s (Evidence 40.6s, RCA 6.6s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
