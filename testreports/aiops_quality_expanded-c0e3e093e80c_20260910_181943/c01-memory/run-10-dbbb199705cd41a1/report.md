## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod 配置了 1Pi 的 memory limit，超出集群所有节点的可用内存，导致调度器因 Insufficient memory 拒绝调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Pending` (fact-0b78ca4c3b86) | 确认 Pod 处于不可用状态 |
| 2 | K8s State | Kubernetes | `pod.condition: PodScheduled=False`，message 明确包含 `3 Insufficient memory` 且 `No preemption victims found` (fact-1cf34e03b7da) | 确认调度失败的具体技术原因 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 1Pi` (fact-68be9ef4df40) | 确认可疑的资源配置数值 |
| 4 | K8s Event | Kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient memory` (fact-0bc3cacdd9a5, fact-4958aa779023) | 提供来自调度器的直接报错记录 |
| 5 | Metric | Prometheus | `kube_pod_status_phase(Pending): 1` (fact-e5d76fc4eca7) | 从指标维度印证 Pod 当前持续保持 Pending 状态 |

**证据印证说明：**
Kubernetes 状态与事件（证据 #1, #2, #4）直接指出了 `Insufficient memory` 是调度失败的根因；Kubernetes 配置（证据 #3）中高达 1Pi 的 Memory Limit 完美解释了为何 3 个节点均无法满足该请求。Metric 指标（证据 #5）确认了该状态持续存在。虽然 Logging 和 Tracing 因 Pod 未启动而缺失，但 K8s 层面的证据已完全闭合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1Pi 的 memory limit → 超出集群所有节点内存容量 → 调度器判定 Insufficient memory 并拒绝 → 用户可见 Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 的 `memory limit` 被错误配置为 `1Pi`（事实 #3）。该数值远超物理集群的总可用内存，导致 `default-scheduler` 在尝试匹配所有 3 个节点时均因 `Insufficient memory` 而拒绝调度（事实 #1, #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.9s
├─ 问题定位: 17.2s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-v02/workload: 28.6s (Evidence 24.9s, RCA 3.6s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
