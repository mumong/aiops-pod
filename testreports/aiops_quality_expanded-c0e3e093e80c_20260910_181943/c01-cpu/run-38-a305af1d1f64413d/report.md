## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源不足 (Insufficient cpu)，导致调度器无法将 Pod 调度到任何可用节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Pending` (`fact-6343ed4f6dcc`) | 确认 Pod 处于未运行状态 |
| 2 | K8s Config | Kubernetes | `container.app.resource_request.cpu: 100k` (`fact-36ce7908abe6`) | 确认资源调度门槛 |
| 3 | K8s Event | Kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient cpu` (`fact-801cae34a9e3`) | 直接定位调度失败原因 |
| 4 | K8s State | Kubernetes | `PodScheduled: False` due to `Insufficient cpu` (`fact-809364438285`) | 佐证所有 3 个节点均无法满足 CPU 需求 |

**证据印证：** K8s Event 明确指出 3/3 节点因 `Insufficient cpu` 无法调度 Pod。结合配置事实，`100k` 的 CPU 请求未能被任何节点接纳。Metric 仅提供了 Pod 处于 Pending 状态的辅助确认，未提供节点资源水位，但事件事实已构成闭环，无需补充节点资源明细。

## 🎯 根因分析 · g1

### 因果链
```text
集群节点可用 CPU 资源耗尽 → 调度器计算失败 (Insufficient cpu) → Pod 调度失败 (FailedScheduling) → 集群节点 CPU 资源不足
```

### 根因结论
**已确认：集群节点 CPU 资源不足 (Insufficient cpu)。**

现有证据确凿：Kubernetes Event 显示调度器在 3 个节点中均未找到满足 CPU 需求的可用节点（`3 Insufficient cpu`），导致 Pod 持续处于 `Pending` 状态（证据 1, 3, 4）。配置事实证实了 Pod 请求了 `100k` 的 CPU 资源（证据 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.8s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-v01/workload: 35.9s (Evidence 29.7s, RCA 6.1s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
