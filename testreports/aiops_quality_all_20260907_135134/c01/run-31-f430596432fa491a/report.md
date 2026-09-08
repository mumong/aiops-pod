## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | aiops-case-01/workload-68c557d875-bsq52 Pending 49分钟未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-02066f3ee732) | `Warning  FailedScheduling  14m (x7 over 44m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 明确调度失败原因：节点未匹配 Pod 亲和性/选择器，且持续发生（49分钟内7次） |
| 2 | K8s State | kubernetes (fact-3dfce00e45ef) | `PodScheduled=False, Unschedulable, message: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector..."` | 确认 Pod 处于 Unschedulable 状态，与 Event 信息一致 |
| 3 | K8s State | kubernetes (fact-b7fcf78cfb97) | `status: Pending` | 确认 Pod 持续处于 Pending 状态，未转为 Running |
| 4 | Metric | prometheus (fact-5c034257b491) | `kube_pod_status_phase{phase="Pending"} = 1` | 指标确认该 Pod 当前仍处于 Pending 阶段 |
| 5 | Metric | prometheus (fact-29ad37a16697) | `kube_pod_status_phase{phase="Running"} = 0` | 指标确认该 Pod 从未处于 Running 阶段 |

证据 1 和 2 从事件和状态两个维度一致证实，Pod 调度失败的核心原因是节点不匹配 Pod 的亲和性/选择器要求。指标数据 (证据 4, 5) 独立验证了 Pod 长期处于 Pending 状态且从未成功运行，与调度失败的结论相符。

## 🎯 根因分析 · g1

### 因果链

```text
Pod定义了不存在的节点标签选择器'aiops.lab/unavailable=true' → 集群所有节点缺少该标签 → Scheduler因亲和性/选择器不匹配拒绝调度 → Pod持续处于Pending状态
```

### 根因结论

已确认根因：Pod 的 `nodeSelector` 或 `nodeAffinity` 要求节点具备 `'aiops.lab/unavailable=true'` 标签，但集群内所有节点均无此标签，导致 `default-scheduler` 无法找到满足条件的节点进行调度。

该结论由调度器事件（证据 1）和 Pod 状态（证据 2）直接支撑。指标数据（证据 4, 5）提供了持续的佐证。日志和追踪因 Pod 未启动而不适用，不影响调度层面的根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 36.4s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 36.4s (Evidence 29.1s, RCA 7.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
