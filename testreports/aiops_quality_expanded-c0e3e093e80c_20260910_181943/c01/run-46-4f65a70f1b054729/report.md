## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，调度失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-1edf46fe2a0e) | pod.phase: Pending | 确认 Pod 未处于运行状态 |
| 2 | K8s Event | kubernetes (fact-34ed293983d4) | FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 指出调度失败的直接原因：无节点匹配亲和性/选择器 |
| 3 | K8s State | kubernetes (fact-a97f8284e4a8) | pod.condition: PodScheduled=False, Reason=Unschedulable | 佐证调度器判定 Pod 不可调度 |
| 4 | K8s Config | kubernetes (fact-48dc6dfe6520) | pod.spec.nodeSelector: {aiops.lab/unavailable: "true"} | 提供导致调度的关键约束配置：节点需拥有此标签 |

**证据综合说明：**
Kubernetes 事件与状态事实相互印证，明确失败原因在于调度器无法匹配 `nodeSelector` 约束。配置事实确认了 Pod 要求节点具备 `aiops.lab/unavailable: true` 标签。结合事件事实（3 个节点均不匹配），可逻辑闭环地推断集群节点均未设置该标签，导致无法调度。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector=aiops.lab/unavailable=true → 集群节点无该标签匹配 → 调度器触发 FailedScheduling 事件 → Pod 维持 Pending 状态
```

### 根因结论

已确认的根因是：**Pod 声明了不存在的节点亲和性约束（`nodeSelector`）。**

Pod 配置要求节点必须具备 `aiops.lab/unavailable: true` 标签，但集群内的所有节点（3 个）均未设置此标签（证据 #2 指出 3/3 节点不匹配，证据 #4 确认了标签选择器的具体内容）。由于调度器无法找到满足该标签约束的节点，导致 Pod 持续处于 Pending 状态，无法被分配至任何工作节点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.2s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 40.7s (Evidence 33.3s, RCA 7.3s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
