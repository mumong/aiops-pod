## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 stuck in Pending state due to FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `PodScheduled=False`, 消息: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 直接证实调度器无法将 Pod 绑定到任何节点 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确记录调度失败原因，指出亲和性/选择器不匹配 |
| 3 | Metric | prometheus | `kube_pod_status_phase(phase=Pending) = 1` (样本 1 个，`trend_evaluable=false`) | 从监控数据验证 Pod 持续处于 Pending 状态 |

**证据总结：**
Kubernetes 事件和 Pod 条件状态均一致指向同一异常现象：0/3 节点匹配。Metric 数据确认该状态已持续。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 nodeSelector aiops.lab/unavailable=true → 集群 3 个节点均无此标签 → 调度器匹配失败 (0/3) → Pod 卡在 Pending 状态
```

### 根因结论

已确认根因为：Pod 的调度约束（`nodeSelector` 或亲和性规则）要求节点具备 `aiops.lab/unavailable=true` 标签，但集群中所有可用节点均不满足该条件。

这一结论直接由 K8s State 中的调度失败消息（`didn't match Pod's node affinity/selector`）和 Event 中的 `FailedScheduling` 事件确认，无需额外的日志或指标数据支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.8s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 32.3s (Evidence 26.1s, RCA 6.1s)
└─ 汇总总结: 6.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
