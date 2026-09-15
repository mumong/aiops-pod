## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点CPU资源耗尽（Insufficient cpu） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `default-scheduler` Event | `0/3 nodes are available: 3 Insufficient cpu` (fact-282aa39efce2, fact-79fa2fe2dbc3) | 证明集群所有可用节点均无法提供足够的 CPU 资源 |
| 2 | K8s Config | Pod Specification | CPU Request/Limit: `100k` (fact-042e5608a939, fact-0619dc231470) | 展示 Pod 调度所需的 CPU 门槛 |
| 3 | K8s State | Pod Phase & Condition | `Pending`; `Unschedulable` reason: `0/3 nodes are available: 3 Insufficient cpu` (fact-3253784f91c9, fact-deb15e0de3de) | 确认 Pod 因资源不足长期处于不可调度状态 |
| 4 | Metric | Pod Status (`kube_pod_status_phase`) | `Pending=1` (Running=0) (fact-bd36c3c4a51b) | 从监控指标层面印证 Pod 未进入运行阶段 |

Kubernetes 事件明确显示集群 3 个节点 CPU 资源耗尽（Insufficient cpu），由于存在 `No preemption victims`，导致 Pod 无法抢占资源，处于 Pending 状态。Prometheus 指标仅反映了当前的 Pending 状态，未提供节点级别的历史 CPU 消耗趋势。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有节点 CPU 资源耗尽 → 默认调度器无法找到满足 CPU Request (100k) 的节点 → 触发 Unschedulable 事件 → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为**集群节点 CPU 资源耗尽 (Insufficient cpu)**。
根据事实 #1（fact-282aa39efce2），`default-scheduler` 记录到所有 3 个可用节点均报告 `Insufficient cpu`，且无 preempt victims 可抢占。事实 #3 表明 Pod 因此一直处于 `Pending` 且 `Unschedulable` 状态，这与事实 #4 的监控数据一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.2s
├─ 并发证据采集: 51.9s
│  └─ g1 aiops-case-v01/workload: 51.9s (Evidence 47.6s, RCA 4.2s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
