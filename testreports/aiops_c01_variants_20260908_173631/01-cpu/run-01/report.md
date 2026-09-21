## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload in aiops-case-v01 is in Pending state with FailedScheduling condition. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling 81s default-scheduler 0/3 nodes are available: 3 Insufficient cpu...` | 直接指出调度失败原因：集群中所有节点均无足够的可用 CPU |
| 2 | K8s State | `aiops-case-v01/workload` | `phase: Pending`, `PodScheduled: False` (`Unschedulable`) | 确认 Pod 状态异常，调度器无法为其分配节点 |
| 3 | K8s Config | `aiops-case-v01/workload` | `container.app cpu.request: 100k`, `cpu.limit: 100k` | 提供 Pod 的资源申请诉求（100k CPU），为判定资源不足提供基准 |

证据 1 与证据 2、3 相互印证：调度器事件（#1）解释了 Pod 为何持续处于 Pending 状态（#2），且原因直指节点 CPU 不足，而该需求量级（#3）在现有集群中确实无法满足。Logging 与 Tracing 因容器未启动而不存在，属于预期行为，不构成证据缺失。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源不足 → 调度器无法匹配任何节点 → Pod 处于 Unschedulable 状态 → 用户观察到 Pod Pending
```

### 根因结论

**已确认根因：集群 CPU 资源不足导致调度失败。**

集群中所有节点（共 3 个）均报告 CPU 不足，导致调度器无法将 Pod 调度至任何节点，Pod 因此停留在 Pending 状态。

*   **证据支持**：K8s 事件 `FailedScheduling` 明确显示所有节点均因 `Insufficient cpu` 不可用（证据 #1）；Pod 状态为 `Pending` 且条件为 `Unschedulable`（证据 #2）。
*   **证据不足**：虽然故障原因已锁定为“CPU 不足”，但输入中缺失具体的节点级 CPU 分配明细（如 `kube_node_status_allocatable`），因此无法量化确切缺少多少 CPU，也无法指出是哪个特定节点或哪个特定租户占用了过多 CPU。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 34.7s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-v01/workload: 46.7s (Evidence 38.8s, RCA 7.8s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
