## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-01/workload-68c557d875-llhkh` phase=Pending, condition PodScheduled=False (Unschedulable) | 确认 Pod 调度失败的直接状态 |
| 2 | K8s Event | Kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 确认 3 个节点均不满足调度约束 |
| 3 | Metric | Prometheus | `kube_pod_status_phase` phase=Pending 为 1 | 监控指标证实 Pod 持续处于 Pending 状态 |

> **证据说明**：K8s 事件与状态指标相互印证，确认 Pod 长期无法调度。由于 Pod 处于 Pending 状态，日志与追踪数据均不可用（物理限制）；K8s 配置数据（资源请求/限制）与调度失败无直接因果关系，证据集中体现为调度约束与节点状态的冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector `aiops.lab/unavailable=true` → 集群所有 3 个节点均无此标签 → 调度器匹配失败 (0/3) → Pod 保持 Pending 状态，持续报 FailedScheduling 事件
```

### 根因结论

**根因**：Pod `aiops-case-01/workload-68c557d875-llhkh` 的调度策略（`nodeSelector` 或节点亲和性）要求节点必须包含标签 `aiops.lab/unavailable=true`，但集群内所有 3 个 Ready 节点均缺少该标签，导致调度器无法找到可用节点。

**证据支持**：
- K8s 事件显示 3 个节点均未匹配 Pod 的节点亲和性/选择器（#2）。
- K8s 状态与指标均证实该异常是持续性而非瞬时故障（#1, #3）。

**未确认项**：为何 Pod 被配置了要求标签 `aiops.lab/unavailable` 的调度策略，现有工具事实无法解释该配置意图或来源。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.9s
├─ 并发证据采集: 56.9s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 56.9s (Evidence 47.1s, RCA 9.6s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
