## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群中全部3个节点的CPU资源不足（Insufficient cpu），导致调度器无法为Pod分配节点，且无可用资源进行预emption。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (pod.condition) | 类型 `PodScheduled` 状态 `False`；原因 `Unschedulable`；消息 `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 确认 Pod 无法被调度到 3 个节点，且未发生预emption |
| 2 | K8s Config | kubernetes (container.resource_request.cpu) | 容器 `app` CPU 请求值 `100k` (0.1 core) | 确认调度器需要寻找具有至少 0.1 core 可用 CPU 的节点 |
| 3 | K8s Event | kubernetes (event.message) | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu.` (17m) | 验证集群整体 CPU 资源不足，确认调度失败现象 |

*证据相互印证：K8s Event 和 Pod Condition 状态均一致指出 3 个节点均无法满足 CPU 调度需求，且无预emption 空间，证实集群层面资源枯竭。*

## 🎯 根因分析 · g1

### 因果链

```text
集群整体CPU资源枯竭 → 调度器无法满足Pod CPU请求 → FailedScheduling (Insufficient cpu) → Pod处于Pending状态
```

### 根因结论

已确认的根因是集群中全部 3 个节点的 CPU 资源不足（Insufficient cpu），导致调度器无法为 Pod `aiops-case-v01/workload` 分配节点。该现象已通过 `fact-6a6ded4202a4` (Pod 调度条件失败) 和 `fact-2fbce5fc60ee` / `fact-c1cf7056f22e` (FailedScheduling 事件) 证实。由于所有节点资源均无法满足 `100k` CPU 请求且无预emption 机制触发，Pod 持续处于 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.5s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v01/workload: 35.6s (Evidence 29.2s, RCA 6.3s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
