## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes/fact-5f53457ad245 | `FailedScheduling`: 32m (x14 over 97m), 3 node(s) didn't match Pod's node affinity/selector | 确立核心故障现象：集群中不存在匹配该 Pod 调度约束的节点 |
| 2 | K8s State | kubernetes/fact-6f700ceca84c | `Unschedulable`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 验证调度器判定逻辑：预emption（抢占）也无法解决问题，指向硬性配置约束 |
| 3 | Metric | prometheus/fact-0af698363a4d | `kube_pod_status_phase` for phase=Unknown = `0` | 排除因节点或集群层面异常导致的 Pod 状态不明（Unknown），确认问题局限于调度阶段 |
| 4 | K8s State | kubernetes/fact-0e227d4b3ac8 | `PodScheduled` 条件为 `False` | 确认调度条件未满足，Pod 停留在 Pending 状态 |

**证据说明：**
K8s Event 与 Pod Condition 相互印证，明确指出调度失败的原因为“节点不匹配”（didn't match Pod's node affinity/selector），且预emption 机制无效。Metric 数据排除了节点异常状态导致的不可调度。根据调度器给出的匹配失败原因，直接指向 Pod 规范中的亲和性或选择器配置存在集群节点无法匹配的值。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 配置 nodeSelector: {"aiops.lab/unavailable": "true"} → 集群所有节点均无此标签 → 调度器判定 0/3 节点可用 → Pod 持续 Pending/Unschedulable
```

### 根因结论
已确认的根因是 Pod 的调度约束配置不当。Pod 配置了 `nodeSelector`（或节点亲和性），要求节点必须具有标签 `aiops.lab/unavailable=true`，但当前集群中的所有节点均不具备该标签，导致调度器无法为 Pod 找到任何可运行的节点。证据编号：fact-5f53457ad245（节点不匹配错误）、fact-6f700ceca84c（调度条件失败详情）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.7s
├─ 并发证据采集: 45.6s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 45.6s (Evidence 37.5s, RCA 8.0s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
