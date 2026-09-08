## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod配置了强制节点选择器 aiops.lab/unavailable=true，该标签在集群所有节点上均不存在 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Pending` <br> `pod.condition: PodScheduled=False (Unschedulable)` | 确认 Pod 持续处于未调度状态，且未进入尝试启动阶段。 |
| 2 | K8s Event | Kubernetes | `FailedScheduling` 连续报错 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` <br> (记录时间跨度 35 分钟) | 明确调度失败机制：集群所有节点均无法匹配 Pod 的亲和性约束。 |
| 3 | K8s Config | Kubernetes | `nodeSelector: aiops.lab/unavailable=true` <br> `memory_request: 8Mi`, `cpu_request: 5m` <br> `memory_limit: 32Mi`, `cpu_limit: 50m` | 确认故障源于硬性的标签选择器配置，而非资源不足导致的溢出。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` (phase="Pending") 值为 1 (单样本) | 侧面印证 Pod 状态持续为 Pending，无向 Running 或其他状态切换的指标波动。 |

**证据关联说明：**
Kubernetes 事件记录 (#2) 直接指出了“节点不匹配”的调度原因，K8s 配置 (#3) 提供了具体的不匹配标签（`aiops.lab/unavailable=true`）。由于 Pod 尚未启动，Logging (#1) 和 Tracing 维度为不可用，但 K8s State (#1) 与 Metric (#4) 共同确认了这一异常状态已持续并稳定存在。

## 🎯 根因分析 · g1

### 因果链
```text
Pod配置错误的节点选择器 (aiops.lab/unavailable=true) → 调度器检查集群节点标签 → 0/3 节点匹配选择器约束 → 持续 Pending (Unschedulable)
```

### 根因结论
已确认根因为 **Pod 配置了强制节点选择器 `aiops.lab/unavailable=true`，且集群内所有节点均不存在该标签**。

**证据支撑：**
K8s Event 记录（证据 #2）明确指出了 `node affinity/selector` 匹配失败，且涉及集群中全部 3 个节点。K8s 配置事实（证据 #3）锁定了该标签的强制约束配置。排除资源不足或节点宕机因素。

---

## 📊 性能统计

```text
├─ 总耗时: 60.0s
├─ 问题定位: 23.5s
├─ 并发证据采集: 28.1s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 28.1s (Evidence 22.6s, RCA 5.4s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
