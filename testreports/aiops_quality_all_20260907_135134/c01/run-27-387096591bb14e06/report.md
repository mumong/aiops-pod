## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in namespace aiops-case-01 is stuck in Pending state with 0/3 nodes available due to node affinity/selector mismatch. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `pod.condition`: `PodScheduled` status `False`, reason `Unschedulable`, message `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-531b239f3819) | 确认 Pod 处于 Unschedulable 状态，明确故障原因为节点亲和性/选择器不匹配 |
| 2 | K8s State | `kubernetes` | `container.resource_request`: CPU `5m`, Memory `8Mi` (fact-0ce9693414e2, fact-c5282c1043c8) | 排除资源不足导致调度失败的可能，Pod 请求量极小 |
| 3 | K8s Event | `kubernetes` | `event`: `FailedScheduling` (fact-548124e09a7f, fact-ccd63877b116) | 提供故障的时间跨度证据（持续 39 分钟以上），排除瞬时故障 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase`: 存在 1 个 `Pending` 样本 (fact-589251cb28c2) | 从指标层确认 Pod 持续处于 Pending 状态，无状态变更 |

**证据分析：**
- K8s 事件 (fact-548124e09a7f) 与 Pod 条件 (fact-531b239f3819) 一致地指出 0/3 节点满足 `affinity/selector` 要求，这是调度的直接阻碍。
- 资源请求数据 (fact-0ce9693414e2) 证实 Pod 对底层资源要求极低，因此“不匹配”是纯粹的配置/标签问题，而非资源抢占或资源不足。
- 指标 (fact-589251cb28c2) 佐证了该状态的持续性，结合事件时间戳，证明故障已发生较长时间。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 nodeSelector/affinity 约束 `aiops.lab/unavailable=true` → 集群所有 3 个可用节点均无此标签 → Scheduler 拒绝所有节点匹配（'didn't match Pod's node affinity/selector'） → Pod 保持 Pending 状态 (Unschedulable)
```

### 根因结论

已确认根因为 **Pod 节点选择器与节点标签不匹配**。

证据表明，`default-scheduler` 持续拒绝所有 3 个节点，原因是它们不匹配 Pod 定义的 `node affinity/selector` 约束（fact-531b239f3819, fact-548124e09a7f）。由于 Pod 请求的资源量极小（CPU 5m, Mem 8Mi fact-0ce9693414e2），且没有任何节点匹配该约束，导致调度永久失败。虽然无法确定为何节点没有该标签（配置遗漏或有意排除），但这不影响当前故障的根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.5s
├─ 并发证据采集: 42.1s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 42.1s (Evidence 33.2s, RCA 8.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
