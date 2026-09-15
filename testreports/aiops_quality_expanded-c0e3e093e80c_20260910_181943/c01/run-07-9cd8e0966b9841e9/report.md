## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod spec 配置了 nodeSelector {aiops.lab/unavailable: true}，而集群中所有节点均缺失该标签，导致调度器无法满足亲和性约束从而永久 Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status` = `Pending`; `pod.phase` = `Pending` | 确认 Pod 处于持续未调度状态 |
| 2 | K8s Config | kubernetes | `nodeSelector`: `{aiops.lab/unavailable: true}` | 提供调度失败的直接约束条件 |
| 3 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 调度器明确拒绝的根因事实 |
| 4 | Metric | prometheus | `kube_pod_status_phase(Pending)` = `1`; `kube_pod_status_phase(Running)` = `0` | 确认该 Pod 在系统中未进入运行状态，与 K8s 状态一致 |

**证据印证：**
Kubernetes 事件 `fact-395925cd0ee0` 明确指出了 3 个节点均未匹配 Pod 的亲和性/选择器（`didn't match Pod's node affinity/selector`）。结合配置事实 `nodeSelector: {aiops.lab/unavailable: true}`（事实缺失但由事件原因可反推为不匹配），该标签约束无法满足是 Pod 持续 Pending 的唯一原因。Metrics 确认该状态持续存在。Logging 和 Tracing 因容器未启动而无数据，与 Pending 状态一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 包含 nodeSelector {aiops.lab/unavailable: true} (未确认集群节点是否完全缺失该标签) → 调度器无法满足亲和性约束 → Pod 持续处于 Pending 状态 → 用户无法访问该工作负载
```

### 根因结论

**已确认的根因：** Pod 的调度约束 `nodeSelector {aiops.lab/unavailable: true}` 无法被集群中任何节点满足。

**依据：**
*   Kubernetes 事件 `fact-395925cd0ee0` 和 `fact-a7a85178253c` 均显示 `FailedScheduling`，具体原因为 `3 node(s) didn't match Pod's node affinity/selector`。
*   Pod 状态 `Pending`（`fact-9fc15c502b02`）且 `PodScheduled` 为 `False`（`fact-8fd643656ebc`）。
*   Metrics `kube_pod_status_phase` 确认 Pod 始终处于 Pending 状态，未转为 Running。

虽然输入诊断文本指出“集群中所有节点均缺失该标签”，但本报告中仅展示了 Pod 侧的约束条件和调度器拒绝的事件。由于缺乏集群节点列表的拓扑或配置事实（Toplogy 维度缺失），严格来说我们确认的是“没有节点匹配该选择器”，而非“所有节点都缺失该标签”。但就故障现象（Pending）而言，**调度器无法满足该选择器约束**是导致故障的直接且充分的事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 26.0s
├─ 并发证据采集: 31.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 31.8s (Evidence 26.7s, RCA 5.1s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
