## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.condition` type=PodScheduled, status=False, reason=Unschedulable, message="0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector..." (fact-fb22295f15b9) | 确认 Pod 处于 Unschedulable 状态，且直接原因为节点标签不匹配 |
| 2 | K8s Event | kubernetes | `FailedScheduling` 事件: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector." (fact-dd844e849c96) | 调度器日志确认所有节点均因亲和性/选择器不匹配而被拒绝 |
| 3 | K8s Config | kubernetes | `resource_limit.memory`=32Mi, `resource_limit.cpu`=50m, `resource_request.memory`=8Mi, `resource_request.cpu`=5m (fact-0c409191ff15, fact-2009d5424ec1, fact-2c338212467b, fact-3cc4ba39f3bb) | 排除资源配额超限导致调度失败的可能性 |
| 4 | Metric | prometheus | `kube_pod_status_phase` phase=Pending 值为 1 (fact-641f6ed7b538) | 独立确认 Pod 当前生命周期状态为 Pending |

**证据说明：**
1. 调度器事件 (证据 2) 与 Pod 状态条件 (证据 1) 相互印证，明确指出了失败机制为“node affinity/selector”不匹配，而非资源不足（证据 3 证实资源限制极低且无相关警告）。
2. 监控指标 (证据 4) 从外部视角确认了 Pod 卡在 Pending 状态，佐证了调度动作未成功执行。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector: aiops.lab/unavailable=true → 集群节点缺乏匹配标签 → 调度器触发 FailedScheduling 事件 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因：Pod 配置了错误的 nodeSelector (`aiops.lab/unavailable=true`)，导致调度失败。**

该 Pod 被强制要求运行在拥有标签 `aiops.lab/unavailable=true` 的节点上，但集群中所有 3 个节点均不具备此标签。这一配置错误直接导致调度器无法找到任何满足条件的节点，触发 `FailedScheduling` 事件（证据 1, 2）。资源限制配置（证据 3）极小且非瓶颈，进一步排除了资源竞争作为故障原因的可能性，确认为标签配置错误引发的调度死锁。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.0s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 55.2s (Evidence 46.9s, RCA 8.1s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
