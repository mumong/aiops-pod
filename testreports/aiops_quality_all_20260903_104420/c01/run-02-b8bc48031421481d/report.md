## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了 nodeSelector {aiops.lab/unavailable: true}，但集群中所有节点均未包含该标签，导致调度器无法找到满足条件的节点，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-972d4cc6ec23) | `FailedScheduling  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 证明调度器因节点标签不匹配而明确拒绝了 Pod 的调度请求。 |
| 2 | K8s State | kubernetes (fact-a1d877be1470) | `PodScheduled` condition is `False`，原因 `Unschedulable`，消息确认 `3 node(s) didn't match Pod's node affinity/selector`。 | 从 Pod 状态层面确认当前 Pod 无法被分配到任何节点。 |
| 3 | K8s State | kubernetes (fact-15ce4b3dd4f5) | `pod.phase` = `Pending`。 | 确认 Pod 当前所处的异常生命周期阶段。 |
| 4 | Metric | prometheus (fact-48be760c029e) | `kube_pod_status_phase` 显示 `Pending` 状态值为 `1`。 | 通过监控系统独立确认 Pod 处于 Pending 状态，与 K8s 状态一致。 |
| 5 | K8s Config | kubernetes (fact-11da8eab9320) | `container.resource_request.memory` = `8Mi`。 | 提供资源申请量的上下文，说明资源请求本身未超出常规极值。 |

**证据印证说明：**
Kubernetes 事件与 Pod 状态（编号 1、2、3）共同指向了确切的拒绝原因：节点标签不匹配。Metric 数据（编号 4）独立证实了该 Pod 确实持续卡在 Pending 状态。资源配置数据（编号 5）排除了因资源请求异常导致的调度阻塞可能，进一步锁定问题在于节点选择器逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector {aiops.lab/unavailable: true} 而集群节点缺失该标签 → 调度器节点匹配失败 → 触发 FailedScheduling 事件并标记 Pod 为 Unschedulable → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 **调度器因节点标签不匹配而无法调度 Pod**（支撑事实：编号 1、2）。

Pod 被配置了特定的 `nodeSelector` 要求，但集群现有的 3 个节点均未包含该标签，导致调度器找不到任何满足条件的节点进行分配。这一机制直接导致了调度失败事件（编号 1）的生成以及 Pod 状态长期保持为 Pending（编号 3、4）。虽然日志（Logging）与追踪（Tracing）数据因容器未启动而缺失，但 Kubernetes 的控制平面状态与事件已充分证明了调度失败的根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.4s
├─ 并发证据采集: 59.8s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 59.8s (Evidence 53.9s, RCA 5.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
