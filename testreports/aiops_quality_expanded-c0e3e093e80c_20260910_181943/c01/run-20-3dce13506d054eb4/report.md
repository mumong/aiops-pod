## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，未被调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确拒绝原因，指向节点亲和性/选择器不匹配。 |
| 2 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi` / `container.resource_request.cpu: 5m` | 排除因资源请求量过大导致的节点资源不足问题。 |
| 3 | K8s State | Kubernetes | `PodScheduled` Condition: `False` (Reason: `Unschedulable`) | 提供 Pod 停滞在 Pending 状态的直接状态确认。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` for `Pending`: `1` (0 for `Running`) | 通过时序指标佐证 Pod 长期处于待调度状态且未成功运行。 |

**证据关联分析：**
- 证据 #2 显示 Pod 资源需求极低（5m CPU / 8Mi Memory），直接排除了资源耗尽作为调度失败原因。
- 证据 #1 与 #3 共同确认：故障不是资源问题，而是**策略匹配问题**（3个节点均未匹配选择器）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了未存在于集群节点的 nodeSelector/亲和性约束 → 调度器遍历 3 个节点均无匹配 → 触发 FailedScheduling (Unschedulable) → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `workload-68c557d875-gtzc8` 因配置了**节点选择器/亲和性约束（node affinity/selector）**，且集群中所有 3 个可用节点均不满足该约束，导致 `default-scheduler` 无法找到合适节点，从而将 Pod 维持在 `Pending` 状态（证据编号：#1, #3）。

该根因已通过 K8s 调度事件中的明确反馈 `0/3 nodes are available: ... didn't match Pod's node affinity/selector` 得到证实。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 28.5s
├─ 并发证据采集: 88.7s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 88.7s (Evidence 79.6s, RCA 8.7s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
