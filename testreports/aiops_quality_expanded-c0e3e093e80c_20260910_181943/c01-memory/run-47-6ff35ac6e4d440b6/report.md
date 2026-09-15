## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient memory (x8 over 68m) | 提供持续发生 68 分钟的调度失败证据，确认全节点内存不足 |
| 2 | K8s State | Pod Condition | PodScheduled=False, reason=Unschedulable, message: 3 Insufficient memory, 0/3 nodes have preemption victims | 证实 Pod 卡在 Pending 状态，且预emption 机制失效 |
| 3 | K8s Config | Limits (fact-72a66b966ac1) | container `app` memory limit = 1Pi | 展示极端异常的资源申请值，作为导致 Insufficient memory 的直接事实 |
| 4 | K8s Config | Requests (fact-d282e3b09f44) | container `app` memory request = 1Pi | 确认调度器需保留同等规模的内存，导致无法通过 |
| 5 | Metric | kube_pod_status_phase | Pending=1 (sample_count=1, trend_evaluable=false) | 确认 Pod 当前状态确认为 Pending，且因单样本无趋势 |

证据 1、2 从事件和状态两面确认了“3/3 节点内存不足”及“无抢占受害者”的失败机制；证据 3、4 提供了导致内存不足的具体配置事实（1Pi）。由于 Pod 未启动，Logging 和 Tracing 不可用，缺乏运行时的进一步证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 资源配置错误 (limits.memory=1Pi) → 调度器评估节点资源不足 (可用内存 << 1Pi) → 调度器返回 FailedScheduling (3 Insufficient memory) → Pod 持续 Pending
```

### 根因结论

已确认根因为 **Pod 配置了极端的内存上限 `1Pi`（约 1024 PiB），远超集群节点实际内存上限**，导致调度器在所有 3 个节点上均因 `Insufficient memory` 失败且无法抢占。
该结论由事实 `fact-72a66b966ac1`（1Pi limit）与事实 `fact-3bc0c178a76c`（3/3 节点 Insufficient memory）共同支撑。缺少集群节点可用内存上限的 Metric 证据，但配置事实已构成充分且确定的失败条件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 24.1s
├─ 并发证据采集: 52.9s
│  └─ g1 aiops-case-v02/workload: 52.9s (Evidence 45.9s, RCA 6.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
