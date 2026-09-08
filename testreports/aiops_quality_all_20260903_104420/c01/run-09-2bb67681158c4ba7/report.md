## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，Node 为 None |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi`, `container.resource_request.cpu: 5m`, `container.resource_request.memory: 8Mi`, `container.resource_limit.cpu: 50m` | 排除资源配额耗尽导致的调度失败 |
| 2 | K8s State | kubernetes | `PodScheduled: False, Reason: Unschedulable` (fact-2710bc0bcdbd) | 确认 Pod 未处于运行或等待资源状态，而是被调度器直接拒绝 |
| 3 | K8s Event | kubernetes | `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-564454baa56d) | 指出失败机制是节点亲和性/选择器不匹配，而非资源不足 |
| 4 | K8s State | kubernetes | `pod.status: Pending` (fact-3802e4f859f8) | 确认 Pod 始终处于 Pending 状态，未发生状态跃迁 |
| 5 | Metric | prometheus | `kube_pod_status_phase: 1 (phase: Pending)` (fact-8d45637db0c6) | 独立确认 Pod 处于 Pending 阶段，无其他运行阶段记录 |

**证据互证说明**：
Metrics 数据（#5）从指标维度印证了 K8s 状态（#4）的 Pending 现象；而 K8s Event（#3）明确将 Pending 的原因定位到“节点选择器不匹配”，并排除了资源问题（#1）；调度器状态（#2）进一步确认了这是持续的调度失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector `aiops.lab/unavailable=true` → 集群中 3 个节点均无此标签匹配 → 调度器持续触发 FailedScheduling → Pod 保持 Pending 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-01/workload-68c557d875-llhkh` 被调度失败（Pending）的根本原因是其节点选择器（nodeSelector）与集群现有节点不匹配。

证据（#3）显示，调度器报告“3 node(s) didn't match Pod's node affinity/selector”，且资源请求极低（#1），排除了资源不足的可能。该不匹配直接导致调度器持续报错（#3），使 Pod 处于无法调度的 Pending 状态（#2, #4, #5）。

**未知/未确认**：集群中为何没有包含 `aiops.lab/unavailable=true` 标签的节点（可能涉及集群配置错误或运维遗漏），但这不影响当前现象“调度失败”的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 28.5s
├─ 并发证据采集: 48.9s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 48.9s (Evidence 41.2s, RCA 7.6s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
