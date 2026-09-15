## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod resource limit memory (1Pi) exceeds available capacity on all nodes (Insufficient memory) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 45m default-scheduler 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` (fact-12e37f215886) | 确认调度器因内存不足在所有 3 个节点上均调度失败，且无抢占资源。 |
| 2 | K8s State | kubernetes | `PodScheduled` 条件状态 `False`，消息同上 (fact-3a6092c17c91) | 确认 Pod 当前处于不可调度状态。 |
| 3 | K8s Config | kubernetes | 容器 `app` 设置 `memory` 请求及限制均为 `1Pi` (fact-081ff90a1d21, fact-2f209bbbef13) | 证明调度失败的根本原因是配置的 1Pi 资源超出了集群所有可用节点的处理能力。 |
| 4 | K8s State | kubernetes | `phase` 为 `Pending` (fact-54ade962d9c9) | 确认 Pod 停滞在挂起阶段，未进入运行态。 |
| 5 | Metric | prometheus | `kube_pod_status_phase` 值为 `1`，标签 `phase="Pending"`，单样本无法评估趋势 (fact-acdb7c2c1a6f) | 外部监控数据印证 Pod 当前状态为 Pending，排除了其他状态的可能性。 |

**证据分析：**
所有 Kubernetes 事件与状态事实均一致指向“Insufficient memory”这一单一原因。配置事实明确指出了 1Pi 这一极端资源请求量。Metrics 数据仅用于确认当前状态，无额外趋势证据。由于容器未启动，Logging 与 Tracing 维度为 `not_applicable`，这符合预期，不影响根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存资源请求/限制配置过高 (1Pi) → 调度器检查节点可用内存发现不匹配 (Insufficient memory) → 3/3 节点无法调度且无抢占候选 (FailedScheduling) → Pod 进入 Pending 状态
```

### 根因结论

**已确认的根因：** Pod 资源限制（memory 1Pi）超出了集群所有节点（3个节点）的可用容量，导致调度器无法为其分配节点。

该结论由以下证据链支撑：
1.  **直接配置证据**：容器 `app` 的 `resource_request` 和 `resource_limit` 均设置为 `1Pi`（事实 #3）。
2.  **直接失败机制**：K8s Event 和 Condition 明确报告 `0/3 nodes are available: 3 Insufficient memory` 且无预emption 可能（事实 #1, #2）。
3.  **状态确认**：Pod 处于 `Pending` 且 `PodScheduled` 为 `False`（事实 #2, #4），Metric 数据同样确认了 `Pending` 状态（事实 #5）。

没有证据表明存在节点故障、网络隔离或其他资源竞争问题，集群调度失败完全由资源配置不当导致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.7s
├─ 并发证据采集: 32.1s
│  └─ g1 aiops-case-v02/workload: 32.1s (Evidence 28.0s, RCA 4.1s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
