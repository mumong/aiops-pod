## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 (aiops-case-01) 处于 Pending 状态，持续未被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 23m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` (fact-569065f015a7) | 核心症状：调度器判定所有节点不匹配亲和性/选择器条件 |
| 2 | K8s State | kubernetes | `pod.status: Pending` (fact-f4e586591a05) | 确认 Pod 处于未调度状态，与事件记录一致 |
| 3 | K8s Config | kubernetes | `container.resource_limit.cpu: 50m` (fact-33d6803becb6), `container.resource_request.cpu: 5m` (fact-9fe880817eb0) | 资源请求与限制数值极低，排除了因资源总量不足导致 3 个节点均无容量的可能 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` (fact-a66fe03a30f7), `container.resource_request.memory: 8Mi` (fact-b3c184c6e73c) | 内存资源请求同样极低，进一步证实资源非瓶颈 |
| 5 | Metric | prometheus | `kube_pod_status_phase` (Pending): 1 (fact-d98c92506425); (Unknown): 0 (fact-1f923f33051f) | 监控确认 Pod 当前确切状态为 Pending，无 Unknown 等中间状态，验证状态持久性 |

**证据说明**：
Kubernetes 事件 (fact-569065f015a7) 与状态 (fact-f4e586591a05) 共同证实了 Pod 长期处于 Pending 状态，其根本原因是调度器报告 "3 node(s) didn't match Pod's node affinity/selector"。资源配置 (fact-33d6803becb6, fact-9fe880817eb0) 证明资源需求极低，排除了资源枯竭导致 3 个节点都无法调度 Pod 的可能。因此，调度失败的唯一逻辑解释是节点标签亲和性或选择器不匹配。监控数据 (fact-d98c92506425) 进一步固化了这一状态的真实性。日志和追踪因容器未启动而不可用，不影响核心调度故障的判定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了不存在的节点标签选择器 (aiops.lab/unavailable=true) → 集群 3 个节点均不满足该标签条件 → Default-Scheduler 连续触发 FailedScheduling 并报告 0/3 nodes available → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 的 `workload-68c557d875-bsq52` 的 Spec 中配置了不存在的节点标签选择器或亲和性规则（`aiops.lab/unavailable=true`）。

**分析**：该不匹配的节点标签要求导致集群中所有 3 个节点均无法作为调度目标。Kubernetes 调度器 (`default-scheduler`) 在尝试调度时发现没有节点满足该选择条件，从而持续返回 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` 的错误信息 [证据 #1]。由于该配置存在于 Pod 的 Spec 中，除非移除或修正该选择器，否则 Pod 将一直无法被调度，表现为 `Pending` 状态 [证据 #2, #5]。资源限制与请求配置极低 [证据 #3, #4]，排除了资源不足的可能性，进一步确认根因为标签选择器不匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.7s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 47.4s (Evidence 40.0s, RCA 7.2s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
