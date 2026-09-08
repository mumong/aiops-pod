## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了不可满足的 nodeSelector (aiops.lab/unavailable=true)，集群所有节点均缺失该 label，导致调度器永久过滤所有节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact-2928ce6028b9) | 核心证据，证明调度器因节点标签不匹配（节点亲和性/选择器）而拒绝调度，且尝试抢占均告失败。 |
| 2 | K8s Event | default-scheduler | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` (fact-51670d13ef24) | 辅助证据，确认调度失败现象持续发生且未被解决。 |
| 3 | K8s State | Pod Condition | `PodScheduled: False, Reason: Unschedulable, Message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` (fact-5a50fc6d4fee) | 确认 Pod 当前处于不可调度状态，且明确归因于节点亲和性/选择器不匹配。 |
| 4 | K8s State | Pod Status | `Pending` (fact-42760c813b04), `Pending` (fact-f06de7614b03) | 确认 Pod 处于 Pending 状态，未进入运行状态。 |
| 5 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (fact-1033d9faafb1) | 提供指标侧视角，确认目标 Pod 处于 Pending 状态。 |

**证据说明：**
Kubernetes 事件（#1, #2）与 Pod 状态（#3, #4）高度一致，均明确指出 0/3 节点匹配 Pod 的亲和性/选择器规则。Metric 数据（#5）从系统指标层面佐证了 Pod 的 Pending 状态。日志与追踪数据因容器未启动且工具调用受阻，无法获取，但 Kubernetes 层面的调度失败原因已充分且确凿，足以支撑根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不可满足的 nodeSelector (aiops.lab/unavailable=true) → 调度器过滤全部 3 个节点（均未设置该标签） → 调度器返回 FailedScheduling 且预抢占无效 → Pod 永久处于 Pending (Unschedulable) 状态
```

### 根因结论

**已确认的根因**是 Pod 配置了不可满足的 `nodeSelector`（或节点亲和性）条件（具体为 `aiops.lab/unavailable=true`），而集群内所有节点均缺失该 Label。

该配置导致 Kubernetes 调度器在调度阶段永久过滤了所有候选节点，且由于无可用节点，预抢占机制也无法生效（证据 #1, #2, #3）。这与 Pod 长期处于 `Pending` 状态且 `PodScheduled` 条件为 `False`（证据 #3, #4, #5）的现象完全吻合。现有的 Kubernetes 状态与事件证据已经充分且闭环，无需额外的日志或拓扑数据即可确定根因。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 13.3s
├─ 并发证据采集: 567.6s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 567.6s (Evidence 561.8s, RCA 5.6s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
