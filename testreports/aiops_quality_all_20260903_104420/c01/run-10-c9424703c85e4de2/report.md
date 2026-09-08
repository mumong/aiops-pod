## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了节点选择器 `aiops.lab/unavailable=true`，但集群中所有节点均未包含该标签，导致调度器无法匹配可用节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes/fact-44122e666061 | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 确认调度失败直接原因：所有节点无法匹配节点选择器 |
| 2 | K8s Config | kubernetes/fact-12a23ce9699b | `container.resource_request.cpu`: `5m` | 排除 CPU 资源不足导致的调度失败 |
| 3 | K8s State | kubernetes/fact-c2fe1649a7a1 | `PodScheduled`: `False` (reason: `Unschedulable`) | 状态机印证 Pod 处于持续不可调度状态 |
| 4 | Metric | prometheus/fact-31c602afd64a | `kube_pod_status_phase`: `1` (phase: `Pending`) | 确认 Pod 状态持续为 Pending，无流转至其他阶段 |
| 5 | Metric | prometheus/fact-24a63d9ab7bf | `kube_pod_status_phase`: `0` (phase: `Unknown`) | 排除 Pod 因未知状态导致的不确定性，确认稳定处于 Pending |

**证据说明：**
Kubernetes 事件记录（#1）与 Pod 状态（#3）直接指向节点选择器不匹配这一确定性原因，且排除了抢占策略（Preemption）的可行性。资源请求配置（#2）极小，排除了资源竞争因素。Prometheus 指标（#4, #5）确认了 Pod 状态稳定处于 `Pending` 且未发生状态突变，佐证了该配置问题是持续性故障而非瞬时网络或调度抖动。Logging 与 Tracing 因 Pod 未启动被判定为不适用，但现有 Kubernetes 维度的证据已形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
配置节点选择器 `aiops.lab/unavailable=true` (K8s Config) → 调度器无法匹配任何节点 (K8s Event) → 触发 FailedScheduling 且抢占失败 (K8s Event) → Pod 持续处于 Pending 状态 (K8s State/Metric)
```

### 根因结论

已确认的根因是 Pod 配置了集群中不存在的标签选择器 `aiops.lab/unavailable=true`。
- 事实依据：K8s Event (`fact-44122e666061`) 明确报告 `3 node(s) didn't match Pod's node affinity/selector`，且 `preemption` 亦不可用。
- 排除其他因素：资源配置 (`fact-12a23ce9699b`) 极低且无资源争用迹象；Metric 数据 (`fact-31c602afd64a`) 确认状态稳定，非瞬时故障。
- 完整性说明：Logging 与 Tracing 因 Pod 未启动被系统判定为 `not_applicable`，但不影响基于调度器日志和状态机的事实结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.8s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 45.3s (Evidence 41.0s, RCA 4.2s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
