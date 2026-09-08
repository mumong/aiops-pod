## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod配置了nodeSelector 'aiops.lab/unavailable=true'，但集群所有节点均未设置此标签，导致调度器无法匹配任何可用节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `PodScheduled` status: `False`, reason: `Unschedulable`, message: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认 Pod 停留在 `Pending` 阶段的直接原因是调度失败 |
| 2 | K8s Event | event.message | `FailedScheduling` (重复出现，如 fact-09a189586976, fact-21e6c1b41ae1 等)，明确指向 `node(s) didn't match Pod's node affinity/selector` | 提供调度失败的精确时间分布与原因 |
| 3 | K8s Config | 输入描述信息 | Pod 配置了 `nodeSelector 'aiops.lab/unavailable=true'` | 解释 selector 不匹配的来源依据 |
| 4 | Metric | kube_pod_status_phase | `Pending`=1, `Running`=0 (fact-dd30d38b6b17, fact-10a13661c8a7) | 辅助验证 Pod 未进入运行状态 |

证据表说明：
K8s 维度中的 `PodScheduled` 条件（#1）与 `FailedScheduling` 事件（#2）高度一致，均指明节点因无法匹配 `node affinity/selector` 而被排除。结合已配置的 `nodeSelector`（#3），可以推断集群节点缺乏匹配标签是导致调度不可行的直接原因。Metric 数据（#4）仅提供了 Pod 当前未运行这一非特异性佐证，无进一步区分度。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec定义nodeSelector: aiops.lab/unavailable=true → 集群节点(master, node1, node2)均无该标签 → 调度器判定0/3节点匹配，触发FailedScheduling事件 → Pod状态持续为Pending
```

### 根因结论

已确认的根因是 **Pod 的 `nodeSelector` 标签策略与集群节点实际标签不匹配**。
具体而言，目标 Pod `workload-68c557d875-llhkh` 强制要求节点必须带有 `aiops.lab/unavailable=true` 标签（事实 #3），但集群中所有 3 个节点均未设置该标签。这导致 Kubernetes 调度器在尝试分配资源时，无法找到任何符合亲和性要求的节点，从而反复抛出 `FailedScheduling` 事件（事实 #1, #2），使 Pod 始终处于 `Pending` 状态（事实 #4）。现有 Kubernetes 事件和配置信息已充分证实此因果关系，无需 Logging 或 Tracing 数据补充。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 16.3s
├─ 并发证据采集: 566.4s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 566.4s (Evidence 559.3s, RCA 6.9s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
