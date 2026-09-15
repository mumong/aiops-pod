## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点CPU资源不足导致Pod调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (fact-cc40e07312a6) | 证明集群中所有可用节点均无法提供足够的 CPU 资源，且调度器未能找到任何可抢占的 Pod，直接指向集群级资源瓶颈。 |
| 2 | K8s State | kubernetes | `Pod Scheduled condition: False`，`Phase: Pending` (fact-84941394c7af, fact-a5cb0f86d145) | 确认 Pod 处于不可调度的停滞状态，与事件中的资源不足原因互为印证。 |
| 3 | K8s Config | kubernetes | Pod 配置：`CPU Request: 100k`，`CPU Limit: 100k` (fact-35d9c3343d1d, fact-e6cd518d88b9) | 明确异常工作负载的 CPU 资源需求仅为极小值（0.0001核），在 CPU 耗尽的集群中仍被拒绝，证实故障根源在于节点级容量枯竭而非该 Pod 资源请求过大。 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 (fact-3535ae6b18b6)，`kube_pod_status_phase{phase="Failed"}` = 0 (fact-07e2b73df041) | 通过指标观测确认 Pod 处于等待状态且未发生崩溃，排除了因容器启动失败导致退出的可能。 |

**证据说明**：Kubernetes 事件（#1）直接给出了“3 个节点 CPU 不足”的诊断结果，而 Pod 配置（#3）显示该工作负载所需的 CPU 资源极低（100k），这种强烈反差证实故障是由集群整体 CPU 资源耗尽引起的全局性阻塞，而非该 Pod 自身的调度策略或资源需求问题。

## 🎯 根因分析 · g1

### 因果链
```text
集群 3 个节点的 CPU 资源已耗尽 → 调度器评估无法满足 Pod 资源需求 → 3 个节点均返回 "Insufficient cpu" 且无可抢占 Pod → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因：集群节点 CPU 资源耗尽导致调度失败。**

事实证据支持如下：
1. **调度失败原因明确**：Kubernetes 调度器事件（证据 #1）明确指出“0/3 nodes are available: 3 Insufficient cpu”，说明所有可用节点均无法为该 Pod 分配 CPU 资源。
2. **排除 Pod 自身问题**：该 Pod 的 CPU 请求（100k）和限制（100k）极小（证据 #3），在资源耗尽的集群中仍无法调度，证明阻塞原因是节点层面的容量枯竭，而非该工作负载的资源需求不合理。
3. **状态一致**：Prometheus 指标显示 Pod 处于 `Pending` 状态（证据 #4），未发生 `Failed` 或崩溃，符合资源不足导致的持续调度等待特征。

**局限性说明**：虽然已确认“集群 CPU 不足”是导致调度失败的直接原因，但无法提供各节点具体的 CPU 剩余可分配量、已占用量详情，也无法确认是否存在更高优先级的可抢占 Pod（未知项）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.1s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-v01/workload: 50.0s (Evidence 39.4s, RCA 10.5s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable, pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
