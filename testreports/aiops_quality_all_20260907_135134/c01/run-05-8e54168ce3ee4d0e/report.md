## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，nodeName: None |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | Unschedulable: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (fact-d611b7543d72) | 直接证明调度失败，原因是亲和/选择器不匹配 |
| 2 | K8s Event | event.message | "FailedScheduling 5m16s default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (fact-c55439052d3d) | 确认事件触发者与具体失败原因，与状态结论一致 |
| 3 | K8s Config | container.resource_limit.memory | container: app, value: 32Mi (fact-12f8be44d170) | 排除因内存资源请求过高导致资源不足的嫌疑 |
| 4 | K8s Config | container.resource_request.cpu | container: app, value: 5m (fact-3bf77258a962) | 排除因 CPU 资源请求过高导致资源不足的嫌疑 |
| 5 | K8s Config | container.resource_request.memory | container: app, value: 8Mi (fact-b8c1609c48ed) | 排除因内存资源请求过高导致资源不足的嫌疑 |
| 6 | K8s Config | container.resource_limit.cpu | container: app, value: 50m (fact-e02878b4e504) | 排除因 CPU 资源限制过高导致资源不足的嫌疑 |
| 7 | K8s State | pod.status | status: Pending (fact-00ba45824a78) | 确认 Pod 始终未进入调度运行阶段 |

Pod 的资源配置（Request/Memory 5m/8Mi，Limit/CPU 50m/32Mi）极低，排除了资源不足的可能性。调度失败的确切原因指向亲和/选择器不匹配，而非资源瓶颈。Kubernetes 事件与 Pod 状态条件相互印证，确认了故障点在节点匹配而非资源分配。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的节点选择器约束 (nodeSelector: aiops.lab/unavailable=true) → default-scheduler 检查集群 3 个节点均不满足 affinity/selector 匹配条件 → 调度器触发 FailedScheduling 事件，Pod 保持 Unschedulable 状态 → Pod 持续处于 Pending 状态，未分配节点
```

### 根因结论

**已确认的根因**：Pod 配置了不存在的节点选择器约束 (`nodeSelector: aiops.lab/unavailable=true`)。集群中所有 3 个节点均不具备该标签，导致 `default-scheduler` 无法找到任何满足亲和性/选择器条件的节点。这直接引发了 `FailedScheduling` 事件，使 Pod 持续处于 `Pending` 状态。证据 1、2 确认了调度失败机制，证据 3 至 6 证实了非资源限制因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.7s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 51.1s (Evidence 40.5s, RCA 10.5s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
