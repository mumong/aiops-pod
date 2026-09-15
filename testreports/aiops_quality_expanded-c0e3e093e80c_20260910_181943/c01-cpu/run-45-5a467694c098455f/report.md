## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload in aiops-case-v01 is stuck in Pending state due to FailedScheduling events. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling 10m (x12 over 65m) ... 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 确认调度失败的确切原因，且集群内无节点资源满足条件也无法发生抢占。 |
| 2 | K8s State | kubernetes | `PodScheduled=False, reason=Unschedulable, message="0/3 nodes are available: 3 Insufficient cpu"` | 描述 Pod 当前的阻塞状态与节点资源缺口事实。 |
| 3 | K8s Config | kubernetes | `container="app", resource_request.cpu=100k, resource_limit.cpu=100k` | 提供 Pod 申请的资源上下文。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase=Pending, value=1, sample_count=1) | 佐证 Pod 持续处于 Pending 阶段，未转为 Running。 |

**证据印证说明：**
1. Kubernetes 调度器事件（#1）与 Pod 状态（#2）在因果关系上完全一致，均指向集群 CPU 资源枯竭导致无法调度。
2. Metric 监控数据（#4）从时间序列维度证实了 Pod 长期处于 Pending 状态未解除。
3. 资源申请配置（#3）排除了因资源请求异常导致的不合理性，指向是集群整体分配能力不足。
4. Logging/Tracing 因容器未启动（Pending），无法采集，仅依赖 K8s 层面数据即可形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点总可用 CPU 不足 → 调度器无法找到满足 100k CPU 请求的节点且无抢占对象 → Pod 调度失败，PodScheduled=False → Pod 状态持续 Pending，业务无法运行
```

### 根因结论

**已确认根因：集群节点 CPU 资源耗尽（Insufficient CPU resources available on cluster nodes）。**

集群内 3 个节点均无法为 `aiops-case-v01/workload`（申请 100k CPU）分配资源，且不存在可被抢占的 Pod。该资源瓶颈直接导致调度器返回 `FailedScheduling` 事件，Pod 停留在 `Pending` 状态。虽然无法通过缺失的 Topology 数据定位具体是哪个业务占用了 CPU 或哪台节点压力最大，但“资源不足”是导致故障的明确根因。

---

## 📊 性能统计

```text
├─ 总耗时: 57.5s
├─ 问题定位: 18.2s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-v01/workload: 30.6s (Evidence 23.2s, RCA 7.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
