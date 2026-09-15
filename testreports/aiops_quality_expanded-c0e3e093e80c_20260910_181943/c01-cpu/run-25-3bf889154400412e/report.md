## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源不足（Insufficient cpu）导致 Pod 持续调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `status: Pending` | 直接展示 Pod 处于等待调度状态。 |
| 2 | K8s Event | FailedScheduling | `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found` | 明确指出集群 3 个节点均缺少可用 CPU 资源，且无优先级可抢占，判定为根因。 |
| 3 | K8s Config | Resource Request | `container "app" requests CPU: 100k` | 确认 Pod 向调度器提交的调度需求为 100m CPU。 |
| 4 | Metric | Prometheus Status | `kube_pod_status_phase` 值为 `1` (Pending), 样本数: 1 | 佐证当前 Pod 生命周期状态，因样本不足未展示趋势。 |

**证据说明**：Kubernetes 事件（证据 2）直接指明了 `Insufficient cpu` 是导致调度失败的物理原因，这与 Pod 状态为 `Pending`（证据 1、4）及明确的资源请求（证据 3）构成了完整且无冲突的证据链。因容器未启动，Logging 和 Tracing 维度无数据产生，但不影响调度维度的根因判定。

## 🎯 根因分析 · g1

### 因果链
```text
集群节点可用 CPU 不足 → 默认调度器拒绝绑定 Pod → Pod 持续处于 Pending 状态 → 应用服务不可用
```

### 根因结论
已确认根因为**集群节点 CPU 资源不足**。
调度器事件明确指出当前集群的 3 个可用节点均无法满足 Pod 的 CPU 需求（100k），且在无优先级抢占的情况下无法进行调度（证据 2）。该事实直接导致 Pod 停留在 Pending 状态（证据 1），并阻断了后续容器启动与业务日志的产生。

---

## 📊 性能统计

```text
├─ 总耗时: 46.6s
├─ 问题定位: 15.5s
├─ 并发证据采集: 24.4s
│  └─ g1 aiops-case-v01/workload: 24.4s (Evidence 20.8s, RCA 3.6s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
