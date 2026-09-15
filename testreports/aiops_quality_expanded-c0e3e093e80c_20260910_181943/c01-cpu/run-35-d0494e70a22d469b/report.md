## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，未被调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | Pending | 确认当前 Pod 尚未被调度。 |
| 2 | K8s Event | `default-scheduler` | `FailedScheduling` (持续 45m+), "0/3 nodes are available: 3 Insufficient cpu", "No preemption victims found" | 解释 Pod 滞留 Pending 的直接原因：集群节点 CPU 资源耗尽且无法抢占。 |
| 3 | K8s Config | `container.app resource_request.cpu` | `100k` | 提供调度器资源匹配失败的具体请求背景。 |
| 4 | Metric | `kube_pod_status_phase` | Pending=1 (采样时间: 2026-09-11T06:19:01Z) | 从指标侧再次确认 Pod 正处于 Pending 阶段。 |

**证据说明：**
1. **状态与现象一致**：K8s Pod 状态（#1）与 Prometheus 指标（#4）相互印证，Pod 确实处于 Pending 状态。
2. **因果闭环**：调度器明确报错由于 CPU 资源不足（#2）导致无法调度，而 Pod 配置的 CPU 请求量为 `100k`（#3），说明调度失败的原因是集群整体可用 CPU 资源无法满足该 Pod 的调度需求，且集群内无可用资源可用于抢占。

## 🎯 根因分析 · g1

### 因果链

```text
集群可用节点 CPU 资源耗尽 → 调度器资源匹配失败 → 触发 FailedScheduling 事件 → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为：**集群节点 CPU 资源不足（Insufficient cpu）**。

集群内 3 个可用节点均无法提供足够的 CPU 资源来满足该 Pod `100k` 的请求（证据 #2），且由于“无可用抢占对象”，调度器无法通过抢占其他 Pod 来调度当前 Pod。这一资源瓶颈直接导致 Pod 被调度器标记为 `FailedScheduling`，并长期保持 `Pending` 状态无法启动（证据 #1、#2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.1s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v01/workload: 39.9s (Evidence 33.6s, RCA 6.2s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
