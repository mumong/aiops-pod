## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 处于 Pending 状态，持续 22 分钟未调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `PodScheduled=False`, `reason=Unschedulable`, `message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认 Pod 处于 Pending 状态的直接原因：调度器无法找到匹配节点。 |
| 2 | K8s Event | `event.message` | `FailedScheduling`, `3 node(s) didn't match Pod's node affinity/selector` | 记录调度失败的 Warning 事件，确认亲和性/选择器匹配失败。 |
| 3 | Metric | `kube_pod_status_phase` | `phase=Pending`, `value=1` | 验证 Pod 状态从监控维度确认未进入 Running 状态。 |

上述 K8s 事件与状态事实互相印证，一致指向调度亲和性（Affinity/Selector）匹配失败，且 Metric 确认了该持续状态。因容器未启动，无 Logging/Tracing 证据，根因需依赖 K8s 配置事实与事件推断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 指定了 nodeSelector `aiops.lab/unavailable=true` → 集群 3 个节点均无该标签 → 调度器匹配 0/3 节点，触发 FailedScheduling → Pod 持续 Pending 状态
```

### 根因结论

- **已确认根因**：Pod 定义了 `nodeSelector`（`aiops.lab/unavailable=true`），但集群所有节点（master, node1, node2）均未配置该标签（事实 1, 2）。这导致调度器无法将 Pod 调度至任何节点，引发 `Pending` 状态。
- **支持证据**：`FailedScheduling` 事件与 `Unschedulable` 条件明确指出了“未匹配亲和性/选择器”这一机制（证据 #1, #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.8s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 38.3s (Evidence 30.4s, RCA 7.8s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
