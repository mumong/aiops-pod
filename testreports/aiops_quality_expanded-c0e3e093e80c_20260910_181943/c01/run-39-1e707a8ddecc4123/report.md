## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 持续处于 Pending 状态，未分配到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | fact-bc64011bfb37 | Pod `workload-68c557d875-gtzc8` status: Pending | 证实 Pod 处于持续不可用状态 |
| 2 | K8s Event | fact-023722712af2 | Warning `FailedScheduling`：3 个节点均不满足 Pod 的节点亲和性/选择器要求 (0/3 nodes are available) | 明确调度失败的具体机制 |
| 3 | Metric | fact-40416a41dd45 | `kube_pod_status_phase` 状态为 `Running` 的样本值为 `0` | 证实 Pod 从未成功进入运行状态 |
| 4 | K8s Config | fact-310a1247e2b3, fact-60acc9c9d4a1 | 容器请求极低资源：CPU `5m`，内存 `8Mi` | 排除因资源不足导致无法调度的可能性 |

Pod 的 Pending 状态与 FailedScheduling 事件高度一致，且低资源请求进一步证实调度失败是由标签匹配失败而非资源竞争引起。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 NodeSelector 'aiops.lab/unavailable=true' → 集群 3 个节点均无此标签 → 调度器匹配失败 → Pod 持续 Pending
```

### 根因结论

已确认根因为调度器因节点标签不匹配导致无法调度。

事实 `fact-023722712af2` 中的 `FailedScheduling` 事件明确指出，调度器无法找到满足 Pod 节点亲和性/选择器要求的节点（0/3 nodes are available）。结合事实 `fact-310a1247e2b3` 和 `fact-60acc9c9d4a1`，Pod 所需的资源（CPU 5m, Memory 8Mi）极小，排除资源瓶颈。因此，集群节点未配置所需的标签是 Pod 维持 Pending 状态的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 27.4s
├─ 并发证据采集: 556.2s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 556.2s (Evidence 548.6s, RCA 7.5s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
