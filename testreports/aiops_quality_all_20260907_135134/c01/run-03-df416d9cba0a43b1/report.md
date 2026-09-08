## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 处于 Pending 状态，未被调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling` 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 确认调度失败原因，明确是节点亲和性/选择器不匹配 |
| 2 | K8s Config | kubernetes | Pod 定义了节点选择器 `aiops.lab/unavailable=true` | 确认 Pod 侧存在强制调度约束条件 |
| 3 | K8s Config | kubernetes | 容器资源配置：CPU request `5m` / limit `50m`，Memory request `8Mi` / limit `32Mi` | 提供调度上下文，资源请求量极小，非资源不足导致调度失败 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 (样本数: 1, trend_evaluable: false) | 指标确认 Pod 持续处于 Pending 状态 |

证据链通过 K8s 事件与配置直接关联：Pod 配置了严格的节点选择器约束（`aiops.lab/unavailable=true`），导致集群内所有节点均不满足调度条件（事件确认 3/3 节点不匹配）。Metric 仅作为 Pod 持续处于 Pending 状态的外部观测印证，因采集单样本无趋势分析价值。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中包含 Node-Selector: aiops.lab/unavailable=true → 集群中无节点满足该标签选择器条件 → 调度器执行 FailedScheduling，无法分配节点 → Pod 保持 Pending 状态
```

### 根因结论

**已确认根因**：Pod 的节点选择器（Node-Selector）配置为 `aiops.lab/unavailable=true`，与集群实际拓扑不符。

该根因直接解释了 `FailedScheduling` 事件（证据 #1、#2）。集群内 3 个节点均未标记该标签，导致调度器判定无可用节点。此配置层面的逻辑约束是造成 Pod 处于 Pending 状态的唯一原因，无需依赖日志或链路追踪进行验证。

---

## 📊 性能统计

```text
├─ 总耗时: 54.2s
├─ 问题定位: 15.8s
├─ 并发证据采集: 31.2s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 31.2s (Evidence 24.7s, RCA 6.3s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
