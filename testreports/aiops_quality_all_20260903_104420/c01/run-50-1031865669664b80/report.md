## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了 nodeSelector 'aiops.lab/unavailable=true'，但集群中所有节点均无此标签，导致调度器无法匹配任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | phase: Pending | 确认 Pod 当前不可用状态，与 FailedScheduling 结果一致 |
| 2 | K8s Config | nodeSelector | aiops.lab/unavailable=true | 定义 Pod 调度约束，所有节点均无此标签 |
| 3 | K8s Event | default-scheduler | FailedScheduling: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" | 确认调度失败直接原因是不匹配 nodeSelector |
| 4 | K8s State | pod.condition | PodScheduled=False, reason=Unschedulable, message同上 | 确认调度条件未满足，支持节点不匹配结论 |

证据表明：Pod 处于 Pending 状态，K8s 调度器（default-scheduler）明确指出因节点不匹配 `aiops.lab/unavailable=true` 标签导致 0/3 节点可用。节点状态条件也证实调度失败，且该失败模式持续存在（事件发生次数达 x20 over 101m）。Metric 数据仅反映 Pod 仍处于 Pending 阶段，未提供额外资源争用信息；Logging/Tracing 因容器未启动且工具执行受限而无数据。所有维度一致指向标签不匹配导致的调度失败，无冲突或补充现象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector 'aiops.lab/unavailable=true' → 调度器无法匹配节点 → Pod 被挂起(Pending) → 用户不可见 Pod 运行状态
```

### 根因结论

已确认根因：Pod 配置了 `nodeSelector: aiops.lab/unavailable=true`，而集群所有 3 个节点均缺少该标签，导致调度器无法将 Pod 调度到任何节点。

证据支持：
- K8s 事件和状态直接指出节点不匹配 nodeSelector（#1, #2, #3, #4）
- 该现象持续存在（事件 x20 over 101m）

结论可信度高，无需更多证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.3s
├─ 并发证据采集: 52.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 52.1s (Evidence 46.9s, RCA 5.1s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- 未调用 Runbook
