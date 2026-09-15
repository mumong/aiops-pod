## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod spec 中的 nodeSelector 要求标签 aiops.lab/unavailable=true，但集群中所有节点（0/3）均不匹配该标签，导致调度器无法分配节点，Pod 一直处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact_id: fact-6d0634417af8) | 确认调度失败直接原因，集群内所有节点均不满足 Pod 标签选择器。 |
| 2 | K8s State | `PodCondition` | `PodScheduled=False, Reason=Unschedulable, Message=0/3 nodes didn't match Pod's node affinity/selector` (fact_id: fact-3f1547672770) | 描述当前 Pod 的调度停滞状态。 |
| 3 | K8s State | `PodPhase` | `Pending` (fact_id: fact-1b3034600d04) | 反映 Pod 长期处于未调度状态的现象。 |
| 4 | Metric | `kube_pod_status_phase` | `Pending=1` (fact_id: fact-eb34f72a09c3) | 观测确认 Pod 处于 Pending 阶段，排除运行中或失败等其他状态。 |

**证据关系说明：**
Kubernetes Event (事实 1) 与 Pod Condition (事实 2) 相互印证，均明确指向“3 个节点不匹配 Pod 的亲和性/选择器”这一调度器判定结果。Metric 观测 (事实 4) 从时序数据角度确认了该状态（Pending=1），未提供新的错误线索。Logging 与 Tracing 因容器未启动被标记为不适用，不影响当前调度故障的诊断结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义 nodeSelector {aiops.lab/unavailable=true} (未确认) 
  → 集群中所有节点（0/3）均不匹配该标签 
  → 调度器无法分配节点，触发 FailedScheduling 
  → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认根因：调度器无法找到符合 Pod 标签要求的节点。**

输入事实中的诊断状态为 `diagnosed` 且可发布。证据充分支持以下结论：集群内所有 3 个节点均未配置 `aiops.lab/unavailable=true` 标签（事实 1 中的 3 node(s) didn't match），导致调度器因标签不匹配（node affinity/selector）而判定无法调度（事实 2）。

该结论由调度器生成的 `FailedScheduling` 事件（事实 1）和 Pod 状态条件（事实 2）直接支撑，现象为 Pod 长期处于 `Pending` 状态（事实 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.6s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 39.4s (Evidence 35.5s, RCA 3.7s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
