## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了节点选择器约束 aiops.lab/unavailable=true，但集群中所有节点均不匹配该标签，导致调度器无法分配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-6993b5f37b31) | 明确调度器因节点选择器不匹配拒绝调度，直接指向集群状态与 Pod 约束冲突。 |
| 2 | K8s State | `kubernetes` | `pod.status: Pending` (fact-04528153cc3d) | 确认 Pod 处于挂起状态，符合被调度器拒绝后的生命周期状态。 |
| 3 | Metric | `prometheus` | `kube_pod_status_phase=1 (phase: Pending)` (fact-5dbf9fde64a9) | 从指标层面独立印证 Pod 当前为 Pending 状态。 |

调度器事件（#1）与 Pod 状态（#2、#3）高度一致：因 3 个节点均不匹配 Pod 的亲和性/选择器，导致 Pod 持续处于 Pending 状态。Logging 和 Tracing 维度因 Pod 未启动且工具访问受限，未提供补充业务日志或调用链事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了节点选择器约束（aiops.lab/unavailable=true） → 集群无节点满足该标签约束 → 调度器返回 FailedScheduling → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 调度失败（FailedScheduling）**。
证据链表明：Pod 定义了特定标签的选择器约束，而集群中所有可用节点均不满足该约束。这导致调度器无法分配计算资源，Pod 维持在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 54.2s
├─ 问题定位: 17.3s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 30.5s (Evidence 25.2s, RCA 5.1s)
└─ 汇总总结: 6.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
