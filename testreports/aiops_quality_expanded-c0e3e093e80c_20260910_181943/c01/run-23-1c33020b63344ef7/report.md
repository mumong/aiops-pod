## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 调度约束 nodeSelector {aiops.lab/unavailable: true} 与集群节点实际标签不匹配，导致 0/3 节点满足亲和性要求，持续无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Pending` (fact-4b4ea98126ee) | 确认 Pod 处于未调度完成的状态。 |
| 2 | K8s State | `pod.condition` | `PodScheduled=False; Reason=Unschedulable; Message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` (fact-52556576a60c) | 明确指出调度失败原因为节点亲和性/选择器不匹配。 |
| 3 | K8s Event | `event.message` | `FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` (fact-378f5a60b777) | 调度器持续报错，佐证上述状态条件。 |
| 4 | K8s State | `pod.status` | `Pending` (fact-90d7e61e7577) | 进一步确认 Pod 的静态运行状态。 |
| 5 | K8s Config | `container.resource_limit.memory` | `32Mi` (fact-19db6cbb3cbe) | 资源限制配置（排除资源耗尽导致的调度失败）。 |
| 6 | K8s Config | `container.resource_request.memory` | `8Mi` (fact-60b79968d320) | 资源请求配置。 |

**证据关联说明：**
1 与 4 提供了 Pod 处于 `Pending` 状态的直接状态证据。2 与 3 提供了状态为 `Pending` 的确切原因（`Unschedulable`），且错误消息中的 `0/3 nodes` 与 `node affinity/selector` 不匹配描述，在逻辑上排除了资源不足或节点不可用等其他调度失败因素。5 与 6 的轻量级资源请求（8Mi/32Mi）进一步印证了 2 和 3 指出的“非资源原因”。日志与追踪数据为空是因为容器未启动，与调度失败的现象一致。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：Pod 声明 nodeSelector: {aiops.lab/unavailable: true}
→ 失败机制：集群节点实际标签缺失该键值对，无法满足选择器约束
→ 直接失败：调度器评估 3/3 节点均不匹配，拒绝分配，返回 FailedScheduling
→ 用户可见现象：Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 调度约束与集群节点标签不匹配**。

输入事实明确指出 Pod 声明了 `nodeSelector: {aiops.lab/unavailable: true}`（参见诊断描述），但 `pod.condition` (fact-52556576a60c) 和 `event.message` (fact-378f5a60b777) 均显示调度器报告“0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector”。这证明了集群内没有任何节点具备该标签，导致调度器无法找到满足条件的节点。

---

## 📊 性能统计

```text
├─ 总耗时: 56.2s
├─ 问题定位: 17.0s
├─ 并发证据采集: 28.3s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 28.3s (Evidence 21.9s, RCA 6.3s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
