## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 的资源请求（memory requests）被错误设置为 1Pi，该值远超集群所有节点的可用内存上限（最大约 32Gi），导致调度器在所有节点上因 Insufficient memory 拒绝调度，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | 44m/33m: Warning FailedScheduling; 0/3 nodes are available: 3 Insufficient memory. | 证实调度器在所有 3 个节点因内存不足拒绝调度 |
| 2 | K8s Config | kubernetes | container `app` requests.memory = 1Pi (fact-107b9b60eb01) | 识别出导致 Insufficient memory 的异常请求源 |
| 3 | K8s Config | kubernetes | container `app` limits.memory = 1Pi (fact-fc78c41a1e19) | 确认容器配置的完整资源限制均为 1Pi |
| 4 | K8s State | kubernetes | Pod `aiops-case-v02/workload` status: Pending, PodScheduled=False, Unschedulable (fact-07ce9bce2a10) | 展示 Pod 当前处于不可调度的失败状态 |
| 5 | Metric | prometheus | kube_pod_status_phase=1 (Pending), sample_count=1 (fact-ca8fc401dd00) | 确认集群观测中该 Pod 持续处于 Pending 阶段 |

**证据说明：**
K8s Event (#1) 和 Pod 状态 (#4) 共同指向调度失败；配置事实 (#2, #3) 揭示了拒绝原因：1Pi 的请求量级远超集群节点可用内存，导致所有节点资源检查均不满足条件。Metric (#5) 作为独立维度确认了 Pending 状态的持续性。Logging 和 Tracing 因容器未启动无数据，但不影响基于 K8s 内部调度逻辑的判定。

## 🎯 根因分析 · g1

### 因果链

```text
容器 requests.memory 被错误设置为 1Pi (fact-107b9b60eb01) → 远超节点可用内存上限 → 3/3 节点返回 Insufficient memory 且无抢占机会 (fact-a485c401c767) → Pod 持续 Pending (fact-add12aac18b5)
```

### 根因结论

已确认根因：Pod `aiops-case-v02/workload` 的容器资源请求 `requests.memory` 被错误设置为 `1Pi`（1 Pebibyte）。

这一配置直接导致调度器在所有 3 个节点上计算剩余内存时判定为 `Insufficient memory`。由于 `1Pi` 远超集群节点的物理内存上限，节点无法通过抢占（Preemption）机制释放足够资源，从而在 `FailedScheduling` 事件中返回“3 No preemption victims found”。这直接导致 Pod 的 `PodScheduled` 条件保持为 `False`，Pod 持续处于 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.5s
├─ 并发证据采集: 72.9s
│  └─ g1 aiops-case-v02/workload: 72.9s (Evidence 64.5s, RCA 8.3s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
