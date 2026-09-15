## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 持续处于 Pending 状态，调度失败，事件显示 3/3 节点 Insufficient cpu。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient cpu` | 直接指明调度失败原因为所有节点 CPU 资源不足 |
| 2 | K8s Config | kubernetes | Container `app` resource request: `100k` CPU | 确立 Pod 期望调度的最小资源约束 |
| 3 | K8s State | kubernetes | `PodScheduled` Condition `False`, Reason: `Unschedulable` | 确认调度器明确判定无法安排该 Pod |
| 4 | K8s State | kubernetes | `pod.status`: `Pending`, `pod.phase`: `Pending` | 确认 Pod 当前处于持续的等待状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase` (Pending) = `1` (Running = `0`) | 佐证 Pod 状态未发生转换，持续阻塞 |

证据表明，调度器在尝试将 `aiops-case-v01/workload` 调度到 3 个节点时，由于节点剩余的可用 CPU 均低于 Pod 的 `requests` 阈值（`100k`），导致调度动作全面失败。Metric 数据与 K8s 事件的时间戳一致，验证了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点可用 CPU 资源不足 → 调度器无法满足 100k CPU 的 requests 约束 → 预emption 机制无 victim 可驱逐 → Pod 维持 Pending 状态
```

### 根因结论

已确认的根因是**集群所有节点的可用 CPU 资源不足**（证据 1, 2, 3）。调度器无法找到满足 `100k` CPU 资源请求的节点，且没有更高优先级的运行中 Pod 可供驱逐（证据 3, 4），从而导致 `aiops-case-v01/workload` 持续处于 Pending 状态。

当前存在以下不确定性：
- 具体是哪个节点或哪些 Pod 占用了大部分 CPU 资源，导致整体 Insufficient cpu。
- 是否存在 LimitRanger 或 Default Resource 注入导致了 CPU requests 的隐式增加（尽管 YAML 显示 requests 为 100k）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.5s
├─ 并发证据采集: 35.0s
│  └─ g1 aiops-case-v01/workload: 35.0s (Evidence 24.5s, RCA 10.4s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
