## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 的 nodeSelector 配置 `aiops.lab/unavailable=true` 在集群中不存在的节点标签上，导致调度器无法匹配任何节点（3/3 nodes didn't match），Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 26m (x8 over 61m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 明确调度失败原因，所有节点均因 Pod 亲和性/选择器不匹配被过滤。 |
| 2 | K8s State | kubernetes | `PodScheduled`: `False`, Reason: `Unschedulable`, Message: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 验证 Pod 未调度的当前状态。 |
| 3 | K8s State | kubernetes | `Pod Phase`: `Pending` | 确认 Pod 长时间停留在初始调度阶段。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase: `Pending`): `1`；`kube_pod_status_phase` (phase: `Running`): `0` | 确认集群中该 Pod 实例未从 Pending 进入 Running 状态。 |

**证据关联分析**
1. K8s Event 和 K8s State 中的调度失败信息完全一致，均指向节点标签 `node affinity/selector` 不匹配是阻塞调度的直接原因。
2. Prometheus 指标确认了 Pod 状态未发生变化（Pending），排除了 Pod 已启动但发生内部故障的可能性。
3. Logging 和 Tracing 维度由于 Pod 无法调度启动且查询工具失败，不存在应用层日志或追踪数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的 nodeSelector (`aiops.lab/unavailable=true`) → 调度器过滤所有节点导致 0/3 匹配 → Pod 被阻塞在 Pending 状态 → 无法启动并产生业务日志
```

### 根因结论

**已确认根因**：Pod `aiops-case-01/workload-68c557d875-llhkh` 的调度失败是由其 `nodeSelector` 配置中引用的节点标签在集群现有节点中不存在导致的。

**证据支撑**：
*   K8s Event (`fact-1d60c8f9919c`) 和 K8s State (`fact-cadf542df8ee`) 明确记录了调度器拒绝调度的原因是 `3 node(s) didn't match Pod's node affinity/selector`。
*   该配置导致所有可用节点被过滤，且无法通过 Preemption 解决。

**证据局限性**：
*   虽然日志和追踪数据因 Pod 无法启动而不可用，但 K8s 调度层面的证据（Event、State）已足以确认该单一配置错误是导致当前现象的直接且唯一原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.4s
├─ 并发证据采集: 58.9s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 58.9s (Evidence 52.6s, RCA 6.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
