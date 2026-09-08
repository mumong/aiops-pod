## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in namespace aiops-case-01 is stuck in Pending state with FailedScheduling events. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | status: `Pending` | 确定 Pod 当前停留在调度阶段，未完成启动 |
| 2 | K8s Event | `event.message` | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 提供调度的直接失败原因及集群节点数量（3个） |
| 3 | K8s Config | `container.resource_request.cpu` | `app`: `5m` | 排除 CPU 资源耗尽导致的调度失败 |
| 4 | K8s Config | `container.resource_request.memory` | `app`: `8Mi` | 排除内存资源耗尽导致的调度失败 |
| 5 | Metric | `kube_pod_status_phase` | 值: `1`, labels: `phase: Pending` | 从观测层面确认 Pod 持续处于 Pending 状态，排除 Unknown 状态波动 |

**证据关联说明：**
1. Pod 当前状态（#1）与调度失败事件（#2）高度一致。
2. 尽管 CPU 和内存请求量极低（#3、#4），调度仍然失败，证明瓶颈不在资源计算，而在其他过滤条件（如标签）。
3. 事件明确指出“0/3 nodes are available”是由于“didn't match Pod's node affinity/selector”（#2），这直接指向了配置层面的选择器不匹配。
4. 度量数据（#5）持续确认 Pending 状态，排除了瞬时波动或状态不一致的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 node_selector 'aiops.lab/unavailable=true' → 调度器匹配集群节点标签 → 集群中 3 个节点均不存在该标签 → 调度器拒绝分配任何节点 → Pod 保持在 Pending 状态并产生 FailedScheduling 事件
```

### 根因结论

已确认的根因是：**Pod 的 `node_selector` 设置了一个在集群中不存在的标签 `aiops.lab/unavailable=true`。**

该配置直接导致 Kubernetes 调度器在遍历集群内的所有可用节点时，无法找到任何节点满足调度条件。结合 `FailedScheduling` 事件明确指出的“0/3 nodes are available”及“didn't match Pod's node affinity/selector”原因，以及资源请求（5m CPU, 8Mi Memory）远未触及集群瓶颈的事实，可以判定该调度策略配置错误是 Pod 无法调度的决定性原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 43.9s (Evidence 35.6s, RCA 8.2s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
