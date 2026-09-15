## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群 CPU 总容量不足 (Insufficient cpu)，且无可抢占资源 (No preemption victims)，导致 default-scheduler 无法将 Pod 调度至任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found` | 明确说明所有 3 个节点均缺乏 CPU 资源，且调度器因无可抢占目标而放弃尝试 |
| 2 | K8s State | `pod.condition` | `Unschedulable (0/3 nodes are available: 3 Insufficient cpu...)` | 记录 Pod 最终调度失败状态，与 Event 事实一致 |
| 3 | K8s Config | `container.resource_request.cpu` | `100k` | 确认 Pod 请求的 CPU 资源量，证明非资源配置缺失导致的调度失败 |

## 🎯 根因分析 · g1

```text
集群 3 个节点 CPU 资源耗尽 → 调度器触发抢占机制但无可抢占目标 → Pod 保持 Unschedulable (Pending) 状态 → 无法分配到节点
```

**根因结论**
已确认根因为集群 CPU 容量不足。所有 3 个可用节点均报告 `Insufficient cpu`，且调度器因找不到任何可抢占的工作负载（`No preemption victims`），导致 Pod `aiops-case-v01/workload` 无法满足调度要求并保持 `Pending` 状态（见证据 1, 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 55.8s
├─ 问题定位: 20.2s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-v01/workload: 30.5s (Evidence 24.3s, RCA 6.0s)
└─ 汇总总结: 5.1s
```

📋 Runbook 参考

- 未调用 Runbook
