## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `PodScheduled: False, reason: Unschedulable` (fact-bd69400f6692) | 确认 Pod 无法被调度且未匹配节点 |
| 2 | K8s Config | Kubernetes | `cpu request: 5m, limit: 50m` (fact-0a79ec23d0ca, fact-1bb4bde84313) | 排除资源配额不足导致无法调度 |
| 3 | K8s Config | Kubernetes | `memory request: 8Mi, limit: 32Mi` (fact-9874db464ae9, fact-ddec96d90731) | 排除内存资源不足导致无法调度 |
| 4 | K8s Event | Kubernetes | `Warning FailedScheduling 3 node(s) didn't match Pod's node affinity/selector` (fact-3e2eae252529) | 提供调度失败的直接报错原文 |
| 5 | Metric | Prometheus | `kube_pod_status_phase=1` for `Pending` (fact-9313819a2451) | 独立验证 Pod 持续处于 Pending 状态 |

证据 1、2、3 确认 Pod 处于 Pending 且资源请求极低（5m CPU/8Mi Memory），说明调度失败非资源耗尽导致。证据 4 明确指出失败原因为“node affinity/selector 不匹配”，结合集群中无其他资源报错，直接指向节点选择器配置问题。证据 5 从指标层面印证了该状态持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 设置 nodeSelector: aiops.lab/unavailable=true → 集群内 0/3 节点具备该标签 → 调度器执行 FailedScheduling 匹配失败 → Pod 维持在 Pending 状态 (Unschedulable)
```

### 根因结论

已确认的根因为：**Pod 配置了 `nodeSelector` 约束（涉及 `aiops.lab/unavailable` 标签），而集群中 3 个节点均未匹配该选择器，导致调度器无法找到可用节点。**

*   **证据支撑**：
    *   `K8s Event` (fact-3e2eae252525, fact-497b3050b7d2) 中的 `FailedScheduling` 事件明确指出 `3 node(s) didn't match Pod's node affinity/selector`。
    *   `K8s State` (fact-bd69400f6692) 中的 `Unschedulable` 条件与事件相互印证。
    *   `K8s Config` (fact-0a79ec23d0ca, fact-9874db464ae9) 显示资源请求极小，排除了资源不足的可能性。
    *   `Metric` (fact-9313819a2451) 确认了 Pod 持续处于 Pending 状态。

*   **排除项**：资源不足（CPU/Memory 请求量极小）及其他非选择器类调度限制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.8s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 41.4s (Evidence 34.1s, RCA 7.0s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
