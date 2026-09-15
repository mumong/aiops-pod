## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8持续处于Pending状态，调度失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-3ba525a3f93b, fact-af5924875ba7) | `FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 记录调度失败的具体原因：节点亲和性/选择器不匹配。 |
| 2 | K8s State | kubernetes (fact-1da8450fa435) | `pod.condition: PodScheduled=False, reason=Unschedulable` | 提供 Pod 处于 Pending 状态的直接状态证据。 |
| 3 | K8s Config | kubernetes (fact-42b5e4015f95) | `container.resource_request.memory: 8Mi` | 确认资源请求非常小，排除资源容量不足导致的调度失败。 |
| 4 | K8s Config | kubernetes (fact-82986fe38b88) | `container.resource_request.cpu: 5m` | 确认资源请求非常小，排除资源容量不足导致的调度失败。 |
| 5 | Metric | prometheus (fact-6399e7668778) | `kube_pod_status_phase: 1` (phase=Pending) | 确认 Pod 状态持续维持在 Pending，无自动恢复迹象。 |

**证据分析：**
1. **现象与状态确认**：`fact-22022eba3fa3` 和 `fact-d95bd636a73c` 确认 Pod 处于 Pending 状态；`fact-6399e7668778` 通过 Prometheus 监控确认该状态持续存在。
2. **直接原因**：`fact-1da8450fa435` 的 `Unschedulable` 状态与 `fact-3ba525a3f93b`、`fact-af5924875ba7` 的 `FailedScheduling` 事件完全一致，表明问题出在调度器分配节点时。
3. **机制推断**：事件明确指出 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，这排除了资源（CPU/Memory）不足的可能性，因为 `fact-42b5e4015f95` 和 `fact-82986fe38b88` 显示资源请求极小（5m CPU, 8Mi Memory），足以被任意节点满足。因此，故障必然是由于节点选择器（nodeSelector）或亲和性规则导致的硬性不匹配。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec中定义了nodeSelector: {aiops.lab/unavailable: true} → 集群中所有节点均不具备该标签 → 调度器因节点亲和性/选择器不匹配拒绝调度(FailedScheduling) → Pod持续处于Pending状态且Node为None
```

### 根因结论

已确认的根因为 **调度亲和性/选择器配置错误**。

Pod `workload-68c557d875-gtzc8` 的调度失败直接由节点选择器（nodeSelector）要求不满足引起。
1. **机制不匹配**：K8s 事件 `fact-3ba525a3f93b` 明确指出 `3 node(s) didn't match Pod's node affinity/selector`，且所有 3 个节点均因该原因被拒绝。
2. **排除资源竞争**：Pod 请求的资源极小（CPU 5m, Memory 8Mi），在集群中不可能因为资源不足（Insufficient）而被拒绝。
3. **结论**：Pod 要求节点具备 `aiops.lab/unavailable=true` 标签，但当前集群环境中的节点均未配置此标签，导致调度器无法找到合适的节点进行绑定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.3s
├─ 并发证据采集: 33.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 33.0s (Evidence 25.9s, RCA 6.9s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
