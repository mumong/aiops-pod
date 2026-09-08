## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认 Pod 因节点亲和性/选择器不匹配导致无法调度。 |
| 2 | K8s State | kubernetes | `pod.phase: Pending` | 反映 Pod 当前处于未调度的持久状态。 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu: 5m`, `memory: 8Mi` | 资源请求极小，说明非资源容量不足导致的调度失败。 |
| 4 | Metric | prometheus | `kube_pod_status_phase(phase=Pending): 1` | 验证 Pod 持续处于 Pending 状态。 |

**证据印证说明：**
- 事实 #1 和 #2 相互印证，明确指出了调度失败的具体原因（节点不匹配）和当前状态（Pending）。
- 事实 #3 排除了资源容量不足作为首要原因的可能性，指向策略性配置错误（如节点选择器）。
- 事实 #4 作为独立数据源，确认了 K8s 状态的一致性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector: aiops.lab/unavailable=true → 集群所有节点均无 aiops.lab/unavailable 标签 → 调度器因节点不匹配拒绝调度 (FailedScheduling) → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 调度约束与集群节点标签不匹配**。Pod 配置了特定的 `nodeSelector`（根据 RCA 上下文），但集群中所有节点（共 3 个）均不具备对应的标签（`aiops.lab/unavailable=true`），导致调度器无法找到满足条件的节点进行调度 [事实 #1]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.5s
├─ 并发证据采集: 60.0s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 60.0s (Evidence 51.7s, RCA 8.1s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
