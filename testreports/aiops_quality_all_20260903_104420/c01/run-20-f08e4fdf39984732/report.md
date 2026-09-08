## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pending` (Unschedulable: 0/3 nodes match affinity) | 确认 Pod 当前无法被调度的核心现象 |
| 2 | K8s Event | Kubernetes | `FailedScheduling`: `3 node(s) didn't match Pod's node affinity/selector` (45m 内发生) | 确认调度器在 3 个节点上均因亲和性/选择器不匹配而失败 |
| 3 | K8s Config | Kubernetes | `container.app resource_request.memory: 8Mi` | 确认 Pod 资源请求，证明内存不足并非导致调度的原因 |

日志与追踪维度均因 Pod 未启动或 Pod IP 缺失而无法采集，本组仅依赖 K8s 核心事实即可闭环诊断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector (aiops.lab/unavailable=true) → 集群所有节点均缺少该标签 → 调度器判定 0/3 节点匹配，触发 FailedScheduling → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 配置了不存在的 `nodeSelector` 标签。

*   **证据支持**：
    *   Pod 状态为 `Pending` 且持续 `45m`（证据 1）。
    *   K8s Event 明确指出 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`（证据 2）。
    *   资源请求（8Mi 内存、5m CPU）极低，排除了资源不足导致调度失败的可能（证据 3）。
*   **作用机制**：由于集群中没有任何节点打上了 `aiops.lab/unavailable: "true"` 标签，`default-scheduler` 无法为该 Pod 找到任何一个满足亲和性要求的节点，导致调度器主动将其置于 `Unschedulable` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.8s
├─ 并发证据采集: 54.8s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 54.8s (Evidence 47.1s, RCA 7.6s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
