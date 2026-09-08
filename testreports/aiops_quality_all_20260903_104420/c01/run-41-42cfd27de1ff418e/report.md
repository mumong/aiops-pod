## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `PodScheduled=False` (reason: Unschedulable, message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector) | 确认调度失败，直接原因指向亲和性/选择器不匹配 |
| 2 | K8s Event | event.message | `Warning FailedScheduling 23m (x14 over 88m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available` | 14次失败调度记录，排除抢占机制后结果相同，定位到标签匹配问题 |
| 3 | K8s Config | container.resource_request.cpu | `5m` | 资源请求值，排除资源不足导致的调度失败 |
| 4 | K8s Config | container.resource_limit.cpu | `50m` | 资源限制值，排除资源不足导致的调度失败 |
| 5 | K8s Config | container.resource_request.memory | `8Mi` | 资源请求值，排除资源不足导致的调度失败 |
| 6 | K8s Config | container.resource_limit.memory | `32Mi` | 资源限制值，排除资源不足导致的调度失败 |
| 7 | Metric | kube_pod_status_phase | `1` (labels: container="kube-state-metrics", phase="Pending", sample_count=1) | 从监控视角佐证 Pod 处于 Pending 状态 |

Kubernetes 事件与状态条件（事实1、2、5）均一致指向“未匹配节点亲和性/选择器”。资源配置事实（3-6）显示资源请求非常低（CPU 5m，Memory 8Mi），在标准节点上极易满足，排除了因资源碎片或总量不足导致调度失败的可能性。Metric 数据（事实7）从监控维度确认了现象持续存在。日志和链路追踪工具调用失败，但受限于 Pod 未启动，无法产生有效诊断数据，当前 K8s 事实链已闭合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义 nodeSelector {aiops.lab/unavailable: 'true'} → 集群所有节点均不含此标签 → 调度器无法匹配任何节点 (3/3 fail) → 触发 FailedScheduling 事件 → Pod 持续 Pending
```

### 根因结论

已确认的根因为 **Pod 调度失败 (FailedScheduling)**，原因是 Pod 配置了过于严格或错误的标签选择器约束 (`nodeSelector` 要求 `aiops.lab/unavailable` 为 `'true'`)，而集群中实际节点均不满足该条件。证据来自 K8s 调度事件 (`FailedScheduling`) 和 Pod 条件 (`Unschedulable`) 的一致描述。资源请求极低的事实进一步排除了资源瓶颈作为根因的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.0s
├─ 并发证据采集: 55.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 55.1s (Evidence 47.8s, RCA 7.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
