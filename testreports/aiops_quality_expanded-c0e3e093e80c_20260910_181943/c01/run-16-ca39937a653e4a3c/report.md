## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 node_selector 'aiops.lab/unavailable=true'，但集群内所有节点均不具备该标签，导致调度器持续失败并无法将 Pod 调度至任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Pending | 确认 Pod 处于未调度状态 |
| 2 | K8s Config | kubernetes | `node_selector`: `aiops.lab/unavailable=true` | 提供 Pod 的调度约束条件 |
| 3 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 直接指出 3 个节点均不满足亲和性/选择器要求，且预调度不可行 |
| 4 | Metric | prometheus | `kube_pod_status_phase`: `Pending` = 1, `Unknown` = 0 | 确认 Pod 持续处于 Pending 阶段，未进入运行或未知状态 |

**证据印证说明：**
K8s Event 明确指出 3 个节点均不匹配 Pod 的 `node_affinity/selector`，这与 K8s Config 中指定的 `aiops.lab/unavailable=true` 约束一致。由于集群中没有任何节点具备该标签，调度器判定无可用节点（0/3），导致 Pod 持续处于 Pending 状态，Metric 数据进一步证实了该状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点缺失 'aiops.lab/unavailable=true' 标签 → 调度器因节点选择器不匹配判定无可用节点 → Pod 持续 Pending 且无法调度 → 业务服务不可用
```

### 根因结论

已确认根因：Pod 配置了 `node_selector` 为 `aiops.lab/unavailable=true`，但集群内所有节点均不具备该标签，导致调度器无法找到满足条件的节点进行调度（见证据 #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 57.9s
├─ 问题定位: 24.6s
├─ 并发证据采集: 27.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 27.0s (Evidence 23.0s, RCA 3.9s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
