## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector (事实 ID: `fact-1cf1505c35e8`) | 直接指出调度失败原因：无匹配节点 |
| 2 | K8s Config | kubernetes | Container `app` CPU request: `5m`, limit: `50m` (事实 ID: `fact-01909911e8fa`) | 排除资源资源请求过载导致调度的可能 |
| 3 | K8s State | kubernetes | `Unschedulable` 状态：3 node(s) didn't match Pod's node affinity/selector (事实 ID: `fact-cca81779c6dc`) | 确认调度器判断逻辑与事件日志一致 |
| 4 | K8s State | kubernetes | Pod 持续处于 `Pending` 状态，31m 内重复触发调度失败 (事实 ID: `fact-52a92cd49761`) | 确认异常状态的持续性 |

Kubernetes 状态与事件日志高度一致，均指向节点亲和性/选择器不匹配。由于 Pod 资源请求极低且集群存在可用节点，进一步印证了问题出在硬性拓扑约束而非资源竞争。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 NodeSelector: aiops.lab/unavailable=true → 集群节点 (master, node1, node2) 缺少对应标签 → 调度器 0/3 节点匹配，触发 FailedScheduling → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 配置了节点选择器 (NodeSelector) `aiops.lab/unavailable=true`，而集群内所有节点（共 3 个）均缺少该标签**，导致调度器无法匹配任何节点。
该结论由以下证据支撑：
- 事实 1 和事实 3 显示调度器明确报错 `3 node(s) didn't match Pod's node affinity/selector`，且 `preemption: 0/3 nodes are available`。
- 事实 2 显示资源请求极小，排除了资源不足导致的调度失败。
- 事实 4 确认了该异常状态的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 57.4s
├─ 问题定位: 17.3s
├─ 并发证据采集: 31.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 31.9s (Evidence 25.0s, RCA 6.8s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
