## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，未分配到节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-45c4f2407b84) | `Warning FailedScheduling 22m ... 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 核心异常证据：明确指调度失败原因为集群全节点（3/3）CPU 不足且无法抢占 |
| 2 | K8s State | kubernetes (fact-ad41e4e12263) | `pod.status: Pending` | 确认异常现象：Pod 持续处于 Pending 状态，未分配到节点 |
| 3 | K8s Config | kubernetes (fact-0a6015defa67) | `container.resource_request.cpu: 100k` | 提供上下文：目标容器申请的 CPU 资源量为 0.1 Core |
| 4 | K8s Config | kubernetes (fact-de4111dda351) | `container.resource_limit.cpu: 100k` | 提供上下文：容器 CPU 上限同样限制为 100k |
| 5 | Metric | prometheus (fact-904b7c670995) | `kube_pod_status_phase: 1` (labels: `phase: Pending`) | 辅助验证：通过 Metric 数据侧面印证 Pod 处于 Pending 生命周期 |

**证据说明：**
K8s Event 的 `FailedScheduling` 信息直接解释了 Pod (fact-45c4f2407b84) 无法启动的原因，即所有可用节点均报 `Insufficient cpu`。同时，状态为 `Pending` 的 Event (fact-ad41e4e12263) 与 Prometheus 采集到的 `Pending` 状态指标 (fact-904b7c670995) 形成了多维度的互相印证，证实了 Pod 未得到资源分配的事实。由于日志与追踪维度均标注为 `not_applicable`（容器未启动），本次诊断主要依赖 K8s 事件与状态事实。

## 🎯 根因分析 · g1

### 因果链

```text
集群 3 个节点 CPU 资源不足 → 默认调度器执行调度判断并触发 FailedScheduling → Pod 持续 Pending，无法分配节点 → 应用容器未启动
```

### 根因结论

**已确认的根因：**
集群内所有节点（3/3）的 CPU 可用资源无法满足 Pod 的调度需求。证据 (fact-45c4f2407b84) 明确显示调度器报出 `3 Insufficient cpu` 且无抢占方案，导致 Pod 始终处于 `Pending` 状态（fact-ad41e4e12263）。

**未确认事项（证据不足）：**
*   节点 CPU 不足的具体诱因（如系统预留过高、其他业务 Pod 占用等）在当前采集中未明确展示。
*   集群整体的 CPU 供需平衡全貌未完全评估。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 23.1s
├─ 并发证据采集: 28.7s
│  └─ g1 aiops-case-v01/workload: 28.7s (Evidence 20.7s, RCA 7.9s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
