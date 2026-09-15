## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Cluster CPU resource exhaustion: All 3 available nodes lack sufficient CPU capacity to schedule the 'workload' pod, and no preemption candidates exist to free resources. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found (fact-d244c8b14eef) | 记录调度失败原因：集群所有节点 CPU 不足，且无抢占候选对象 |
| 2 | K8s State | kubernetes | PodScheduled=False, reason=Unschedulable, message=0/3 nodes are available: 3 Insufficient cpu (fact-9542c174ff3a) | 确认 Pod 实际状态为 Unschedulable，由 CPU 资源缺口导致 |
| 3 | K8s Config | kubernetes | CPU resource_request=100k, resource_limit=100k (fact-13e8877cb6d1) | 提供调度的资源约束基准，用于判断节点是否满足要求 |
| 4 | Metric | prometheus | kube_pod_status_phase(phase=Pending)=1, sample_count=1 (fact-42a27a457db8) | 从监控视角独立确认 Pod 仍处于 Pending 状态 |

* 事件（#1）与当前状态（#2）高度一致，明确将失败归因为“Insufficient cpu”且排除“Preemption”。
* 监控数据（#4）作为外部指标验证了调度器侧记录的状态（#2），排除了数据不一致的可能。
* 资源请求配置（#3）确立了故障的约束条件，但因缺少节点级别的 Allocatable/Requested 明细，无法判断是突发流量还是配置不合理。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源耗尽（0/3 节点可用） → 调度器无法满足 100k CPU 请求且无法执行抢占 → 调度失败（Unschedulable） → Pod 停留在 Pending 状态
```

### 根因结论

已确认的根因为：**集群 CPU 资源耗尽且缺乏抢占空间导致调度失败**。

证据链闭环：
1. 调度器明确报告 `0/3 nodes are available: 3 Insufficient cpu`（证据 #1, #2）；
2. 抢占机制因 `No preemption victims found` 失效（证据 #1）；
3. Pod 长期处于 `Pending` 状态（证据 #4）。

**未决项**：
目前缺乏 3 个节点具体的 CPU Allocatable 与 Requested 对比数据，无法进一步界定是“正常资源耗尽”、“资源碎片化”还是“其他非工作负载资源抢占”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.9s
├─ 并发证据采集: 35.2s
│  └─ g1 aiops-case-v01/workload: 35.2s (Evidence 26.9s, RCA 8.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
