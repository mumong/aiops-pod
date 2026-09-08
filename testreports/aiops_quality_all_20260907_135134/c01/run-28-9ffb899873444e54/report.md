## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in aiops-case-01 remains in Pending state with FailedScheduling events |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-4a376b9962f2, fact-56f759c7b684) | `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 直接症状：调度器判定集群中所有节点均不满足 Pod 的选择器要求 |
| 2 | K8s State | kubernetes (fact-fb5ce1f8fe05) | `PodScheduled: False`，消息同上 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认 Pod 长期处于 `Unschedulable` 状态 |
| 3 | Metric | prometheus (fact-8e94c0b58a2b) | `kube_pod_status_phase{phase="Pending"}` = `1` | 状态指标印证 Pod 卡在 Pending 阶段 |
| 4 | K8s Config | kubernetes (fact-69dedd02d09e) | `container.app.memory` request = `8Mi` | 排除内存资源不足的可能性 |
| 5 | K8s Config | kubernetes (fact-ae78a778261e) | `container.app.cpu` request = `5m` | 排除 CPU 资源不足的可能性 |

**证据分析**
1. **排除资源瓶颈**：容器请求资源极低（5m CPU, 8Mi 内存），而调度失败信息指出是“3个节点都不匹配”，且抢占（Preemption）被判定为无帮助，说明失败原因非资源不足，而是标签/选择器不匹配。
2. **确认节点不匹配**：K8s Event 和 Pod Condition 一致显示 3 个节点（即整个集群规模）均无法匹配 Pod 的 `node affinity/selector`。结合资源配置极低的事实，故障根因指向 Node Selector 或 Node Affinity 配置错误（如要求的标签不存在于任何节点）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 定义了不存在的节点标签要求（nodeSelector/Affinity） → 调度器遍历全集群 3 个节点均无法匹配标签 → 所有节点被调度器拒绝（FailedScheduling） → Pod 持续保持 Pending 状态，无法正常启动
```

### 根因结论

**已确认根因：Pod 调度失败（FailedScheduling），由于节点选择器（Node Selector）或亲和性规则与集群节点标签不匹配。**

*   证据 `fact-4a376b9962f2` 和 `fact-fb5ce1f8fe05` 明确显示，集群中所有 3 个节点均因不匹配 Pod 的 `node affinity/selector` 而被调度器拒绝。
*   由于资源请求量（CPU 5m, Memory 8Mi）远低于一般节点阈值（见证据 4, 5），且抢占机制无效，排除了资源不足导致的调度失败。
*   根本原因在于 Pod 的调度约束要求了特定标签，但该标签在集群的任何节点上均未找到（即“标签错配”）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.1s
├─ 并发证据采集: 32.2s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 32.2s (Evidence 25.0s, RCA 7.1s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
