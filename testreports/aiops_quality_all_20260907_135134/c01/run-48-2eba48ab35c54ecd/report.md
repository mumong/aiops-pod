## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，持续 64 分钟未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning FailedScheduling ... 4m8s (x13 over 64m) ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认调度失败的根本原因是亲和性/选择器不匹配，故障持续 64 分钟。 |
| 2 | K8s State | `kubernetes` | `pod.condition` PodScheduled=False, `phase=Pending` | 确认 Pod 目前处于无法进入运行的等待状态。 |
| 3 | K8s Config | `kubernetes` | `container.resource_request.cpu=5m`, `memory=8Mi` | 资源请求极小，排除因资源耗尽导致调度失败的可能。 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase{phase="Pending"}=1` | 独立监控数据证实该 Pod 确实长时间处于 Pending 状态。 |

**证据关联说明**：
Kubernetes Event (fact-b080c874492b) 直接指出调度失败是因为“didn't match Pod's node affinity/selector”。Metric 监控 (fact-368585a9fc5d) 证实 Pod 状态与 Pod 资源请求量极小 (fact-0415e5265c11) 的事实不冲突，排除了资源不足导致无节点可用的情况。日志和追踪无数据是因容器未启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector 约束 → 集群所有节点（3个）不满足该标签匹配规则 → Scheduler 触发 FailedScheduling → Pod 状态保持 Pending 达 64 分钟
```

### 根因结论

**已确认的根因**：Pod 的调度约束与集群节点标签不匹配。

根据事实 `fact-b080c874492b`（FailedScheduling 事件）与 `fact-227f115934b4`（Unschedulable 状态），Pod 因为 `node affinity/selector` 不匹配而失败，3个节点均未被选中。结合 `fact-0415e5265c11` 和 `fact-8dd5efe3b187` 极小的资源请求（5m CPU, 8Mi 内存），可排除资源瓶颈，确认为逻辑标签匹配失败导致无法调度。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.8s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 38.3s (Evidence 30.1s, RCA 8.1s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
