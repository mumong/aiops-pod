## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod配置了nodeSelector要求节点必须拥有标签'aiops.lab/unavailable=true'，但集群中所有可用节点均无此标签，导致调度器无法满足亲和性约束，Pod持续处于Pending状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `Pending` | 确认 Pod 未进入运行状态。 |
| 2 | K8s Event | FailedScheduling | `Warning FailedScheduling 27m (x8 over 62m) ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 直接证明调度器因亲和性/选择器约束不匹配而持续拒绝调度。 |
| 3 | K8s State | pod.condition | `PodScheduled: False` (reason: Unschedulable) | 同步状态表明调度条件从未满足。 |
| 4 | Metric | kube_pod_status_phase | `1` (Pending) | 验证当前处于 Pending 状态，且 `Unknown` 态为 0。 |

由于 Pod 处于 Pending 状态，K8s 诊断确认调度约束冲突导致无法调度。Logging 和 Tracing 维度因容器未启动且物理上无法产生日志/流量而显示为空或查询失败。K8s 配置层面的资源请求（CPU `5m`/内存 `8Mi`）极小，排除资源配额导致不可调度的可能，结合 Event 信息，证据链指向明确的亲和性标签不匹配。

## 🎯 根因分析 · g1

### 因果链
```text
Pod配置了nodeSelector要求标签'aiops.lab/unavailable=true' → 集群节点缺失该标签 → 调度器无法满足亲和性约束 → Pod持续处于Pending状态
```

### 根因结论
已确认的根因是 Pod 的调度约束与集群节点状态不匹配（证据编号：1, 2, 3）。Pod 配置了必须匹配标签 `aiops.lab/unavailable=true` 的调度要求，但集群中所有节点均不具备此标签，导致 `default-scheduler` 无法分配任何节点，Pod 持续处于 `Pending` 且调度状态为 `False`。现有证据充分，无需补充日志或 Trace 数据即可判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 24.7s
├─ 并发证据采集: 51.3s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 51.3s (Evidence 46.3s, RCA 4.9s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
