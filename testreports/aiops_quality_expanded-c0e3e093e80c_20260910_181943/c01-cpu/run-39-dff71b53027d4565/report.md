## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Cluster CPU resource exhaustion preventing pod scheduling on any of the 3 available nodes. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling 3m7s (x12 over 58m) 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` (fact-fc0ae21277fd) | 确认 3 个可用节点均因 CPU 资源不足拒绝调度，且因无抢占受害者导致无法强制调度。 |
| 2 | K8s Config | Kubernetes | CPU 请求/限制：`100k` (fact-03685bb51b22, fact-3033dd2fe7b4) | 提供导致集群资源耗尽的异常高资源需求数值。 |
| 3 | K8s State | Kubernetes | Pod 状态：`Pending`，调度条件：`PodScheduled=False, Unschedulable` (fact-1b15f574c64e, fact-f054ac2fc1b9, fact-ff92ed1627b9) | 证实 Pod 处于不可调度状态，且长期无法进入运行阶段。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` (Pending)=1, (Running)=0 (fact-36c2eaefe42d, fact-46aba08ef767) | 从监控侧证实该 Pod 实例目前不可用（Pending）且集群中无其他运行实例。 |

**证据说明：**
Kubernetes 事件明确指出集群层面所有节点均无法满足调度条件，根本原因为 `Insufficient cpu` [证据1]。该调度拒绝是由 Pod 配置中极高的 CPU 请求/限制值 `100k` [证据2] 直接导致的；结合 `Pending` 状态和调度失败事件，形成了完整的资源耗尽导致调度失败的证据闭环 [证据3]。Prometheus 监控数据确认了 Pod 当前处于不可用的 Pending 状态，排除了短暂延迟的可能 [证据4]。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 100k CPU 请求 [证据2] → 集群中所有可用节点的 CPU 资源耗尽 [证据1] → 调度器无法满足调度条件导致 Pod 处于 Pending 状态 [证据3]
```

### 根因结论

已确认的根因为**集群 CPU 资源耗尽**。

证据表明，集群中可用的 3 个节点均因 CPU 资源不足而无法容纳该 Pod（`3 Insufficient cpu`）[证据1]。由于集群中没有 CPU 资源需求更低的 Pod 可供抢占（`No preemption victims found`），调度器无法强制调度 [证据1]。导致这一现象的具体触发原因是该 Pod 配置了极其异常的 CPU 资源请求和限制 `100k` [证据2]。当前所有证据一致指向 CPU 资源短缺是导致 Pod 无法调度的决定性因素。

---

## 📊 性能统计

```text
├─ 总耗时: 56.5s
├─ 问题定位: 14.3s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-v01/workload: 32.3s (Evidence 27.9s, RCA 4.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
