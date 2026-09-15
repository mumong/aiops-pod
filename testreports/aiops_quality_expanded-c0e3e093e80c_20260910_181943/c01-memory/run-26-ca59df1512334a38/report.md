## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod内存请求（1Pi）远超集群节点可用内存容量，导致调度器无法找到满足资源的节点，且集群资源紧张（所有节点内存耗尽）导致预抢占失败，Pod持续处于Pending状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | `resource_request.memory: 1Pi` (fact-00d61438d49a7d) | 提供引发异常的显性资源请求量，远超常规容量。 |
| 2 | K8s Config | kubernetes | `resource_limit.memory: 1Pi` (fact-00e407728d2dcef) | 确认内存硬限制与请求一致，排除资源超卖干扰。 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` (fact-00e9e0ff4a453b3) | 确证 Pod 未进入运行状态。 |
| 4 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory` (fact-015bf1800d1f) | 提供调度过失败的确切机制与集群资源状态。 |
| 5 | K8s State | kubernetes | `pod.condition: Unschedulable, No preemption victims found` (fact-00dcd5bfb13d136) | 证实集群全量节点耗尽，无法执行预抢占。 |
| 6 | Metric | prometheus | `kube_pod_status_phase(Pending) = 1` (fact-00eda29bd189686) | 监控指标证实 Pod 长期停留在 Pending 状态。 |

调度器事件（#4, #5）直接指出集群无可用内存且无法抢占，这一物理限制与 `1Pi` 的内存请求（#1, #2）形成完整的因果闭环，Metric（#6）进一步印证了该现象的持续性。由于 Pod 始终未调度成功，Logging 与 Tracing 维度缺失属于正常物理状态，不参与故障分析。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置内存请求1Pi → 调度器无法满足任何节点容量 → 预抢占无资源可牺牲 → Pod持续Pending
```

### 根因结论

已确认的根因为 `Pod内存请求（1Pi）远超集群节点可用内存容量`（依据证据 #1, #4, #5）。

该资源请求量级导致调度器在评估所有 3 个节点时均判定为 `Insufficient memory`，进而触发了 `No preemption victims found` 机制。集群整体资源耗尽使得 Pod 无法在任何节点上分配资源，从而维持 `Pending` 状态（依据证据 #3, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.8s
├─ 问题定位: 13.3s
├─ 并发证据采集: 31.6s
│  └─ g1 aiops-case-v02/workload: 31.6s (Evidence 26.8s, RCA 4.7s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
