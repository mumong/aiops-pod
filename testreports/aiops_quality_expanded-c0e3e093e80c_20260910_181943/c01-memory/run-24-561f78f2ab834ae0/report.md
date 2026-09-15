## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 remains in Pending state due to FailedScheduling (Insufficient memory) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-2714fd2a88ab` | Pod `status`: `Pending` | 确认 Pod 处于未调度状态 |
| 2 | K8s Config | `fact-dc51fdb2e564` | `container.resource_limit.memory`: `1Pi` | 暴露出极不合理的内存硬限制 |
| 3 | K8s Config | `fact-eb5d62533e00` | `container.resource_request.memory`: `1Pi` | 证明调度器必须寻址且无法超售 1Pi 内存 |
| 4 | K8s Event | `fact-3f3fc7aa0792` | `message`: `0/3 nodes are available: 3 Insufficient memory` | 确认所有节点因内存不足拒绝调度 |
| 5 | K8s Event | `fact-3f3fc7aa0792` | `message`: `preemption: 0/3 nodes are available: 3 No preemption victims found` | 确认集群没有可被踢出的低资源 Pod 来腾挪空间 |

**证据说明：**
Kubernetes 事件（#4, #5）直接证实了调度失败的原因是 `Insufficient memory`。K8s 配置证据（#2, #3）明确了具体的资源配置为 `1Pi`，这在物理集群中是不合理的，解释了为什么所有 3 个节点都会报内存不足。

## 🎯 根因分析 · g1

### 因果链

```text
Pod resource configuration specifies memory limit/request as 1Pi → Scheduler evaluates node capacity against 1Pi requirement → All 3 nodes report Insufficient memory and no preemption victims found → Pod remains unscheduled in Pending state
```

### 根因结论

已确认的根因是 **Pod 资源配置错误**。Pod 的 `resources.requests.memory` 和 `resources.limits.memory` 被错误地设置为 `1Pi`（1 Pebibyte）。由于这一数值远超集群中任何节点的可用内存，调度器无法在 3 个节点中的任何一个上找到满足条件的资源，导致调度失败（`FailedScheduling`）且无抢占（Preemption）机会，Pod 最终停留在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 50.4s
├─ 问题定位: 11.9s
├─ 并发证据采集: 30.7s
│  └─ g1 aiops-case-v02/workload: 30.7s (Evidence 22.7s, RCA 7.9s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
