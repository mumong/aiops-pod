## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 配置了 nodeSelector `aiops.lab/unavailable=true`，但集群中所有节点均不满足此标签选择器，导致 DefaultScheduler 连续 42 分钟返回 FailedScheduling 事件，使 Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes (default-scheduler) | `Warning  FailedScheduling  42m ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` (`fact-b934c1d82854`) | 直接表明调度失败，原因是所有 3 个节点均不匹配 Pod 的亲和性/选择器条件。 |
| 2 | K8s State | Kubernetes | Pod 状态为 `Pending` (`fact-f183b025ffd7`) | 确认 Pod 未启动，与调度失败的预期现象一致。 |
| 3 | K8s Config | Kubernetes | Pod 配置 `container.resource_request.memory`: 8Mi, `cpu`: 5m (`fact-0c9d94d42a67`, `fact-ea467203429f`) | 资源请求极低，排除因资源不足导致调度失败的可能性。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 值为 `1`，Phase 为 `Pending` (`fact-ddeb76a28f0a`) | 监控数据佐证 Pod 长期处于 Pending 状态，无其他运行阶段转换。 |

**证据关联说明：**
1 号和 2 号证据共同确认了 Pod 因调度问题长期处于 Pending 状态。3 号证据排除了资源竞争因素，指向调度逻辑或标签匹配问题。4 号证据从监控视角固化了这一持续状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了 nodeSelector: aiops.lab/unavailable=true → 集群 3 个节点均不匹配该 nodeSelector 条件 → DefaultScheduler 执行 0/3 节点可用性检查并拒绝调度 → Pod 状态保持 Pending 且 node 字段为 <none>
```

### 根因结论

已确认的根因为 Pod 配置了无法被集群中任何节点满足的 `nodeSelector` 标签选择器（`aiops.lab/unavailable=true`）。

该配置导致 DefaultScheduler 在调度时进行节点亲和性/选择器匹配失败（证据 1、3），且集群中不存在满足该标签的节点，使得抢占机制也无法解决问题。最终 Pod 持续处于 Pending 状态（证据 2、4）。

证据 1 明确指出 `3 node(s) didn't match Pod's node affinity/selector`，结合证据 3 中极低的资源请求，排除了资源不足的可能，直接指向标签匹配失败是唯一的故障原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 40.3s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 33.4s (Evidence 26.0s, RCA 7.3s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
