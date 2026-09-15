## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload in aiops-case-v01 is stuck in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 30m (x6 over 55m) default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 直接证明调度器因集群 CPU 资源不足拒绝调度，且无法通过抢占解决。 |
| 2 | K8s State | kubernetes | `Pod status: Pending` | 描述 Pod 当前停滞的异常状态。 |
| 3 | Metric | prometheus | `kube_pod_status_phase = 1` (labels: `phase=Pending`, `sample_count=1`, `trend_evaluable=false`) | 从监控维度独立观测并确认 Pod 停留在 Pending 状态。 |

**证据关联与印证**：
1. K8s 事件（#1）直接指出失败原因是 `Insufficient cpu`，说明集群层面资源耗尽是导致调度失败的根源。
2. Metric 观测结果（#3）与 K8s 状态（#2）相互印证，确认该异常已持续且处于停滞状态。
3. Logging 和 Tracing 维度因容器未启动物理上无法采集，排除应用层逻辑错误。

## 🎯 根因分析 · g1

### 因果链

```text
Cluster CPU resource exhaustion → 0/3 nodes available due to Insufficient cpu, no preemption victims found → Pod scheduling rejected by default-scheduler → Pod stuck in Pending phase
```

### 根因结论

已确认根因为：**集群 CPU 资源耗尽（Cluster CPU resource exhaustion）**。

- **机制分析**：集群中所有 3 个节点均报告 CPU 资源不足，且无法找到可抢占的受害者，导致 `default-scheduler` 拒绝调度请求（证据 #1）。
- **现象确认**：Pod 因此一直停留在 Pending 状态，无法进入 Running 阶段（证据 #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 13.4s
├─ 并发证据采集: 558.1s
│  └─ g1 aiops-case-v01/workload: 558.1s (Evidence 551.5s, RCA 6.4s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
