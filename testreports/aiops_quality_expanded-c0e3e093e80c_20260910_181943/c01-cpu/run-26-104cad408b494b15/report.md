## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，持续报 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition (fact-7915f3ab13d6) | PodScheduled=False; reason=Unschedulable; message="0/3 nodes are available: 3 Insufficient cpu" | 确认 Pod 处于不可调度状态，直接原因是 CPU 不足 |
| 2 | K8s State | pod.phase (fact-4988fcae3dd0) | phase=Pending | 确认 Pod 持续停留在 Pending 状态 |
| 3 | K8s Event | event.message (fact-5279f4c698f3) | Warning FailedScheduling 8m54s (x6 over 33m) 3 Insufficient cpu. No preemption victims found | 证实调度器在过去 33 分钟内反复尝试失败，且无法通过抢占解决 |
| 4 | K8s Config | container.resource_request.cpu (fact-164b1041f1db) | value=100k (container: app) | 确认该 Pod 请求 0.1 CPU 资源，但集群节点无余量可满足 |

**证据总结：**
K8s 事件与状态事实互相印证：Pod 因 Insufficient cpu 被调度器拒绝，且所有 3 个节点均无预emption 对象。日志与链路追踪未采集到数据，符合 Pod 未启动的物理状态，无冲突证据。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点可分配 CPU 资源耗尽 → Pod cpu=100k 请求无法满足且无抢占对象 → 调度器返回 Unschedulable → Pod 保持 Pending 并触发 FailedScheduling
```

### 根因结论

已确认根因为**集群可用 CPU 资源枯竭**。
证据编号 [1, 2, 3] 显示 3/3 节点均报告 "Insufficient cpu"，且缺乏可抢占的 Pod（"No preemption victims found"），导致调度器无法将 `aiops-case-v01/workload` 放置在任何节点上。
**未知点**：当前证据未能识别具体是哪个工作负载占满了这 3 个节点的可分配 CPU 资源。

---

## 📊 性能统计

```text
├─ 总耗时: 57.3s
├─ 问题定位: 15.7s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-v01/workload: 33.9s (Evidence 26.3s, RCA 7.5s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
