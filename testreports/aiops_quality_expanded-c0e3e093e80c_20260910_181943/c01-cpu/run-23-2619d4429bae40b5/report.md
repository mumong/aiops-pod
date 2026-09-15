## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | aiops-case-v01/workload处于Pending状态，无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v01/workload` (fact-552add6e4869, fact-d34e2aa8eb54) | `status: Pending`, `phase: Pending` | 确认工作负载处于不可调度的停滞状态 |
| 2 | K8s Event | default-scheduler (fact-2c6d808a949a) | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient cpu` (发生2次) | 直接指明调度失败原因为节点 CPU 资源不足 |
| 3 | K8s State | Pod Condition (fact-6b34526ae6ee) | `PodScheduled=False`, `Unschedulable`: `0/3 nodes are available: 3 Insufficient cpu` (2026-09-11T05:28:07Z) | 提供调度失败的具体时间戳和系统判断依据 |
| 4 | K8s Config | Resource Request (fact-4fd8ee1b14c1) | `container.resource_request.cpu: 100k` | 定义该 Pod 对 CPU 资源的硬性调度需求（100 millicores） |
| 5 | K8s Config | Resource Limit (fact-0178ab468b77) | `container.resource_limit.cpu: 100k` | 确认 CPU 硬限制与请求量一致 |
| 6 | Metric | kube-state-metrics (fact-01abff560495) | `kube_pod_status_phase=1` (labels: phase="Pending", sample_count=1) | 确认集群监控中存在且仅存在一个处于 Pending 状态的 Pod |

**证据关联说明：**
事件（#2）与调度条件（#3）相互印证，确认集群中全部 3 个节点均无法满足该 Pod 对 100k CPU 的调度请求，且不存在抢占 victim。指标（#6）进一步从监控维度佐证了该 Pod 的停滞状态持续存在。由于容器始终未能调度启动，Logging 与 Tracing 维度物理上不可用，诊断完全基于 K8s 调度状态与配置。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有3个节点（master, node1, node2）的可用CPU < 100k (fact-4fd8ee1b14c1)
  → Scheduler 无法匹配任何节点满足 CPU request
    → 触发 FailedScheduling 事件，Pod 持续保持 Pending 状态 (fact-2c6d808a949a)
      → 用户可见 workload 无法调度启动
```

### 根因结论

**已确认根因：集群节点 CPU 资源不足（Insufficient cpu）且无抢占资源可用。**

该根因由 K8s Event `FailedScheduling` (fact-2c6d808a949a) 与 Pod Condition `Unschedulable` (fact-6b34526ae6ee) 确凿支撑。事实明确显示，集群全部 3 个节点均无法满足 Pod 对 `100k` CPU 的调度请求，且调度器未找到任何用于抢占的资源（`No preemption victims found`）。

**证据充分性说明：**
现有证据完整覆盖了从调度失败原因（CPU 不足）到最终现象（Pending 状态）的闭环，无需 Logging 或 Tracing 数据即可下结论。RCA 事实绑定正确，证据不足判定不适用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 39.6s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-v01/workload: 30.2s (Evidence 24.1s, RCA 6.0s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
