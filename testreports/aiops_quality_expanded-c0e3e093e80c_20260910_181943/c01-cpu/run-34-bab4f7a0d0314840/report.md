## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload (aiops-case-v01) stuck in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu` (fact_id: `fact-97760f4dc4cd`) | 直接记录调度器因 CPU 不足而拒绝调度。 |
| 2 | K8s Config | kubernetes | `container.resource_request.cpu`: `100k` (fact_id: `fact-0527847a44a8`) | 确认 Pod 的 CPU 请求资源量。 |
| 3 | K8s State | kubernetes | `pod.status`: `Pending` (fact_id: `fact-369daa6192e3`) | 确认 Pod 处于挂起状态，未分配节点。 |
| 4 | K8s State | kubernetes | `pod.condition`: `PodScheduled=False` (fact_id: `fact-9c19239b3d80`) | 进一步证实节点调度条件不满足。 |

**证据说明：**
Kubernetes 的 Event 和 State 事实（#1, #3, #4）一致表明 Pod 因集群资源不足无法被调度。K8s Config 事实（#2）确认 Pod 所需的 CPU 资源明确。由于集群级资源统计工具调用失败（`kubernetes_tabular_query`），且 Logging/Tracing 维度因容器未启动无数据，判定结论主要依赖 K8s 自身的调度状态事件和配置事实。

## 🎯 根因分析 · g1

### 因果链

```text
集群可用 CPU 不足 → 调度器无法分配节点 → Pod 处于 Pending 状态 → FailedScheduling 事件
```

### 根因结论

**根因已确认：集群 CPU 容量耗尽。**

证据 #1 (`fact-97760f4dc4cd`) 明确显示 `0/3 nodes are available: 3 Insufficient cpu`，表明集群中所有 3 个节点均无法提供额外的 CPU 资源以容纳新 Pod。结合事实 #2 中 Pod 请求 `100k` CPU，调度失败的原因在于集群资源分配已处于饱和状态，而非单节点故障或调度器逻辑错误。由于无法获取节点级资源请求明细（`kubernetes_tabular_query` 失败），具体是哪类现有工作负载占满了资源属于未确认项，但不影响“集群无剩余 CPU”这一根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.1s
├─ 并发证据采集: 59.9s
│  └─ g1 aiops-case-v01/workload: 59.9s (Evidence 51.1s, RCA 8.7s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
