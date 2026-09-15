## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 nodeSelector {aiops.lab/unavailable: true}，但集群中所有可用节点均无此标签，导致调度器无法匹配任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition (fact-7f4b43adc6b2) | `type: PodScheduled, status: False, reason: Unschedulable, message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 证明 Pod 处于 Unschedulable 状态，且原因明确为节点亲和性/选择器不匹配。 |
| 2 | K8s Event | Scheduler Event (fact-f37883b2aec5) | `Warning FailedScheduling 16m (x13 over 76m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器持续拒绝调度，反复报出相同的标签不匹配错误。 |
| 3 | K8s Config | Pod Configuration (implied) | `nodeSelector {aiops.lab/unavailable: true}` | 提供导致调度失败的具体约束条件，即集群节点缺乏此特定标签。 |
| 4 | Metric | kube_pod_status_phase (fact-91abdc56d839) | `phase: Pending, value: 1` | 验证 Pod 持续处于 Pending 状态的客观数据。 |

上述证据链闭合：Pod 配置了 `aiops.lab/unavailable: true` 标签选择器，而集群所有可用节点均不满足该条件，导致调度器返回 `FailedScheduling` 事件且 Pod 状态锁定为 `Pending`。日志与追踪系统因容器未启动显示为空，符合调度阻塞的物理事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了集群节点不存在的 nodeSelector标签 {aiops.lab/unavailable: true} → 调度器无法匹配任何节点 → FailedScheduling 事件触发 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 的 nodeSelector 配置与集群节点标签不匹配**。

证据编号 #1 和 #2 明确显示所有 3 个可用节点均未匹配 Pod 的亲和性/选择器要求；证据 #3 指出具体的匹配标签 `aiops.lab/unavailable: true` 在集群中不存在。由于缺乏运行节点，Pod 无法进入 Scheduling 或 Running 阶段，进而导致 K8s State 层面表现为持续的 `Unschedulable` 和 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 57.6s
├─ 问题定位: 17.2s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 32.0s (Evidence 26.8s, RCA 5.1s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
