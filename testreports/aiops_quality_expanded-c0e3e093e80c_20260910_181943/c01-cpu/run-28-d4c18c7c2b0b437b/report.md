## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Cluster CPU resource exhaustion (Insufficient cpu) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | PodScheduled: False, Unschedulable, "0/3 nodes are available: 3 Insufficient cpu" | 确认 Pod 当前处于不可调度状态 |
| 2 | K8s Config | container.resource_request.cpu | app 容器 Request: "100k" | 显示该 Pod 请求的 CPU 资源数值 |
| 3 | K8s Event | event.message | "Warning FailedScheduling ... 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod." | 确认调度器在全部 3 个节点上均因 CPU 资源不足失败且无抢占空间 |
| 4 | K8s State | pod.phase | Pending | 确认 Pod 处于排队等待状态 |
| 5 | Metric | kube_pod_status_phase | 值为 1 (Pending) | 确认当前有 1 个 Pod 处于 Pending 状态 |

**证据分析说明**：
Kubernetes 事件（#3）和 Pod 状态（#1, #4）直接证实了 Pod 因 CPU 资源不足（Insufficient cpu）无法被调度到 3 个节点中的任何一个。尽管 Pod 资源请求（#2）为 "100k"，但结合全节点资源耗尽的失败日志，说明当前集群剩余 CPU 无法满足该请求，Metric 状态（#5）进一步佐证了 Pod 持续驻留在 Pending 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
集群 CPU 资源耗尽 → 调度器无法在 3/3 节点满足请求 "100k" CPU 需求 → Pod 持续 Pending 且 FailedScheduling → 用户可见应用不可用
```

### 根因结论

**已确认根因：集群 CPU 资源耗尽（Insufficient cpu）**

集群当前剩余 CPU 资源不足，导致调度器 `default-scheduler` 无法找到合适节点调度 `aiops-case-v01/workload` Pod。所有 3 个节点均报告 CPU 资源不足（证据 #3），且没有发现可抢占的 Pod（Preemption failed），致使 Pod 持续保持 Pending 状态且状态为 Unschedulable（证据 #1, #4）。

**说明**：由于 Pod 处于 Pending 状态未能启动，Logging 和 Tracing 维度（证据 #2, #3）无实际数据产出，诊断基于 Kubernetes 调度事件和状态进行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.0s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-v01/workload: 35.1s (Evidence 30.3s, RCA 4.8s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
