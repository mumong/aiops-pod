## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod 配置了 1Pi (Pebibyte) 的内存限制与请求，远超集群节点可用内存，导致调度器在所有 3 个节点上因 Insufficient memory 拒绝调度且无预emption 空间。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `type: PodScheduled, status: False, reason: Unschedulable, message: 0/3 nodes are available: 3 Insufficient memory` | 展示 Pod 当前调度失败的直接状态与错误原因 |
| 2 | K8s Event | event.message | `FailedScheduling ... 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` | 提供调度器判定无法调度的具体日志证据 |
| 3 | K8s Config | container.resource_limit.memory | `value: 1Pi` | 揭示导致资源不足的根本配置错误 |
| 4 | K8s Config | container.resource_request.memory | `value: 1Pi` | 确认内存请求量同样高达 1Pi，排除了仅请求过高但限制较低的情况 |
| 5 | Metric | kube_pod_status_phase | `labels: {phase: Pending}, value: 1` | 从监控指标层面确认 Pod 长期处于 Pending 状态 |

**证据说明：**
*   **配置与现象的关联**：证据 3 和 4 显示容器 `app` 同时设置了 1Pi 的内存请求和限制，这是一个远超常规节点可用内存的数值。
*   **调度器日志的印证**：证据 1 和 2 明确指出调度器在所有 3 个节点上都因为 `Insufficient memory` 拒绝了 Pod，且没有发现可用于抢占的受害者。这直接证明了 1Pi 内存需求是导致调度失败的唯一物理瓶颈。
*   **监控数据的侧面确认**：证据 5 的 Pending 计数与 K8s 状态完全一致，确认了故障的持续状态。Logging 和 Tracing 因容器未启动而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存资源配置错误 (1Pi) → 调度器评估所有节点内存不足 → 调度器拒绝分配且无预emption 空间 → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 资源配置错误**。
具体表现为 `aiops-case-v02/workload` 中的容器 `app` 将 `resources.limits.memory` 和 `resources.requests.memory` 均设置为 `1Pi`（Pebibyte）。这一数值远超集群中任何单节点的可用内存，导致 `default-scheduler` 在尝试调度时，在所有 3 个节点上都因 `Insufficient memory` 而失败（证据 #1, #2, #3, #4）。由于没有足够的资源可被抢占，Pod 无法被调度到任何节点，从而维持在 `Pending` 状态（证据 #1, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 31.3s
├─ 并发证据采集: 34.3s
│  └─ g1 aiops-case-v02/workload: 34.3s (Evidence 27.3s, RCA 6.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
