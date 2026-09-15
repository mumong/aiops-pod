## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 持续处于 Pending 状态且无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling` (fact-607d65981504)：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 确认调度失败且失败原因为标签不匹配 |
| 2 | K8s State | kubernetes | `pod.condition`: PodScheduled=False, reason=Unschedulable (fact-5f57dbf1eb54) | 确认 Pod 当前不可调度状态 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory`: 8Mi (fact-1203cf70fc42) | 确认资源请求极低，非资源耗尽导致 |
| 4 | K8s State | kubernetes | `pod.phase`: Pending (fact-54193ec52a0c) | 确认 Pod 持续停留在 Pending 状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase` value=1, label=Pending (fact-624b96014b5f) | 监控层面确认 Pod 处于 Pending 状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase` value=0, label=Running (fact-2ca1b2361a52) | 确认该 Pod 从未进入 Running 状态 |

**证据关联说明：**
Kubernetes 事件（#1）直接指出调度失败原因是“节点不匹配 Pod 的 node affinity/selector”，结合 K8s 状态（#2, #4）证实 Pod 因该原因持续无法调度。Metric 数据（#5, #6）从监控维度独立确认了该 Pod 长期处于 Pending 且未运行，排除了短暂调度异常的可能。资源配置（#3）显示资源需求极低，佐证了非资源瓶颈问题。Logging 与 Tracing 因容器未启动而未获取数据，不影响根因判断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含不存在的 nodeSelector 约束 (aiops.lab/unavailable=true) → 调度器评估集群全部 3 个节点均不匹配该标签 → Pod 被标记为 Unschedulable 且处于 Pending 状态 → 用户可见 Pod 持续 Pending 且无法运行
```

### 根因结论

**已确认根因：** Pod `aiops-case-01/workload-68c557d875-gtzc8` 配置了不存在的节点选择器 `aiops.lab/unavailable=true`。

**事实支撑：**
- 调度器事件明确指出 3 个节点均因“不匹配 Pod 的 node affinity/selector”而被排除（证据 #1）。
- 集群当前共有 3 个节点（根据 `0/3 nodes` 信息推断），且无证据表明其中任一节点存在该特定标签，导致调度器无法找到任何可调度节点。
- 资源请求极低（证据 #3）且无资源争抢，进一步排除其他调度失败原因。

**结论：** 根因为 **标签配置错误**。Pod 期望调度至带有特定标签的节点，但集群中所有节点均未设置该标签，导致调度器无法将 Pod 分配至任何节点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.1s
├─ 并发证据采集: 42.1s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 42.1s (Evidence 33.3s, RCA 8.7s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
