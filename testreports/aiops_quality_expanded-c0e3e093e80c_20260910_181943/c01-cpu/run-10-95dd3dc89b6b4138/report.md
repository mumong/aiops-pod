## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点可用 CPU 资源不足（Insufficient cpu），导致 Pod 无法被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 Insufficient cpu. (fact-760f44b7166a) | 调度器明确拒绝调度的直接原因 |
| 2 | K8s Event | kubernetes | `FailedScheduling`: preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod. (fact-a2a1ffd50563) | 确认无法通过抢占高优资源缓解调度失败 |
| 3 | K8s State | kubernetes | `PodScheduled=False`, reason: `Unschedulable` (fact-7b4b10bd839f) | 确认 Pod 持续处于不可调度状态 |
| 4 | K8s State | kubernetes | `phase: Pending` (fact-d16d4bfa066a) | 确认 Pod 停留在初始化等待阶段 |
| 5 | K8s Config | kubernetes | `resource_request.cpu: 100k`, `resource_limit.cpu: 100k` (fact-70f466f9a380, fact-1b21cf98f524) | 提供资源需求数值，为“Insufficient cpu”判定提供上下文支撑 |
| 6 | Metric | prometheus | `kube_pod_status_phase`: Pending=1 (fact-553686680857) | 指标侧确认 Pod 处于 Pending 状态 |

证据 1、2 与 3 相互印证，Kubernetes 调度器在三个节点上均报出 `Insufficient cpu`，且由于没有任何可抢占资源，调度行为被完全阻断。Metric 数据在事实侧印证了 Pod 未发生状态转移。

## 🎯 根因分析 · g1

```text
集群节点可用 CPU 资源不足（Insufficient cpu） → 调度器无法分配有效节点 → Pod 调度失败 → 现象：Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为**集群节点可用 CPU 资源不足**。

*   **证据支撑**：Kubernetes 事件（证据 1、2）与 Pod 状态（证据 3、4）一致表明 `default-scheduler` 因集群所有 3 个节点均无足够的 `Insufficient cpu` 而拒绝调度。
*   **机制补充**：证据 2 指出集群内存在 3 个节点，且无可用抢占资源（No preemption victims found），彻底排除了通过资源抢占解决调度冲突的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.1s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v01/workload: 40.2s (Evidence 33.1s, RCA 7.0s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
